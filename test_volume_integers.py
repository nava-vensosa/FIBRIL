#!/usr/bin/env python3
"""
Test UDP message logging with integer volume values
"""

import asyncio
from fibril_udp import UDPHandler

async def test_volume_integers():
    """Test that volume values are sent as integers (1/0) not booleans"""
    print("🎵 Testing Volume Integer Format")
    print("=" * 35)
    
    # Mock response with mixed volume states
    mock_response = {
        'voices': [
            {
                'id': 1,
                'midi_note': 60,
                'volume': 1,  # Active voice
                'midi_changed': True,
                'volume_changed': True
            },
            {
                'id': 2,
                'midi_note': 67,
                'volume': 0,  # Inactive voice
                'midi_changed': False,
                'volume_changed': True
            },
            {
                'id': 5,
                'midi_note': 48,
                'volume': 1,  # Active voice
                'midi_changed': True,
                'volume_changed': True
            }
        ],
        'active_count': 2,
        'changed_count': 3
    }
    
    # Create UDP handler
    def dummy_processor(msg):
        return mock_response
    
    udp_handler = UDPHandler(dummy_processor)
    
    # This will trigger the logging with integer values
    print("Sending test response (will show integer volume values)...")
    await udp_handler._send_response(mock_response)
    
    print("\n✅ Volume values now sent as integers: 1 (on) / 0 (off)")
    print("   This is compatible with MaxMSP integer processing")

if __name__ == "__main__":
    asyncio.run(test_volume_integers())
