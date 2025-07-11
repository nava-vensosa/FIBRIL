#!/usr/bin/env python3
"""
FIBRIL Main Entry Point

Complete FIBRIL system implementation:
- Listens on port 1761 for MaxMSP OSC messages  
- Updates system state based on incoming rank data
- Runs FIBRIL algorithm to allocate voices
- Sends voice data to port 8998
- Real-time processing with configurable buffer time
"""

import asyncio
import logging
import time
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

# Import FIBRIL components
import fibril_init
import fibril_algorithms

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FibrilMain:
    """Main FIBRIL system controller"""
    
    def __init__(self):
        # FIBRIL system components
        self.system = fibril_init.fibril_system
        
        # Network components
        self.osc_server = None
        self.osc_client = SimpleUDPClient("127.0.0.1", 8998)
        
        # Processing state
        self.last_process_time = 0
        self.process_interval = 0.220  # 220ms processing interval
        self.previous_state = None
        
        # Setup OSC dispatcher
        self.dispatcher = Dispatcher()
        self._setup_osc_handlers()
        
        logger.info("FIBRIL Main System initialized")
    
    def _setup_osc_handlers(self):
        """Setup OSC message handlers for different message types"""
        
        # Handle rank grey code bits (e.g., /R1_1000, /R2_0100, etc.)
        self.dispatcher.map("/R*", self._handle_rank_message)
        
        # Handle global parameters
        self.dispatcher.map("/sustain", self._handle_sustain)
        self.dispatcher.map("/keyCenter", self._handle_key_center)
        
        # Default handler for unknown messages
        self.dispatcher.set_default_handler(self._handle_unknown_message)
    
    def _handle_rank_message(self, address: str, *args):
        """Handle rank-related OSC messages"""
        try:
            if '_' not in address:
                return
                
            parts = address.split('_')
            rank_part = parts[0]
            
            # Extract rank number (e.g., /R1 -> 1, /R2 -> 2)
            if not rank_part.startswith('/R'):
                return
                
            rank_num = int(rank_part[2:])  # Remove '/R' prefix
            parameter = parts[1]
            value = args[0] if args else 0
            
            # Handle grey code bits
            if parameter in ['1000', '0100', '0010', '0001']:
                bit_value = 1 if value else 0
                self.system.update_rank_grey_bit(rank_num, parameter, bit_value)
                logger.debug(f"Updated rank {rank_num} bit {parameter} = {bit_value}")
            
            # Handle rank position
            elif parameter == 'pos':
                self.system.update_rank_position(rank_num, int(value))
                logger.debug(f"Updated rank {rank_num} position = {value}")
                
        except Exception as e:
            logger.error(f"Error handling rank message {address}: {e}")
    
    def _handle_sustain(self, address: str, *args):
        """Handle sustain pedal messages"""
        try:
            value = args[0] if args else 0
            self.system.sustain = int(value)
            logger.debug(f"Updated sustain = {value}")
        except Exception as e:
            logger.error(f"Error handling sustain message: {e}")
    
    def _handle_key_center(self, address: str, *args):
        """Handle key center messages"""
        try:
            value = args[0] if args else 0
            self.system.key_center = int(value)
            logger.debug(f"Updated key center = {value}")
        except Exception as e:
            logger.error(f"Error handling key center message: {e}")
    
    def _handle_unknown_message(self, address: str, *args):
        """Handle unknown OSC messages"""
        logger.debug(f"Unknown OSC message: {address} {args}")
    
    def _get_current_state(self):
        """Get a snapshot of current system state for comparison"""
        return {
            'sustain': self.system.sustain,
            'key_center': self.system.key_center,
            'ranks': [
                {
                    'number': rank.number,
                    'position': rank.position,
                    'grey_code': rank.grey_code.copy(),
                    'gci': rank.gci,
                    'density': rank.density,
                    'tonicization': rank.tonicization
                }
                for rank in self.system.ranks
            ]
        }
    
    def _has_state_changed(self, current_state):
        """Check if current state differs from previous state"""
        if self.previous_state is None:
            return True  # First time, always process
        
        # Check global parameters
        if (current_state['sustain'] != self.previous_state['sustain'] or
            current_state['key_center'] != self.previous_state['key_center']):
            return True
        
        # Check each rank
        for curr_rank, prev_rank in zip(current_state['ranks'], self.previous_state['ranks']):
            if (curr_rank['position'] != prev_rank['position'] or
                curr_rank['grey_code'] != prev_rank['grey_code'] or
                curr_rank['gci'] != prev_rank['gci'] or
                curr_rank['density'] != prev_rank['density'] or
                curr_rank['tonicization'] != prev_rank['tonicization']):
                return True
        
        return False
    
    def _process_algorithm(self):
        """Run the FIBRIL algorithm and send voice updates"""
        try:
            # Get current state
            current_state = self._get_current_state()
            
            # Only process if state has actually changed
            if self._has_state_changed(current_state):
                
                # Print current system state (only when processing)
                self.system.print_system_state()
                
                # Clear previous voices if sustain is off
                if not self.system.sustain:
                    fibril_algorithms.deallocate_all_voices()
                
                # Run probabilistic voice allocation
                result = fibril_algorithms.probabilistic_voice_allocation(max_voices=8)
                
                # Send all voice states to MaxMSP (always send all voices to ensure consistency)
                for voice in self.system.voices:
                    self._send_voice_update(voice.id, voice.midi_note, voice.volume)
                
                # Log allocation results
                if result['allocated'] > 0:
                    active_voices = len(fibril_algorithms.get_active_midi_notes())
                    logger.info(f"Probabilistic allocation: {result['allocated']}/{result['target']} voices, {active_voices} total active")
                
                # Update state tracking
                self.previous_state = current_state
                self.last_process_time = time.time()
                
        except Exception as e:
            logger.error(f"Error in algorithm processing: {e}")
            import traceback
            traceback.print_exc()
    
    def _send_voice_update(self, voice_id: int, midi_note: int, volume: bool):
        """Send voice update to MaxMSP via OSC"""
        try:
            address = f"/voice_{voice_id}"
            volume_int = 1 if volume else 0
            
            self.osc_client.send_message(address, [midi_note, volume_int])
            self.osc_client.send_message(f"{address}_MIDI", midi_note)
            self.osc_client.send_message(f"{address}_Volume", volume_int)
            
            logger.debug(f"Sent {address}: MIDI={midi_note}, Volume={volume_int}")
            
        except Exception as e:
            logger.error(f"Error sending voice update: {e}")
    
    def start_server(self):
        """Start the OSC server on port 1761"""
        try:
            self.osc_server = ThreadingOSCUDPServer(("127.0.0.1", 1761), self.dispatcher)
            logger.info("FIBRIL server listening on 127.0.0.1:1761, sending to 127.0.0.1:8998")
            self.osc_server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            if self.osc_server:
                self.osc_server.shutdown()
                logger.info("Server stopped")
    
    async def start_processing_loop(self):
        """Start the algorithm processing loop"""
        logger.info(f"Starting processing loop (interval: {self.process_interval*1000:.0f}ms)")
        
        try:
            while True:
                self._process_algorithm()
                await asyncio.sleep(0.050)  # Check every 50ms, but only process when needed
        except Exception as e:
            logger.error(f"Processing loop error: {e}")
    
    async def run_system(self):
        """Run the complete FIBRIL system"""
        logger.info("Starting FIBRIL System...")
        
        # Start the processing loop in the background
        processing_task = asyncio.create_task(self.start_processing_loop())
        
        # Start OSC server (this will block)
        try:
            # Run server in executor to make it non-blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.start_server)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            processing_task.cancel()
            logger.info("FIBRIL System stopped")


def main():
    """Main entry point"""
    try:
        fibril_main = FibrilMain()
        asyncio.run(fibril_main.run_system())
    except KeyboardInterrupt:
        logger.info("System interrupted by user")
    except Exception as e:
        logger.error(f"System error: {e}")


if __name__ == "__main__":
    main()
