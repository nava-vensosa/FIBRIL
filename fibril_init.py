#!/usr/bin/env python3
"""
FIBRIL Initialization

Initialize all rank and voice objects for the FIBRIL system:
- 8 Rank objects (numbered 1-8)
- 48 Voice objects (numbered 1-48)
"""

import sys
import importlib.util
import random

# Import fibril_classes
import fibril_classes

from typing import List


class FibrilSystem:
    """Container for all FIBRIL system objects"""
    
    def __init__(self):
        # Rank assignments to scale degrees:
        # R3→tonic(1), R4→subdominant(4), R2→supertonic(2), R6→dominant(5), 
        # R1→submediant(6), R5→mediant(3), R7→leading(7), R8→subtonic(8)
        rank_tonicizations = {
            1: 6,  # R1 plays submediant (scale degree 6)
            2: 2,  # R2 plays supertonic (scale degree 2)  
            3: 1,  # R3 plays tonic (scale degree 1)
            4: 4,  # R4 plays subdominant (scale degree 4)
            5: 3,  # R5 plays mediant (scale degree 3)
            6: 5,  # R6 plays dominant (scale degree 5)
            7: 7,  # R7 plays leading tone (scale degree 7)
            8: 8   # R8 plays subtonic (scale degree 8)
        }
        
        # Priority order: [3, 4, 2, 6, 1, 5, 7, 8]
        priority_order = [3, 4, 2, 6, 1, 5, 7, 8]
        rank_positions = {rank_num: pos + 1 for pos, rank_num in enumerate(priority_order)}
        
        # Initialize 8 ranks with correct tonicizations and positions
        self.ranks = []
        for i in range(8):
            rank_number = i + 1
            rank = fibril_classes.Rank(
                number=rank_number,                        # Rank number 1-8
                position=rank_positions[rank_number],      # Position based on priority order
                grey_code=[0, 0, 0, 0],                   # Default grey code
                tonicization=rank_tonicizations[rank_number]  # Scale degree to play
            )
            self.ranks.append(rank)
        
        # Initialize 48 voices with random MIDI notes from specified set
        midi_notes = [48, 55, 60, 67, 72]
        self.voices = []
        for i in range(48):
            voice = fibril_classes.Voice(
                midi_note=random.choice(midi_notes),  # Random from (48, 55, 60, 67, 72)
                volume=False,           # Default off
                id=i + 1               # Voice ID 1-48
            )
            self.voices.append(voice)
        
        # Initialize system state
        self.system_state = fibril_classes.SystemState()
        
        # Global system parameters
        self.sustain = 0
        self.key_center = 0
    
    def get_rank(self, number: int):
        """Get rank by number (1-8)"""
        if 1 <= number <= 8:
            return self.ranks[number - 1]
        raise ValueError(f"Rank number must be 1-8, got {number}")
    
    def get_voice(self, id: int):
        """Get voice by ID (1-48)"""
        if 1 <= id <= 48:
            return self.voices[id - 1]
        raise ValueError(f"Voice ID must be 1-48, got {id}")
    
    def update_rank_grey_bit(self, rank_num: int, bit_pattern: str, value: int):
        """Update a specific bit in a rank's grey code"""
        rank = self.get_rank(rank_num)
        
        bit_map = {'1000': 0, '0100': 1, '0010': 2, '0001': 3}
        if bit_pattern in bit_map:
            bit_index = bit_map[bit_pattern]
            
            # Set the specific bit (ensure it's 0 or 1)
            rank.grey_code[bit_index] = 1 if value else 0
            
            # Recalculate GCI and density
            rank.__post_init__()
    
    def update_rank_position(self, rank_num: int, position: int):
        """Update rank position"""
        rank = self.get_rank(rank_num)
        rank.position = position
    
    def print_system_state(self):
        """Print current system state for debugging"""
        print("\n=== FIBRIL System State ===")
        print(f"Sustain: {self.sustain}")
        print(f"Key Center: {self.key_center}")
        print("\nRanks:")
        for rank in self.ranks:
            print(f"  Rank {rank.number}: pos={rank.position}, "
                  f"grey={rank.grey_code}, gci={rank.gci}, density={rank.density}")
        print("\nActive Voices:")
        active_voices = [v for v in self.voices if v.volume]
        if active_voices:
            for voice in active_voices:
                print(f"  Voice {voice.id}: MIDI={voice.midi_note}, Volume={voice.volume}")
        else:
            print("  No active voices")
        print("=" * 30)


# Create global system instance
fibril_system = FibrilSystem()


# Export for use by other modules
__all__ = ['fibril_system', 'FibrilSystem']
