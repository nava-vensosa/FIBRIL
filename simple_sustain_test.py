#!/usr/bin/env python3
"""
Simple test for sustain pedal logic
"""

from fibril_init import FibrilSystem
from fibril_algorithms import FibrilAlgorithm
from fibril_classes import SystemState

def test_sustain():
    print("Testing Sustain Pedal Logic")
    print("=" * 40)
    
    # Initialize system
    fibril_system = FibrilSystem()
    algorithm = FibrilAlgorithm()
    
    system_state = SystemState(
        ranks=fibril_system.ranks,
        voices=fibril_system.voices,
        sustain=False,
        key_center=60
    )
    
    # Activate rank 1 
    system_state.ranks[0].grey_code = [1, 1, 0, 0]
    system_state.ranks[0].__post_init__()
    print(f"Rank 1 density: {system_state.ranks[0].density}")
    
    # Initial allocation
    print("\n1. Initial allocation (sustain OFF):")
    new_state = algorithm.allocate_voices(system_state)
    active = [v for v in new_state.voices if v.volume]
    print(f"Active voices: {len(active)}")
    initial_notes = {v.midi_note for v in active}
    print(f"Active notes: {sorted(initial_notes)}")
    
    # Turn sustain ON
    print("\n2. Turn sustain ON:")
    new_state.sustain = True
    new_state = algorithm.allocate_voices(new_state)
    sustained = [v for v in new_state.voices if getattr(v, 'sustained', False)]
    print(f"Sustained voices: {len(sustained)}")
    sustained_notes = {v.midi_note for v in sustained}
    print(f"Sustained notes: {sorted(sustained_notes)}")
    
    # Verify sustain protection
    print(f"Notes protected by sustain: {len(initial_notes.intersection(sustained_notes))}/{len(initial_notes)}")
    
    # Add more activity while sustain is ON
    print("\n3. Add rank 2 activity while sustain ON:")
    new_state.ranks[1].grey_code = [1, 0, 1, 0]
    new_state.ranks[1].__post_init__()
    print(f"Rank 2 density: {new_state.ranks[1].density}")
    
    new_state = algorithm.allocate_voices(new_state)
    all_active = [v for v in new_state.voices if v.volume]
    still_sustained = [v for v in new_state.voices if getattr(v, 'sustained', False)]
    print(f"Total active voices: {len(all_active)}")
    print(f"Still sustained: {len(still_sustained)}")
    
    # Turn sustain OFF
    print("\n4. Turn sustain OFF:")
    new_state.sustain = False
    new_state = algorithm.allocate_voices(new_state)
    final_active = [v for v in new_state.voices if v.volume]
    remaining_sustained = [v for v in new_state.voices if getattr(v, 'sustained', False)]
    print(f"Final active voices: {len(final_active)}")
    print(f"Voices still marked sustained: {len(remaining_sustained)}")
    
    if len(remaining_sustained) == 0:
        print("✓ SUCCESS: Sustain flags properly cleared")
    else:
        print("✗ ERROR: Some voices still sustained")
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_sustain()
