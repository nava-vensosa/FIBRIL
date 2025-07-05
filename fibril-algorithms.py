#!/usr/bin/env python3
"""
FIBRIL Algorithms

Core FIBRIL voice allocation algorithms implementing the complete
state transition system with probability curve overlays.
"""

import math
import random
from typing import List, Dict, Tuple, Set
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fibril_classes import Rank, Voice, SystemState


class ProbabilityCurve:
    """Represents different probability distribution curves for voice allocation"""
    
    @staticmethod
    def gaussian(center: float, width: float, midi_range: range = range(128)) -> List[float]:
        """Generate Gaussian (normal) distribution centered at 'center' with given width"""
        curve = []
        for midi in midi_range:
            # Gaussian formula: e^(-(x-μ)²/(2σ²))
            sigma = width / 3.0  # width represents ~3 standard deviations
            exponent = -((midi - center) ** 2) / (2 * sigma ** 2)
            curve.append(math.exp(exponent))
        return curve
    
    @staticmethod
    def poisson_like(center: float, skew: float = 1.0, midi_range: range = range(128)) -> List[float]:
        """Generate Poisson-like distribution with controllable center and skew"""
        curve = []
        lambda_param = center / 10.0  # Scale for reasonable lambda values
        
        for midi in midi_range:
            # Modified Poisson-like: use distance from center
            x = abs(midi - center) / 10.0
            if x == 0:
                prob = 1.0
            else:
                # Exponential decay with skew adjustment
                prob = math.exp(-x * skew) * (lambda_param ** x) / math.factorial(min(int(x), 20))
        
            curve.append(prob)
        return curve
    
    @staticmethod
    def exponential_decay(center: float, decay_rate: float, midi_range: range = range(128)) -> List[float]:
        """Generate exponential decay from center point"""
        curve = []
        for midi in midi_range:
            distance = abs(midi - center)
            curve.append(math.exp(-decay_rate * distance))
        return curve
    
    @staticmethod
    def voice_leading_bias(current_notes: List[int], direction: int, strength: float = 2.0) -> List[float]:
        """Generate voice leading bias curve based on current notes and movement direction
        
        Args:
            current_notes: List of currently active MIDI notes
            direction: 1 for upward bias, -1 for downward bias, 0 for neutral
            strength: How strong the voice leading bias is (higher = more focused)
        """
        curve = [0.0] * 128
        
        if not current_notes:
            return [1.0] * 128  # Neutral if no current notes
        
        for current_note in current_notes:
            for midi in range(128):
                distance = midi - current_note
                
                # Bias based on direction and proximity
                if direction > 0 and distance > 0:  # Upward movement
                    # Stronger bias for +1, +2 semitones, diminishing for larger intervals
                    if 1 <= distance <= 2:
                        curve[midi] += strength * (3 - distance)  # +2 for +1 semitone, +1 for +2 semitones
                    elif 3 <= distance <= 5:
                        curve[midi] += strength * 0.5
                        
                elif direction < 0 and distance < 0:  # Downward movement
                    # Stronger bias for -1, -2 semitones
                    abs_distance = abs(distance)
                    if 1 <= abs_distance <= 2:
                        curve[midi] += strength * (3 - abs_distance)
                    elif 3 <= abs_distance <= 5:
                        curve[midi] += strength * 0.5
                        
                elif direction == 0:  # Neutral - slight bias for small movements
                    abs_distance = abs(distance)
                    if abs_distance <= 2:
                        curve[midi] += strength * 0.3
        
        # Normalize to prevent extreme values
        max_val = max(curve) if max(curve) > 0 else 1.0
        return [val / max_val for val in curve]


