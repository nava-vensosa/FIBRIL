#!/usr/bin/env python3
"""
FIBRIL Algorithm Classes - Cascading Harmonic Construction System

This module implements the core classes for the normalized probability distribution
system with cascading harmonic relationships and rank-by-rank processing.
"""

import math
import random
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass


# ============================================================================
# CONFIGURATION CLASSES
# ============================================================================

@dataclass
class AlgorithmParameters:
    """Centralized parameter configuration for the algorithm"""
    # Probability Map Parameters
    NORMALIZATION_TOLERANCE: float = 1e-6
    MIN_PROBABILITY: float = 1e-8
    
    # Extreme Range Blocking
    LOW_RANGE_MAX: int = 14
    HIGH_RANGE_MIN: int = 113
    
    # Rank Spread
    STRICT_SPREAD_ENFORCEMENT: bool = True
    SPREAD_FALLOFF_FACTOR: float = 0.1
    
    # Key Center Adherence
    ALLOW_SUBTONIC_CHROMATICISM: bool = True
    OUT_OF_KEY_PENALTY: float = 0.0
    
    # Root Voicing
    ROOT_FORCE_PROBABILITY: float = 0.85
    ROOT_BOOST_FACTOR: float = 5.0
    
    # Perfect Intervals
    PERFECT_FIFTH_BOOST: float = 4.0
    PERFECT_FOURTH_BOOST: float = 3.0
    OCTAVE_BOOST: float = 2.0
    COMPOUND_INTERVAL_DECAY: float = 0.7
    
    # Harmonic Functions
    ROOT_WEIGHT: float = 0.30
    FIFTH_WEIGHT: float = 0.25
    THIRD_WEIGHT: float = 0.20
    SEVENTH_WEIGHT: float = 0.15
    NINTH_WEIGHT: float = 0.10
    OTHER_WEIGHT: float = 0.05
    
    # Spatial Preferences
    GAUSSIAN_STRENGTH: float = 2.0
    SPREAD_MULTIPLIER: float = 1.0
    CENTER_BIAS_FACTOR: float = 1.5
    
    # Processing Control
    RANK_PRIORITY_ORDER: List[int] = None
    MAX_TOTAL_VOICES: int = 48
    MAX_SELECTION_ATTEMPTS: int = 100
    ALLOCATION_TIMEOUT: float = 10.0
    
    def __post_init__(self):
        if self.RANK_PRIORITY_ORDER is None:
            self.RANK_PRIORITY_ORDER = [3, 4, 2, 6, 1, 5, 7, 8]

@dataclass
class DebugSettings:
    """Debug and logging configuration"""
    DEBUG_VERBOSE: bool = False
    PRINT_PROBABILITY_MAPS: bool = False
    PRINT_CONSTRAINT_APPLICATIONS: bool = False
    PRINT_SELECTIONS: bool = False
    SNAPSHOT_FREQUENCY: str = "every_selection"
    MAX_HISTORY_SIZE: int = 1000


# ============================================================================
# CORE PROBABILITY MANAGEMENT
# ============================================================================

