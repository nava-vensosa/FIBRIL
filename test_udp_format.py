#!/usr/bin/env python3
"""
Test UDP/OSC message sending with the new format
"""

import asyncio
import logging
from fibril_udp import UDPHandler, build_osc_response

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_udp_messages():
    """Test UDP message sending with new OSC format"""
    print("Testing UDP/OSC message format...")
    
    # Create a mock response with changed voices
    mock_response = {
        'voices': [
            {
                'id': 1,
                'midi_note': 60,
                'volume': 1,
                'midi_changed': True,
                'volume_changed': True
            },
            {
                'id': 2,
                'midi_note': 67,
                'volume': 1,
                'midi_changed': False,
                'volume_changed': True
            },
            {
                'id': 3,
                'midi_note': 72,
                'volume': 0,
                'midi_changed': True,
                'volume_changed': False
            }
        ],
        'active_count': 2,
        'changed_count': 3
    }
    
    # Create UDP handler (won't actually bind since we're just testing message building)
    def dummy_processor(msg):
        return mock_response
    
    udp_handler = UDPHandler(dummy_processor)
    
    # Test the response sending (this will show the logging)
    print("\nSending test response...")
    await udp_handler._send_response(mock_response)
    
    # Also test the OSC message building directly
    print("\n--- OSC Message Building Test ---")
    osc_data = build_osc_response(mock_response)
    print(f"Built OSC bundle: {len(osc_data)} bytes")
    print(f"Raw data (first 100 bytes): {osc_data[:100].hex()}")
    
    print("\nExpected OSC messages in this bundle:")
    print("  /voice_1_MIDI 60")
    print("  /voice_1_Volume true")
    print("  /voice_2_Volume true")
    print("  /voice_3_MIDI 72")
    print("  /active_count 2")

if __name__ == "__main__":
    asyncio.run(test_udp_messages())
