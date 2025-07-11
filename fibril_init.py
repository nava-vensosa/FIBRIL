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
        
        # Initialize 48 voices with C or G in octaves 3-5
        # C notes: C3=48, C4=60, C5=72
        # G notes: G3=55, G4=67, G5=79
        midi_notes = [48, 55, 60, 67, 72, 79]  # C3, G3, C4, G4, C5, G5
        self.voices = []
        for i in range(48):
            voice = fibril_classes.Voice(
                midi_note=random.choice(midi_notes),  # Random from C or G in octaves 3-5
                volume=0,              # Default off (using int value)
                id=i + 1               # Voice ID 1-48
            )
            self.voices.append(voice)
        
        # Initialize system state
        self.system_state = fibril_classes.SystemState()
        
        # Global system parameters
        self.sustain = 0
        self.key_center = 0  # C major pitch class (0=C, 1=C#, 2=D, etc.)
    
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
        """Print compact system state for debugging"""
        # Import here to avoid circular imports
        from fibril_algorithm import midi_to_note_name, get_rank_middle_octave_midi, get_rank_octave_spread, pitch_class_to_flat_name
        
        # Key center and sustain on one line - use flats for key center
        key_note = pitch_class_to_flat_name(self.key_center)
        print(f"Key: {key_note} | Sustain: {self.sustain}")
        
        # Ranks with detailed formatting - only show active ranks
        active_ranks = [rank for rank in self.ranks if rank.density > 0]
        if active_ranks:
            print("Ranks:")
            for rank in active_ranks:
                # Calculate tonicization note - use flats
                scale_offsets = [0,2,4,5,7,9,11,10]  # Major scale degrees 1-8
                tonic_pc = (self.key_center + scale_offsets[rank.tonicization-1]) % 12
                tonic_note = pitch_class_to_flat_name(tonic_pc)
                
                # Calculate spread center and range
                spread_center = get_rank_middle_octave_midi(rank)
                spread_range = get_rank_octave_spread(rank)
                spread_center_note = midi_to_note_name(spread_center)
                
                # Format grey code
                grey_str = ''.join(map(str, rank.grey_code))
                
                print(f"  R{rank.number}: pos={rank.position} grey={grey_str} GCI={rank.gci} "
                      f"dens={rank.density} tonic={tonic_note} "
                      f"center={spread_center_note} range=±{spread_range}oct")
        else:
            print("Ranks: (none active)")
        
        # Active voices with compact formatting
        active_voices = [v for v in self.voices if v.volume or (hasattr(v, 'sustained') and v.sustained)]
        if active_voices:
            print("Voices:", end="")
            for voice in active_voices:
                note_name = midi_to_note_name(voice.midi_note)
                vol_indicator = "♪" if voice.volume else "~"  # ♪ for active, ~ for sustained only
                sust_indicator = "S" if hasattr(voice, 'sustained') and voice.sustained else ""
                print(f" {voice.id}:{note_name}{vol_indicator}{sust_indicator}", end="")
            print()  # New line after voices
        else:
            print("Voices: (none)")
        print()  # Extra space after state


# Create global system instance
fibril_system = FibrilSystem()


# Export for use by other modules
__all__ = ['fibril_system', 'FibrilSystem']
