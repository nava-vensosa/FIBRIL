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
from pythonosc import osc_message_builder, osc_bundle_builder
from pythonosc.osc_message import OscMessage
from pythonosc.osc_packet import ParseError
import struct

# Import FIBRIL components
from fibril_classes import SystemState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_osc_message(data: bytes) -> Optional[Dict[str, Any]]:
    """Parse OSC message from MaxMSP into a dictionary"""
    try:
        # Simple OSC parsing for FIBRIL messages
        # OSC messages start with address pattern followed by type tags and arguments
        
        # Find the null terminator for the address
        null_idx = data.find(b'\x00')
        if null_idx == -1:
            return None
            
        address = data[:null_idx].decode('ascii')
        
        # Parse FIBRIL-specific message formats
        message_dict = {'address': address}
        
        # Handle rank messages like '/R3_0100'
        if address.startswith('/R') and '_' in address:
            parts = address[1:].split('_')  # Remove leading '/', split on '_'
            if len(parts) == 2:
                rank_part = parts[0]  # 'R3'
                bit_part = parts[1]   # '0100'
                
                if rank_part.startswith('R') and rank_part[1:].isdigit():
                    rank_number = int(rank_part[1:])
                    
                    # Parse the integer argument (1 or 0)
                    # OSC integers are 4 bytes, big-endian, after type tags
                    try:
                        # Find type tag section (starts after padded address)
                        addr_len = len(address) + 1  # Include null terminator
                        addr_padded_len = (addr_len + 3) & ~3  # Round up to multiple of 4
                        
                        # Type tags start here, should be ",i" for integer
                        type_start = addr_padded_len
                        if type_start < len(data) and data[type_start:type_start+2] == b',i':
                            # Integer argument starts after padded type tags
                            type_len = 2 + 1  # ",i" + null terminator
                            type_padded_len = (type_len + 3) & ~3
                            arg_start = type_start + type_padded_len
                            
                            if arg_start + 4 <= len(data):
                                # Parse 4-byte big-endian integer
                                value = struct.unpack('>i', data[arg_start:arg_start+4])[0]
                                
                                message_dict = {
                                    'type': 'rank_update',
                                    'rank_number': rank_number,
                                    'bit_pattern': bit_part,
                                    'value': value
                                }
                                
                    except (struct.error, IndexError):
                        logger.warning(f"Could not parse OSC integer argument from {address}")
        
        # Handle other message types (sustain, key center, etc.)
        elif address == '/sustain':
            # Similar parsing for sustain messages
            pass
        elif address == '/key_center':
            # Similar parsing for key center messages  
            pass
            
        return message_dict
        
    except Exception as e:
        logger.error(f"Error parsing OSC message: {e}")
        return None


def build_osc_response(response_data: Dict[str, Any]) -> bytes:
    """Build OSC message for sending back to MaxMSP"""
    try:
        # Build OSC bundle with voice data
        bundle_builder = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
        
        # Add individual voice parameter messages for changed voices
        if 'voices' in response_data:
            for voice in response_data['voices']:
                voice_id = voice['id']
                
                # Send separate messages for MIDI note and volume if they changed
                if voice.get('midi_changed', True):  # Default to True if not specified
                    midi_msg = osc_message_builder.OscMessageBuilder(f"/voice_{voice_id}_MIDI")
                    midi_msg.add_arg(voice['midi_note'])
                    bundle_builder.add_content(midi_msg.build())
                
                if voice.get('volume_changed', True):  # Default to True if not specified
                    volume_msg = osc_message_builder.OscMessageBuilder(f"/voice_{voice_id}_Volume")
                    volume_msg.add_arg(1 if voice['volume'] else 0)  # Send as integer (1 or 0)
                    bundle_builder.add_content(volume_msg.build())
        
        # Add summary message if provided
        if 'active_count' in response_data:
            msg_builder = osc_message_builder.OscMessageBuilder("/active_count")
            msg_builder.add_arg(response_data['active_count'])
            bundle_builder.add_content(msg_builder.build())
        
        return bundle_builder.build().dgram
        
    except Exception as e:
        logger.error(f"Error building OSC response: {e}")
        return b''


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
                    # Parse OSC message
                    try:
                        message = parse_osc_message(data)
                        if message:
                            logger.debug(f"Received OSC message from {addr}: {message}")
                            
                            # Process message
                            response = self.message_processor(message)
                            
                            # Send response if we have one
                            if response:
                                await self._send_response(response)
                        else:
                            logger.debug(f"Could not parse OSC message from {addr}")
                            
                    except Exception as e:
                        logger.error(f"Error processing OSC message: {e}")
                        logger.debug(f"Raw data: {data}")
                
            except socket.error:
                # No data available, continue
                await asyncio.sleep(0.001)  # 1ms sleep
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                break
    
    async def _send_response(self, response: Dict[Any, Any]):
        """Send OSC response to MaxMSP"""
        try:
            response_data = build_osc_response(response)
            if response_data:
                loop = asyncio.get_event_loop()
                await loop.sock_sendto(self.send_socket, response_data, ("127.0.0.1", self.send_port))
                
                # Print detailed UDP message info
                print(f"\n📤 SENDING UDP MESSAGE TO MAXMSP (Port {self.send_port}):")
                print(f"   Response data size: {len(response_data)} bytes")
                if 'voices' in response:
                    changed_voices = response['voices']
                    print(f"   Changed voices: {len(changed_voices)}")
                    for voice in changed_voices[:5]:  # Show first 5 changed voices
                        changes = []
                        if voice.get('midi_changed'):
                            changes.append(f"MIDI: {voice['midi_note']}")
                        if voice.get('volume_changed'):
                            changes.append(f"Volume: {1 if voice['volume'] else 0}")
                        change_str = ", ".join(changes)
                        print(f"     /voice_{voice['id']}_* -> {change_str}")
                    if len(changed_voices) > 5:
                        print(f"     ... and {len(changed_voices) - 5} more changed voices")
                if 'changed_count' in response:
                    print(f"   Total changed voices: {response['changed_count']}")
                if 'active_count' in response:
                    print(f"   Total active voices: {response['active_count']}")
                print(f"   Raw OSC data: {response_data[:50].hex()}{'...' if len(response_data) > 50 else ''}")
                print("─" * 60)
                print()  # Extra line break
                
                logger.debug(f"Sent OSC response: {len(response_data)} bytes")
        except Exception as e:
            logger.error(f"Error sending OSC response: {e}")

