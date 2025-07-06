#!/usr/bin/env python3
"""
Test script for verifying sustain pedal logic implementation
"""

import logging
from fibril_init import FibrilSystem
from fibril_algorithms import FibrilAlgorithm
from fibril_classes import SystemState

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_sustain_pedal():
    """Test the sustain pedal logic"""
    
    print("=" * 60)
    print("TESTING SUSTAIN PEDAL LOGIC")
    print("=" * 60)
    
    # Initialize system
    fibril_system = FibrilSystem()
    algorithm = FibrilAlgorithm()
    
    # Create initial system state
    system_state = SystemState(
        ranks=fibril_system.ranks,
        voices=fibril_system.voices,
        sustain=False,
        key_center=60  # Middle C
    )
    
    # Set up some ranks to have activity
    print("\n1. Setting up initial rank activity...")
    system_state.ranks[0].grey_code = [1, 1, 0, 0]  # R1 with some density
    system_state.ranks[0].__post_init__()
    system_state.ranks[1].grey_code = [1, 0, 1, 0]  # R2 with some density
    system_state.ranks[1].__post_init__()
    
    print(f"R1 density: {system_state.ranks[0].density}")
    print(f"R2 density: {system_state.ranks[1].density}")
    
    # Allocate voices initially
    print("\n2. Initial voice allocation...")
    new_state = algorithm.allocate_voices(system_state)
    
    active_voices_initial = [v for v in new_state.voices if v.volume]
    print(f"Active voices after initial allocation: {len(active_voices_initial)}")
    for v in active_voices_initial[:5]:  # Show first 5
        print(f"  Voice {v.id}: MIDI {v.midi_note}, sustained: {getattr(v, 'sustained', False)}")
    
    # Turn ON sustain pedal
    print("\n3. Turning ON sustain pedal...")
    new_state.sustain = True
    new_state = algorithm.allocate_voices(new_state)
    
    sustained_voices = [v for v in new_state.voices if v.volume and getattr(v, 'sustained', False)]
    print(f"Sustained voices after pedal ON: {len(sustained_voices)}")
    for v in sustained_voices[:5]:  # Show first 5
        print(f"  Voice {v.id}: MIDI {v.midi_note}, sustained: {getattr(v, 'sustained', False)}")
    
    # Change rank activity while sustain is ON
    print("\n4. Changing rank activity while sustain is ON...")
    system_state.ranks[2].grey_code = [1, 1, 1, 0]  # R3 with more density
    system_state.ranks[2].__post_init__()
    print(f"R3 density: {system_state.ranks[2].density}")
    
    new_state = algorithm.allocate_voices(new_state)
    
    all_active_voices = [v for v in new_state.voices if v.volume]
    still_sustained = [v for v in new_state.voices if v.volume and getattr(v, 'sustained', False)]
    
    print(f"Total active voices after change: {len(all_active_voices)}")
    print(f"Still sustained voices: {len(still_sustained)}")
    print("Checking if original sustained voices are still protected...")
    
    original_sustained_midis = {v.midi_note for v in sustained_voices}
    current_sustained_midis = {v.midi_note for v in still_sustained}
    
    protected_count = len(original_sustained_midis.intersection(current_sustained_midis))
    print(f"Originally sustained notes still active: {protected_count}/{len(original_sustained_midis)}")
    
    # Turn OFF sustain pedal
    print("\n5. Turning OFF sustain pedal...")
    new_state.sustain = False
    new_state = algorithm.allocate_voices(new_state)
    
    post_sustain_voices = [v for v in new_state.voices if v.volume]
    post_sustain_sustained = [v for v in new_state.voices if getattr(v, 'sustained', False)]
    
    print(f"Active voices after sustain OFF: {len(post_sustain_voices)}")
    print(f"Voices still marked as sustained: {len(post_sustain_sustained)}")
    
    # Verify all sustained flags are cleared
    if len(post_sustain_sustained) == 0:
        print("✓ PASS: All sustained flags cleared when pedal released")
    else:
        print("✗ FAIL: Some voices still marked as sustained")
    
    print("\n" + "=" * 60)
    print("SUSTAIN PEDAL TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_sustain_pedal()
