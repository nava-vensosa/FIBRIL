#!/usr/bin/env python3
"""
FIBRIL Main Entry Point

This is the main file to run the complete FIBRIL system.
It initializes all components and starts the UDP listener for MaxMSP communication.

Usage:
    python fibril_main.py
"""

import asyncio
import sys
import logging
import argparse
from typing import Optional

# Import FIBRIL components
from fibril_init import FibrilSystem
from fibril_udp import UDPHandler
from fibril_algorithms import FibrilAlgorithm
from fibril_classes import SystemState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FibrilMain:
    """Main FIBRIL system orchestrator"""
    
    def __init__(self, listen_port: int = 1761, send_port: int = 1762):
        self.listen_port = listen_port
        self.send_port = send_port
        
        # Initialize system components
        logger.info("Initializing FIBRIL system...")
        self.fibril_system = FibrilSystem()
        self.algorithm = FibrilAlgorithm()
        
        # Create system state from initialized components
        self.system_state = SystemState(
            ranks=self.fibril_system.ranks,
            voices=self.fibril_system.voices,
            sustain=False,
            key_center=0  # C major
        )
        
        # Initialize UDP handler
        self.udp_handler = UDPHandler(
            message_processor=self.process_message,
            listen_port=listen_port,
            send_port=send_port,
            system_state=self.system_state
        )
        
        logger.info("FIBRIL system initialized successfully")
        logger.info(f"Listening on port {listen_port}, sending to port {send_port}")
        logger.info(f"Total ranks: {len(self.system_state.ranks)}")
        logger.info(f"Total voices: {len(self.system_state.voices)}")
    
    def process_message(self, message: dict) -> Optional[dict]:
        """
        Process incoming OSC message from MaxMSP and return response
        
        Args:
            message: Parsed OSC message containing rank updates, sustain, key changes, etc.
            
        Returns:
            dict: Response message with voice allocations, or None if no change
        """
        try:
            # Update system state based on message
            state_changed = self._update_system_state(message)
            
            if not state_changed:
                return None
            
            # Run FIBRIL algorithm to allocate voices
            logger.debug("Running FIBRIL algorithm...")
            new_state = self.algorithm.allocate_voices(self.system_state)
            
            # Update our system state
            self.system_state = new_state
            
            # Generate response message for MaxMSP
            response = self._generate_voice_response()
            
            logger.info(f"Generated response with {len([v for v in self.system_state.voices if v.volume])} active voices")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None
    
    def _update_system_state(self, message: dict) -> bool:
        """
        Update system state based on incoming OSC message
        
        Returns:
            bool: True if state changed, False otherwise
        """
        state_changed = False
        
        # Handle rank updates from OSC messages like '/R3_0100'
        if message.get('type') == 'rank_update':
            rank_number = message.get('rank_number')
            bit_pattern = message.get('bit_pattern')
            value = message.get('value')
            
            if rank_number and bit_pattern and value is not None:
                if 1 <= rank_number <= 8:
                    rank = self.system_state.ranks[rank_number - 1]
                    
                    # Store previous GCI for voice leading
                    rank.previous_gci = rank.gci
                    
                    # Update the specific bit based on the pattern
                    bit_map = {'1000': 0, '0100': 1, '0010': 2, '0001': 3}
                    if bit_pattern in bit_map:
                        bit_index = bit_map[bit_pattern]
                        old_grey_code = rank.grey_code.copy()
                        
                        # Set the specific bit (1 if value > 0, 0 otherwise)
                        rank.grey_code[bit_index] = 1 if value > 0 else 0
                        
                        # Recalculate GCI and density
                        rank.__post_init__()
                        
                        if old_grey_code != rank.grey_code:
                            logger.info(f"Rank {rank_number} bit {bit_pattern} -> {value}: "
                                      f"GCI={rank.gci}, density={rank.density}, "
                                      f"grey_code={rank.grey_code}")
                            state_changed = True
        
        # Handle sustain pedal updates
        elif message.get('address') == '/sustain':
            old_sustain = self.system_state.sustain
            self.system_state.sustain = bool(message.get('value', 0))
            if old_sustain != self.system_state.sustain:
                logger.info(f"Sustain pedal: {'ON' if self.system_state.sustain else 'OFF'}")
                state_changed = True
        
        # Handle key center updates
        elif message.get('address') == '/key_center':
            old_key = self.system_state.key_center
            self.system_state.key_center = int(message.get('value', 0)) % 12
            if old_key != self.system_state.key_center:
                logger.info(f"Key center changed to: {self.system_state.key_center}")
                state_changed = True
        
        # Legacy support for direct updates (for testing)
        if 'sustain' in message:
            old_sustain = self.system_state.sustain
            self.system_state.sustain = bool(message['sustain'])
            if old_sustain != self.system_state.sustain:
                logger.info(f"Sustain pedal: {'ON' if self.system_state.sustain else 'OFF'}")
                state_changed = True
        
        if 'key_center' in message:
            old_key = self.system_state.key_center
            self.system_state.key_center = int(message['key_center']) % 12
            if old_key != self.system_state.key_center:
                logger.info(f"Key center changed to: {self.system_state.key_center}")
                state_changed = True
        
        if 'ranks' in message:
            for rank_data in message['ranks']:
                rank_number = rank_data.get('number')
                grey_code = rank_data.get('grey_code')
                
                if rank_number and grey_code and 1 <= rank_number <= 8:
                    rank = self.system_state.ranks[rank_number - 1]
                    old_grey_code = rank.grey_code.copy()
                    rank.grey_code = grey_code
                    
                    # This will trigger recalculation of GCI and density
                    rank.__post_init__()
                    
                    if old_grey_code != rank.grey_code:
                        logger.info(f"Rank {rank_number} updated: GCI={rank.gci}, density={rank.density}")
                        state_changed = True
        
        return state_changed
    
    def _generate_voice_response(self) -> dict:
        """Generate response message for MaxMSP with current voice allocations"""
        voice_data = []
        
        for voice in self.system_state.voices:
            voice_data.append({
                'id': voice.id,
                'midi_note': voice.midi_note,
                'volume': 1 if voice.volume else 0
            })
        
        return {
            'voices': voice_data,
            'active_count': sum(1 for v in self.system_state.voices if v.volume),
            'timestamp': asyncio.get_event_loop().time()
        }
    
    async def run(self):
        """Start the FIBRIL system"""
        logger.info("Starting FIBRIL system...")
        
        try:
            # Start UDP handler
            await self.udp_handler.start()
            logger.info("FIBRIL system is running. Press Ctrl+C to stop.")
            
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down FIBRIL system...")
        except Exception as e:
            logger.error(f"Error running FIBRIL system: {e}")
        finally:
            # Cleanup
            if self.udp_handler:
                await self.udp_handler.stop()
            logger.info("FIBRIL system stopped")


def main():
    """Command line entry point"""
    parser = argparse.ArgumentParser(description='FIBRIL 48-Voice Allocation System')
    parser.add_argument('--listen-port', type=int, default=1761,
                        help='UDP port to listen for MaxMSP messages (default: 1761)')
    parser.add_argument('--send-port', type=int, default=1762,
                        help='UDP port to send voice data to MaxMSP (default: 1762)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run FIBRIL system
    fibril_main = FibrilMain(
        listen_port=args.listen_port,
        send_port=args.send_port
    )
    
    try:
        asyncio.run(fibril_main.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
