#!/usr/bin/env python3

import sys
import struct
sys.path.append('/workspaces/FIBRIL')

from fibril_udp import parse_osc_message_for_fibril

def encode_string(s):
    data = s.encode('utf-8') + b'\x00'
    while len(data) % 4 != 0:
        data += b'\x00'
    return data

def encode_int(value):
    return struct.pack('>i', value)

def test_priority_message():
    print("=== Testing Priority Message ===")
    
    # Create OSC message for /R1_priority with value 5
    address = "/R1_priority"
    msg = b''
    msg += encode_string(address)
    msg += b',i\x00\x00'  # Type tag for integer  
    msg += encode_int(5)
    
    print(f"Created message for '{address}' with value 5")
    print(f"Message bytes: {msg.hex()}")
    
    # Parse it
    try:
        result = parse_osc_message_for_fibril(msg)
        print(f"Parsed result: {result}")
        
        if result and result.get('type') == 'rank_priority':
            print("✅ SUCCESS: Message parsed as rank_priority")
            print(f"   Rank Number: {result.get('rank_number')}")
            print(f"   Priority: {result.get('priority')}")
        else:
            print("❌ FAILED: Message not parsed correctly")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_tonicization_message():
    print("\n=== Testing Tonicization Message ===")
    
    # Create OSC message for /R3_tonicization with value 7
    address = "/R3_tonicization"
    msg = b''
    msg += encode_string(address)
    msg += b',i\x00\x00'  # Type tag for integer  
    msg += encode_int(7)
    
    print(f"Created message for '{address}' with value 7")
    print(f"Message bytes: {msg.hex()}")
    
    # Parse it
    try:
        result = parse_osc_message_for_fibril(msg)
        print(f"Parsed result: {result}")
        
        if result and result.get('type') == 'rank_tonicization':
            print("✅ SUCCESS: Message parsed as rank_tonicization")
            print(f"   Rank Number: {result.get('rank_number')}")
            print(f"   Tonicization: {result.get('tonicization')}")
        else:
            print("❌ FAILED: Message not parsed correctly")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_priority_message()
    test_tonicization_message()
