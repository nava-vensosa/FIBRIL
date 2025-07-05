#!/usr/bin/env python3
"""
FIBRIL UDP Handler

UDP communication for FIBRIL system:
- Listens on port 1761 for MaxMSP OSC messages
- Sends voice data to port 1762 
- 18ms input buffer
- Updates rank and voice objects from fibril-init.py
"""

import asyncio
import socket
import time
import logging
import json
from typing import Callable, Optional, Dict, Any

# Import FIBRIL components
from fibril_classes import SystemState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UDPHandler:
    """Handles UDP communication with MaxMSP"""
    
    def __init__(self, message_processor: Callable, listen_port: int = 1761, 
                 send_port: int = 1762, system_state: SystemState = None):
        self.message_processor = message_processor
        self.listen_port = listen_port
        self.send_port = send_port
        self.listen_socket = None
        self.send_socket = None
        self.system_state = system_state
        self.running = False
    
    async def start(self):
        """Start UDP listener and sender"""
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.bind(("127.0.0.1", self.listen_port))
        self.listen_socket.setblocking(False)
        
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.setblocking(False)
        
        self.running = True
        logger.info(f"UDP Handler listening on port {self.listen_port}, sending to {self.send_port}")
        
        # Start the listening loop
        await self._listen_loop()
    
    async def stop(self):
        """Stop UDP handler"""
        self.running = False
        if self.listen_socket:
            self.listen_socket.close()
        if self.send_socket:
            self.send_socket.close()
        logger.info("UDP Handler stopped")
    
    async def _listen_loop(self):
        """Main listening loop for UDP messages"""
        loop = asyncio.get_event_loop()
        
        while self.running:
            try:
                # Check for incoming data
                data, addr = await loop.sock_recvfrom(self.listen_socket, 1024)
                
                if data:
                    # Parse message (assuming JSON for now, can be adapted for OSC)
                    try:
                        message = json.loads(data.decode('utf-8'))
                        logger.debug(f"Received message from {addr}: {message}")
                        
                        # Process message
                        response = self.message_processor(message)
                        
                        # Send response if we have one
                        if response:
                            await self._send_response(response)
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON received from {addr}: {data}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                
            except socket.error:
                # No data available, continue
                await asyncio.sleep(0.001)  # 1ms sleep
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                break
    
    async def _send_response(self, response: Dict[Any, Any]):
        """Send response to MaxMSP"""
        try:
            response_data = json.dumps(response).encode('utf-8')
            loop = asyncio.get_event_loop()
            await loop.sock_sendto(self.send_socket, response_data, ("127.0.0.1", self.send_port))
            logger.debug(f"Sent response: {len(response_data)} bytes")
        except Exception as e:
            logger.error(f"Error sending response: {e}")
        
        while True:
            try:
                data, addr = await asyncio.get_event_loop().sock_recvfrom(
                    self.listen_socket, 1024
                )
                await self.process_message(data)
            except Exception as e:
                logger.error(f"Listener error: {e}")
                await asyncio.sleep(0.001)
    
    async def process_message(self, data: bytes):
        """Process incoming OSC message and update system state silently"""
        try:
            address, value = self._decode_osc(data)
            
            # Update system state without logging (silent updates)
            # Handle rank grey code bits (e.g., /R1_1000, /R2_0100, etc.)
            if address.startswith('/R') and '_' in address:
                parts = address.split('_')
                rank_num = int(parts[0][2:])  # Extract rank number (R1 -> 1, R2 -> 2, etc.)
                bit_pattern = parts[1]
                
                if bit_pattern in ['1000', '0100', '0010', '0001']:
                    # Convert value to 0 or 1 (handle any non-zero as 1)
                    bit_value = 1 if value else 0
                    # Update silently - no print statements
                    rank = self.system.get_rank(rank_num)
                    bit_map = {'1000': 0, '0100': 1, '0010': 2, '0001': 3}
                    bit_index = bit_map[bit_pattern]
                    rank.grey_code[bit_index] = bit_value
                    rank.__post_init__()  # Recalculate GCI and density
            
            # Handle rank positions (e.g., /R1_pos, /R2_pos, etc.)
            elif address.startswith('/R') and address.endswith('_pos'):
                rank_num = int(address[2:address.find('_')])
                rank = self.system.get_rank(rank_num)
                rank.position = value
            
            # Handle global parameters
            elif address == '/sustain':
                self.system.sustain = value
                
            elif address == '/keyCenter':
                self.system.key_center = value
            
            # Don't trigger buffer processing for each message
            # The buffer will process on its own 18ms timer
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
    
    def _decode_osc(self, data: bytes) -> tuple:
        """Simple OSC message decoder"""
        try:
            # Find address (ends with null byte)
            addr_end = data.find(b'\x00')
            if addr_end == -1:
                return "", 0
                
            address = data[:addr_end].decode('utf-8')
            
            # Skip to data section (aligned to 4 bytes)
            data_start = (addr_end + 4) & ~0x03
            
            # Find type tags (usually ",i" for integer)
            tag_end = data.find(b'\x00', data_start)
            if tag_end == -1:
                return address, 0
                
            data_start = (tag_end + 4) & ~0x03
            
            # Extract integer value (big-endian)
            if len(data) >= data_start + 4:
                value = int.from_bytes(data[data_start:data_start+4], 'big', signed=True)
            else:
                value = 0
            
            return address, value
            
        except Exception as e:
            logger.error(f"OSC decode error: {e}")
            return "", 0
    
    async def send_voice(self, voice_id: int, midi_note: int, volume: bool):
        """Send voice data to MaxMSP on port 1762"""
        try:
            address = f"/voice_{voice_id}"
            message = self._encode_osc(address, midi_note, int(volume))
            
            await asyncio.get_event_loop().sock_sendto(
                self.send_socket, message, ("127.0.0.1", 1762)
            )
            
            logger.debug(f"Sent voice {voice_id}: MIDI={midi_note}, Volume={volume}")
            
        except Exception as e:
            logger.error(f"Send error: {e}")
    
    def _encode_osc(self, address: str, midi: int, volume: int) -> bytes:
        """Simple OSC message encoder for voice data"""
        # Address with null padding
        addr_bytes = address.encode('utf-8') + b'\x00'
        addr_padded = addr_bytes + b'\x00' * ((4 - len(addr_bytes) % 4) % 4)
        
        # Type tags for two integers
        type_tags = b",ii\x00"
        
        # Data (MIDI note and volume as integers)
        data = midi.to_bytes(4, 'big', signed=True) + volume.to_bytes(4, 'big', signed=True)
        
        return addr_padded + type_tags + data
    
    def close(self):
        """Close sockets"""
        if self.listen_socket:
            self.listen_socket.close()
        if self.send_socket:
            self.send_socket.close()