class NormalizedProbabilityMap:
    """
    Maintains a 128-element probability array that always sums to 1.0
    Handles all probability modifications with automatic rebalancing
    """
    
    def __init__(self, params: AlgorithmParameters):
        self.params = params
        self.probabilities = [0.0] * 128
        self.forbidden_notes: Set[int] = set()
        self.initialize_uniform()
    
    def initialize_uniform(self):
        """Set all notes to uniform probability (1/128)"""
        uniform_prob = 1.0 / 128
        self.probabilities = [uniform_prob] * 128
        self.forbidden_notes.clear()
    
    def boost_notes(self, midi_list: List[int], factor: float):
        """Multiply specified notes by factor, then rebalance"""
        for midi in midi_list:
            if 0 <= midi <= 127 and midi not in self.forbidden_notes:
                self.probabilities[midi] *= factor
        self.rebalance()
    
    def zero_notes(self, midi_list: List[int]):
        """Set notes to 0, mark as forbidden, then rebalance"""
        for midi in midi_list:
            if 0 <= midi <= 127:
                self.probabilities[midi] = 0.0
                self.forbidden_notes.add(midi)
        self.rebalance()
    
    def apply_gaussian(self, center: int, spread: float, weight: float):
        """Apply Gaussian distribution around center with given spread and weight"""
        for midi in range(128):
            if midi not in self.forbidden_notes:
                distance = abs(midi - center)
                gaussian_factor = math.exp(-(distance ** 2) / (2 * (spread / 2) ** 2))
                self.probabilities[midi] *= (1.0 + weight * gaussian_factor)
        self.rebalance()
    
    def rebalance(self):
        """Normalize probabilities so sum = 1.0, respecting forbidden notes"""
        # Keep forbidden notes at zero
        for midi in self.forbidden_notes:
            self.probabilities[midi] = 0.0
        
        # Calculate sum of non-forbidden notes
        total = sum(p for i, p in enumerate(self.probabilities) if i not in self.forbidden_notes)
        
        if total <= self.params.NORMALIZATION_TOLERANCE:
            # If all allowed notes have zero probability, reset to uniform
            allowed_count = 128 - len(self.forbidden_notes)
            if allowed_count > 0:
                uniform_prob = 1.0 / allowed_count
                for i in range(128):
                    self.probabilities[i] = 0.0 if i in self.forbidden_notes else uniform_prob
        else:
            # Normalize non-forbidden notes
            for i in range(128):
                if i not in self.forbidden_notes:
                    self.probabilities[i] /= total
                    # Enforce minimum probability
                    if self.probabilities[i] < self.params.MIN_PROBABILITY:
                        self.probabilities[i] = self.params.MIN_PROBABILITY
    
    def get_selection_weights(self) -> List[float]:
        """Return copy of probabilities for weighted random selection"""
        return self.probabilities.copy()
    
    def validate_integrity(self) -> bool:
        """Debug check: verify sum = 1.0 within tolerance"""
        total = sum(self.probabilities)
        return abs(total - 1.0) < self.params.NORMALIZATION_TOLERANCE


# ============================================================================
# CONSTRAINT SYSTEM
# ============================================================================

class ProbabilityConstraint(ABC):
    """Abstract base class for all probability constraints"""
    
    def __init__(self, params: AlgorithmParameters, debug: DebugSettings):
        self.params = params
        self.debug = debug
        self.constraint_name = self.__class__.__name__
        self.priority_level = 1  # Override in subclasses
    
    @abstractmethod
    def apply(self, prob_map: NormalizedProbabilityMap, context: Dict[str, Any]):
        """Apply this constraint to the probability map"""
        pass
    
    def get_affected_notes(self, context: Dict[str, Any]) -> List[int]:
        """Return which MIDI notes this constraint affects"""
        return list(range(128))  # Default: all notes
    
    def is_hard_constraint(self) -> bool:
        """True if this creates forbidden zones (zero probability)"""
        return self.priority_level <= 2


class ExtremeRangeConstraint(ProbabilityConstraint):
    """Hard block extreme MIDI ranges"""
    
    def __init__(self, params: AlgorithmParameters, debug: DebugSettings):
        super().__init__(params, debug)
        self.priority_level = 1  # Highest priority
    
    def apply(self, prob_map: NormalizedProbabilityMap, context: Dict[str, Any]):
        """Zero out extreme ranges"""
        extreme_notes = []
        extreme_notes.extend(range(0, self.params.LOW_RANGE_MAX + 1))  # 0-14
        extreme_notes.extend(range(self.params.HIGH_RANGE_MIN, 128))   # 113-127
        
        if self.debug.PRINT_CONSTRAINT_APPLICATIONS:
            print(f"   Applying {self.constraint_name}: blocking MIDI 0-{self.params.LOW_RANGE_MAX} and {self.params.HIGH_RANGE_MIN}-127")
        
        prob_map.zero_notes(extreme_notes)


