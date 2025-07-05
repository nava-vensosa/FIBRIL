#!/usr/bin/env python3
"""
Quick test of FIBRIL main system
"""

from fibril_main import FibrilMain
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_fibril():
    """Test FIBRIL initialization"""
    print("Testing FIBRIL system initialization...")
    
    # Create FIBRIL system
    fibril = FibrilMain()
    
    # Test message processing
    test_message = {
        'sustain': False,
        'key_center': 0,
        'ranks': [
            {'number': 1, 'grey_code': [0, 0, 1, 0]},  # GCI=1, density=2
            {'number': 3, 'grey_code': [0, 0, 1, 1]},  # GCI=2, density=3
        ]
    }
    
    print("Processing test message...")
    response = fibril.process_message(test_message)
    
    if response:
        print(f"Response generated with {response['active_count']} active voices")
        # Show first few voices
        for i, voice in enumerate(response['voices'][:5]):
            if voice['volume'] > 0:
                print(f"  Voice {voice['id']}: MIDI {voice['midi_note']}, Volume {voice['volume']}")
    else:
        print("No response generated")
    
    print("FIBRIL test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_fibril())
