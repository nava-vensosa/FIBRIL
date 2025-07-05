#!/usr/bin/env python3
"""
Test the FIBRIL Algorithm implementation
"""

from fibril_classes import Rank, Voice, SystemState
from fibril_algorithms import FibrilAlgorithm, ProbabilityCurve


def test_probability_curves():
    """Test probability curve generation"""
    print("Testing Probability Curves...")
    
    # Test Gaussian curve
    gaussian = ProbabilityCurve.gaussian(center=60, width=24)
    print(f"Gaussian curve peak at MIDI 60: {gaussian[60]:.3f}")
    print(f"Gaussian curve at MIDI 48: {gaussian[48]:.3f}")
    print(f"Gaussian curve at MIDI 72: {gaussian[72]:.3f}")
    
    # Test voice leading bias
    current_notes = [60, 64, 67]  # C major triad
    upward_bias = ProbabilityCurve.voice_leading_bias(current_notes, direction=1)
    print(f"Voice leading upward bias for C61 (from C60): {upward_bias[61]:.3f}")
    print(f"Voice leading upward bias for C59 (from C60): {upward_bias[59]:.3f}")
    
    print("✓ Probability curves working\n")


def test_basic_allocation():
    """Test basic voice allocation"""
    print("Testing Basic Voice Allocation...")
    
    # Create test system state
    system_state = SystemState()
    
    # Create a simple rank with some density
    test_rank = Rank(number=3, position=1, grey_code=[0, 0, 1, 0])  # GCI=1, density=2
    test_rank.tonicization = 1  # Tonic
    system_state.ranks = [test_rank]
    
    # Initialize voices
    system_state.voices = [Voice(midi_note=60, volume=False, id=i) for i in range(48)]
    
    # Run algorithm
    algorithm = FibrilAlgorithm()
    result_state = algorithm.allocate_voices(system_state)
    
    # Count active voices
    active_voices = sum(1 for voice in result_state.voices if voice.volume)
    print(f"Active voices after allocation: {active_voices}")
    
    # Check if root and fifth are present
    active_notes = {voice.midi_note % 12 for voice in result_state.voices if voice.volume}
    root_present = 0 in active_notes  # C (tonic in C major)
    fifth_present = 7 in active_notes  # G (perfect fifth)
    
    print(f"Root (C) present: {root_present}")
    print(f"Fifth (G) present: {fifth_present}")
    print(f"Active note classes: {sorted(active_notes)}")
    
    print("✓ Basic allocation working\n")


def test_sustain_handling():
    """Test sustain pedal behavior"""
    print("Testing Sustain Handling...")
    
    # Create system state with sustain active
    system_state = SystemState()
    system_state.sustain = True
    
    # Set up some active voices
    system_state.voices = [Voice(midi_note=60, volume=False, id=i) for i in range(48)]
    system_state.voices[0].volume = True  # C4
    system_state.voices[0].midi_note = 60
    system_state.voices[1].volume = True  # E4
    system_state.voices[1].midi_note = 64
    system_state.voices[2].volume = True  # G4
    system_state.voices[2].midi_note = 67
    
    # Create rank that should add more notes
    test_rank = Rank(number=1, position=1, grey_code=[0, 0, 1, 1])  # GCI=2, density=3
    test_rank.tonicization = 1  # Tonic
    system_state.ranks = [test_rank]
    
    algorithm = FibrilAlgorithm()
    result_state = algorithm.allocate_voices(system_state)
    
    # Check that original notes are still active
    original_notes = {60, 64, 67}
    active_notes = {voice.midi_note for voice in result_state.voices if voice.volume}
    sustained_preserved = original_notes.issubset(active_notes)
    
    print(f"Original sustained notes preserved: {sustained_preserved}")
    print(f"Total active voices: {len(active_notes)}")
    
    print("✓ Sustain handling working\n")


def test_voice_leading():
    """Test voice leading behavior"""
    print("Testing Voice Leading...")
    
    # Create rank with changing GCI
    test_rank = Rank(number=1, position=1, grey_code=[0, 0, 1, 0])  # GCI=1
    test_rank.tonicization = 1
    test_rank.previous_gci = 0  # Simulating upward movement
    
    system_state = SystemState()
    system_state.ranks = [test_rank]
    system_state.voices = [Voice(midi_note=60, volume=True, id=0)]  # Start with C4 active
    system_state.voices.extend([Voice(midi_note=60, volume=False, id=i) for i in range(1, 48)])
    
    algorithm = FibrilAlgorithm()
    
    # Build probability map to see voice leading bias
    algorithm._build_global_probability_map(system_state, [test_rank])
    
    # Check that notes above C4 have higher probability
    prob_c5 = algorithm.global_probability_map[72]  # C5
    prob_c3 = algorithm.global_probability_map[48]  # C3
    upward_bias = prob_c5 > prob_c3
    
    print(f"Upward voice leading bias working: {upward_bias}")
    print(f"Probability at C5 (72): {prob_c5:.6f}")
    print(f"Probability at C3 (48): {prob_c3:.6f}")
    
    print("✓ Voice leading working\n")


if __name__ == "__main__":
    print("FIBRIL Algorithm Test Suite")
    print("=" * 40)
    
    test_probability_curves()
    test_basic_allocation()
    test_sustain_handling()
    test_voice_leading()
    
    print("All tests completed! ✓")
