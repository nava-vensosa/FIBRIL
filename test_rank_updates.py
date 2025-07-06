#!/usr/bin/env python3
"""
Test rank priority and tonicization updates via UDP messages
"""

import socket
import struct
import time
from fibril_main import FibrilMain

def encode_string(s):
    """Encode string for OSC message"""
    data = s.encode('utf-8') + b'\x00'
    while len(data) % 4 != 0:
        data += b'\x00'
    return data

def encode_int(value):
    """Encode integer for OSC message"""
    return struct.pack('>i', value)

def send_priority_message(rank_num: int, priority: int, target_port: int = 1761):
    """Send a rank priority update message to FIBRIL"""
    try:
        address = f"/R{rank_num}_priority"
        
        msg = b''
        msg += encode_string(address)
        msg += b',i\x00\x00'  # Type tag for integer
        msg += encode_int(priority)
        
        # Send via UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(msg, ("127.0.0.1", target_port))
        sock.close()
        
        print(f"📤 Sent {address} = {priority} to port {target_port}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending priority message: {e}")
        return False

def send_tonicization_message(rank_num: int, tonicization: int, target_port: int = 1761):
    """Send a rank tonicization update message to FIBRIL"""
    try:
        address = f"/R{rank_num}_tonicization"
        
        msg = b''
        msg += encode_string(address)
        msg += b',i\x00\x00'  # Type tag for integer
        msg += encode_int(tonicization)
        
        # Send via UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(msg, ("127.0.0.1", target_port))
        sock.close()
        
        print(f"📤 Sent {address} = {tonicization} to port {target_port}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending tonicization message: {e}")
        return False

def test_rank_updates():
    """Test rank priority and tonicization updates"""
    print("🧪 Testing Rank Priority and Tonicization Updates")
    print("=" * 60)
    
    # Initialize FIBRIL system
    fibril_main = FibrilMain(listen_port=1761, send_port=8998)
    
    print("\n📡 Testing priority updates...")
    
    # Test priority updates - scramble the priorities
    priority_updates = [
        (1, 5),  # Rank 1 to priority 5
        (2, 3),  # Rank 2 to priority 3
        (3, 8),  # Rank 3 to priority 8
        (4, 1),  # Rank 4 to priority 1
        (5, 7),  # Rank 5 to priority 7
        (6, 2),  # Rank 6 to priority 2
        (7, 6),  # Rank 7 to priority 6
        (8, 4),  # Rank 8 to priority 4
    ]
    
    for rank, priority in priority_updates:
        send_priority_message(rank, priority)
        time.sleep(0.5)
    
    print("\n📡 Testing tonicization updates...")
    
    # Test tonicization updates - mix up the scale degrees
    tonicization_updates = [
        (1, 7),  # Rank 1 to leading tone
        (2, 1),  # Rank 2 to tonic
        (3, 5),  # Rank 3 to dominant
        (4, 3),  # Rank 4 to mediant
        (5, 2),  # Rank 5 to supertonic
        (6, 4),  # Rank 6 to subdominant
        (7, 6),  # Rank 7 to submediant
        (8, 9),  # Rank 8 to subtonic (should stay 9)
    ]
    
    for rank, tonicization in tonicization_updates:
        send_tonicization_message(rank, tonicization)
        time.sleep(0.5)
    
    print("\n✅ Rank update test complete!")
    print("Check the FIBRIL system state display to see updated priorities and tonicizations.")

if __name__ == "__main__":
    test_rank_updates()
