#!/usr/bin/env python3
"""
Test the octave separation heuristic for FIBRIL ranks
"""

import sys
sys.path.append('.')

from fibril_init import fibril_system
from fibril_algorithms import FibrilAlgorithm

def test_octave_separation():
    """Test how different rank priorities affect octave centers"""
    print("=" * 70)
    print("FIBRIL OCTAVE SEPARATION HEURISTIC TEST")
    print("=" * 70)
    print("Formula: octave_number = (priority + 7) / 2")
    print("Center MIDI = key_center + (octave_number - 4) * 12")
    print("(Octave numbers are relative to key center at octave 4)")
    print()
    
    key_center = 60  # C4 for example
    
    print("Priority | Octave Number | Center MIDI | Relative to Key | Notes")
    print("---------|---------------|-------------|-----------------|------------------")
    
    for priority in range(1, 9):
        octave_number = (priority + 7) / 2
        center_midi = key_center + (octave_number - 4) * 12
        octave_display = f"{octave_number:.1f}" if octave_number != int(octave_number) else str(int(octave_number))
        
        octave_diff = octave_number - 4
        if octave_diff == 0:
            relative_desc = "at key center"
        elif octave_diff > 0:
            relative_desc = f"{octave_diff:.1f} oct above" if octave_diff != int(octave_diff) else f"{int(octave_diff)} oct above"
        else:
            relative_desc = f"{abs(octave_diff):.1f} oct below" if octave_diff != int(octave_diff) else f"{int(abs(octave_diff))} oct below"
        
        description = ""
        if priority <= 2:
            description = "High priority - center octaves"
        elif priority <= 4:
            description = "Medium priority - higher octaves"
        else:
            description = "Low priority - high octaves"
        
        print(f"   {priority}     |     {octave_display:4s}      |    {center_midi:5.1f}    |  {relative_desc:14s} | {description}")
    
    print()
    print("This creates natural voice separation:")
    print("• Priority 1: Octave 4 (at key center)")
    print("• Priority 2: Octave 4.5 (half octave above key center)")
    print("• Priority 3: Octave 5 (one octave above key center)")
    print("• Priority 8: Octave 7.5 (3.5 octaves above key center)")
    print("• Lower priority ranks voice progressively higher")
    print()
    
    # Test with actual system
    print("Testing with live FIBRIL system...")
    print("Setting up ranks with different priorities...")
    
    system = fibril_system.system_state
    algorithm = FibrilAlgorithm()
    
    # Set up different rank priorities and densities
    system.ranks[0].priority = 1  # R1 - highest priority
    system.ranks[0].grey_code = [1, 1, 0, 0]  # Some density
    system.ranks[0].__post_init__()
    
    system.ranks[6].priority = 7  # R7 - low priority  
    system.ranks[6].grey_code = [1, 1, 0, 0]  # Same density
    system.ranks[6].__post_init__()
    
    print(f"\nR1 priority {system.ranks[0].priority}, density {system.ranks[0].density}")
    print(f"R7 priority {system.ranks[6].priority}, density {system.ranks[6].density}")
    
    # Run algorithm
    print("\nRunning algorithm with octave separation...")
    new_state = algorithm.allocate_voices(system)
    
    # Analyze results
    active_voices = [(v.id, v.midi_note) for v in new_state.voices if v.volume]
    if active_voices:
        active_voices.sort(key=lambda x: x[1])  # Sort by MIDI note
        print(f"\nAllocated {len(active_voices)} voices:")
        print("Voice ID | MIDI | Octave | Note")
        print("---------|------|--------|------")
        for voice_id, midi in active_voices[:10]:  # Show first 10
            octave = midi // 12 - 1
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            note = note_names[midi % 12]
            print(f"   {voice_id:3d}   | {midi:3d}  |   {octave}    | {note}{octave}")
    else:
        print("No voices allocated")
    
    print("\n✅ Octave separation test complete!")

if __name__ == "__main__":
    test_octave_separation()
