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

def send_message(address: str, value: int, target_port: int = 1761):
    """Send a message to FIBRIL"""
    try:
        msg = b''
        msg += encode_string(address)
        msg += b',i\x00\x00'  # Type tag for integer
        msg += encode_int(value)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(msg, ('127.0.0.1', target_port))
        sock.close()
        
        print(f"✅ Sent: {address} -> {value}")
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")

if __name__ == "__main__":
    print("Testing FIBRIL with key center and rank updates...")
    time.sleep(1)
    
    # Test key center change to F# (MIDI 66)
    print("\n=== Testing Key Center Change ===")
    send_message("/keyCenter", 66)
    time.sleep(0.5)
    
    # Test priority updates
    print("\n=== Testing Priority Updates ===")
    send_message("/R1_priority", 3)
    time.sleep(0.1)
    send_message("/R2_priority", 1)
    time.sleep(0.1)
    send_message("/R3_priority", 5)
    time.sleep(0.1)
    
    # Test some bit patterns to create density
    print("\n=== Testing Density Changes ===")
    send_message("/R1_0001", 1)  # Low density
    time.sleep(0.2)
    send_message("/R2_0010", 1)  # Medium density
    time.sleep(0.2)
    send_message("/R2_0001", 1)  # Increase R2 density
    time.sleep(0.2)
    
    # Now reduce density to test voice clearing
    print("\n=== Testing Density Reduction ===")
    send_message("/R2_0010", 0)  # Reduce R2 density
    time.sleep(0.2)
    send_message("/R2_0001", 0)  # Turn off R2 completely
    time.sleep(0.2)
    
    # Test key center change to C (MIDI 72 = C5)
    print("\n=== Testing Another Key Center Change ===")
    send_message("/keyCenter", 72)
    time.sleep(0.5)
    
    print("\nTest sequence complete. Check FIBRIL terminal output.")
