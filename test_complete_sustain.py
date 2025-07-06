#!/usr/bin/env python3
"""
Complete test demonstrating sustain pedal behavior
"""

from fibril_main import FibrilMain
import time

def test_complete_sustain():
    print("Complete Sustain Pedal Test")
    print("=" * 40)
    
    # Create FIBRIL main instance (but don't start UDP)
    fibril = FibrilMain()
    
    # Test rank update message to activate rank 1
    print("1. Activating Rank 1...")
    rank1_bit1 = {
        'type': 'rank_update',
        'rank_number': 1,
        'bit_pattern': '1000',
        'value': 1.0
    }
    rank1_bit2 = {
        'type': 'rank_update',
        'rank_number': 1,
        'bit_pattern': '0100',
        'value': 1.0
    }
    
    # Update state and force processing
    fibril._update_system_state(rank1_bit1)
    fibril._update_system_state(rank1_bit2)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    # Check active voices
    active_voices = [v for v in fibril.system_state.voices if v.volume]
    active_notes = sorted([v.midi_note for v in active_voices])
    print(f"Active voices: {len(active_voices)}")
    print(f"Active notes: {active_notes}")
    
    # Turn on sustain pedal
    print("\n2. Turning ON sustain pedal...")
    sustain_on = {
        'address': '/sustain',
        'value': 1
    }
    
    fibril._update_system_state(sustain_on)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    # Check sustained voices
    sustained_voices = [v for v in fibril.system_state.voices if getattr(v, 'sustained', False)]
    sustained_notes = sorted([v.midi_note for v in sustained_voices])
    print(f"Sustained voices: {len(sustained_voices)}")
    print(f"Sustained notes: {sustained_notes}")
    
    # Add rank 2 activity while sustain is on
    print("\n3. Adding Rank 2 while sustain ON...")
    rank2_bit1 = {
        'type': 'rank_update',
        'rank_number': 2,
        'bit_pattern': '1000',
        'value': 1.0
    }
    rank2_bit2 = {
        'type': 'rank_update',
        'rank_number': 2,
        'bit_pattern': '0100',
        'value': 1.0
    }
    
    fibril._update_system_state(rank2_bit1)
    fibril._update_system_state(rank2_bit2)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    # Check all voices now
    all_active = [v for v in fibril.system_state.voices if v.volume]
    still_sustained = [v for v in fibril.system_state.voices if getattr(v, 'sustained', False)]
    all_notes = sorted([v.midi_note for v in all_active])
    still_sustained_notes = sorted([v.midi_note for v in still_sustained])
    
    print(f"Total active voices: {len(all_active)}")
    print(f"All active notes: {all_notes}")
    print(f"Still sustained voices: {len(still_sustained)}")
    print(f"Still sustained notes: {still_sustained_notes}")
    
    # Check if original sustained notes are protected
    protected = set(sustained_notes).intersection(set(still_sustained_notes))
    print(f"Original sustained notes still protected: {len(protected)}/{len(sustained_notes)}")
    
    # Turn off sustain pedal
    print("\n4. Turning OFF sustain pedal...")
    sustain_off = {
        'address': '/sustain',
        'value': 0
    }
    
    fibril._update_system_state(sustain_off)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    # Check final state
    final_active = [v for v in fibril.system_state.voices if v.volume]
    remaining_sustained = [v for v in fibril.system_state.voices if getattr(v, 'sustained', False)]
    final_notes = sorted([v.midi_note for v in final_active])
    
    print(f"Final active voices: {len(final_active)}")
    print(f"Final active notes: {final_notes}")
    print(f"Voices still marked sustained: {len(remaining_sustained)}")
    
    # Results
    print("\nTEST RESULTS:")
    print(f"✓ Initial voices created: {len(active_voices) > 0}")
    print(f"✓ Voices sustained when pedal ON: {len(sustained_voices) > 0}")
    print(f"✓ Sustained voices protected during changes: {len(protected) == len(sustained_notes)}")
    print(f"✓ Sustained flags cleared when pedal OFF: {len(remaining_sustained) == 0}")
    
    overall_success = (len(active_voices) > 0 and 
                      len(sustained_voices) > 0 and 
                      len(protected) == len(sustained_notes) and 
                      len(remaining_sustained) == 0)
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED: Sustain pedal logic working correctly!")
    else:
        print("\n❌ SOME TESTS FAILED: Check implementation")

if __name__ == "__main__":
    test_complete_sustain()