class RankSpreadConstraint(ProbabilityConstraint):
    """Enforce rank's GCI ± spread boundaries"""
    
    def __init__(self, params: AlgorithmParameters, debug: DebugSettings):
        super().__init__(params, debug)
        self.priority_level = 2  # High priority
    
    def apply(self, prob_map: NormalizedProbabilityMap, context: Dict[str, Any]):
        """Enforce rank spread boundaries"""
        rank = context.get('current_rank')
        if not rank:
            return
        
        min_midi, max_midi = self.calculate_rank_boundaries(rank)
        
        if self.debug.PRINT_CONSTRAINT_APPLICATIONS:
            print(f"   Applying {self.constraint_name}: rank {rank.number} range MIDI {min_midi}-{max_midi}")
        
        if self.params.STRICT_SPREAD_ENFORCEMENT:
            # Hard boundary: zero notes outside range
            forbidden_notes = []
            forbidden_notes.extend(range(0, min_midi))
            forbidden_notes.extend(range(max_midi + 1, 128))
            prob_map.zero_notes(forbidden_notes)
        else:
            # Soft boundary: apply falloff
            for midi in range(128):
                if midi < min_midi or midi > max_midi:
                    prob_map.probabilities[midi] *= self.params.SPREAD_FALLOFF_FACTOR
            prob_map.rebalance()
    
    def calculate_rank_boundaries(self, rank) -> Tuple[int, int]:
        """Calculate MIDI range for rank based on GCI and density"""
        # Import here to avoid circular imports
        from fibril_algorithm import get_rank_middle_octave_midi, get_rank_octave_spread
        
        center_midi = get_rank_middle_octave_midi(rank)
        octave_spread = get_rank_octave_spread(rank)
        
        if octave_spread == 0:
            octave_spread = 1  # Minimum spread
        
        spread_semitones = octave_spread * 12
        min_midi = max(0, center_midi - spread_semitones)
        max_midi = min(127, center_midi + spread_semitones)
        
        return min_midi, max_midi


class KeyCenterConstraint(ProbabilityConstraint):
    """Enforce major scale adherence (except subtonic rank)"""
    
    def __init__(self, params: AlgorithmParameters, debug: DebugSettings):
        super().__init__(params, debug)
        self.priority_level = 2  # High priority
        self.MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
    
    def apply(self, prob_map: NormalizedProbabilityMap, context: Dict[str, Any]):
        """Enforce key center adherence"""
        rank = context.get('current_rank')
        key_center = context.get('key_center', 0)
        
        if not rank:
            return
        
        # Allow subtonic rank to use any notes
        if rank.tonicization == 8 and self.params.ALLOW_SUBTONIC_CHROMATICISM:
            return
        
        allowed_pcs = self.get_allowed_pitch_classes(key_center)
        forbidden_notes = []
        
        for midi in range(128):
            pc = midi % 12
            if pc not in allowed_pcs:
                forbidden_notes.append(midi)
        
        if self.debug.PRINT_CONSTRAINT_APPLICATIONS:
            print(f"   Applying {self.constraint_name}: key {key_center}, allowed PCs {sorted(allowed_pcs)}")
        
        if self.params.OUT_OF_KEY_PENALTY == 0.0:
            # Hard constraint: zero out-of-key notes
            prob_map.zero_notes(forbidden_notes)
        else:
            # Soft constraint: penalize out-of-key notes
            for midi in forbidden_notes:
                prob_map.probabilities[midi] *= self.params.OUT_OF_KEY_PENALTY
            prob_map.rebalance()
    
    def get_allowed_pitch_classes(self, key_center: int) -> Set[int]:
        """Return set of allowed pitch classes for major scale"""
        return set((key_center + offset) % 12 for offset in self.MAJOR_SCALE_INTERVALS)
    
    def is_note_in_key(self, midi_note: int, key_center: int) -> bool:
        """Check if note is in key"""
        pc = midi_note % 12
        return pc in self.get_allowed_pitch_classes(key_center)


