#!/usr/bin/env python3
"""
Test to verify that no duplicate MIDI notes exist in the voice allocation,
especially during sustain pedal operations.
"""

import time
import logging
from fibril_main import FibrilMain
from fibril_classes import SystemState
from fibril_algorithms import FibrilAlgorithm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_for_duplicates(system_state, test_name=""):
    """Check for duplicate MIDI notes in active voices"""
    active_voices = [v for v in system_state.voices if v.volume]
    midi_notes = [v.midi_note for v in active_voices]
    unique_notes = set(midi_notes)
    
    duplicates = []
    for note in unique_notes:
        voices_with_note = [v for v in active_voices if v.midi_note == note]
        if len(voices_with_note) > 1:
            voice_ids = [v.id for v in voices_with_note]
            duplicates.append((note, voice_ids))
    
    if duplicates:
        logger.error(f"❌ {test_name}: DUPLICATES FOUND!")
        for note, voice_ids in duplicates:
            logger.error(f"   MIDI {note} is assigned to voices: {voice_ids}")
        return False
    else:
        logger.info(f"✅ {test_name}: No duplicates found - {len(unique_notes)} unique notes in {len(active_voices)} voices")
        return True

def test_no_duplicates():
    """Test that no duplicate MIDI notes are created"""
    
    logger.info("=== Testing No Duplicate MIDI Notes ===")
    
    # Create FIBRIL system
    from fibril_init import FibrilSystem
    fibril_system = FibrilSystem()
    algorithm = FibrilAlgorithm()
    
    # Create system state
    system_state = SystemState(
        ranks=fibril_system.ranks,
        voices=fibril_system.voices,
        sustain=False,
        key_center=60
    )
    
    logger.info("Initial state created")
    
    # Test 1: Basic allocation without sustain
    logger.info("\n--- TEST 1: Basic allocation ---")
    
    system_state.ranks[0].grey_code = [1, 1, 1, 1]  # R1: max density
    system_state.ranks[0].__post_init__()
    system_state.ranks[1].grey_code = [1, 1, 1, 0]  # R2: high density
    system_state.ranks[1].__post_init__()
    
    system_state = algorithm.allocate_voices(system_state)
    no_duplicates_1 = check_for_duplicates(system_state, "Basic allocation")
    
    # Test 2: Add more ranks (stress test)
    logger.info("\n--- TEST 2: Multiple ranks ---")
    
    for i in range(2, 6):  # R3-R6
        system_state.ranks[i].grey_code = [1, 0, 1, 0]  # Medium density
        system_state.ranks[i].__post_init__()
    
    system_state = algorithm.allocate_voices(system_state)
    no_duplicates_2 = check_for_duplicates(system_state, "Multiple ranks")
    
    # Test 3: Press sustain pedal
    logger.info("\n--- TEST 3: Press sustain pedal ---")
    
    system_state.sustain = True
    system_state = algorithm.allocate_voices(system_state)
    no_duplicates_3 = check_for_duplicates(system_state, "Sustain pressed")
    
    # Show frozen voices
    logger.info(f"Frozen voices: {len(system_state.frozen_voices)}")
    frozen_midi_notes = [midi for _, midi in system_state.frozen_voices]
    frozen_unique = set(frozen_midi_notes)
    if len(frozen_midi_notes) != len(frozen_unique):
        logger.error(f"❌ DUPLICATES in frozen_voices! {len(frozen_midi_notes)} total, {len(frozen_unique)} unique")
    else:
        logger.info(f"✅ No duplicates in frozen_voices: {len(frozen_unique)} unique notes")
    
    # Test 4: Change ranks while sustain is held
    logger.info("\n--- TEST 4: Change ranks while sustain held ---")
    
    # Modify existing ranks
    system_state.ranks[0].grey_code = [1, 1, 0, 1]  # Change R1
    system_state.ranks[0].__post_init__()
    system_state.ranks[6].grey_code = [0, 1, 1, 1]  # Activate R7
    system_state.ranks[6].__post_init__()
    
    system_state = algorithm.allocate_voices(system_state)
    no_duplicates_4 = check_for_duplicates(system_state, "Rank changes during sustain")
    
    # Test 5: More aggressive changes
    logger.info("\n--- TEST 5: Aggressive rank changes during sustain ---")
    
    # Activate all ranks with different patterns
    patterns = [
        [1, 1, 1, 1],  # R1: 6 voices
        [1, 1, 1, 0],  # R2: 4 voices  
        [1, 1, 0, 1],  # R3: 4 voices
        [1, 0, 1, 1],  # R4: 4 voices
        [0, 1, 1, 1],  # R5: 4 voices
        [1, 1, 0, 0],  # R6: 3 voices
        [1, 0, 1, 0],  # R7: 3 voices
        [0, 1, 0, 1]   # R8: 3 voices
    ]
    
    for i, pattern in enumerate(patterns):
        system_state.ranks[i].grey_code = pattern
        system_state.ranks[i].__post_init__()
    
    system_state = algorithm.allocate_voices(system_state)
    no_duplicates_5 = check_for_duplicates(system_state, "All ranks active during sustain")
    
    # Show detailed voice allocation
    active_voices = [v for v in system_state.voices if v.volume]
    logger.info(f"Total active voices: {len(active_voices)}")
    logger.info(f"Sustained voices: {sum(1 for v in active_voices if v.sustained)}")
    
    # Test 6: Release sustain
    logger.info("\n--- TEST 6: Release sustain ---")
    
    system_state.sustain = False
    system_state = algorithm.allocate_voices(system_state)
    no_duplicates_6 = check_for_duplicates(system_state, "Sustain released")
    
    # Test 7: Multiple sustain cycles
    logger.info("\n--- TEST 7: Multiple sustain cycles ---")
    
    for cycle in range(3):
        logger.info(f"  Cycle {cycle + 1}:")
        
        # Press
        system_state.sustain = True
        system_state = algorithm.allocate_voices(system_state)
        check_for_duplicates(system_state, f"Cycle {cycle + 1} press")
        
        # Change something
        rank_to_change = cycle % 3
        system_state.ranks[rank_to_change].grey_code = [1, 0, 0, 1] if cycle % 2 == 0 else [0, 1, 1, 0]
        system_state.ranks[rank_to_change].__post_init__()
        system_state = algorithm.allocate_voices(system_state)
        check_for_duplicates(system_state, f"Cycle {cycle + 1} change")
        
        # Release
        system_state.sustain = False
        system_state = algorithm.allocate_voices(system_state)
        check_for_duplicates(system_state, f"Cycle {cycle + 1} release")
    
    # Test 8: Edge case - try to create maximum density
    logger.info("\n--- TEST 8: Maximum density stress test ---")
    
    # Set all ranks to maximum density
    for i in range(8):
        system_state.ranks[i].grey_code = [1, 1, 1, 1]  # 6 voices each = 48 total
        system_state.ranks[i].__post_init__()
    
    system_state = algorithm.allocate_voices(system_state)
    no_duplicates_8a = check_for_duplicates(system_state, "Maximum density")
    
    # Press sustain at maximum density
    system_state.sustain = True
    system_state = algorithm.allocate_voices(system_state)
    no_duplicates_8b = check_for_duplicates(system_state, "Maximum density + sustain")
    
    # Release sustain
    system_state.sustain = False
    system_state = algorithm.allocate_voices(system_state)
    no_duplicates_8c = check_for_duplicates(system_state, "Maximum density sustain released")
    
    # Summary
    all_tests_passed = all([
        no_duplicates_1, no_duplicates_2, no_duplicates_3, 
        no_duplicates_4, no_duplicates_5, no_duplicates_6, 
        no_duplicates_8a, no_duplicates_8b, no_duplicates_8c
    ])
    
    logger.info(f"\n=== TEST SUMMARY ===")
    if all_tests_passed:
        logger.info("✅ ALL TESTS PASSED - No duplicate MIDI notes found in any scenario!")
    else:
        logger.error("❌ SOME TESTS FAILED - Duplicate MIDI notes were detected!")
    
    return all_tests_passed

if __name__ == "__main__":
    try:
        success = test_no_duplicates()
        exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
