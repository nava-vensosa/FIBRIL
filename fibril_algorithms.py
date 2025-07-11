#!/usr/bin/env python3
"""
FIBRIL Algorithms - Probabilistic Harmony System

This module implements a probability-based voice allocation system that builds
harmonic probabilities through layered analysis and uses weighted random selection.
"""

import math
import random

try:
    from fibril_init import fibril_system
    print("✓ Successfully imported fibril_system")
    USING_MOCK = False
except Exception as e:
    print(f"⚠ Import failed: {e}")
    print("  Will create mock system for testing...")
    fibril_system = None  # Will be set by mock system
    USING_MOCK = True


# Global probability map and visualization tracking
probability_map = [0.0] * 128
voice_probability_history = []
selection_metadata = []

# Layer weights for probability building
LAYER_WEIGHTS = {
    'spatial': 0.25,
    'harmonic': 0.40,
    'interval': 0.35
}

def get_active_midi_notes():
    """Get list of currently active MIDI notes"""
    return [voice.midi_note for voice in fibril_system.voices if voice.volume and not voice.sustained]

def get_active_ranks():
    """Get list of currently active ranks (density > 0)"""
    return [rank for rank in fibril_system.ranks if rank.density > 0]

def calculate_target_voice_count(active_ranks, max_voices=8):
    """Calculate how many voices should be allocated based on rank density"""
    total_density = sum(rank.density for rank in active_ranks)
    return min(max_voices, total_density)

def rank_to_position(rank_number):
    """Convert rank number to (row, column) position on 4x2 interface grid"""
    # Layout:
    # Row 4 (top):    [R7] [R8]  
    # Row 3:          [R5] [R6]
    # Row 2:          [R3] [R4]  
    # Row 1 (bottom): [R1] [R2]
    # Left column: odd ranks, Right column: even ranks
    
    if rank_number % 2 == 1:  # Odd ranks - left column
        col = 0
        row = (rank_number + 1) // 2  # R1→1, R3→2, R5→3, R7→4
    else:  # Even ranks - right column
        col = 1
        row = rank_number // 2  # R2→1, R4→2, R6→3, R8→4
    
    return (row, col)

def calculate_spatial_clustering(active_ranks):
    """Calculate spatial clustering metrics for active ranks"""
    if not active_ranks:
        return (0, 0), 0.0, "dispersed"
    
    # Get positions for all active ranks
    positions = [rank_to_position(rank.number) for rank in active_ranks]
    
    # Calculate centroid (center point of active buttons)
    centroid_row = sum(pos[0] for pos in positions) / len(positions)
    centroid_col = sum(pos[1] for pos in positions) / len(positions)
    centroid = (centroid_row, centroid_col)
    
    # Calculate spread (variance from centroid)
    spread = 0.0
    for pos in positions:
        spread += ((pos[0] - centroid_row) ** 2 + (pos[1] - centroid_col) ** 2) ** 0.5
    spread = spread / len(positions)
    
    # Determine clustering mode
    CLUSTER_THRESHOLD = 1.2  # Tunable threshold
    cluster_mode = "clustered" if spread < CLUSTER_THRESHOLD else "dispersed"
    
    return centroid, spread, cluster_mode

def build_spatial_probability_layer(active_ranks):
    """Build spatial probability layer based on button clustering"""
    layer_probabilities = [0.0] * 128
    
    if not active_ranks:
        return layer_probabilities
    
    # Calculate spatial clustering
    centroid, spread, cluster_mode = calculate_spatial_clustering(active_ranks)
    
    # Keyboard center bias (around C4 = MIDI 60)
    keyboard_center = 60
    
    if cluster_mode == "clustered":
        # Clustered mode: concentrate notes in 2-3 octaves around a target point
        target_octave_offset = (centroid[0] - 2.5) * 12  # Center around row 2.5
        target_center = keyboard_center + target_octave_offset
        cluster_width = 24  # 2 octaves spread
        
        for midi in range(128):
            # Gaussian bias around target center
            distance = abs(midi - target_center)
            octave_bias = math.exp(-(distance ** 2) / (2 * (cluster_width / 3) ** 2))
            
            # Anti-muddiness adjustments
            if midi < 48:
                octave_bias *= 0.3
            elif midi < 60:
                octave_bias *= 0.7
            elif midi > 72:
                octave_bias *= 1.2
            
            layer_probabilities[midi] = octave_bias
    else:
        # Dispersed mode: spread notes across multiple octaves
        peak_octaves = [48, 60, 72, 84]  # C3, C4, C5, C6
        
        for midi in range(128):
            total_bias = 0.0
            for peak in peak_octaves:
                distance = abs(midi - peak)
                peak_bias = math.exp(-(distance ** 2) / (2 * (18) ** 2))
                total_bias += peak_bias
            
            # Anti-muddiness for dispersed mode
            if midi < 48:
                total_bias *= 0.1
            elif midi < 60:
                total_bias *= 0.5
            elif midi > 72:
                total_bias *= 1.5
            
            layer_probabilities[midi] = total_bias
    
    # Normalize layer
    max_prob = max(layer_probabilities) if max(layer_probabilities) > 0 else 1.0
    layer_probabilities = [p / max_prob for p in layer_probabilities]
    
    return layer_probabilities