class RootVoicingConstraint(ProbabilityConstraint):
    """Enforce root voicing requirement per rank"""
    
    def __init__(self, params: AlgorithmParameters, debug: DebugSettings):
        super().__init__(params, debug)
        self.priority_level = 2  # High priority when triggered
    
    def apply(self, prob_map: NormalizedProbabilityMap, context: Dict[str, Any]):
        """Apply root voicing constraint"""
        rank = context.get('current_rank')
        active_voices = context.get('active_voices', [])
        key_center = context.get('key_center', 0)
        
        if not rank:
            return
        
        if not self.is_root_voiced(rank, active_voices, key_center):
            # Root is not voiced - force root selection
            if self.debug.PRINT_CONSTRAINT_APPLICATIONS:
                print(f"   Applying {self.constraint_name}: forcing root for rank {rank.number}")
            self.force_root_selection(prob_map, rank, key_center)
    
    def is_root_voiced(self, rank, active_voices: List[int], key_center: int) -> bool:
        """Check if rank's root is already voiced"""
        root_pc = self.get_rank_root_pc(rank, key_center)
        return any((voice % 12) == root_pc for voice in active_voices)
    
    def get_rank_root_pc(self, rank, key_center: int) -> int:
        """Get rank's root pitch class"""
        if rank.tonicization == 8:  # Subtonic - use 3rd of key center
            return (key_center + 4) % 12
        else:
            scale_degree_offsets = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}
            offset = scale_degree_offsets.get(rank.tonicization, 0)
            return (key_center + offset) % 12
    
    def force_root_selection(self, prob_map: NormalizedProbabilityMap, rank, key_center: int):
        """Force selection of root note by giving it dominant probability"""
        root_pc = self.get_rank_root_pc(rank, key_center)
        
        # Zero all non-root notes
        non_root_notes = []
        for midi in range(128):
            if (midi % 12) != root_pc:
                non_root_notes.append(midi)
        
        prob_map.zero_notes(non_root_notes)


class PerfectIntervalHeuristic(ProbabilityConstraint):
    """Boost perfect 4ths/5ths relative to active voices"""
    
    def __init__(self, params: AlgorithmParameters, debug: DebugSettings):
        super().__init__(params, debug)
        self.priority_level = 3  # Medium priority
        self.PERFECT_INTERVALS = {
            0: self.params.OCTAVE_BOOST,
            5: self.params.PERFECT_FOURTH_BOOST,
            7: self.params.PERFECT_FIFTH_BOOST
        }
    
    def apply(self, prob_map: NormalizedProbabilityMap, context: Dict[str, Any]):
        """Boost notes at perfect intervals from active voices"""
        active_voices = context.get('active_voices', [])
        
        if not active_voices:
            return
        
        boosted_notes = []
        for midi in range(128):
            boost_factor = self.calculate_interval_boost(midi, active_voices)
            if boost_factor > 1.0:
                boosted_notes.append(midi)
        
        if boosted_notes and self.debug.PRINT_CONSTRAINT_APPLICATIONS:
            print(f"   Applying {self.constraint_name}: boosting {len(boosted_notes)} notes with perfect intervals")
        
        for midi in boosted_notes:
            boost_factor = self.calculate_interval_boost(midi, active_voices)
            prob_map.probabilities[midi] *= boost_factor
        
        if boosted_notes:
            prob_map.rebalance()
    
    def calculate_interval_boost(self, midi_note: int, active_voices: List[int]) -> float:
        """Calculate boost factor for a note based on perfect intervals"""
        max_boost = 1.0
        
        for active_voice in active_voices:
            interval = abs(midi_note - active_voice) % 12
            if interval in self.PERFECT_INTERVALS:
                boost = self.PERFECT_INTERVALS[interval]
                # Apply compound interval decay for large separations
                if abs(midi_note - active_voice) > 12:
                    boost *= self.params.COMPOUND_INTERVAL_DECAY
                max_boost = max(max_boost, boost)
        
        return max_boost


class HarmonicFunctionHeuristic(ProbabilityConstraint):
    """Apply harmonic weights based on interval from rank root"""
    
    def __init__(self, params: AlgorithmParameters, debug: DebugSettings):
        super().__init__(params, debug)
        self.priority_level = 4  # Lower priority
        self.HARMONIC_WEIGHTS = {
            0: self.params.ROOT_WEIGHT,     # Root
            7: self.params.FIFTH_WEIGHT,    # Perfect fifth
            3: self.params.THIRD_WEIGHT,    # Major third
            4: self.params.THIRD_WEIGHT,    # Minor third
            10: self.params.SEVENTH_WEIGHT, # Minor seventh
            11: self.params.SEVENTH_WEIGHT, # Major seventh
            2: self.params.NINTH_WEIGHT,    # Major ninth
            1: self.params.OTHER_WEIGHT,    # Minor ninth
            5: self.params.OTHER_WEIGHT,    # Perfect fourth
            6: self.params.OTHER_WEIGHT,    # Tritone
            8: self.params.OTHER_WEIGHT,    # Minor sixth
            9: self.params.OTHER_WEIGHT,    # Major sixth
        }
    
    def apply(self, prob_map: NormalizedProbabilityMap, context: Dict[str, Any]):
        """Apply harmonic function weights"""
        rank = context.get('current_rank')
        key_center = context.get('key_center', 0)
        
        if not rank:
            return
        
        # Import here to avoid circular imports
        from fibril_algorithm import get_rank_root_pc
        
        root_pc = get_rank_root_pc(rank, key_center)
        
        if self.debug.PRINT_CONSTRAINT_APPLICATIONS:
            print(f"   Applying {self.constraint_name}: rank {rank.number} root PC {root_pc}")
        
        for midi in range(128):
            if midi not in prob_map.forbidden_notes:
                interval = (midi - root_pc) % 12
                weight = self.HARMONIC_WEIGHTS.get(interval, self.params.OTHER_WEIGHT)
                # Convert weight to boost factor (weight + base factor)
                boost_factor = 1.0 + weight
                prob_map.probabilities[midi] *= boost_factor
        
        prob_map.rebalance()


