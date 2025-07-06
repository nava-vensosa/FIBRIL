#!/usr/bin/env python3
"""
FIBRIL Main Entry Point

This is the main file to run the complete FIBRIL system.
It initializes all components and starts the UDP listener for MaxMSP communication.

Usage:
    python fibril_main.py
"""

import time
import threading
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
    
    def __init__(self, listen_port: int = 1761, send_port: int = 8998):
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
            key_center=60  # Middle C (MIDI note 60)
        )
        
        # Initialize UDP handler for rank messages (port 1761)
        self.udp_handler = UDPHandler(
            message_processor=self.process_message,
            listen_port=listen_port,
            send_port=send_port,
            system_state=self.system_state
        )
        
        # Initialize second UDP handler for sustain/keyCenter messages (port 1762)
        self.control_udp_handler = UDPHandler(
            message_processor=self.process_control_message,
            listen_port=1762,
            send_port=send_port,
            system_state=self.system_state
        )
        
        # Buffer timing and state tracking
        self.buffer_time = 0.018  # 18ms buffer as specified
        self.last_state_hash = None
        self.pending_state_change = False
        self.last_buffer_time = 0
        self.state_change_pending = False
        self.buffer_task = None
        
        # Voice change tracking for efficient OSC updates
        self.previous_voice_states = {}  # voice_id -> {'midi': int, 'volume': bool}
        
        logger.info("FIBRIL system initialized successfully")
        logger.info(f"Listening on port {listen_port}, sending to port {send_port}")
        logger.info(f"18ms buffer enabled for state processing")
        
        # Display initial system state
        self.display_system_state()
    
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
            
            # Mark that we have a pending state change
            self.state_change_pending = True
            
            # Check if we should process immediately (buffer time has passed)
            current_time = time.time()
            time_since_last_buffer = current_time - self.last_buffer_time
            
            if time_since_last_buffer >= self.buffer_time:
                logger.debug("Buffer time exceeded, processing immediately")
                return self._process_buffered_state_change()
            else:
                # Schedule buffer processing if not already scheduled
                if self.buffer_task is None or not self.buffer_task.is_alive():
                    remaining_time = self.buffer_time - time_since_last_buffer
                    self.buffer_task = threading.Timer(remaining_time, self._delayed_buffer_processing)
                    self.buffer_task.start()
                    logger.debug(f"State change buffered, will process in {remaining_time:.3f}s")
                
                return None  # Don't send response yet, wait for buffer
                
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
        
        # Handle rank priority updates from OSC messages like '/R1_priority', '/R2_priority', etc.
        elif message.get('type') == 'rank_priority':
            rank_number = message.get('rank_number')
            priority = message.get('priority')
            
            if rank_number and priority is not None:
                if 1 <= rank_number <= 8:
                    rank = self.system_state.ranks[rank_number - 1]
                    old_priority = rank.priority
                    rank.priority = int(priority)
                    
                    if old_priority != rank.priority:
                        logger.info(f"Rank {rank_number} priority updated: {old_priority} -> {rank.priority}")
                        state_changed = True
        
        # Handle rank tonicization updates from OSC messages like '/R1_tonicization', '/R2_tonicization', etc.
        elif message.get('type') == 'rank_tonicization':
            rank_number = message.get('rank_number')
            tonicization = message.get('tonicization')
            
            if rank_number and tonicization is not None:
                if 1 <= rank_number <= 8:
                    rank = self.system_state.ranks[rank_number - 1]
                    old_tonicization = rank.tonicization
                    rank.tonicization = int(tonicization)
                    
                    if old_tonicization != rank.tonicization:
                        logger.info(f"Rank {rank_number} tonicization updated: {old_tonicization} -> {rank.tonicization}")
                        state_changed = True
        
        # Handle sustain pedal updates
        elif message.get('address') == '/sustain':
            old_sustain = self.system_state.sustain
            self.system_state.sustain = bool(message.get('value', 0))
            if old_sustain != self.system_state.sustain:
                logger.info(f"Sustain pedal: {'ON' if self.system_state.sustain else 'OFF'}")
                state_changed = True
        
        # Handle key center updates
        elif message.get('address') == '/keyCenter' or message.get('type') == 'key_center':
            # Get the value from either format
            new_key_center = message.get('value') if message.get('type') == 'key_center' else message.get('value')
            
            if new_key_center is not None:
                old_key = self.system_state.key_center
                self.system_state.key_center = int(new_key_center)  # Full MIDI value, not modulo 12
                if old_key != self.system_state.key_center:
                    logger.info(f"Key center changed from MIDI {old_key} to MIDI {self.system_state.key_center}")
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
            self.system_state.key_center = int(message['key_center'])  # Full MIDI value
            if old_key != self.system_state.key_center:
                logger.info(f"Key center changed from MIDI {old_key} to MIDI {self.system_state.key_center}")
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
        changed_voices = []
        
        for voice in self.system_state.voices:
            current_midi = voice.midi_note
            current_volume = bool(voice.volume)
            voice_id = voice.id
            
            # Check if this voice has changed since last time
            previous_state = self.previous_voice_states.get(voice_id, {})
            previous_midi = previous_state.get('midi', None)
            previous_volume = previous_state.get('volume', None)
            
            midi_changed = previous_midi != current_midi
            volume_changed = previous_volume != current_volume
            
            # Only include voices that have changed
            if midi_changed or volume_changed:
                voice_data.append({
                    'id': voice_id,
                    'midi_note': current_midi,
                    'volume': 1 if current_volume else 0,
                    'midi_changed': midi_changed,
                    'volume_changed': volume_changed
                })
                changed_voices.append(voice_id)
            
            # Update our tracking
            self.previous_voice_states[voice_id] = {
                'midi': current_midi,
                'volume': current_volume
            }
        
        # Log changes if any
        if changed_voices:
            logger.debug(f"Voice changes detected for voices: {changed_voices}")
        
        return {
            'voices': voice_data,
            'active_count': sum(1 for v in self.system_state.voices if v.volume),
            'changed_count': len(changed_voices),
            'timestamp': time.time()
        }
    
    def run(self):
        """Start the FIBRIL system"""
        logger.info("Starting FIBRIL system...")
        
        try:
            # Initialize buffer timing
            self.last_buffer_time = time.time()
            
            # Start UDP handler
            self.udp_handler.start()
            logger.info("FIBRIL system is running. Press Ctrl+C to stop.")
            logger.info("18ms input buffer active for smooth state processing")
            
            # Keep running until interrupted
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down FIBRIL system...")
        except Exception as e:
            logger.error(f"Error running FIBRIL system: {e}")
        finally:
            # Cleanup buffer task
            if self.buffer_task and self.buffer_task.is_alive():
                self.buffer_task.cancel()
            
            # Cleanup UDP handler
            if self.udp_handler:
                self.udp_handler.stop()
            logger.info("FIBRIL system stopped")
    
    def _delayed_buffer_processing(self):
        """Process buffer after delay (called by threading.Timer)"""
        if self.state_change_pending:
            response = self._process_buffered_state_change()
            if response:
                # Send the response through UDP handler
                self.udp_handler._send_response(response)
    
    def _process_buffered_state_change(self) -> Optional[dict]:
        """Process accumulated state changes after buffer period"""
        if not self.state_change_pending:
            return None
            
        try:
            # Run FIBRIL algorithm to allocate voices
            logger.debug("Running FIBRIL algorithm (buffered)...")
            new_state = self.algorithm.allocate_voices(self.system_state)
            
            # Update our system state
            self.system_state = new_state
            
            # Generate response message for MaxMSP
            response = self._generate_voice_response()
            
            # Update buffer timing
            self.last_buffer_time = time.time()
            self.state_change_pending = False
            
            active_voice_count = len([v for v in self.system_state.voices if v.volume])
            logger.info(f"Generated buffered response with {active_voice_count} active voices")
            
            # Display updated system state
            self.display_system_state()
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing buffered state change: {e}")
            self.state_change_pending = False
            return None
    
    def display_system_state(self):
        """Display current system state in formatted output"""
        print("\n" + "=" * 80)
        print("FIBRIL SYSTEM STATE")
        print("=" * 80)
        
        # Display voices FIRST
        print("\nVOICES:")
        print("ID  | MIDI | Volume")
        print("----|------|-------")
        for voice in self.system_state.voices:
            volume_str = "ON " if voice.volume else "OFF"
            print(f"{voice.id:3d} | {voice.midi_note:4d} | {volume_str}")
        
        # Display ranks SECOND
        print("\nRANKS:")
        print("Number | Priority | Grey Code    | GCI | Density | Tonicization")
        print("-------|----------|--------------|-----|---------|-------------")
        for rank in self.system_state.ranks:
            grey_str = f"[{','.join(map(str, rank.grey_code))}]"
            print(f"  {rank.number:2d}   |    {rank.priority:2d}    | {grey_str:12s} | {rank.gci:3d} |   {rank.density:2d}    |      {rank.tonicization:2d}")
        
        # Display active notes THIRD (sorted from lowest to highest)
        active_notes = []
        for voice in self.system_state.voices:
            if voice.volume:
                active_notes.append(voice.midi_note)
        
        active_notes.sort()  # Sort from lowest to highest
        
        print(f"\nACTIVE NOTES ({len(active_notes)}):")
        if active_notes:
            note_names = [self._midi_to_note_name(midi) for midi in active_notes]
            print(" ".join(note_names))
        else:
            print("(none)")
        
        # Display system parameters FOURTH
        print(f"\nSYSTEM PARAMETERS:")
        print(f"Key Center: MIDI {self.system_state.key_center} ({self._midi_to_note_name(self.system_state.key_center)})")
        print(f"Sustain: {'ON' if self.system_state.sustain else 'OFF'}")
        print("=" * 80)

    def _midi_to_note_name(self, midi_note: int) -> str:
        """Convert MIDI note to note name (e.g., 60 -> C4)"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = midi_note // 12 - 1
        note = note_names[midi_note % 12]
        return f"{note}{octave}"

    def process_control_message(self, message: dict) -> Optional[dict]:
        """
        Process incoming control messages (sustain, keyCenter) from port 1762
        
        Args:
            message: Parsed OSC message containing sustain or keyCenter updates
            
        Returns:
            dict: Response message with voice allocations, or None if no change
        """
        try:
            # Update system state based on control message
            state_changed = self._update_control_state(message)
            
            if not state_changed:
                return None
            
            # Mark that we have a pending state change
            self.state_change_pending = True
            
            # Check if we should process immediately (buffer time has passed)
            current_time = time.time()
            time_since_last_buffer = current_time - self.last_buffer_time
            
            if time_since_last_buffer >= self.buffer_time:
                logger.debug("Buffer time exceeded, processing control change immediately")
                return self._process_buffered_state_change()
            else:
                # Schedule buffer processing if not already scheduled
                if self.buffer_task is None or not self.buffer_task.is_alive():
                    remaining_time = self.buffer_time - time_since_last_buffer
                    self.buffer_task = threading.Timer(remaining_time, self._delayed_buffer_processing)
                    self.buffer_task.start()
                    logger.debug(f"Control change buffered, will process in {remaining_time:.3f}s")
                
                return None  # Don't send response yet, wait for buffer
                
        except Exception as e:
            logger.error(f"Error processing control message: {e}")
            return None
    
    def _update_control_state(self, message: dict) -> bool:
        """
        Update system state based on incoming control OSC message (sustain, keyCenter)
        
        Returns:
            bool: True if state changed, False otherwise
        """
        state_changed = False
        
        # Handle sustain pedal updates
        if message.get('address') == '/sustain':
            old_sustain = self.system_state.sustain
            self.system_state.sustain = bool(message.get('value', 0))
            if old_sustain != self.system_state.sustain:
                logger.info(f"Sustain pedal: {'ON' if self.system_state.sustain else 'OFF'}")
                state_changed = True
        
        # Handle key center updates - note the different case
        elif message.get('address') == '/keyCenter':
            old_key = self.system_state.key_center
            self.system_state.key_center = int(message.get('value', 0)) % 12
            if old_key != self.system_state.key_center:
                logger.info(f"Key center changed to: {self.system_state.key_center}")
                state_changed = True
        
        return state_changed

def main():
    """Command line entry point"""
    parser = argparse.ArgumentParser(description='FIBRIL 48-Voice Allocation System')
    parser.add_argument('--listen-port', type=int, default=1761,
                        help='UDP port to listen for MaxMSP messages (default: 1761)')
    parser.add_argument('--send-port', type=int, default=8998,
                        help='UDP port to send voice data to MaxMSP (default: 8998)')
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
        fibril_main.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
