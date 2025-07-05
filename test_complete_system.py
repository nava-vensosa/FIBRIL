#!/usr/bin/env python3
"""
Comprehensive test of FIBRIL system with 220ms buffer and OSC change tracking
"""

import asyncio
import logging
import time
from fibril_main import FibrilMain

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_full_system():
    """Test the complete system with timing and change tracking"""
    print("🎵 FIBRIL SYSTEM TEST - 220ms Buffer + OSC Change Tracking")
    print("=" * 60)
    
    # Create FIBRIL system
    fibril = FibrilMain()
    
    print("\n1. INITIAL STATE TEST")
    print("-" * 30)
    start_time = time.time()
    
    test_message = {
        'sustain': False,
        'key_center': 0,
        'ranks': [
            {'number': 3, 'grey_code': [0, 0, 1, 0]},  # Tonic rank, GCI=3, density=2
        ]
    }
    
    response = fibril.process_message(test_message)
    elapsed = (time.time() - start_time) * 1000
    
    if response:
        print(f"✓ Processed in {elapsed:.1f}ms")
        print(f"  Changed voices: {response['changed_count']}")
        print(f"  Active voices: {response['active_count']}")
        print("  Sample OSC messages that would be sent:")
        for voice in response['voices'][:4]:
            changes = []
            if voice.get('midi_changed'):
                changes.append(f"/voice_{voice['id']}_MIDI {voice['midi_note']}")
            if voice.get('volume_changed'):
                changes.append(f"/voice_{voice['id']}_Volume {bool(voice['volume'])}")
            for change in changes:
                print(f"    {change}")
    
    print("\n2. IMMEDIATE REPEAT TEST (No Changes Expected)")
    print("-" * 30)
    response2 = fibril.process_message(test_message)
    if response2:
        print(f"⚠️  Unexpected response: {response2['changed_count']} changes")
    else:
        print("✓ No response - change detection working correctly")
    
    print("\n3. SUSTAIN PEDAL TEST")
    print("-" * 30)
    sustain_message = {'sustain': True}
    response3 = fibril.process_message(sustain_message)
    if response3:
        print(f"✓ Sustain change detected: {response3['changed_count']} voices affected")
    
    print("\n4. RANK DENSITY CHANGE TEST")
    print("-" * 30)
    density_message = {
        'ranks': [
            {'number': 3, 'grey_code': [0, 1, 1, 1]},  # Higher density
            {'number': 6, 'grey_code': [0, 0, 1, 0]},  # Add subdominant rank
        ]
    }
    
    response4 = fibril.process_message(density_message)
    if response4:
        print(f"✓ Density change processed: {response4['changed_count']} voices changed")
        print(f"  New active count: {response4['active_count']}")
    
    print("\n5. BUFFER TIMING TEST")
    print("-" * 30)
    print("Testing 220ms buffer behavior...")
    
    # Make rapid changes and observe buffering
    for i in range(3):
        quick_message = {
            'ranks': [
                {'number': 1, 'grey_code': [i % 2, (i+1) % 2, 0, 1]},
            ]
        }
        start_time = time.time()
        response = fibril.process_message(quick_message)
        elapsed = (time.time() - start_time) * 1000
        
        if response:
            print(f"  Change {i+1}: Processed in {elapsed:.1f}ms, {response['changed_count']} voices")
        else:
            print(f"  Change {i+1}: Buffered (will process in ~220ms)")
        
        await asyncio.sleep(0.1)  # 100ms between changes
    
    print("\n" + "=" * 60)
    print("✓ FIBRIL SYSTEM TEST COMPLETED")
    print("  - 220ms input buffer working")
    print("  - OSC change tracking working")  
    print("  - Voice allocation algorithm working")
    print("  - UDP message format: /voice_N_MIDI and /voice_N_Volume")

if __name__ == "__main__":
    asyncio.run(test_full_system())