class SpatialPreferenceHeuristic(ProbabilityConstraint):
    """Apply spatial clustering around rank's GCI center"""
    
    def __init__(self, params: AlgorithmParameters, debug: DebugSettings):
        super().__init__(params, debug)
        self.priority_level = 5  # Lowest priority
    
    def apply(self, prob_map: NormalizedProbabilityMap, context: Dict[str, Any]):
        """Apply spatial preference around rank center"""
        rank = context.get('current_rank')
        
        if not rank:
            return
        
        center_midi = self.get_rank_spatial_center(rank)
        spread = self.calculate_spatial_spread(rank)
        
        if self.debug.PRINT_CONSTRAINT_APPLICATIONS:
            print(f"   Applying {self.constraint_name}: center MIDI {center_midi}, spread {spread}")
        
        prob_map.apply_gaussian(center_midi, spread, self.params.GAUSSIAN_STRENGTH)
    
    def get_rank_spatial_center(self, rank) -> int:
        """Get rank's spatial center MIDI note"""
        # Import here to avoid circular imports
        from fibril_algorithm import get_rank_middle_octave_midi
        return get_rank_middle_octave_midi(rank)
    
    def calculate_spatial_spread(self, rank) -> float:
        """Calculate spatial spread for Gaussian"""
        # Import here to avoid circular imports
        from fibril_algorithm import get_rank_octave_spread
        
        octave_spread = get_rank_octave_spread(rank)
        if octave_spread == 0:
            octave_spread = 1
        
        return octave_spread * 12 * self.params.SPREAD_MULTIPLIER


# ============================================================================
# PROCESSING LOGIC
# ============================================================================

class RankProcessor:
    """Handles allocation logic for a single rank"""
    
    def __init__(self, params: AlgorithmParameters, debug: DebugSettings):
        self.params = params
        self.debug = debug
        self.current_rank = None
        self.allocated_voices: List[int] = []
    
    def process_rank(self, rank, prob_map: NormalizedProbabilityMap, context: Dict[str, Any]) -> int:
        """Process allocation for a single rank, return number of voices allocated"""
        self.current_rank = rank
        self.allocated_voices = []
        
        if self.debug.DEBUG_VERBOSE:
            print(f"\n🎯 Processing Rank {rank.number} (density={rank.density}, tonicization={rank.tonicization})")
        
        # Update context
        context['current_rank'] = rank
        
        # Calculate how many voices this rank should get
        target_voices = rank.density
        allocated_count = 0
        
        # Allocate voices one by one
        for voice_index in range(target_voices):
            if self.debug.DEBUG_VERBOSE:
                print(f"   Voice {voice_index + 1}/{target_voices} for rank {rank.number}:")
            
            success = self.allocate_single_voice(prob_map, context, voice_index)
            if success:
                allocated_count += 1
            else:
                if self.debug.DEBUG_VERBOSE:
                    print(f"   Failed to allocate voice {voice_index + 1}")
                break
        
        return allocated_count
    
    def allocate_single_voice(self, prob_map: NormalizedProbabilityMap, context: Dict[str, Any], voice_index: int) -> bool:
        """Allocate a single voice for the current rank"""
        # Reset probability map to uniform
        prob_map.initialize_uniform()
        
        # Apply all constraints in order
        constraint_list = context.get('constraints', [])
        self.apply_all_constraints(prob_map, context, constraint_list)
        
        # Select and allocate voice
        from fibril_algorithm import select_and_allocate_voice
        
        selected_midi = select_and_allocate_voice(prob_map, context)
        if selected_midi is not None:
            self.allocated_voices.append(selected_midi)
            # Update active voices in context
            if 'active_voices' not in context:
                context['active_voices'] = []
            context['active_voices'].append(selected_midi)
            return True
        
        return False
    
    def apply_all_constraints(self, prob_map: NormalizedProbabilityMap, context: Dict[str, Any], constraint_list: List[ProbabilityConstraint]):
        """Apply all constraints in priority order"""
        # Sort by priority level
        sorted_constraints = sorted(constraint_list, key=lambda c: c.priority_level)
        
        for constraint in sorted_constraints:
            constraint.apply(prob_map, context)
            
            # Validate map integrity after each constraint
            if not prob_map.validate_integrity():
                if self.debug.DEBUG_VERBOSE:
                    print(f"   Warning: Probability map sum = {sum(prob_map.probabilities):.6f} after {constraint.constraint_name}")