def get_rank_harmonic_series(rank, key_center):
    """Get harmonic series for a rank with probability weights"""
    harmonic_map = {}
    
    # Get rank's root note
    if rank.tonicization == 8:  # Subtonic - use 3rd of key center
        rank_root = (key_center + 4) % 12
    else:
        scale_degree_offsets = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}
        offset = scale_degree_offsets.get(rank.tonicization, 0)
        rank_root = (key_center + offset) % 12
    
    # Get valid destinations for this rank
    valid_notes = rank.get_valid_destinations(key_center)
    
    # Map each note to its harmonic function and assign probability weight
    for note in valid_notes:
        if 0 <= note <= 127:
            note_pc = note % 12
            interval = (note_pc - rank_root) % 12
            
            # Assign probability weights based on harmonic function
            if interval == 0:  # Root
                weight = 0.25
            elif interval == 7:  # Fifth
                weight = 0.20
            elif interval in [3, 4]:  # Third (major/minor)
                weight = 0.15
            elif interval in [10, 11]:  # Seventh
                weight = 0.12
            elif interval == 2:  # 9th
                weight = 0.08
            elif interval in [5, 9]:  # 11th, 13th
                weight = 0.08
            else:
                weight = 0.03
            
            harmonic_map[note] = weight
    
    return harmonic_map

def build_harmonic_probability_layer(active_ranks, key_center):
    """Build harmonic probability layer based on rank destinations"""
    layer_probabilities = [0.0] * 128
    
    for rank in active_ranks:
        harmonic_series = get_rank_harmonic_series(rank, key_center)
        rank_density_multiplier = rank.density * 0.1  # Scale by density
        
        for note, weight in harmonic_series.items():
            if 0 <= note <= 127:
                # Add weighted probability, scaled by rank density
                layer_probabilities[note] += weight * (1.0 + rank_density_multiplier)
    
    # Normalize layer
    max_prob = max(layer_probabilities) if max(layer_probabilities) > 0 else 1.0
    layer_probabilities = [p / max_prob for p in layer_probabilities]
    
    return layer_probabilities

def analyze_intervals_to_active_voices(candidate_midi, active_notes):
    """Analyze intervallic relationships between candidate note and active voices"""
    if not active_notes:
        return 0.0
    
    total_score = 0.0
    
    for active_note in active_notes:
        interval = abs(candidate_midi - active_note) % 12
        
        # Special bias for 9th intervals (major 2nd = 2 semitones)
        if interval == 2:  # Major 9th bias
            total_score += 0.15
        elif interval == 10:  # Minor 7th - also consonant
            total_score += 0.08
        elif interval in [3, 4]:  # Major/minor 3rd
            total_score += 0.06
        elif interval == 7:  # Perfect 5th
            total_score += 0.05
        elif interval in [5, 9]:  # Perfect 4th, Major 6th
            total_score += 0.04
        elif interval == 0:  # Unison/octave - penalty for duplicates
            total_score -= 0.5
        elif interval == 1 or interval == 11:  # Minor 2nd, Major 7th - dissonant
            total_score -= 0.1
    
    return total_score / len(active_notes)  # Average score

def build_interval_probability_layer(active_notes):
    """Build interval probability layer based on relationships to active voices"""
    layer_probabilities = [0.0] * 128
    
    if not active_notes:
        # No active voices - return neutral probabilities
        return [0.1] * 128
    
    for midi in range(128):
        interval_score = analyze_intervals_to_active_voices(midi, active_notes)
        
        # Convert score to probability (ensuring non-negative)
        probability = max(0.0, 0.1 + interval_score)
        layer_probabilities[midi] = probability
    
    # Normalize layer
    max_prob = max(layer_probabilities) if max(layer_probabilities) > 0 else 1.0
    layer_probabilities = [p / max_prob for p in layer_probabilities]
    
    return layer_probabilities

def reset_probability_map():
    """Reset the global probability map to zeros"""
    global probability_map
    probability_map = [0.0] * 128

