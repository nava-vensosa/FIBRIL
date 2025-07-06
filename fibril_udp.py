#!/usr/bin/env python3
"""
FIBRIL UDP Handler

UDP communication for FIBRIL system:
- Listens on port 1761 for MaxMSP OSC messages
- Sends voice data to port 8998 
- 18ms input buffer
- Updates rank and voice objects from fibril-init.py
"""

import socket
import time
import logging
import json
import struct
import math
import threading
from typing import Callable, Optional, Dict, Any, Union, List, Tuple
from dataclasses import dataclass

# Import pythonosc SimpleUDPClient for sending
from pythonosc.udp_client import SimpleUDPClient

# Import FIBRIL components
from fibril_classes import SystemState

# ============================================================================
# Minimal OSC Implementation (no external dependencies)
# ============================================================================

def pad_to_multiple_of_4(data: bytes) -> bytes:
    """Pad data to multiple of 4 bytes (OSC requirement)"""
    while len(data) % 4 != 0:
        data += b'\x00'
    return data

def encode_string(s: str) -> bytes:
    """Encode string for OSC message"""
    return pad_to_multiple_of_4(s.encode('utf-8') + b'\x00')

def encode_int(value: int) -> bytes:
    """Encode integer for OSC message"""
    return struct.pack('>i', value)

def encode_float(value: float) -> bytes:
    """Encode float for OSC message"""
    return struct.pack('>f', value)

def build_osc_message(address: str, *args) -> bytes:
    """Build an OSC message from address and arguments"""
    # Start with address
    message = encode_string(address)
    
    # Build type tag string
    type_tags = ','
    arg_data = b''
    
    for arg in args:
        if isinstance(arg, int):
            type_tags += 'i'
            arg_data += encode_int(arg)
        elif isinstance(arg, float):
            type_tags += 'f'
            arg_data += encode_float(arg)
        elif isinstance(arg, str):
            type_tags += 's'
            arg_data += encode_string(arg)
        else:
            # Convert to string as fallback
            type_tags += 's'
            arg_data += encode_string(str(arg))
    
    # Add type tags
    message += encode_string(type_tags)
    
    # Add arguments
    message += arg_data
    
    return message

def parse_osc_string(data: bytes, offset: int) -> Tuple[str, int]:
    """Parse OSC string from bytes"""
    # Find null terminator
    null_idx = data.find(b'\x00', offset)
    if null_idx == -1:
        raise ValueError("No null terminator found in OSC string")
    
    # Extract string
    string = data[offset:null_idx].decode('utf-8')
    
    # Calculate next offset (padded to 4-byte boundary)
    next_offset = null_idx + 1
    while next_offset % 4 != 0:
        next_offset += 1
    
    return string, next_offset

def parse_osc_int(data: bytes, offset: int) -> Tuple[int, int]:
    """Parse OSC int from bytes"""
    value = struct.unpack('>i', data[offset:offset+4])[0]
    return value, offset + 4

def parse_osc_float(data: bytes, offset: int) -> Tuple[float, int]:
    """Parse OSC float from bytes"""
    value = struct.unpack('>f', data[offset:offset+4])[0]
    return value, offset + 4

def parse_osc_message(data: bytes) -> Tuple[str, List[Union[str, int, float]]]:
    """Parse an OSC message from bytes"""
    offset = 0
    
    # Parse address
    address, offset = parse_osc_string(data, offset)
    
    # Parse type tags
    type_tags, offset = parse_osc_string(data, offset)
    
    # Parse arguments
    args = []
    for tag in type_tags[1:]:  # Skip the leading comma
        if tag == 's':
            arg, offset = parse_osc_string(data, offset)
            args.append(arg)
        elif tag == 'i':
            arg, offset = parse_osc_int(data, offset)
            args.append(arg)
        elif tag == 'f':
            arg, offset = parse_osc_float(data, offset)
            args.append(arg)
        else:
            # Skip unknown types
            offset += 4
    
    return address, args

