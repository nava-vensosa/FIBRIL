#!/usr/bin/env python3
"""
Test sustain pedal via message interface (simulating MaxMSP)
"""

from fibril_main import FibrilMain
import time

def test_sustain_via_messages():
    print("Testing Sustain via OSC Message Interface")
    print("=" * 50)
    
    # Create FIBRIL main instance (but don't start UDP)
    fibril = FibrilMain()
    
    # Test rank update message
    print("1. Setting up rank activity...")
    rank_message = {
        'type': 'rank_update',
        'rank_number': 1,
        'bit_pattern': '1000',
        'value': 1.0
    }
    
    fibril._update_system_state(rank_message)
    
    rank_message = {
        'type': 'rank_update', 
        'rank_number': 1,
        'bit_pattern': '0100',
        'value': 1.0
    }
    
    fibril._update_system_state(rank_message)
    
    print(f"Rank 1 density: {fibril.system_state.ranks[0].density}")
    
    # Process to get initial voices
    response = fibril._process_buffered_state_change()
    if response:
        print(f"Initial active voices: {response['active_count']}")
    
    # Turn on sustain
    print("\n2. Turning ON sustain pedal...")
    sustain_message = {
        'address': '/sustain',
        'value': 1
    }
    
    fibril._update_system_state(sustain_message)
    response = fibril._process_buffered_state_change()
    
    sustained_voices = [v for v in fibril.system_state.voices if getattr(v, 'sustained', False)]
    print(f"Sustained voices: {len(sustained_voices)}")
    
    # Add more rank activity while sustain is on
    print("\n3. Adding rank 2 activity while sustain ON...")
    rank2_message = {
        'type': 'rank_update',
        'rank_number': 2,
        'bit_pattern': '1000',
        'value': 1.0
    }
    
    fibril._update_system_state(rank2_message)
    response = fibril._process_buffered_state_change()
    
    if response:
        print(f"Total active voices: {response['active_count']}")
    
    still_sustained = [v for v in fibril.system_state.voices if getattr(v, 'sustained', False)]
    print(f"Still sustained: {len(still_sustained)}")
    
    # Turn off sustain
    print("\n4. Turning OFF sustain pedal...")
    sustain_off_message = {
        'address': '/sustain',
        'value': 0
    }
    
    fibril._update_system_state(sustain_off_message)
    response = fibril._process_buffered_state_change()
    
    if response:
        print(f"Final active voices: {response['active_count']}")
    
    remaining_sustained = [v for v in fibril.system_state.voices if getattr(v, 'sustained', False)]
    print(f"Voices still marked sustained: {len(remaining_sustained)}")
    
    if len(remaining_sustained) == 0:
        print("✓ SUCCESS: Sustain integration working correctly")
    else:
        print("✗ ERROR: Sustain integration has issues")
    
    print("\nMessage interface test complete!")

if __name__ == "__main__":
    test_sustain_via_messages()
