#!/usr/bin/env python3
"""
Test the new GCI-based voice allocation system
"""

import sys
import os
sys.path.append('/workspaces/FIBRIL')

import fibril_init
import fibril_algorithms

def test_new_system():
    """Test the new GCI-based voice allocation with density mapping"""
    
    print("🎯 Testing New GCI-Based Voice Allocation System")
    print("=" * 55)
    
    # Test different rank configurations
    test_configs = [
        {
            "name": "Single rank with density 2",
            "ranks": [(1, [1, 0, 0, 0])]  # GCI=1, density=2
        },
        {
            "name": "Two ranks with different densities", 
            "ranks": [(1, [1, 1, 0, 0]), (3, [0, 1, 0, 0])]  # GCI=3 density=3, GCI=2 density=2
        },
        {
            "name": "High density rank",
            "ranks": [(2, [1, 1, 1, 1])]  # GCI=15, density=6
        }
    ]
    
    for i, config in enumerate(test_configs):
        print(f"\n--- Test {i+1}: {config['name']} ---")
        
        # Reset all ranks
        for rank in fibril_algorithms.fibril_system.ranks:
            rank.grey_code = [0, 0, 0, 0]
            rank.gci = 0
            rank.density = 0
        fibril_algorithms.deallocate_all_voices()
        
        # Set up test configuration
        total_expected_voices = 0
        for rank_num, grey_code in config["ranks"]:
            rank = fibril_algorithms.fibril_system.ranks[rank_num - 1]
            rank.grey_code = grey_code
            rank.__post_init__()  # Recalculate GCI and density
            
            middle_midi = fibril_algorithms.get_rank_middle_octave_midi(rank)
            octave_spread = fibril_algorithms.get_rank_octave_spread(rank)
            note_name = fibril_algorithms.midi_to_note_name(middle_midi)
            
            print(f"  Rank {rank_num}: grey={grey_code}, GCI={rank.gci}, density={rank.density}")
            print(f"    Middle: {note_name} (MIDI {middle_midi}), Spread: ±{octave_spread} octaves")
            
            total_expected_voices += rank.density
        
        print(f"  Expected total voices: {total_expected_voices}")
        
        # Run allocation
        result = fibril_algorithms.probabilistic_voice_allocation(max_voices=48)
        
        print(f"  Actual allocated voices: {result['allocated']}")
        print(f"  Target voices: {result['target']}")
        
        # Show which voices were allocated
        active_voices = [v for v in fibril_algorithms.fibril_system.voices if v.volume]
        if active_voices:
            print("  Allocated voices:")
            for voice in active_voices[:5]:  # Show first 5
                note_name = fibril_algorithms.midi_to_note_name(voice.midi_note)
                print(f"    Voice {voice.id}: MIDI {voice.midi_note} ({note_name})")
            if len(active_voices) > 5:
                print(f"    ... and {len(active_voices) - 5} more")
        
        print(f"  ✓ Test completed")
    
    # Reset system
    for rank in fibril_algorithms.fibril_system.ranks:
        rank.grey_code = [0, 0, 0, 0]
        rank.gci = 0
        rank.density = 0
    fibril_algorithms.deallocate_all_voices()
    
    print(f"\n✅ All tests completed!")

if __name__ == "__main__":
    test_new_system()
