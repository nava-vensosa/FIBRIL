#!/usr/bin/env python3
"""
Test harmonic degree fitting to major scale and whole tone scale
"""

import sys
import importlib.util

# Import fibril_classes
import fibril_classes

def test_harmonic_destinations():
    """Test the harmonic destination calculation"""
    print("Testing Harmonic Destination Calculation")
    print("=" * 50)
    
    # Test with C major (key_center = 0)
    key_center = 0  # C major
    
    print(f"Key Center: {key_center} (C major)")
    print("Major scale notes: C D E F G A B")
    print("Whole tone scale: C D E F# G# A#")
    print()
    
    # Test each rank
    for rank_num in range(1, 9):
        tonicization = rank_num  # R1=tonic, R2=supertonic, etc.
        rank = fibril_classes.Rank(
            number=rank_num,
            position=rank_num,
            grey_code=[1, 0, 0, 0],  # Some activity
            tonicization=tonicization
        )
        
        destinations = rank.get_valid_destinations(key_center)
        
        # Convert MIDI to note names for first octave
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        first_octave_notes = [dest for dest in destinations if 48 <= dest <= 72]  # Around middle C
        note_name_list = [f"{note_names[note % 12]}{note // 12 - 1}" for note in first_octave_notes[:10]]
        
        scale_type = "Whole Tone" if tonicization == 8 else "Major"
        tonicization_names = {1: "tonic", 2: "supertonic", 3: "mediant", 4: "subdominant", 
                             5: "dominant", 6: "submediant", 7: "leading tone", 8: "subtonic"}
        
        print(f"R{rank_num} ({tonicization_names[tonicization]}) - {scale_type} scale:")
        print(f"  Sample destinations: {note_name_list}")
        print(f"  Total destinations: {len(destinations)} MIDI notes")
        print()

def test_specific_rank():
    """Test a specific rank in detail"""
    print("\n" + "=" * 50)
    print("Detailed Test: R1 (Tonic) in C Major")
    print("=" * 50)
    
    rank = fibril_classes.Rank(
        number=1,
        position=1,
        grey_code=[1, 0, 0, 0],
        tonicization=1  # Tonic
    )
    
    key_center = 0  # C major
    destinations = rank.get_valid_destinations(key_center)
    
    # Show first few octaves
    for octave in range(3, 6):  # Show octaves 3, 4, 5
        octave_notes = [dest for dest in destinations if octave * 12 <= dest < (octave + 1) * 12]
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note_list = [f"{note_names[note % 12]}" for note in octave_notes]
        print(f"Octave {octave}: {note_list}")

if __name__ == "__main__":
    test_harmonic_destinations()
    test_specific_rank()