class InputBuffer:
    """220ms timer-based processor"""
    
    def __init__(self, processor: Callable):
        self.processor = processor
        self.buffer_time = 0.220  # 220ms
        self.running = False
    
    async def process_buffer(self):
        """Process system state every 220ms regardless of input"""
        self.running = True
        logger.info("Input buffer started - processing every 220ms")
        
        while self.running:
            try:
                # Wait exactly 180ms
                await asyncio.sleep(self.buffer_time)
                
                # Process current system state
                await self.processor()
                
            except Exception as e:
                logger.error(f"Buffer error: {e}")
                await asyncio.sleep(0.001)
    
    def stop(self):
        """Stop the buffer processor"""
        self.running = False


class FibrilUDP:
    """Main FIBRIL UDP controller"""
    
    def __init__(self):
        self.udp_handler = UDPHandler(self._dummy_processor)  # No longer needs message processor
        self.input_buffer = InputBuffer(self._process_buffered_update)
        self.running = False
        
        # Store previous state for change detection
        self.previous_state = None
    
    async def _dummy_processor(self):
        """Dummy processor - not used anymore"""
        pass
    
    async def _process_buffered_update(self):
        """Handle system state update every 180ms"""
        # Get current system state
        current_state = self._get_current_state()
        
        # Check if state has changed
        if self._has_state_changed(current_state):
            # Print current system state (only when changed)
            self.udp_handler.system.print_system_state()
            
            # Run voice allocation algorithm
            await self._run_voice_algorithm()
            
            # Update previous state
            self.previous_state = current_state
    
    def _get_current_state(self):
        """Get a snapshot of current system state for comparison"""
        system = self.udp_handler.system
        return {
            'sustain': system.sustain,
            'key_center': system.key_center,
            'ranks': [
                {
                    'number': rank.number,
                    'position': rank.position,
                    'grey_code': rank.grey_code.copy(),
                    'gci': rank.gci,
                    'density': rank.density
                }
                for rank in system.ranks
            ]
        }
    
    def _has_state_changed(self, current_state):
        """Check if current state differs from previous state"""
        if self.previous_state is None:
            return True  # First time, always print
        
        # Check global parameters
        if (current_state['sustain'] != self.previous_state['sustain'] or
            current_state['key_center'] != self.previous_state['key_center']):
            return True
        
        # Check each rank
        for curr_rank, prev_rank in zip(current_state['ranks'], self.previous_state['ranks']):
            if (curr_rank['position'] != prev_rank['position'] or
                curr_rank['grey_code'] != prev_rank['grey_code'] or
                curr_rank['gci'] != prev_rank['gci'] or
                curr_rank['density'] != prev_rank['density']):
                return True
        
        return False
    
    async def _run_voice_algorithm(self):
        """Example voice allocation algorithm"""
        try:
            # Calculate total system density
            total_density = sum(rank.density for rank in self.udp_handler.system.ranks)
            
            if total_density == 0:
                return  # No active ranks
            
            # Simple algorithm: allocate voices based on active ranks
            voice_id = 1
            base_midi = 60 + self.udp_handler.system.key_center
            
            for rank in self.udp_handler.system.ranks:
                if rank.density > 0:  # Rank is active
                    # Calculate MIDI note based on rank number and key center
                    midi_note = base_midi + (rank.number - 1) * 2
                    
                    # Update voice object
                    if voice_id <= 48:
                        voice = self.udp_handler.system.get_voice(voice_id)
                        voice.midi_note = midi_note
                        voice.volume = True
                        
                        # Send to MaxMSP
                        await self.udp_handler.send_voice(voice_id, midi_note, True)
                        
                        voice_id += 1
            
            # Turn off remaining voices
            for i in range(voice_id, 49):
                voice = self.udp_handler.system.get_voice(i)
                if voice.volume:  # Only update if currently on
                    voice.volume = False
                    await self.udp_handler.send_voice(i, voice.midi_note, False)
            
            logger.debug(f"Voice algorithm processed {voice_id-1} active voices")
            
        except Exception as e:
            logger.error(f"Voice algorithm error: {e}")
    
    async def run(self):
        """Run the UDP handler"""
        self.running = True
        logger.info("Starting FIBRIL UDP Handler")
        
        try:
            await asyncio.gather(
                self.udp_handler.start_listener(),
                self.input_buffer.process_buffer()
            )
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            self.udp_handler.close()


if __name__ == "__main__":
    fibril = FibrilUDP()
    asyncio.run(fibril.run())
