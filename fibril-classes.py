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
    """Rank with grey code interpretation"""
    number: int  # Scale degree (1-8)
    position: int  # Priority position (1-8)
    grey_code: List[int]  # 4 bits [0,0,0,0]
    gci: int = 0  # Grey Code Integer
    density: int = 0  # Number of 1s in grey code
    
    def __post_init__(self):
        """Calculate GCI and density from grey code"""
        self.density = sum(self.grey_code)
        self.gci = self._grey_to_int(self.grey_code)
    
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
        return Rank(
            number=self.number,
            position=self.position,
            grey_code=self.grey_code.copy(),
            gci=self.gci,
            density=self.density
        )


@dataclass
class Voice:
    """Voice with MIDI note and volume"""
    midi_note: int
    volume: bool
    id: int