def apply_probability_layer(layer_probabilities, layer_weight):
    """Apply a probability layer to the global map with given weight"""
    global probability_map
    for i in range(128):
        probability_map[i] += layer_probabilities[i] * layer_weight

def normalize_probability_map():
    """Normalize the probability map to ensure values stay reasonable"""
    global probability_map
    max_prob = max(probability_map) if max(probability_map) > 0 else 1.0
    
    # Scale so maximum probability is around 0.7 (never guarantee anything)
    target_max = 0.7
    probability_map = [p * (target_max / max_prob) for p in probability_map]

def capture_probability_snapshot(voice_index):
    """Capture a deep copy of current probability map for visualization"""
    global voice_probability_history, probability_map
    
    # Ensure we have enough space in history
    while len(voice_probability_history) <= voice_index:
        voice_probability_history.append([0.0] * 128)
    
    # Deep copy current state
    voice_probability_history[voice_index] = probability_map.copy()

def weighted_random_selection(prob_map):
    """Select a MIDI note using weighted random selection from probability map"""
    # Create cumulative distribution
    total_probability = sum(prob_map)
    
    if total_probability <= 0:
        # Fallback to uniform random if no probabilities
        return random.randint(48, 84)  # Middle range fallback
    
    # Normalize to create proper probability distribution
    cumulative = []
    running_sum = 0.0
    for prob in prob_map:
        running_sum += prob / total_probability
        cumulative.append(running_sum)
    
    # Roll the dice
    roll = random.random()
    
    # Find which MIDI note the roll selected
    for midi, cum_prob in enumerate(cumulative):
        if roll <= cum_prob:
            return midi
    
    # Fallback (shouldn't happen)
    return len(cumulative) - 1

def find_available_voice():
    """Find an available voice slot (not active, not sustained)"""
    for voice in fibril_system.voices:
        if not voice.volume and not voice.sustained:
            return voice.id
    return None

def allocate_voice_safely(voice_id, midi_note):
    """Safely allocate a MIDI note to a specific voice"""
    if voice_id is None:
        return False
    
    # Validate inputs
    if not (1 <= voice_id <= 48):
        print(f"✗ Invalid voice ID: {voice_id}")
        return False
    
    if not (0 <= midi_note <= 127):
        print(f"✗ Invalid MIDI note: {midi_note}")
        return False
    
    # Get target voice
    target_voice = fibril_system.voices[voice_id - 1]
    
    # Check if voice is sustained
    if target_voice.sustained:
        print(f"✗ Cannot allocate to sustained voice {voice_id}")
        return False
    
    # Check for duplicates
    active_notes = get_active_midi_notes()
    if midi_note in active_notes:
        print(f"✗ MIDI note {midi_note} already in use")
        return False
    
    # Safe to allocate
    target_voice.midi_note = midi_note
    target_voice.volume = 1
    target_voice.sustained = False
    
    print(f"✓ Allocated MIDI {midi_note} to voice {voice_id}")
    return True

def record_selection_metadata(voice_number, selected_note, context):
    """Record metadata about a voice selection for visualization"""
    global selection_metadata
    
    # Ensure we have enough space
    while len(selection_metadata) <= voice_number:
        selection_metadata.append({})
    
    selection_metadata[voice_number] = {
        'voice_number': voice_number,
        'selected_note': selected_note,
        'selected_probability': probability_map[selected_note] if 0 <= selected_note < 128 else 0.0,
        **context  # Merge in additional context
    }

def initialize_visualization_tracking():
    """Initialize visualization tracking arrays"""
    global voice_probability_history, selection_metadata
    voice_probability_history = []
    selection_metadata = []

def get_visualization_data():
    """Get complete visualization data for p5.js"""
    return {
        'voice_count': len(voice_probability_history),
        'probability_maps': voice_probability_history,
        'selections': selection_metadata,
        'layer_weights': LAYER_WEIGHTS,
        'midi_range': 128
    }

def clear_visualization_history():
    """Clear visualization tracking data"""
    global voice_probability_history, selection_metadata
    voice_probability_history = []
    selection_metadata = []

