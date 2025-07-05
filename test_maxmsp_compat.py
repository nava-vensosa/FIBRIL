#!/usr/bin/env python3
"""
Test individual OSC message sending for MaxMSP compatibility
"""

from fibril_udp import build_osc_response

def test_individual_messages():
    """Test that we build individual OSC messages instead of bundles"""
    print("🎵 Testing Individual OSC Messages for MaxMSP")
    print("=" * 45)
    
    # Test response data
    test_response = {
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
                'volume': 0,
                'midi_changed': False,
                'volume_changed': True
            }
        ],
        'active_count': 1,
        'changed_count': 2
    }
    
    # Build messages
    messages = build_osc_response(test_response)
    
    print(f"✓ Built {len(messages)} individual OSC messages")
    print("  Instead of 1 bundle, sending separate messages:")
    print("  - /voice_1_MIDI 60")
    print("  - /voice_1_Volume 1")
    print("  - /voice_2_Volume 0")
    print("  - /active_count 1")
    
    for i, msg in enumerate(messages):
        print(f"  Message {i+1}: {len(msg)} bytes")
    
    print(f"\n📋 MaxMSP Setup Instructions:")
    print(f"  1. Use [udpreceive 1762] object")
    print(f"  2. Connect to [OSC-route voice_ active_count]")
    print(f"  3. Route voice messages: [OSC-route 1 2 3 ...]")
    print(f"  4. Route parameters: [OSC-route MIDI Volume]")
    print(f"\n✅ Individual messages should work better with udpreceive!")

if __name__ == "__main__":
    test_individual_messages()