class VoiceSelector:
    """Handles voice selection and allocation"""
    
    def __init__(self, params: AlgorithmParameters, debug: DebugSettings):
        self.params = params
        self.debug = debug
        
        # Initialize random seed if specified
        if hasattr(params, 'RANDOM_SEED') and params.RANDOM_SEED is not None:
            random.seed(params.RANDOM_SEED)
    
    def select_note(self, prob_map: NormalizedProbabilityMap) -> Optional[int]:
        """Perform weighted random selection from probability map"""
        probabilities = prob_map.get_selection_weights()
        total_prob = sum(probabilities)
        
        if total_prob <= prob_map.params.NORMALIZATION_TOLERANCE:
            if self.debug.DEBUG_VERBOSE:
                print(f"   No selectable notes (total prob: {total_prob})")
            return None
        
        # Weighted random selection
        roll = random.random() * total_prob
        cumulative = 0.0
        
        for midi, prob in enumerate(probabilities):
            cumulative += prob
            if roll <= cumulative:
                return midi
        
        # Fallback
        return len(probabilities) - 1
    
    def allocate_voice(self, midi_note: int, fibril_system) -> Optional[int]:
        """Find available voice and allocate MIDI note"""
        # Find first available voice
        for voice in fibril_system.voices:
            if not voice.volume and not voice.sustained:
                voice.midi_note = midi_note
                voice.volume = 1
                voice.sustained = False
                return voice.id
        
        return None
    
    def prevent_duplicates(self, prob_map: NormalizedProbabilityMap, active_voices: List[int]):
        """Zero out notes that are already active"""
        prob_map.zero_notes(active_voices)


class AllocationHistory:
    """Tracks allocation history for visualization and analysis"""
    
    def __init__(self, debug: DebugSettings):
        self.debug = debug
        self.probability_snapshots: List[List[float]] = []
        self.selection_metadata: List[Dict] = []
        self.constraint_applications: List[Dict] = []
        self.timing_data: List[float] = []
    
    def record_selection(self, voice_id: int, midi_note: int, prob_map: NormalizedProbabilityMap, metadata: Dict):
        """Record a voice selection"""
        if self.debug.SNAPSHOT_FREQUENCY == "every_selection":
            self.probability_snapshots.append(prob_map.get_selection_weights())
        
        selection_record = {
            'voice_id': voice_id,
            'midi_note': midi_note,
            'probability': prob_map.probabilities[midi_note] if 0 <= midi_note < 128 else 0.0,
            'timestamp': time.time(),
            **metadata
        }
        
        self.selection_metadata.append(selection_record)
        
        # Limit history size
        if len(self.selection_metadata) > self.debug.MAX_HISTORY_SIZE:
            self.selection_metadata.pop(0)
            if self.probability_snapshots:
                self.probability_snapshots.pop(0)
    
    def record_constraint_application(self, constraint_name: str, before_sum: float, after_sum: float):
        """Record constraint application"""
        self.constraint_applications.append({
            'constraint': constraint_name,
            'before_sum': before_sum,
            'after_sum': after_sum,
            'timestamp': time.time()
        })
    
    def get_visualization_data(self) -> Dict:
        """Get complete data for visualization"""
        return {
            'voice_count': len(self.selection_metadata),
            'probability_maps': self.probability_snapshots,
            'selections': self.selection_metadata,
            'constraints': self.constraint_applications,
            'midi_range': 128
        }
    
    def clear(self):
        """Clear all history"""
        self.probability_snapshots.clear()
        self.selection_metadata.clear()
        self.constraint_applications.clear()
        self.timing_data.clear()


