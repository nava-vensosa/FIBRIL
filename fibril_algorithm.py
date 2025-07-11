#!/usr/bin/env python3
"""
FIBRIL New Algorithm - Cascading Harmonic Construction System

This module implements the main interface for the normalized probability distribution
system with rank-by-rank processing and cascading harmonic relationships.
"""

import math
import random
from typing import List, Dict, Set, Optional, Tuple, Any

try:
    from fibril_init import fibril_system
    print("✓ Successfully imported fibril_system")
    USING_MOCK = False
except Exception as e:
    print(f"⚠ Import failed: {e}")
    print("  Will create mock system for testing...")
    fibril_system = None  # Will be set by mock system
    USING_MOCK = True

# Import our new classes
from fibril_algorithm_classes import (
    AlgorithmParameters, DebugSettings, NormalizedProbabilityMap,
    AllocationEngine, VoiceSelector, AllocationHistory
)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def midi_to_note_name(midi_note: int) -> str:
    """Convert MIDI note number to note name (e.g., 60 -> 'C4')"""
    if midi_note < 0 or midi_note > 127:
        return f"MIDI{midi_note}"
    
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    note = note_names[midi_note % 12]
    return f"{note}{octave}"

def get_active_midi_notes() -> List[int]:
    """Get list of currently active MIDI notes (including sustained)"""
    return [voice.midi_note for voice in fibril_system.voices if voice.volume or voice.sustained]

def get_active_ranks():
    """Get list of currently active ranks (density > 0)"""
    return [rank for rank in fibril_system.ranks if rank.density > 0]

def calculate_target_voice_count(active_ranks, max_voices: int = 48) -> int:
    """Calculate how many voices should be allocated based on total rank density"""
    total_density = sum(rank.density for rank in active_ranks)
    return min(max_voices, total_density)

def get_rank_middle_octave_midi(rank) -> int:
    """Calculate rank's middle octave MIDI note from GCI"""
    middle_c = 60  # MIDI 60 = C4
    octave_offset = 1 + ((rank.gci - 5) // 3)
    return middle_c + (octave_offset * 12)

def get_rank_octave_spread(rank) -> int:
    """Calculate octave spread based on rank density (density // 2)"""
    return rank.density // 2

def get_rank_root_pc(rank, key_center: int) -> int:
    """Get the root pitch class for a rank based on its tonicization"""
    if rank.tonicization == 8:  # Subtonic - use 3rd of key center
        return (key_center + 4) % 12
    else:
        scale_degree_offsets = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}
        offset = scale_degree_offsets.get(rank.tonicization, 0)
        return (key_center + offset) % 12


# ============================================================================
# VOICE SELECTION AND ALLOCATION
# ============================================================================

def select_and_allocate_voice(prob_map: NormalizedProbabilityMap, context: Dict[str, Any]) -> Optional[int]:
    """Select a note from probability map and allocate to an available voice"""
    voice_selector = context.get('voice_selector')
    if not voice_selector:
        # Create temporary selector
        params = context.get('params', AlgorithmParameters())
        debug = context.get('debug', DebugSettings())
        voice_selector = VoiceSelector(params, debug)
    
    # Prevent duplicates
    active_voices = context.get('active_voices', [])
    voice_selector.prevent_duplicates(prob_map, active_voices)
    
    # Select note
    selected_midi = voice_selector.select_note(prob_map)
    if selected_midi is None:
        return None
    
    # Allocate voice
    fibril_sys = context.get('fibril_system', fibril_system)
    voice_id = voice_selector.allocate_voice(selected_midi, fibril_sys)
    
    if voice_id is not None:
        # Record allocation in history
        history = context.get('allocation_history')
        if history:
            metadata = {
                'rank_number': context.get('current_rank', {}).get('number', 0),
                'selection_method': 'weighted_random'
            }
            history.record_selection(voice_id, selected_midi, prob_map, metadata)
        
        if context.get('debug', DebugSettings()).DEBUG_VERBOSE:
            note_name = midi_to_note_name(selected_midi)
            print(f"     Selected MIDI {selected_midi} ({note_name}) → Voice {voice_id}")
        
        return selected_midi
    
    return None


# ============================================================================
# MAIN PUBLIC INTERFACE
# ============================================================================

