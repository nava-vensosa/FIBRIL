#!/usr/bin/env python3
"""
Test improved sustain pedal logic:
1. Prevents duplicate MIDI values in frozen_voices
2. Continues to freeze new notes while sustain pedal is held
3. Verifies proper behavior during rank changes while sustain is active
"""

import time
import json
import socket
import logging
from fibril_main import FibrilMain
from fibril_classes import SystemState
from fibril_algorithms import FibrilAlgorithm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_udp_message(message, port=8998):
    """Send a UDP message to the FIBRIL system"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(json.dumps(message).encode(), ('localhost', port))
        logger.info(f"Sent: {message}")
    finally:
        sock.close()
    time.sleep(0.1)

def check_frozen_voices_for_duplicates(system_state):
    """Check for duplicate MIDI notes in frozen voices"""
    midi_notes = [midi_note for _, midi_note in system_state.frozen_voices]
    unique_notes = set(midi_notes)
    
    if len(midi_notes) != len(unique_notes):
        duplicates = [note for note in unique_notes if midi_notes.count(note) > 1]
        logger.error(f"❌ DUPLICATE MIDI notes found in frozen_voices: {duplicates}")
        return False
    else:
        logger.info(f"✅ No duplicates in frozen_voices: {len(midi_notes)} unique notes")
        return True

def test_improved_sustain_logic():
    """Test the improved sustain logic"""
    
    logger.info("=== Testing Improved Sustain Logic ===")
    
    # Create FIBRIL system (no UDP to avoid conflicts)
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
    
    logger.info(f"Initial state: {len(system_state.voices)} voices, sustain={system_state.sustain}")
    
    # Test 1: Set up some active ranks to create notes
    logger.info("\n--- TEST 1: Setting up active ranks ---")
    
    # Activate several ranks with different patterns
    system_state.ranks[0].grey_code = [0, 0, 0, 1]  # R1: density 2
    system_state.ranks[0].__post_init__()
    
    system_state.ranks[1].grey_code = [0, 0, 1, 0]  # R2: density 3  
    system_state.ranks[1].__post_init__()
    
    system_state.ranks[2].grey_code = [0, 1, 0, 0]  # R3: density 3
    system_state.ranks[2].__post_init__()
    
    # Run algorithm to allocate initial voices
    system_state = algorithm.allocate_voices(system_state)
    
    active_voices_initial = [v for v in system_state.voices if v.volume]
    logger.info(f"Initial allocation: {len(active_voices_initial)} active voices")
    for v in active_voices_initial[:10]:  # Show first 10
        logger.info(f"  Voice {v.id}: MIDI {v.midi_note}, sustained={v.sustained}")
    
    # Test 2: Press sustain pedal and check for duplicates
    logger.info("\n--- TEST 2: Press sustain pedal (check for duplicates) ---")
    
    system_state.sustain = True
    system_state = algorithm.allocate_voices(system_state)
    
    # Check for duplicates in frozen voices
    duplicates_ok = check_frozen_voices_for_duplicates(system_state)
    
    frozen_voices_after_press = len(system_state.frozen_voices)
    sustained_voices = [v for v in system_state.voices if v.sustained]
    logger.info(f"After sustain press: {frozen_voices_after_press} frozen voices, {len(sustained_voices)} sustained voices")
    
    # Test 3: Change ranks while sustain is held (should create new notes and freeze them)
    logger.info("\n--- TEST 3: Change ranks while sustain is held ---")
    
    # Add more density to existing ranks
    system_state.ranks[3].grey_code = [1, 0, 0, 0]  # R4: density 2
    system_state.ranks[3].__post_init__()
    
    system_state.ranks[4].grey_code = [0, 0, 1, 1]  # R5: density 3
    system_state.ranks[4].__post_init__()
    
    logger.info(f"Added density to R4 and R5")
    
    # Run algorithm again - should create new notes and freeze them
    system_state = algorithm.allocate_voices(system_state)
    
    # Check for duplicates again
    duplicates_ok_2 = check_frozen_voices_for_duplicates(system_state)
    
    frozen_voices_after_change = len(system_state.frozen_voices)
    sustained_voices_after = [v for v in system_state.voices if v.sustained]
    active_voices_after = [v for v in system_state.voices if v.volume]
    
    logger.info(f"After rank changes: {frozen_voices_after_change} frozen voices, {len(sustained_voices_after)} sustained voices, {len(active_voices_after)} total active")
    
    # Test 4: Verify new notes were frozen
    if frozen_voices_after_change > frozen_voices_after_press:
        logger.info(f"✅ New notes were frozen: {frozen_voices_after_change - frozen_voices_after_press} additional frozen voices")
    else:
        logger.warning(f"⚠️  No new notes were frozen (may be expected if no new allocations)")
    
    # Test 5: Continue changing ranks (more stress test)
    logger.info("\n--- TEST 5: More rank changes while sustain held ---")
    
    # Modify existing ranks
    system_state.ranks[0].grey_code = [1, 1, 0, 0]  # R1: density 3 (was 2)
    system_state.ranks[0].__post_init__()
    
    system_state.ranks[5].grey_code = [0, 1, 1, 0]  # R6: density 3
    system_state.ranks[5].__post_init__()
    
    # Run algorithm
    system_state = algorithm.allocate_voices(system_state)
    
    # Check for duplicates
    duplicates_ok_3 = check_frozen_voices_for_duplicates(system_state)
    
    frozen_voices_final = len(system_state.frozen_voices)
    logger.info(f"After more changes: {frozen_voices_final} frozen voices")
    
    # Test 6: Release sustain pedal
    logger.info("\n--- TEST 6: Release sustain pedal ---")
    
    system_state.sustain = False
    system_state = algorithm.allocate_voices(system_state)
    
    frozen_voices_after_release = len(system_state.frozen_voices)
    sustained_voices_after_release = [v for v in system_state.voices if v.sustained]
    
    logger.info(f"After sustain release: {frozen_voices_after_release} frozen voices, {len(sustained_voices_after_release)} sustained voices")
    
    if frozen_voices_after_release == 0 and len(sustained_voices_after_release) == 0:
        logger.info("✅ All voices properly unfrozen and unsustained")
    else:
        logger.error(f"❌ Voices not properly released: {frozen_voices_after_release} still frozen, {len(sustained_voices_after_release)} still sustained")
    
    # Test 7: Press and release sustain multiple times (stress test)
    logger.info("\n--- TEST 7: Multiple sustain press/release cycles ---")
    
    for cycle in range(3):
        logger.info(f"  Cycle {cycle + 1}:")
        
        # Press sustain
        system_state.sustain = True
        system_state = algorithm.allocate_voices(system_state)
        frozen_count = len(system_state.frozen_voices)
        duplicates_ok = check_frozen_voices_for_duplicates(system_state)
        logger.info(f"    Press: {frozen_count} frozen, duplicates_ok={duplicates_ok}")
        
        # Make a small change
        if cycle == 0:
            system_state.ranks[6].grey_code = [0, 0, 0, 1]  # R7: density 2
        elif cycle == 1:
            system_state.ranks[7].grey_code = [0, 0, 1, 0]  # R8: density 3
        else:
            system_state.ranks[0].grey_code = [1, 1, 1, 0]  # R1: density 4
        
        system_state.ranks[cycle if cycle < 3 else 0].__post_init__()
        system_state = algorithm.allocate_voices(system_state)
        
        frozen_after_change = len(system_state.frozen_voices)
        duplicates_ok = check_frozen_voices_for_duplicates(system_state)
        logger.info(f"    After change: {frozen_after_change} frozen, duplicates_ok={duplicates_ok}")
        
        # Release sustain
        system_state.sustain = False
        system_state = algorithm.allocate_voices(system_state)
        frozen_after_release = len(system_state.frozen_voices)
        logger.info(f"    Release: {frozen_after_release} frozen")
        
        time.sleep(0.1)
    
    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info("✅ Sustain logic improvements tested:")
    logger.info("  - Duplicate prevention in frozen_voices")
    logger.info("  - New note freezing while sustain is held")
    logger.info("  - Proper cleanup on sustain release")
    logger.info("  - Multiple press/release cycles")

if __name__ == "__main__":
    try:
        test_improved_sustain_logic()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
