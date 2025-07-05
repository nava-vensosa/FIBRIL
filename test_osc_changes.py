#!/usr/bin/env python3
"""
Test the new OSC message format with change tracking
"""

import asyncio
import logging
from fibril_main import FibrilMain

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_osc_changes():
    """Test OSC message format with voice changes"""
    print("Testing FIBRIL OSC change tracking...")
    
    # Create FIBRIL system
    fibril = FibrilMain()
    
    print("\n1. Initial state - should send all 48 voices (first time)")
    test_message_1 = {
        'sustain': False,
        'key_center': 0,
        'ranks': [
            {'number': 1, 'grey_code': [0, 0, 1, 0]},  # GCI=1, density=2
        ]
    }
    
    response1 = fibril.process_message(test_message_1)
    if response1:
        print(f"First response: {response1['changed_count']} changed voices, {response1['active_count']} active")
        print("Sample OSC messages that would be sent:")
        for voice in response1['voices'][:3]:  # Show first 3
            if voice.get('midi_changed'):
                print(f"  /voice_{voice['id']}_MIDI {voice['midi_note']}")
            if voice.get('volume_changed'):
                print(f"  /voice_{voice['id']}_Volume {bool(voice['volume'])}")
    
    print("\n2. Second update with same data - should send no changes")
    response2 = fibril.process_message(test_message_1)
    if response2:
        print(f"Second response: {response2['changed_count']} changed voices")
    else:
        print("No response - no changes detected ✓")
    
    print("\n3. Update with different rank - should send only changed voices")
    test_message_2 = {
        'ranks': [
            {'number': 1, 'grey_code': [0, 1, 1, 0]},  # Different GCI, more density
        ]
    }
    
    response3 = fibril.process_message(test_message_2)
    if response3:
        print(f"Third response: {response3['changed_count']} changed voices, {response3['active_count']} active")
        print("Sample OSC messages for changed voices:")
        for voice in response3['voices'][:3]:  # Show first 3 changed
            if voice.get('midi_changed'):
                print(f"  /voice_{voice['id']}_MIDI {voice['midi_note']}")
            if voice.get('volume_changed'):
                print(f"  /voice_{voice['id']}_Volume {bool(voice['volume'])}")
    
    print("\nOSC change tracking test completed!")

if __name__ == "__main__":
    asyncio.run(test_osc_changes())