class FibrilAlgorithm:
    """Main FIBRIL voice allocation algorithm"""
    
    def __init__(self):
        self.global_probability_map = [0.0] * 128
        self.rooted_notes_cache = set()  # Cache for required root/fifth notes
    
    def allocate_voices(self, system_state: SystemState) -> SystemState:
        """Main algorithm entry point - allocate voices based on current state"""
        new_state = system_state.copy()
        
        # Step 1: StateTransitionBypass - skip inactive ranks
        active_ranks = self._get_active_ranks(new_state)
        if not active_ranks:
            # No ranks active - turn off all voices
            for voice in new_state.voices:
                voice.volume = 0
            return new_state
        
        # Step 2: SustainBypass - handle sustain pedal
        sustained_notes = self._handle_sustain(new_state)
        
        # Step 3: Rooted Note Requirement - ensure root/fifth coverage
        self._ensure_rooted_notes(new_state, active_ranks, sustained_notes)
        
        # Step 4: Calculate total voice budget
        total_density = sum(rank.density for rank in active_ranks)
        available_voices = min(48, total_density + len(sustained_notes))
        
        # Step 5: Build global probability map
        self._build_global_probability_map(new_state, active_ranks)
        
        # Step 6: Allocate remaining voices
        self._allocate_remaining_voices(new_state, active_ranks, available_voices, sustained_notes)
        
        return new_state
    
    def _get_active_ranks(self, system_state: SystemState) -> List[Rank]:
        """Get ranks with non-zero density"""
        return [rank for rank in system_state.ranks if rank.density > 0]
    
    def _handle_sustain(self, system_state: SystemState) -> Set[int]:
        """Handle sustain pedal logic and return set of sustained MIDI notes"""
        sustained_notes = set()
        
        if system_state.sustain:
            # Collect currently active notes
            active_notes = []
            for i, voice in enumerate(system_state.voices):
                if voice.volume > 0:
                    active_notes.append((voice.midi_note, i))
            
            # If we have more than 48 voices, release the lowest MIDI notes (FIFO)
            if len(active_notes) > 48:
                active_notes.sort(key=lambda x: x[0])  # Sort by MIDI note
                to_release = active_notes[:-48]  # Keep only the highest 48
                for midi_note, voice_idx in to_release:
                    system_state.voices[voice_idx].volume = 0
                active_notes = active_notes[-48:]
            
            # Mark remaining notes as sustained
            sustained_notes = {midi_note for midi_note, _ in active_notes}
        
        return sustained_notes
    
    def _ensure_rooted_notes(self, system_state: SystemState, active_ranks: List[Rank], sustained_notes: Set[int]):
        """Ensure each active rank has its root and perfect fifth voiced"""
        self.rooted_notes_cache.clear()
        
        for rank in active_ranks:
            root_midi = self._get_rank_root(rank, system_state.key_center)
            fifth_midi = (root_midi + 7) % 12  # Perfect fifth
            
            # Check all octaves for root and fifth
            root_present = any((root_midi + oct * 12) in sustained_notes or 
                             any(voice.volume > 0 and voice.midi_note % 12 == root_midi 
                                 for voice in system_state.voices) 
                             for oct in range(11))
            
            fifth_present = any((fifth_midi + oct * 12) in sustained_notes or 
                              any(voice.volume > 0 and voice.midi_note % 12 == fifth_midi 
                                  for voice in system_state.voices) 
                              for oct in range(11))
            
            # Force allocation of missing root/fifth
            if not root_present:
                self._force_allocate_note(system_state, root_midi, rank.position)
                self.rooted_notes_cache.add(root_midi)
            
            if not fifth_present:
                self._force_allocate_note(system_state, fifth_midi, rank.position)
                self.rooted_notes_cache.add(fifth_midi)
    
    def _get_rank_root(self, rank: Rank, key_center: int) -> int:
        """Get the root note (MIDI % 12) for a rank based on its tonicization"""
        scale_degree_offsets = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11, 8: 0}
        offset = scale_degree_offsets.get(rank.tonicization, 0)
        return (key_center + offset) % 12
    
    def _force_allocate_note(self, system_state: SystemState, midi_note_class: int, rank_priority: int):
        """Force allocation of a specific note class, choosing optimal octave"""
        # Find the best octave based on rank priority and current voicing
        best_octave = self._choose_optimal_octave(system_state, midi_note_class, rank_priority)
        target_midi = midi_note_class + best_octave * 12
        
        # Find an available voice or steal the lowest priority one
        target_voice_idx = self._find_or_steal_voice(system_state, target_midi)
        if target_voice_idx is not None:
            system_state.voices[target_voice_idx].midi_note = target_midi
            system_state.voices[target_voice_idx].volume = 1
    
    def _choose_optimal_octave(self, system_state: SystemState, midi_note_class: int, rank_priority: int) -> int:
        """Choose optimal octave for a note based on priority and current voicing"""
        # Lower priority ranks prefer higher octaves to avoid muddiness
        # Higher priority ranks get midrange
        priority_factor = (8 - rank_priority) / 8.0  # 0.0 for highest priority, 0.875 for lowest
        
        # Base octave: 4 for high priority, 5-6 for low priority
        base_octave = 4 + int(priority_factor * 2)
        
        # Ensure MIDI note is in valid range
        target_midi = midi_note_class + base_octave * 12
        if target_midi > 127:
            base_octave = (127 - midi_note_class) // 12
        elif target_midi < 0:
            base_octave = (-midi_note_class) // 12 + 1
        
        return base_octave
    
    def _find_or_steal_voice(self, system_state: SystemState, target_midi: int) -> int:
        """Find available voice or steal lowest priority voice"""
        # First, try to find an empty voice
        for i, voice in enumerate(system_state.voices):
            if voice.volume == 0:
                return i
        
        # If no empty voices, steal from the voice with the least desirable note
        # (prefer to steal from higher MIDI notes for lower priority ranks)
        worst_voice_idx = 0
        worst_score = -1
        
        for i, voice in enumerate(system_state.voices):
            # Simple scoring: prefer to replace higher notes
            score = voice.midi_note
            if score > worst_score:
                worst_score = score
                worst_voice_idx = i
        
        return worst_voice_idx
    
    def _build_global_probability_map(self, system_state: SystemState, active_ranks: List[Rank]):
        """Build the global probability map by overlaying all rank probability curves"""
        self.global_probability_map = [0.0] * 128
        
        # Get currently active notes for voice leading
        current_notes = [voice.midi_note for voice in system_state.voices if voice.volume > 0]
        
        for rank in active_ranks:
            # Get valid destinations for this rank
            valid_destinations = rank.get_valid_destinations(system_state.key_center)
            
            # Base probability curve - uniform across valid destinations
            rank_curve = [0.0] * 128
            for midi in valid_destinations:
                rank_curve[midi] = 1.0
            
            # Apply voice leading bias
            gci_direction = rank.gci - rank.previous_gci
            if gci_direction != 0:
                direction = 1 if gci_direction > 0 else -1
                voice_leading_curve = ProbabilityCurve.voice_leading_bias(
                    current_notes, direction, strength=2.0
                )
                # Multiply curves together
                rank_curve = [a * b for a, b in zip(rank_curve, voice_leading_curve)]
            
            # Apply octave/priority bias using Gaussian curve
            priority_bias_center = 60 + (8 - rank.position) * 6  # Higher priority = lower center
            octave_bias_curve = ProbabilityCurve.gaussian(
                priority_bias_center, width=24  # 2 octave spread
            )
            rank_curve = [a * b for a, b in zip(rank_curve, octave_bias_curve)]
            
            # Weight by rank priority and add to global map
            rank_weight = (9 - rank.position) / 8.0  # Higher priority = higher weight
            for i in range(128):
                self.global_probability_map[i] += rank_curve[i] * rank_weight
        
        # Normalize the global probability map
        total_prob = sum(self.global_probability_map)
        if total_prob > 0:
            self.global_probability_map = [p / total_prob for p in self.global_probability_map]
    
    def _allocate_remaining_voices(self, system_state: SystemState, active_ranks: List[Rank], 
                                 available_voices: int, sustained_notes: Set[int]):
        """Allocate remaining voices based on global probability map"""
        # Count currently allocated voices
        allocated_count = sum(1 for voice in system_state.voices if voice.volume > 0)
        remaining_allocations = available_voices - allocated_count
        
        if remaining_allocations <= 0:
            return
        
        # Get notes to avoid (already allocated or sustained)
        forbidden_notes = sustained_notes.copy()
        for voice in system_state.voices:
            if voice.volume > 0:
                forbidden_notes.add(voice.midi_note)
        
        # Sample from probability map for remaining allocations
        for _ in range(remaining_allocations):
            selected_midi = self._sample_from_probability_map(forbidden_notes)
            if selected_midi is not None:
                voice_idx = self._find_or_steal_voice(system_state, selected_midi)
                if voice_idx is not None:
                    system_state.voices[voice_idx].midi_note = selected_midi
                    system_state.voices[voice_idx].volume = 1
                    forbidden_notes.add(selected_midi)
    
    def _sample_from_probability_map(self, forbidden_notes: Set[int]) -> int:
        """Sample a MIDI note from the global probability map, avoiding forbidden notes"""
        # Create filtered probability map
        filtered_map = []
        valid_indices = []
        
        for i, prob in enumerate(self.global_probability_map):
            if i not in forbidden_notes and prob > 0:
                filtered_map.append(prob)
                valid_indices.append(i)
        
        if not filtered_map:
            return None
        
        # Weighted random selection
        total_weight = sum(filtered_map)
        if total_weight == 0:
            return random.choice(valid_indices) if valid_indices else None
        
        rand_val = random.random() * total_weight
        cumulative = 0
        
        for i, weight in enumerate(filtered_map):
            cumulative += weight
            if rand_val <= cumulative:
                return valid_indices[i]
        
        return valid_indices[-1] if valid_indices else None