# ============================================================================
# End Minimal OSC Implementation
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_osc_message_for_fibril(data: bytes) -> Optional[Dict[str, Any]]:
    """Parse OSC message from MaxMSP into FIBRIL message format"""
    try:
        # Use our generic OSC parser
        address, args = parse_osc_message(data)
        
        # Convert to FIBRIL message format
        message_dict = {'address': address}
        
        # Handle rank messages like '/R3_0100'
        if address.startswith('/R') and '_' in address:
            parts = address[1:].split('_')  # Remove leading '/', split on '_'
            if len(parts) == 2:
                rank_part = parts[0]  # 'R3'
                bit_part = parts[1]   # '0100'
                
                if rank_part.startswith('R') and rank_part[1:].isdigit():
                    rank_number = int(rank_part[1:])
                    
                    # Get the value argument
                    if args and isinstance(args[0], int):
                        value = args[0]
                        
                        message_dict = {
                            'type': 'rank_update',
                            'rank_number': rank_number,
                            'bit_pattern': bit_part,
                            'value': value
                        }
        
        # Handle rank priority messages like '/R1_priority', '/R2_priority', etc.
        elif address.startswith('/R') and address.endswith('_priority'):
            rank_part = address[1:-9]  # Remove '/R' prefix and '_priority' suffix
            if rank_part.startswith('R') and rank_part[1:].isdigit():
                rank_number = int(rank_part[1:])
                
                # Get the priority value argument
                if args and isinstance(args[0], int):
                    priority = args[0]
                    
                    message_dict = {
                        'type': 'rank_priority',
                        'rank_number': rank_number,
                        'priority': priority
                    }
        
        # Handle rank tonicization messages like '/R1_tonicization', '/R2_tonicization', etc.
        elif address.startswith('/R') and address.endswith('_tonicization'):
            rank_part = address[1:-13]  # Remove '/R' prefix and '_tonicization' suffix
            if rank_part.startswith('R') and rank_part[1:].isdigit():
                rank_number = int(rank_part[1:])
                
                # Get the tonicization value argument
                if args and isinstance(args[0], int):
                    tonicization = args[0]
                    
                    message_dict = {
                        'type': 'rank_tonicization',
                        'rank_number': rank_number,
                        'tonicization': tonicization
                    }
        
        # Handle other message types (sustain, key center, etc.)
        elif address == '/sustain':
            if args and isinstance(args[0], int):
                message_dict = {
                    'type': 'sustain',
                    'value': args[0]
                }
        elif address == '/key_center':
            if args and isinstance(args[0], int):
                message_dict = {
                    'type': 'key_center',
                    'value': args[0]
                }
            
        return message_dict
        
    except Exception as e:
        logger.error(f"Error parsing OSC message: {e}")
        return None


def send_osc_messages_simple(client: SimpleUDPClient, response_data: Dict[str, Any]) -> int:
    """Send OSC messages using pythonosc SimpleUDPClient for MaxMSP communication"""
    message_count = 0
    
    try:
        # Send individual voice parameter messages for changed voices
        if 'voices' in response_data:
            for voice in response_data['voices']:
                voice_id = voice['id']
                
                # Send separate messages for MIDI note and volume if they changed
                if voice.get('midi_changed', True):
                    client.send_message(f"/voice_{voice_id}_MIDI", voice['midi_note'])
                    message_count += 1
                    # Optional small delay for message clarity (can be removed if not needed)
                    # time.sleep(0.001)  # 1ms
                
                if voice.get('volume_changed', True):
                    client.send_message(f"/voice_{voice_id}_Volume", 1 if voice['volume'] else 0)
                    message_count += 1
                    # Optional small delay for message clarity (can be removed if not needed)
                    # time.sleep(0.001)  # 1ms
        
        # Send summary message if provided
        if 'active_count' in response_data:
            client.send_message("/active_count", response_data['active_count'])
            message_count += 1
            
        return message_count
        
    except Exception as e:
        logger.error(f"Error sending OSC messages: {e}")
        return 0