def probabilistic_voice_allocation(max_voices: int = 48, custom_params: AlgorithmParameters = None, custom_debug: DebugSettings = None) -> Dict:
    """
    Main entry point for cascading harmonic construction
    
    Args:
        max_voices (int): Maximum number of voices to allocate
        custom_params (AlgorithmParameters): Custom parameter configuration
        custom_debug (DebugSettings): Custom debug configuration
        
    Returns:
        dict: Results including allocation count, timing, and visualization data
    """
    # Use custom parameters or defaults
    params = custom_params or AlgorithmParameters()
    debug = custom_debug or DebugSettings()
    
    # Override max voices if specified
    params.MAX_TOTAL_VOICES = max_voices
    
    # Create allocation engine
    engine = AllocationEngine(fibril_system, params, debug)
    
    # Run allocation
    result = engine.allocate_all_voices()
    
    return result

def deallocate_all_voices():
    """Deallocate all non-sustained voices"""
    deallocated = 0
    for voice in fibril_system.voices:
        if voice.volume and not voice.sustained:
            voice.volume = 0
            voice.midi_note = 0
            deallocated += 1
    
    # Removed print statement for cleaner output

def state_readout():
    """Complete state readout of the FIBRIL system"""
    print("\n=== FIBRIL Voice States ===")
    print("Voice | MIDI Note     | Vol | Sustained")
    print("------|---------------|-----|----------")
    active_count = 0
    
    for voice in fibril_system.voices:
        note_name = midi_to_note_name(voice.midi_note)
        midi_display = f"{voice.midi_note:3d} ({note_name})"
        volume = voice.volume
        sustained = "YES" if hasattr(voice, 'sustained') and voice.sustained else "NO"
        
        print(f"  {voice.id:2d}  | {midi_display:13s} |  {volume}  |    {sustained}")
        
        if voice.volume:
            active_count += 1
    
    print(f"\nTotal active voices: {active_count}/48")
    
    # Show key system attributes
    print(f"\nKey system state:")
    print(f"  Key center: {fibril_system.key_center}")
    print(f"  Sustain: {fibril_system.sustain}")
    print(f"  Total voices: {len(fibril_system.voices)}")
    print(f"  Total ranks: {len(fibril_system.ranks)}")


# ============================================================================
# CONFIGURATION AND TESTING
# ============================================================================

def configure_algorithm_parameters(**kwargs) -> AlgorithmParameters:
    """Create custom algorithm parameters with keyword overrides"""
    params = AlgorithmParameters()
    
    for key, value in kwargs.items():
        if hasattr(params, key.upper()):
            setattr(params, key.upper(), value)
        else:
            print(f"Warning: Unknown parameter '{key}'")
    
    return params

def configure_debug_settings(**kwargs) -> DebugSettings:
    """Create custom debug settings with keyword overrides"""
    debug = DebugSettings()
    
    for key, value in kwargs.items():
        if hasattr(debug, key.upper()):
            setattr(debug, key.upper(), value)
        else:
            print(f"Warning: Unknown debug setting '{key}'")
    
    return debug

def test_probabilistic_allocation():
    """Test the new allocation system with simulated data"""
    print("\n🧪 Testing Cascading Harmonic Construction...")
    
    # Set up test scenario
    fibril_system.key_center = 0  # C major (pitch class)
    fibril_system.ranks[2].density = 3  # R3 (tonic) with density 3
    fibril_system.ranks[3].density = 2  # R4 (subdominant) with density 2
    fibril_system.ranks[1].density = 1  # R2 (supertonic) with density 1
    
    print("Test scenario:")
    for rank in fibril_system.ranks:
        if rank.density > 0:
            print(f"  Rank {rank.number}: density {rank.density}, tonicization {rank.tonicization}")
    
    # Configure test parameters
    test_params = configure_algorithm_parameters(
        debug_verbose=True,
        print_constraint_applications=True,
        perfect_fifth_boost=5.0,
        root_force_probability=0.9
    )
    
    test_debug = configure_debug_settings(
        debug_verbose=True,
        print_selections=True
    )
    
    # Run allocation
    result = probabilistic_voice_allocation(
        max_voices=6,
        custom_params=test_params,
        custom_debug=test_debug
    )
    
    # Show results
    print(f"\n📊 Test Results:")
    print(f"  Allocated: {result['allocated']}/{result['target']} voices")
    print(f"  Ranks processed: {result['ranks_processed']}")
    print(f"  Elapsed time: {result['elapsed_time']:.3f}s")
    
    # Show allocation details
    viz_data = result.get('visualization_data', {})
    selections = viz_data.get('selections', [])
    
    if selections:
        print(f"\n🎵 Voice Allocations:")
        for i, selection in enumerate(selections):
            midi_note = selection['midi_note']
            voice_id = selection['voice_id']
            rank_num = selection.get('rank_number', '?')
            prob = selection['probability']
            note_name = midi_to_note_name(midi_note)
            
            print(f"  {i+1:2d}. MIDI {midi_note:3d} ({note_name:4s}) → Voice {voice_id:2d} | Rank {rank_num} | p={prob:.4f}")
    
    # Clean up
    deallocate_all_voices()
    for rank in fibril_system.ranks:
        rank.density = 0
    
    print(f"\n✅ Test completed!")