def probabilistic_voice_allocation(max_voices=8):
    """
    Main probabilistic voice allocation function
    
    Args:
        max_voices (int): Maximum number of voices to allocate
        
    Returns:
        dict: Results including visualization data
    """
    print("🎲 Starting probabilistic voice allocation...")
    
    # Initialize tracking
    initialize_visualization_tracking()
    
    # Get active ranks and calculate target
    active_ranks = get_active_ranks()
    if not active_ranks:
        print("No active ranks - nothing to allocate")
        return {'allocated': 0, 'target': 0, 'spatial_mode': 'none'}
    
    target_voice_count = calculate_target_voice_count(active_ranks, max_voices)
    current_active = len(get_active_midi_notes())
    
    # Calculate spatial clustering info for context
    centroid, spread, cluster_mode = calculate_spatial_clustering(active_ranks)
    
    print(f"   Target voices: {target_voice_count}, Current: {current_active}")
    print(f"   Spatial mode: {cluster_mode} (spread: {spread:.2f})")
    print(f"   Active ranks: {[r.number for r in active_ranks]}")
    
    allocated_count = 0
    
    # Allocate voices one by one
    for voice_number in range(target_voice_count):
        print(f"\n   Voice {voice_number + 1}/{target_voice_count}:")
        
        # Reset and rebuild probability map
        reset_probability_map()
        
        # Build probability layers
        spatial_layer = build_spatial_probability_layer(active_ranks)
        harmonic_layer = build_harmonic_probability_layer(active_ranks, fibril_system.key_center)
        
        # Get current active notes for interval analysis
        current_active_notes = get_active_midi_notes()
        interval_layer = build_interval_probability_layer(current_active_notes)
        
        # Apply layers with weights
        apply_probability_layer(spatial_layer, LAYER_WEIGHTS['spatial'])
        apply_probability_layer(harmonic_layer, LAYER_WEIGHTS['harmonic'])
        apply_probability_layer(interval_layer, LAYER_WEIGHTS['interval'])
        
        # Normalize final map
        normalize_probability_map()
        
        # Capture snapshot for visualization
        capture_probability_snapshot(voice_number)
        
        # Select note using weighted random
        selected_note = weighted_random_selection(probability_map)
        
        # Find available voice and allocate
        voice_id = find_available_voice()
        if allocate_voice_safely(voice_id, selected_note):
            allocated_count += 1
            
            # Record metadata
            record_selection_metadata(voice_number, selected_note, {
                'spatial_mode': cluster_mode,
                'active_ranks': [r.number for r in active_ranks],
                'voice_id': voice_id,
                'centroid': centroid,
                'spread': spread
            })
            
            print(f"     Selected MIDI {selected_note} (probability: {probability_map[selected_note]:.3f})")
        else:
            print(f"     Failed to allocate voice")
            break
    
    print(f"\n✓ Probabilistic allocation complete: {allocated_count}/{target_voice_count} voices allocated")
    
    return {
        'allocated': allocated_count,
        'target': target_voice_count,
        'spatial_mode': cluster_mode,
        'visualization_data': get_visualization_data()
    }

def state_readout():
    """Complete state readout of the FIBRIL system"""
    print("\n=== FIBRIL Voice States ===")
    print("Voice | MIDI | Vol | Sustained")
    print("------|------|-----|----------")
    active_count = 0
    
    for voice in fibril_system.voices:
        midi_note = f"{voice.midi_note:3d}"
        volume = voice.volume
        sustained = "YES" if hasattr(voice, 'sustained') and voice.sustained else "NO"
        
        print(f"  {voice.id:2d}  | {midi_note} |  {volume}  |    {sustained}")
        
        if voice.volume:
            active_count += 1
    
    print(f"\nTotal active voices: {active_count}/48")
    
    # Show key system attributes
    print(f"\nKey system state:")
    print(f"  Key center: {fibril_system.key_center}")
    print(f"  Sustain: {fibril_system.sustain}")
    print(f"  Total voices: {len(fibril_system.voices)}")
    print(f"  Total ranks: {len(fibril_system.ranks)}")

def deallocate_all_voices():
    """Deallocate all non-sustained voices for testing"""
    deallocated = 0
    for voice in fibril_system.voices:
        if voice.volume and not voice.sustained:
            voice.volume = 0
            deallocated += 1
    print(f"✓ Deallocated {deallocated} voices")


