#!/usr/bin/env python3
"""
Test the enhanced 48-voice display that shows all voices at all times.
"""

from fibril_classes import SystemState, Voice
from fibril_init import FibrilSystem
from fibril_udp import UDPHandler

def test_enhanced_voice_display():
    """Test the enhanced voice display with full system state"""
    print("🎹 TESTING ENHANCED 48-VOICE DISPLAY:")
    print("=" * 60)
    
    # Initialize FIBRIL system
    fibril_system = FibrilSystem()
    system_state = fibril_system.system_state
    
    # Simulate some voices being active by setting their volumes and MIDI notes
    print("Setting up test scenario...")
    system_state.voices[0].midi_note = 60   # Voice 1: C4
    system_state.voices[0].volume = 0.8
    
    system_state.voices[4].midi_note = 64   # Voice 5: E4  
    system_state.voices[4].volume = 0.7
    
    system_state.voices[11].midi_note = 67  # Voice 12: G4
    system_state.voices[11].volume = 0.9
    
    system_state.voices[23].midi_note = 72  # Voice 24: C5
    system_state.voices[23].volume = 0.6
    
    system_state.voices[47].midi_note = 76  # Voice 48: E5
    system_state.voices[47].volume = 0.5
    
    # Create UDP handler
    udp_handler = UDPHandler(
        message_processor=lambda x: [],
        listen_port=1761,
        send_port=1762,
        system_state=system_state
    )
    
    # Create a mock response with some changes
    response = {
        'voices': [
            {'id': 1, 'midi_note': 60, 'volume': True, 'midi_changed': True, 'volume_changed': True},
            {'id': 5, 'midi_note': 64, 'volume': True, 'midi_changed': False, 'volume_changed': True},
            {'id': 12, 'midi_note': 67, 'volume': True, 'midi_changed': True, 'volume_changed': False},
        ],
        'active_count': 5,
        'changed_count': 3
    }
    
    print("Displaying 48-voice status with enhanced view:")
    udp_handler._print_voice_status(response)
    
    print("=" * 60)
    print("✅ Enhanced voice display test completed!")
    print("\nFeatures demonstrated:")
    print("- Shows all 48 voices every time (not just changed ones)")
    print("- Uses system_state to show current MIDI notes and volumes")
    print("- Highlights recently changed voices with '→' marker")
    print("- Shows active/inactive status with 🔊/🔇 icons")
    print("- Provides summary of active and changed voices")

if __name__ == "__main__":
    test_enhanced_voice_display()