def build_osc_response(response_data: Dict[str, Any]) -> List[bytes]:
    """Build OSC messages for sending back to MaxMSP"""
    try:
        # Build individual OSC messages
        messages = []
        
        # Add individual voice parameter messages for changed voices
        if 'voices' in response_data:
            for voice in response_data['voices']:
                voice_id = voice['id']
                
                # Send separate messages for MIDI note and volume if they changed
                if voice.get('midi_changed', True):  # Default to True if not specified
                    midi_msg = build_osc_message(f"/voice_{voice_id}_MIDI", voice['midi_note'])
                    messages.append(midi_msg)
                
                if voice.get('volume_changed', True):  # Default to True if not specified
                    volume_msg = build_osc_message(f"/voice_{voice_id}_Volume", 1 if voice['volume'] else 0)
                    messages.append(volume_msg)
        
        # Add summary message if provided
        if 'active_count' in response_data:
            count_msg = build_osc_message("/active_count", response_data['active_count'])
            messages.append(count_msg)
        
        return messages
        
    except Exception as e:
        logger.error(f"Error building OSC response: {e}")
        return []


class UDPHandler:
    """Handles UDP communication with MaxMSP"""
    
    def __init__(self, message_processor: Callable, listen_port: int = 1761, 
                 send_port: int = 8998, system_state: SystemState = None):
        self.message_processor = message_processor
        self.listen_port = listen_port
        self.send_port = send_port
        self.listen_socket = None
        self.send_socket = None
        self.system_state = system_state
        self.running = False
        
        # Create pythonosc SimpleUDPClient for sending messages to MaxMSP
        self.osc_client = SimpleUDPClient("127.0.0.1", send_port)
    
    def start(self):
        """Start UDP listener in a background thread"""
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.bind(("127.0.0.1", self.listen_port))
        self.listen_socket.settimeout(0.1)  # 100ms timeout for responsiveness
        
        self.running = True
        logger.info(f"UDP Handler listening on port {self.listen_port}, sending to {self.send_port}")
        logger.info("Using pythonosc SimpleUDPClient for message sending to MaxMSP")
        
        # Start the listening loop in a background thread
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
    
    def stop(self):
        """Stop UDP handler"""
        self.running = False
        if self.listen_socket:
            self.listen_socket.close()
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join(timeout=1.0)
        # SimpleUDPClient doesn't need explicit closing
        logger.info("UDP Handler stopped")
    
    def _listen_loop(self):
        """Main listening loop for UDP messages"""
        while self.running:
            try:
                # Check for incoming data
                data, addr = self.listen_socket.recvfrom(1024)
                
                if data:
                    # Parse OSC message
                    try:
                        message = parse_osc_message_for_fibril(data)
                        if message:
                            logger.debug(f"Received OSC message from {addr}: {message}")
                            
                            # Process message
                            response = self.message_processor(message)
                            
                            # Send response if we have one
                            if response:
                                self._send_response(response)
                        else:
                            logger.debug(f"Could not parse OSC message from {addr}")
                            
                    except Exception as e:
                        logger.error(f"Error processing OSC message: {e}")
                        logger.debug(f"Raw data: {data}")
                
            except socket.timeout:
                # No data available, continue
                time.sleep(0.001)  # 1ms sleep
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                break
    
    def _send_response(self, response: Dict[Any, Any]):
        """Send OSC response to MaxMSP using pythonosc SimpleUDPClient"""
        try:
            # Use the simple client for sending - much more reliable
            message_count = send_osc_messages_simple(self.osc_client, response)
            
            if message_count > 0:
                # Print brief UDP message info
                print(f"📤 SENT {message_count} OSC MESSAGES TO MAXMSP (Port {self.send_port})")
                
                if 'active_count' in response:
                    print(f"   Active voices: {response['active_count']}/48")
                if 'changed_count' in response:
                    print(f"   Changed voices: {response['changed_count']}")
                
                logger.debug(f"Sent {message_count} OSC messages via pythonosc SimpleUDPClient to 127.0.0.1:{self.send_port}")
            else:
                logger.warning("No OSC messages were sent (message_count = 0)")
                
        except Exception as e:
            logger.error(f"Error sending OSC response: {e}")
            # Try to recreate the client if there's a connection issue
            try:
                self.osc_client = SimpleUDPClient("127.0.0.1", self.send_port)
                logger.info("Recreated OSC client after error")
            except Exception as recreate_error:
                logger.error(f"Failed to recreate OSC client: {recreate_error}")
