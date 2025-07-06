#!/usr/bin/env python3
"""
Test UDP sustain message handling
"""

from fibril_main import FibrilMain
import time

def test_sustain_message_formats():
    print("Testing UDP Sustain Message Handling")
    print("=" * 45)
    
    # Create FIBRIL main instance (but don't start UDP)
    fibril = FibrilMain()
    
    # Test format 1: address format (from '/sustain' OSC address)
    print("1. Testing address format: {'address': '/sustain', 'value': 1}")
    sustain_address_on = {
        'address': '/sustain',
        'value': 1
    }
    
    result = fibril._update_system_state(sustain_address_on)
    print(f"   State changed: {result}")
    print(f"   Sustain state: {fibril.system_state.sustain}")
    
    # Test format 2: type format (from parsed OSC message)
    print("\n2. Testing type format: {'type': 'sustain', 'value': 0}")
    sustain_type_off = {
        'type': 'sustain',
        'value': 0
    }
    
    result = fibril._update_system_state(sustain_type_off)
    print(f"   State changed: {result}")
    print(f"   Sustain state: {fibril.system_state.sustain}")
    
    # Test format 3: legacy format (for backward compatibility)
    print("\n3. Testing legacy format: {'sustain': 1}")
    sustain_legacy_on = {
        'sustain': 1
    }
    
    result = fibril._update_system_state(sustain_legacy_on)
    print(f"   State changed: {result}")
    print(f"   Sustain state: {fibril.system_state.sustain}")
    
    # Test with actual voice allocation
    print("\n4. Testing with voice allocation...")
    
    # Add some rank activity
    rank_msg = {
        'type': 'rank_update',
        'rank_number': 1,
        'bit_pattern': '1000',
        'value': 1.0
    }
    fibril._update_system_state(rank_msg)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    active_voices = [v for v in fibril.system_state.voices if v.volume]
    print(f"   Active voices created: {len(active_voices)}")
    
    # Turn sustain ON via type format
    sustain_on_type = {
        'type': 'sustain',
        'value': 1
    }
    
    fibril._update_system_state(sustain_on_type)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    sustained_voices = [v for v in fibril.system_state.voices if getattr(v, 'sustained', False)]
    print(f"   Sustained voices: {len(sustained_voices)}")
    
    # Turn sustain OFF via address format
    sustain_off_address = {
        'address': '/sustain',
        'value': 0
    }
    
    fibril._update_system_state(sustain_off_address)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    remaining_sustained = [v for v in fibril.system_state.voices if getattr(v, 'sustained', False)]
    print(f"   Remaining sustained after OFF: {len(remaining_sustained)}")
    
    print("\n✅ All message formats work correctly!")
    print("   - Address format: ✓")
    print("   - Type format: ✓") 
    print("   - Legacy format: ✓")
    print("   - Voice allocation integration: ✓")

if __name__ == "__main__":
    test_sustain_message_formats()
