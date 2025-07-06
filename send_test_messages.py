#!/usr/bin/env python3

import socket
import struct
import time

def encode_string(s):
    data = s.encode('utf-8') + b'\x00'
    while len(data) % 4 != 0:
        data += b'\x00'
    return data

def encode_int(value):
    return struct.pack('>i', value)

def send_priority_message(rank_num: int, priority: int, target_port: int = 1761):
    """Send a rank priority update message to FIBRIL"""
    try:
        address = f"/R{rank_num}_priority"
        
        msg = b''
        msg += encode_string(address)
        msg += b',i\x00\x00'  # Type tag for integer
        msg += encode_int(priority)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(msg, ('127.0.0.1', target_port))
        sock.close()
        
        print(f"✅ Sent priority message: Rank {rank_num} -> Priority {priority}")
        
    except Exception as e:
        print(f"❌ Error sending priority message: {e}")

def send_bit_message(rank_num: int, bit_pattern: str, value: int, target_port: int = 1761):
    """Send a rank bit pattern message to FIBRIL"""
    try:
        address = f"/R{rank_num}_{bit_pattern}"
        
        msg = b''
        msg += encode_string(address)
        msg += b',i\x00\x00'  # Type tag for integer
        msg += encode_int(value)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(msg, ('127.0.0.1', target_port))
        sock.close()
        
        print(f"✅ Sent bit message: Rank {rank_num} {bit_pattern} -> {value}")
        
    except Exception as e:
        print(f"❌ Error sending bit message: {e}")

if __name__ == "__main__":
    print("Sending test messages to FIBRIL...")
    time.sleep(1)  # Give a moment for any previous operations
    
    # Test priority updates
    print("\n=== Testing Priority Updates ===")
    send_priority_message(1, 5)
    time.sleep(0.1)
    send_priority_message(2, 3)
    time.sleep(0.1)
    send_priority_message(3, 7)
    time.sleep(0.1)
    
    # Test some bit patterns to see the state
    print("\n=== Testing Bit Pattern Updates ===")
    send_bit_message(1, "0001", 1)
    time.sleep(0.1)
    send_bit_message(2, "0010", 1)
    time.sleep(0.1)
    
    print("\nTest messages sent. Check FIBRIL terminal for responses.")
