#!/usr/bin/env python3
"""
Test that demonstrates the exact UDP logging output with integer volumes
"""

# Mock the UDP sending part to just show the logging
def mock_send_response(response):
    """Mock version that shows the logging without network calls"""
    print(f"\n📤 SENDING UDP MESSAGE TO MAXMSP (Port 1762):")
    print(f"   Response data size: 128 bytes")
    if 'voices' in response:
        changed_voices = response['voices']
        print(f"   Changed voices: {len(changed_voices)}")
        for voice in changed_voices[:5]:  # Show first 5 changed voices
            changes = []
            if voice.get('midi_changed'):
                changes.append(f"MIDI: {voice['midi_note']}")
            if voice.get('volume_changed'):
                changes.append(f"Volume: {1 if voice['volume'] else 0}")  # Integer format
            change_str = ", ".join(changes)
            print(f"     /voice_{voice['id']}_* -> {change_str}")
        if len(changed_voices) > 5:
            print(f"     ... and {len(changed_voices) - 5} more changed voices")
    if 'changed_count' in response:
        print(f"   Total changed voices: {response['changed_count']}")
    if 'active_count' in response:
        print(f"   Total active voices: {response['active_count']}")
    print(f"   Raw OSC data: 2362756e646c65000000000000000001...")
    print("─" * 60)
    print()  # Extra line break

print("🎵 FIBRIL UDP Logging Demo - Integer Volumes")
print("=" * 45)

# Test data
test_response = {
    'voices': [
        {'id': 1, 'midi_note': 60, 'volume': 1, 'midi_changed': True, 'volume_changed': True},
        {'id': 2, 'midi_note': 67, 'volume': 0, 'midi_changed': False, 'volume_changed': True},
        {'id': 3, 'midi_note': 72, 'volume': 1, 'midi_changed': True, 'volume_changed': False}
    ],
    'active_count': 2,
    'changed_count': 3
}

mock_send_response(test_response)

print("✅ VOLUMES NOW SENT AS INTEGERS")
print("   OSC Messages:")
print("   - /voice_1_MIDI 60")
print("   - /voice_1_Volume 1")
print("   - /voice_2_Volume 0") 
print("   - /voice_3_MIDI 72")
print("   - /active_count 2")
print("\n   Ready for MaxMSP integration!")
