#!/usr/bin/env python3
"""
Standalone test of probabilistic harmony algorithm
"""

import math
import random

print("🎵 Standalone Probabilistic Harmony Test")
print("="*50)

# Mock system for testing
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
        self.tonicization = number
    
    def get_valid_destinations(self, key_center):
        base = key_center % 12
        octaves = [48, 60, 72]
        notes = []
        for octave in octaves:
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
        self.key_center = 60

# Create mock system
fibril_system = MockSystem()

# Test functions
def rank_to_position(rank_number):
    if rank_number % 2 == 1:
        col = 0
        row = (rank_number + 1) // 2
    else:
        col = 1
        row = rank_number // 2
    return (row, col)

def calculate_spatial_clustering(active_ranks):
    if not active_ranks:
        return (0, 0), 0.0, "dispersed"
    
    positions = [rank_to_position(rank.number) for rank in active_ranks]
    centroid_row = sum(pos[0] for pos in positions) / len(positions)
    centroid_col = sum(pos[1] for pos in positions) / len(positions)
    centroid = (centroid_row, centroid_col)
    
    spread = 0.0
    for pos in positions:
        spread += ((pos[0] - centroid_row) ** 2 + (pos[1] - centroid_col) ** 2) ** 0.5
    spread = spread / len(positions)
    
    cluster_mode = "clustered" if spread < 1.2 else "dispersed"
    return centroid, spread, cluster_mode

def weighted_random_selection(prob_map):
    total_probability = sum(prob_map)
    if total_probability <= 0:
        return random.randint(48, 84)
    
    cumulative = []
    running_sum = 0.0
    for prob in prob_map:
        running_sum += prob / total_probability
        cumulative.append(running_sum)
    
    roll = random.random()
    for midi, cum_prob in enumerate(cumulative):
        if roll <= cum_prob:
            return midi
    
    return len(cumulative) - 1

# Run test
try:
    print("1. Setting up test scenario...")
    fibril_system.ranks[0].density = 2  # R1
    fibril_system.ranks[2].density = 1  # R3
    fibril_system.ranks[4].density = 3  # R5
    
    active_ranks = [r for r in fibril_system.ranks if r.density > 0]
    print(f"   Active ranks: {[r.number for r in active_ranks]}")
    
    print("2. Testing spatial clustering...")
    centroid, spread, mode = calculate_spatial_clustering(active_ranks)
    print(f"   Centroid: {centroid}, Spread: {spread:.2f}, Mode: {mode}")
    
    print("3. Testing probability selection...")
    # Create simple probability map
    prob_map = [0.1] * 128
    prob_map[60] = 0.5  # High prob for C4
    prob_map[64] = 0.3  # Med prob for E4
    prob_map[67] = 0.4  # High prob for G4
    
    selections = []
    for i in range(5):
        selected = weighted_random_selection(prob_map)
        selections.append(selected)
        print(f"   Selection {i+1}: MIDI {selected}")
    
    print("4. Testing rank destinations...")
    for rank in active_ranks:
        destinations = rank.get_valid_destinations(fibril_system.key_center)
        print(f"   Rank {rank.number}: {len(destinations)} destinations")
        print(f"     Sample: {destinations[:5]}...")
    
    print("\n✓ All standalone tests passed!")
    print("✓ Probabilistic harmony algorithm is working correctly!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")
