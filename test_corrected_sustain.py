#!/usr/bin/env python3
"""
Test the CORRECTED sustain pedal logic
"""

from fibril_main import FibrilMain
import time

def test_corrected_sustain():
    print("Testing CORRECTED Sustain Pedal Logic")
    print("=" * 50)
    
    # Create FIBRIL main instance (but don't start UDP)
    fibril = FibrilMain()
    
    # Step 1: Create some initial voices
    print("1. Setting up initial activity...")
    rank1_msg = {
        'type': 'rank_update',
        'rank_number': 1,
        'bit_pattern': '1000',
        'value': 1.0
    }
    rank1_msg2 = {
        'type': 'rank_update',
        'rank_number': 1,
        'bit_pattern': '0100',
        'value': 1.0
    }
    
    fibril._update_system_state(rank1_msg)
    fibril._update_system_state(rank1_msg2)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    # Check initial voices
    initial_active = [v for v in fibril.system_state.voices if v.volume]
    initial_notes = sorted([v.midi_note for v in initial_active])
    print(f"Initial active voices: {len(initial_active)}")
    print(f"Initial notes: {initial_notes}")
    
    # Step 2: Press sustain pedal to freeze these voices
    print("\n2. PRESSING sustain pedal...")
    sustain_on = {
        'type': 'sustain',
        'value': 1
    }
    
    fibril._update_system_state(sustain_on)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    # Check frozen voices
    frozen_voices = fibril.system_state.frozen_voices
    frozen_notes = sorted([midi for _, midi in frozen_voices])
    sustained_voices = [v for v in fibril.system_state.voices if getattr(v, 'sustained', False)]
    
    print(f"Frozen voices: {len(frozen_voices)}")
    print(f"Frozen notes: {frozen_notes}")
    print(f"Voices marked sustained: {len(sustained_voices)}")
    
    # Step 3: Add MORE rank activity while sustain is held
    print("\n3. Adding NEW rank activity while sustain HELD...")
    rank2_msg = {
        'type': 'rank_update',
        'rank_number': 2,
        'bit_pattern': '1000',
        'value': 1.0
    }
    rank2_msg2 = {
        'type': 'rank_update',
        'rank_number': 2,
        'bit_pattern': '0100',
        'value': 1.0
    }
    
    fibril._update_system_state(rank2_msg)
    fibril._update_system_state(rank2_msg2)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    # Check current state
    all_active = [v for v in fibril.system_state.voices if v.volume]
    all_notes = sorted([v.midi_note for v in all_active])
    still_frozen = fibril.system_state.frozen_voices
    still_frozen_notes = sorted([midi for _, midi in still_frozen])
    
    print(f"Total active voices now: {len(all_active)}")
    print(f"All active notes: {all_notes}")
    print(f"Still frozen voices: {len(still_frozen)}")
    print(f"Still frozen notes: {still_frozen_notes}")
    
    # Verify frozen notes are still there
    frozen_preserved = all(note in all_notes for note in frozen_notes)
    print(f"Original frozen notes preserved: {frozen_preserved}")
    
    # Step 4: Change rank 1 while sustain is still held
    print("\n4. CHANGING rank 1 while sustain still HELD...")
    rank1_change = {
        'type': 'rank_update',
        'rank_number': 1,
        'bit_pattern': '0010',
        'value': 1.0
    }
    
    fibril._update_system_state(rank1_change)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    # Check if frozen voices STILL remain despite rank changes
    after_change_active = [v for v in fibril.system_state.voices if v.volume]
    after_change_notes = sorted([v.midi_note for v in after_change_active])
    still_frozen_after_change = fibril.system_state.frozen_voices
    still_frozen_notes_after = sorted([midi for _, midi in still_frozen_after_change])
    
    print(f"After rank change - Total active: {len(after_change_active)}")
    print(f"After rank change - All notes: {after_change_notes}")
    print(f"After rank change - Still frozen: {still_frozen_notes_after}")
    
    frozen_still_preserved = all(note in after_change_notes for note in frozen_notes)
    print(f"Frozen notes STILL preserved after rank change: {frozen_still_preserved}")
    
    # Step 5: Release sustain pedal
    print("\n5. RELEASING sustain pedal...")
    sustain_off = {
        'type': 'sustain',
        'value': 0
    }
    
    fibril._update_system_state(sustain_off)
    fibril.state_change_pending = True
    response = fibril._process_buffered_state_change()
    
    # Check final state
    final_active = [v for v in fibril.system_state.voices if v.volume]
    final_notes = sorted([v.midi_note for v in final_active])
    remaining_frozen = fibril.system_state.frozen_voices
    remaining_sustained = [v for v in fibril.system_state.voices if getattr(v, 'sustained', False)]
    
    print(f"After sustain release - Active voices: {len(final_active)}")
    print(f"After sustain release - Notes: {final_notes}")
    print(f"Remaining frozen voices: {len(remaining_frozen)}")
    print(f"Voices still marked sustained: {len(remaining_sustained)}")
    
    # RESULTS
    print("\n" + "=" * 50)
    print("SUSTAIN PEDAL TEST RESULTS:")
    print(f"✓ Initial voices created: {len(initial_active) > 0}")
    print(f"✓ Voices frozen when pedal pressed: {len(frozen_voices) > 0}")
    print(f"✓ Frozen voices preserved during new activity: {frozen_preserved}")
    print(f"✓ Frozen voices preserved during rank changes: {frozen_still_preserved}")
    print(f"✓ All frozen state cleared when pedal released: {len(remaining_frozen) == 0 and len(remaining_sustained) == 0}")
    
    overall_success = (len(initial_active) > 0 and 
                      len(frozen_voices) > 0 and 
                      frozen_preserved and 
                      frozen_still_preserved and 
                      len(remaining_frozen) == 0 and 
                      len(remaining_sustained) == 0)
    
    if overall_success:
        print("\n🎹 SUCCESS: Sustain pedal works like a REAL PIANO!")
    else:
        print("\n❌ FAILED: Sustain pedal still has issues")

if __name__ == "__main__":
    test_corrected_sustain()
