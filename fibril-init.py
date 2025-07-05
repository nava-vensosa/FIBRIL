#!/usr/bin/env python3
"""
FIBRIL Initialization

Initialize all rank and voice objects for the FIBRIL system:
- 8 Rank objects (numbered 1-8)
- 48 Voice objects (numbered 1-48)
"""

import sys
import importlib.util

# Import fibril_classes
spec = importlib.util.spec_from_file_location("fibril_classes", "fibril-classes.py")
fibril_classes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fibril_classes)

from typing import List


class FibrilSystem:
    """Container for all FIBRIL system objects"""
    
    def __init__(self):
        # Initialize 8 ranks with default values
        self.ranks = []
        for i in range(8):
            rank = fibril_classes.Rank(
                number=i + 1,           # Rank number 1-8
                position=i + 1,         # Initial position 1-8 
                grey_code=[0, 0, 0, 0]  # Default grey code
            )
            self.ranks.append(rank)
        
        # Initialize 48 voices with default values
        self.voices = []
        for i in range(48):
            voice = fibril_classes.Voice(
                midi_note=60,           # Default middle C
                volume=False,           # Default off
                id=i + 1               # Voice ID 1-48
            )
            self.voices.append(voice)
        
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
            old_grey_code = rank.grey_code.copy()
            
            # Set the specific bit (ensure it's 0 or 1)
            rank.grey_code[bit_index] = 1 if value else 0
            
            # Recalculate GCI and density
            rank.__post_init__()
            
            print(f"Rank {rank_num}: Updated bit {bit_pattern} -> {rank.grey_code[bit_index]}")
            print(f"  Grey code: {old_grey_code} -> {rank.grey_code}")
            print(f"  GCI: {rank.gci}, Density: {rank.density}")
        else:
            print(f"Warning: Unknown bit pattern '{bit_pattern}' for rank {rank_num}")
    
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
