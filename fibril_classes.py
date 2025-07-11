#!/usr/bin/env python3
"""
FIBRIL Core Classes

Minimal data structures for the FIBRIL system:
- Rank: Tracks GCI, density, and position from grey code
- Voice: MIDI note and volume boolean
- SystemState: Current state of all ranks and voices
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Rank:
    """Rank with grey code interpretation, tonicization, and probability mapping"""
    number: int  # Scale degree (1-8)
    position: int  # Priority position (1-8)
    grey_code: List[int]  # 4 bits [0,0,0,0]
    gci: int = 0  # Grey Code Integer
    density: int = 0  # Mapped density: 1->2, 2->3, 3->4, 4->6 ones
    
    # New properties for FIBRIL algorithm
    tonicization: int = 0  # Scale degree assignment (1=tonic, 2=supertonic, etc.)
    previous_gci: int = 0  # Previous GCI for voice leading
    probability_map: List[float] = None  # Probability weights for MIDI notes
    
    def __post_init__(self):
        """Calculate GCI and density from grey code"""
        # Custom density mapping: 1->2, 2->3, 3->4, 4->6
        ones_count = sum(self.grey_code)
        density_map = {0: 0, 1: 2, 2: 3, 3: 4, 4: 6}
        self.density = density_map.get(ones_count, 0)
        
        # Update previous GCI before calculating new one
        self.previous_gci = self.gci
        self.gci = self._grey_to_int(self.grey_code)
        
        # Initialize probability map if not set
        if self.probability_map is None:
            self.probability_map = [0.0] * 128  # MIDI 0-127
    
    def _grey_to_int(self, grey: List[int]) -> int:
        """Convert grey code to integer"""
        b = 0
        for bit in grey:
            b = (b << 1) | bit
        mask = b
        res = 0
        while mask:
            res ^= mask
            mask >>= 1
        return res
    
    def copy(self) -> 'Rank':
        """Create a copy of this rank"""
        new_rank = Rank(
            number=self.number,
            position=self.position,
            grey_code=self.grey_code.copy(),
            gci=self.gci,
            density=self.density,
            tonicization=self.tonicization,
            previous_gci=self.previous_gci
        )
        if self.probability_map:
            new_rank.probability_map = self.probability_map.copy()
        return new_rank
    
    def get_valid_destinations(self, key_center: int) -> List[int]:
        """Get valid MIDI destinations for this rank based on its tonicization and key center"""
        # Base harmonic degrees: 1, 5, 3, 2, 4, 6, 7, 9, 11
        # These are intervals from the rank's tonic (in semitones)
        base_intervals = [0, 7, 4, 2, 5, 9, 11, 14, 17]  # 1, 5, 3, 2, 4, 6, 7, 9, 11
        
        # Calculate the rank's tonic based on its tonicization and key center
        rank_tonic = (key_center + self._get_scale_degree_offset(self.tonicization)) % 12
        
        valid_destinations = []
        
        if self.tonicization == 8:  # Subtonic - use whole tone scale
            destinations = self._fit_to_whole_tone_scale(rank_tonic, base_intervals, key_center)
        else:  # All other ranks - use major scale
            destinations = self._fit_to_major_scale(rank_tonic, base_intervals, key_center)
        
        # Convert to all octaves (MIDI 0-127)
        for interval in destinations:
            for octave in range(11):  # Covers MIDI range
                midi_note = (rank_tonic + interval + octave * 12) % 128
                if 0 <= midi_note <= 127:
                    valid_destinations.append(midi_note)
        
        return sorted(list(set(valid_destinations)))  # Remove duplicates and sort
    
    def _get_scale_degree_offset(self, degree: int) -> int:
        """Get semitone offset for scale degree in major scale"""
        # Major scale intervals: 1=0, 2=2, 3=4, 4=5, 5=7, 6=9, 7=11, 8=0 (octave)
        offsets = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11, 8: 0}
        return offsets.get(degree, 0)
    
    def _fit_to_major_scale(self, rank_tonic: int, intervals: List[int], key_center: int) -> List[int]:
        """Fit harmonic intervals to major scale, adjusting out-of-key notes"""
        major_scale_offsets = [0, 2, 4, 5, 7, 9, 11]  # Major scale intervals
        key_notes = [(key_center + offset) % 12 for offset in major_scale_offsets]
        
        fitted_intervals = []
        for interval in intervals:
            target_note = (rank_tonic + interval) % 12
            
            if target_note in key_notes:
                fitted_intervals.append(interval)
            else:
                # Find closest in-key note
                closest_up = self._find_closest_in_key(target_note, key_notes, direction=1)
                closest_down = self._find_closest_in_key(target_note, key_notes, direction=-1)
                
                # Choose based on music theory preference
                if self._should_adjust_up(interval, target_note, key_notes):
                    fitted_intervals.append(interval + closest_up)
                else:
                    fitted_intervals.append(interval + closest_down)
        
        return fitted_intervals
    
    def _fit_to_whole_tone_scale(self, rank_tonic: int, intervals: List[int], key_center: int) -> List[int]:
        """Fit harmonic intervals to whole tone scale for subtonic rank"""
        # Whole tone scale: 0, 2, 4, 6, 8, 10
        whole_tone_offsets = [0, 2, 4, 6, 8, 10]
        key_notes = [(key_center + offset) % 12 for offset in whole_tone_offsets]
        
        fitted_intervals = []
        for interval in intervals:
            target_note = (rank_tonic + interval) % 12
            
            if target_note in key_notes:
                fitted_intervals.append(interval)
            else:
                # Find closest whole tone note
                closest_up = self._find_closest_in_key(target_note, key_notes, direction=1)
                closest_down = self._find_closest_in_key(target_note, key_notes, direction=-1)
                
                # For whole tone, prefer the closer option
                if abs(closest_up) <= abs(closest_down):
                    fitted_intervals.append(interval + closest_up)
                else:
                    fitted_intervals.append(interval + closest_down)
        
        return fitted_intervals
    
    def _find_closest_in_key(self, target_note: int, key_notes: List[int], direction: int) -> int:
        """Find closest in-key note in given direction"""
        adjustment = 0
        current_note = target_note
        
        for _ in range(6):  # Max 6 semitones to avoid infinite loop
            adjustment += direction
            current_note = (target_note + adjustment) % 12
            if current_note in key_notes:
                return adjustment
        
        return 0  # Fallback
    
    def _should_adjust_up(self, interval: int, target_note: int, key_notes: List[int]) -> bool:
        """Music theory heuristic for whether to adjust a note up or down"""
        # Harmonic degree based adjustments
        if interval == 6:  # #5 (tritone) - usually resolve up
            return True
        elif interval == 20:  # b13 - usually resolve down  
            return False
        elif interval in [2, 5]:  # 2nd, 4th - tend to resolve up to 3rd, 5th
            return True
        elif interval in [11, 17]:  # 7th, 11th - tend to resolve down
            return False
        else:
            # Default: adjust to closest
            return True


@dataclass
class Voice:
    """Voice with MIDI note and volume"""
    midi_note: int
    volume: int
    id: int


@dataclass
class SystemState:
    """Global system state for FIBRIL algorithm"""
    sustain: int = 0
    key_center: int = 0  # Key center offset
    
    # Layout modes
    right_hand_mode: str = "R->L"  # "R->L" or "Mirrored"
    
    # Priority order for rank evaluation
    rank_priority: List[int] = None  # Will be [3, 4, 2, 6, 1, 5, 7, 8] by default
    
    # Algorithm state
    global_probability_map: List[float] = None  # Global probability weights
    sustained_notes: List[int] = None  # Currently sustained MIDI notes
    current_voicing_notes: List[int] = None  # Currently active MIDI notes
    
    def __post_init__(self):
        """Initialize default values"""
        if self.rank_priority is None:
            # Updated priority order: [R3(tonic), R4(subdominant), R2(supertonic), R6(dominant), R1(submediant), R5(mediant), R7(leading), R8(subtonic)]
            self.rank_priority = [3, 4, 2, 6, 1, 5, 7, 8]
        
        if self.global_probability_map is None:
            self.global_probability_map = [0.0] * 128
        
        if self.sustained_notes is None:
            self.sustained_notes = []
        
        if self.current_voicing_notes is None:
            self.current_voicing_notes = []