# ============================================================================
# MOCK SYSTEM FOR TESTING
# ============================================================================

def create_mock_fibril_system():
    """Create a mock fibril system for testing when import fails"""
    
    class MockVoice:
        def __init__(self, voice_id):
            self.id = voice_id
            self.midi_note = 60
            self.volume = 0
            self.sustained = False
    
    class MockRank:
        def __init__(self, number):
            self.number = number
            self.density = 0
            self.tonicization = number  # Simple mapping
            self.position = number
            self.grey_code = [0, 0, 0, 0]
            self.gci = 1  # Default GCI
            self.previous_gci = 0
        
        def get_valid_destinations(self, key_center):
            """Mock valid destinations - return some notes around key center"""
            base = key_center % 12
            octaves = [48, 60, 72]  # C3, C4, C5
            notes = []
            for octave in octaves:
                # Add some chord tones relative to this rank
                notes.extend([
                    octave + base,
                    octave + base + 4,  # Major third
                    octave + base + 7,  # Perfect fifth
                ])
            return [n for n in notes if 0 <= n <= 127]
    
    class MockSystem:
        def __init__(self):
            self.voices = [MockVoice(i+1) for i in range(48)]
            self.ranks = [MockRank(i+1) for i in range(8)]
            self.key_center = 0  # C major pitch class
            self.sustain = 0
    
    return MockSystem()


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Try to use real system, fall back to mock if import fails
try:
    if fibril_system is None:
        raise NameError("fibril_system is None")
    # Test if fibril_system is available
    fibril_system.voices[0]
    print("✓ Using real fibril_system")
    USING_MOCK = False
except (NameError, AttributeError, Exception):
    print("⚠ fibril_system unavailable, using mock system")
    fibril_system = create_mock_fibril_system()
    USING_MOCK = True


# ============================================================================
# MODULE EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("🎼 Cascading Harmonic Construction System")
    print("=" * 50)
    
    try:
        # Initialize system (real or mock)
        system_type = "mock" if USING_MOCK else "real"
        print(f"Using {system_type} fibril_system")
        print(f"   System has {len(fibril_system.voices)} voices")
        print(f"   System has {len(fibril_system.ranks)} ranks")
        print(f"   Key center: {fibril_system.key_center}")
        
        # Check for active ranks
        print("\n🔍 Checking active ranks...")
        active_ranks = get_active_ranks()
        print(f"   Found {len(active_ranks)} active ranks")
        
        if len(active_ranks) == 0:
            print("   No active ranks detected, running test scenario...")
            test_probabilistic_allocation()
        else:
            print("   Active ranks found:")
            for rank in active_ranks:
                print(f"     Rank {rank.number}: density {rank.density}, tonicization {rank.tonicization}")
            
            # Run allocation with active ranks
            print("\n🎯 Running allocation with active ranks...")
            result = probabilistic_voice_allocation(max_voices=12)
            
            print(f"\n📊 Results:")
            print(f"   Allocated: {result['allocated']}/{result['target']} voices")
            print(f"   Elapsed time: {result['elapsed_time']:.3f}s")
        
        # Show final state
        print("\n📋 Final system state:")
        active_voices = [(v.id, v.midi_note) for v in fibril_system.voices if v.volume]
        if active_voices:
            for voice_id, midi_note in active_voices[:15]:  # Show first 15
                note_name = midi_to_note_name(midi_note)
                print(f"   Voice {voice_id:2d}: MIDI {midi_note:3d} ({note_name})")
            if len(active_voices) > 15:
                print(f"   ... and {len(active_voices) - 15} more")
        else:
            print("   No voices currently active")
        
        print(f"\n✅ System test completed successfully using {system_type} system!")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        print("\nThis might be due to:")
        print("- Missing or incomplete fibril_system initialization")
        print("- Import issues with fibril_classes or fibril_init")
        print("- System state inconsistencies")
    
    print("\n🎯 Done!")