class AllocationEngine:
    """Main orchestration engine for the entire allocation process"""
    
    def __init__(self, fibril_system, params: AlgorithmParameters = None, debug: DebugSettings = None):
        self.fibril_system = fibril_system
        self.params = params or AlgorithmParameters()
        self.debug = debug or DebugSettings()
        
        # Initialize components
        self.probability_map = NormalizedProbabilityMap(self.params)
        self.voice_selector = VoiceSelector(self.params, self.debug)
        self.allocation_history = AllocationHistory(self.debug)
        
        # Initialize constraints
        self.constraints = self.setup_constraints()
        
        # State tracking
        self.active_voices: Set[int] = set()
        self.rank_processors: Dict[int, RankProcessor] = {}
    
    def setup_constraints(self) -> List[ProbabilityConstraint]:
        """Initialize all constraint objects"""
        return [
            ExtremeRangeConstraint(self.params, self.debug),
            RankSpreadConstraint(self.params, self.debug),
            KeyCenterConstraint(self.params, self.debug),
            RootVoicingConstraint(self.params, self.debug),
            PerfectIntervalHeuristic(self.params, self.debug),
            HarmonicFunctionHeuristic(self.params, self.debug),
            SpatialPreferenceHeuristic(self.params, self.debug)
        ]
    
    def allocate_all_voices(self) -> Dict:
        """Main entry point: allocate all voices for all active ranks"""
        start_time = time.time()
        
        if self.debug.DEBUG_VERBOSE:
            print("🎼 Starting Cascading Harmonic Construction...")
        
        # Clear previous allocation
        self.clear_all_voices()
        self.allocation_history.clear()
        
        # Get active ranks
        active_ranks = self.get_active_ranks()
        if not active_ranks:
            return {'allocated': 0, 'target': 0, 'ranks_processed': 0}
        
        # Process ranks in priority order
        total_allocated = self.process_ranks_in_order(active_ranks)
        
        elapsed_time = time.time() - start_time
        
        if self.debug.DEBUG_VERBOSE:
            print(f"\n✅ Allocation complete: {total_allocated} voices in {elapsed_time:.3f}s")
        
        return {
            'allocated': total_allocated,
            'target': sum(rank.density for rank in active_ranks),
            'ranks_processed': len(active_ranks),
            'elapsed_time': elapsed_time,
            'visualization_data': self.allocation_history.get_visualization_data()
        }
    
    def process_ranks_in_order(self, active_ranks: List) -> int:
        """Process ranks in priority order"""
        # Sort by priority order
        ordered_ranks = []
        for rank_num in self.params.RANK_PRIORITY_ORDER:
            for rank in active_ranks:
                if rank.number == rank_num:
                    ordered_ranks.append(rank)
                    break
        
        total_allocated = 0
        
        for rank in ordered_ranks:
            processor = RankProcessor(self.params, self.debug)
            context = self.build_context()
            
            allocated_count = processor.process_rank(rank, self.probability_map, context)
            total_allocated += allocated_count
            
            # Update global active voices
            self.active_voices.update(processor.allocated_voices)
        
        return total_allocated
    
    def build_context(self) -> Dict[str, Any]:
        """Build context dictionary for constraints"""
        return {
            'key_center': self.fibril_system.key_center,
            'active_voices': list(self.active_voices),
            'constraints': self.constraints,
            'fibril_system': self.fibril_system
        }
    
    def get_active_ranks(self) -> List:
        """Get ranks with density > 0"""
        return [rank for rank in self.fibril_system.ranks if rank.density > 0]
    
    def clear_all_voices(self):
        """Clear all non-sustained voices"""
        for voice in self.fibril_system.voices:
            if voice.volume and not voice.sustained:
                voice.volume = 0
                voice.midi_note = 0
        self.active_voices.clear()