def test_probabilistic_allocation():
    """Test the probabilistic allocation with simulated active ranks"""
    print("\n🧪 Testing probabilistic allocation with simulated data...")
    
    # Simulate some active ranks
    fibril_system.ranks[0].density = 2  # R1 
    fibril_system.ranks[2].density = 1  # R3
    fibril_system.ranks[4].density = 3  # R5
    
    # Set a key center
    fibril_system.key_center = 60  # C major
    
    print("Simulated active ranks:")
    for i, rank in enumerate(fibril_system.ranks):
        if rank.density > 0:
            print(f"  Rank {rank.number}: density {rank.density}, tonicization {rank.tonicization}")
    
    # Run allocation
    result = probabilistic_voice_allocation(max_voices=6)
    
    # Show results
    print(f"\nAllocation results:")
    print(f"  Allocated: {result['allocated']}/{result['target']} voices")
    print(f"  Spatial mode: {result['spatial_mode']}")
    
    # Show visualization data summary
    viz_data = result['visualization_data']
    print(f"\nVisualization data:")
    print(f"  Voice count: {viz_data['voice_count']}")
    print(f"  Probability maps captured: {len(viz_data['probability_maps'])}")
    print(f"  Selection metadata: {len(viz_data['selections'])}")
    
    # Show some probability statistics
    if viz_data['probability_maps']:
        first_map = viz_data['probability_maps'][0]
        max_prob = max(first_map)
        max_note = first_map.index(max_prob)
        print(f"  First voice saw max probability {max_prob:.3f} at MIDI {max_note}")
    
    # Reset for clean state
    deallocate_all_voices()
    for rank in fibril_system.ranks:
        rank.density = 0


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
            self.gci = 0
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
            self.key_center = 60
            self.sustain = 0
    
    return MockSystem()

# Try to use real system, fall back to mock if import fails
try:
    # Test if fibril_system is available
    fibril_system.voices[0]
    print("✓ Using real fibril_system")
    USING_MOCK = False
except (NameError, AttributeError, Exception):
    print("⚠ fibril_system unavailable, using mock system")
    fibril_system = create_mock_fibril_system()
    USING_MOCK = True


if __name__ == "__main__":
    print("🎵 Probabilistic Harmony System Test")
    print("="*50)
    
    try:
        # Initialize system (real or mock)
        if USING_MOCK:
            print("Initializing mock system...")
            system_type = "mock"
        else:
            system_type = "real"
        
        print(f"Using {system_type} fibril_system")
        print(f"   System has {len(fibril_system.voices)} voices")
        print(f"   System has {len(fibril_system.ranks)} ranks")
        print(f"   Key center: {fibril_system.key_center}")
        
        # Check for active ranks
        print("\n2. Checking active ranks...")
        active_ranks = get_active_ranks()
        print(f"   Found {len(active_ranks)} active ranks")
        
        if len(active_ranks) == 0:
            print("   No active ranks detected, setting up test scenario...")
            
            # Set up test scenario
            fibril_system.key_center = 60  # C major
            fibril_system.ranks[0].density = 2  # R1 with density 2
            fibril_system.ranks[2].density = 1  # R3 with density 1  
            fibril_system.ranks[4].density = 3  # R5 with density 3
            
            # Verify setup
            active_ranks = get_active_ranks()
            print(f"   Test setup complete: {len(active_ranks)} active ranks")
            for rank in active_ranks:
                print(f"     Rank {rank.number}: density {rank.density}, tonicization {rank.tonicization}")
        
        # Test the probabilistic allocation
        print("\n3. Running probabilistic voice allocation...")
        result = probabilistic_voice_allocation(max_voices=4)
        
        # Show results
        print(f"\n4. Results:")
        print(f"   Allocated: {result['allocated']}/{result['target']} voices")
        print(f"   Spatial mode: {result['spatial_mode']}")
        
        # Show visualization data
        if 'visualization_data' in result:
            viz = result['visualization_data']
            print(f"   Visualization data captured: {viz['voice_count']} voice selections")
            
            if viz['selections']:
                print("   Selected notes:")
                for i, selection in enumerate(viz['selections']):
                    note = selection['selected_note']
                    prob = selection['selected_probability']
                    voice_id = selection.get('voice_id', 'unknown')
                    print(f"     Voice {i+1}: MIDI {note} (prob: {prob:.3f}, voice_id: {voice_id})")
        
        # Show current voice states
        print("\n5. Current voice states:")
        active_voices = [(v.id, v.midi_note) for v in fibril_system.voices if v.volume]
        if active_voices:
            for voice_id, midi_note in active_voices[:10]:  # Show first 10
                print(f"   Voice {voice_id}: MIDI {midi_note}")
            if len(active_voices) > 10:
                print(f"   ... and {len(active_voices) - 10} more")
        else:
            print("   No voices currently active")
        
        # Clean up for next run
        print("\n6. Cleaning up...")
        deallocate_all_voices()
        for rank in fibril_system.ranks:
            rank.density = 0
        fibril_system.key_center = 0
        
        print(f"✓ Test completed successfully using {system_type} system!")
        
    except Exception as e:
        print(f"\n✗ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        print("\nThis might be due to:")
        print("- Missing or incomplete fibril_system initialization")
        print("- Import issues with fibril_classes or fibril_init")
        print("- System state inconsistencies")
    
    print("\nDone!")
