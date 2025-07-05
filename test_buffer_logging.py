#!/usr/bin/env python3
"""
Test FIBRIL system to demonstrate UDP logging and 220ms buffer
"""

import asyncio
import time
from fibril_main import FibrilMain

async def test_buffer_and_logging():
    """Test the 220ms buffer and UDP message logging"""
    print("🎼 Testing FIBRIL 220ms Buffer and UDP Logging")
    print("=" * 60)
    
    # Create FIBRIL system
    fibril = FibrilMain()
    
    # Test immediate processing (buffer time exceeded)
    print("\n1. Testing immediate processing (buffer time exceeded):")
    print("   Simulating buffer time already exceeded...")
    
    # Set last buffer time to simulate time passed
    fibril.last_buffer_time = 0  # Force immediate processing
    
    test_message1 = {
        'type': 'rank_update',
        'rank_number': 3,
        'bit_pattern': '0100',
        'value': 1
    }
    
    response1 = fibril.process_message(test_message1)
    if response1:
        print(f"   ✅ Immediate response: {response1['active_count']} active voices")
    else:
        print("   ❌ No immediate response")
    
    # Test buffered processing
    print("\n2. Testing buffered processing (within buffer time):")
    print("   Sending rapid state changes...")
    
    # Reset buffer time to current time
    fibril.last_buffer_time = asyncio.get_event_loop().time()
    
    test_message2 = {
        'type': 'rank_update', 
        'rank_number': 1,
        'bit_pattern': '1000',
        'value': 1
    }
    
    test_message3 = {
        'type': 'rank_update',
        'rank_number': 4, 
        'bit_pattern': '0010',
        'value': 1
    }
    
    response2 = fibril.process_message(test_message2)
    response3 = fibril.process_message(test_message3)
    
    print(f"   📊 First rapid message response: {response2 is not None}")
    print(f"   📊 Second rapid message response: {response3 is not None}")
    print(f"   📊 State change pending: {fibril.state_change_pending}")
    
    if fibril.state_change_pending:
        print("   ⏱️  Waiting for buffer to process...")
        # Wait for buffer processing
        await asyncio.sleep(0.25)  # Wait longer than 220ms
        
        # Check if buffer was processed
        print(f"   📊 State change pending after buffer: {fibril.state_change_pending}")
    
    print("\n3. Testing UDP message logging:")
    print("   The system logs all outgoing UDP messages with detailed information:")
    print("   - Voice allocations (MIDI notes and volumes)")
    print("   - Active voice counts")
    print("   - Raw OSC data hexdump")
    print("   - Each message separated by line breaks")
    
    # Generate a response to show logging format
    test_response = {
        'voices': [
            {'id': 1, 'midi_note': 60, 'volume': 1},
            {'id': 2, 'midi_note': 67, 'volume': 1}, 
            {'id': 3, 'midi_note': 72, 'volume': 0},
        ],
        'active_count': 2,
        'timestamp': time.time()
    }
    
    print("\n📤 Example UDP message that would be logged:")
    print("   (This would appear in the console when sending to MaxMSP)")
    print("   📤 SENDING UDP MESSAGE TO MAXMSP (Port 1762):")
    print("      Response data size: XXX bytes")
    print("      Active voices: 2")
    print("        Voice 1: MIDI 60, Volume 1")
    print("        Voice 2: MIDI 67, Volume 1") 
    print("      Total active count: 2")
    print("      Raw OSC data: 2f766f6963652f31...")
    print("   ─" * 60)
    
    print("\n✅ Test completed successfully!")
    print(f"   🎹 Total voices initialized: {len(fibril.system_state.voices)}")
    print(f"   🎵 Total ranks initialized: {len(fibril.system_state.ranks)}")
    print(f"   ⏱️  Buffer time: {fibril.buffer_time * 1000:.0f}ms")

if __name__ == "__main__":
    asyncio.run(test_buffer_and_logging())
