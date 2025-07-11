# FIBRIL - Cascading Harmonic Construction System

A real-time probabilistic voice allocation algorithm for MaxMSP integration with advanced sustain pedal logic and spatially-intelligent harmonic voice leading.

## Overview

FIBRIL is a sophisticated voice allocation system that uses normalized probability distributions to intelligently assign MIDI voices based on harmonic functions, spatial clustering, and musical constraints. The system features a cascading harmonic construction approach with rank-by-rank processing and real-time OSC communication.

## Features

### Core Algorithm
- **Normalized Probability Distribution**: All voice selections use probability maps that always sum to 1.0
- **Cascading Harmonic Construction**: Rank-by-rank allocation with priority ordering [R3→R4→R2→R6→R1→R5→R7→R8]
- **Constraint-Based Selection**: Multiple constraint layers including range limits, key adherence, and harmonic functions
- **Perfect Interval Boosting**: Automatic enhancement of perfect 4ths, 5ths, and octaves
- **Spatial Preference**: Gaussian clustering around rank centers based on GCI (Grey Code Index)

### Sustain Pedal Logic
- **Real-time Sustain Control**: OSC message `/sustain` with 0/1 integer values
- **Voice State Management**: Sustained voices persist through algorithm cycles
- **Selective Deallocation**: Only sustained voices are released on pedal release
- **Current Voice Protection**: Active keypresses remain unaffected by sustain operations
- **State Persistence**: Sustained voices treated as "held" for all constraint calculations

### Rank System
- **8 Ranks**: Each with configurable density, position, grey code, and tonicization
- **Tonicization Mapping**: R3→tonic(1), R4→subdominant(4), R2→supertonic(2), R6→dominant(5), R1→submediant(6), R5→mediant(3), R7→leading(7), R8→subtonic(8)
- **GCI-Based Spread**: Automatic octave centering and range calculation
- **Priority Processing**: Musical hierarchy-based allocation order

### Voice Management
- **48 Voices**: Individual MIDI note and volume control
- **Sustained State**: Per-voice sustain tracking independent of volume
- **Duplicate Prevention**: Automatic blocking of already-active notes
- **Root Forcing**: First voice per rank forced to root note of tonicization

## System Architecture

### Core Files
- `fibril_main.py` - Main entry point, OSC server/client, sustain handler
- `fibril_algorithm.py` - Main algorithm interface and utility functions
- `fibril_algorithm_classes.py` - Core algorithm classes, constraints, allocation engine
- `fibril_classes.py` - Data structures (Voice, Rank, SystemState)
- `fibril_init.py` - System initialization and compact state display

### Network Communication
- **Input**: OSC server on port 1761 (receives from MaxMSP)
- **Output**: OSC client to port 8998 (sends to MaxMSP)
- **Message Types**:
  - `/R{rank}_{bit}` - Rank grey code bit updates
  - `/sustain` - Sustain pedal state (0/1)
  - `/keyCenter` - Key center changes (0-11)
  - `/voice_{id}` - Voice state updates (MIDI, volume)

## Algorithm Constraints

### Hard Constraints (Zero Probability)
1. **Extreme Range**: Blocks MIDI 0-14 and 113-127
2. **Rank Spread**: Enforces GCI ± density boundaries
3. **Key Center**: Major scale adherence (except subtonic rank)
4. **Root Voicing**: Forces root note when not already voiced

### Soft Constraints (Probability Weighting)
1. **Perfect Intervals**: Boosts 4ths, 5ths, octaves relative to active voices
2. **Harmonic Functions**: Weights based on interval from rank root
3. **Spatial Preference**: Gaussian clustering around rank center

## Usage

### Starting the System
```bash
python3 fibril_main.py
```

### OSC Message Examples
```
/sustain 1          # Press sustain pedal
/sustain 0          # Release sustain pedal
/keyCenter 5        # Change to F major
/R3_1000 1          # Set rank 3 bit pattern
/R3_pos 1           # Set rank 3 position
```

### Compact Display Output
```
Key: C | Sustain: 0
Ranks:
  R3: pos=1 grey=1011 GCI=7 dens=3 tonic=C center=C5 range=±1oct
  R4: pos=2 grey=0110 GCI=4 dens=2 tonic=F center=C4 range=±1oct
Voices: 1:C4♪ 2:E4♪S 3:G4~S

```

## Configuration

### Algorithm Parameters
- `ROOT_FORCE_PROBABILITY`: 0.85 - Likelihood of forcing root notes
- `PERFECT_FIFTH_BOOST`: 4.0 - Perfect fifth probability multiplier
- `GAUSSIAN_STRENGTH`: 2.0 - Spatial clustering intensity
- `MAX_TOTAL_VOICES`: 48 - Maximum simultaneous voices

### Debug Settings
- `DEBUG_VERBOSE`: False - Detailed allocation logging
- `PRINT_CONSTRAINT_APPLICATIONS`: False - Constraint step-by-step output
- `PRINT_SELECTIONS`: False - Voice selection details

## Voice State Indicators
- `♪` - Active voice (volume=1)
- `~` - Sustained only (volume=0, sustained=True)
- `S` - Sustained flag present

## Key Features Implemented

### ✅ Completed
- [x] Normalized probability distribution system
- [x] Cascading harmonic construction
- [x] All constraint types (hard and soft)
- [x] Sustain pedal with proper state management
- [x] Real-time OSC communication
- [x] Compact state display with detailed rank info
- [x] Root forcing and perfect interval boosting
- [x] Spatial clustering and voice leading
- [x] 48-voice management with sustained state tracking

### 🎯 Performance Characteristics
- **Allocation Speed**: ~6ms for 3 voices
- **Memory Usage**: Minimal (normalized arrays)
- **Real-time Safe**: No blocking operations
- **Musical Intelligence**: Constraint-driven harmonic selection

## Technical Details

### Probability Map Mechanics
1. Initialize uniform distribution (1/128 per note)
2. Apply constraints in priority order
3. Rebalance after each constraint to maintain sum=1.0
4. Perform weighted random selection
5. Allocate to first available voice
6. Update global active voice list

### Sustain Pedal State Machine
```
Sustain OFF → Sustain ON:  Mark all active voices as sustained
Sustain ON → Sustain OFF:  Deallocate all sustained voices
New Allocation:            Skip sustained voices, treat as "held"
```

### GCI to MIDI Conversion
```python
center_midi = 60 + ((rank.gci - 5) // 3) * 12
spread_range = ±(rank.density // 2) octaves
```

## Development Notes

The system represents a complete rewrite of the original FIBRIL algorithm, moving from additive/class-based allocation to a normalized probability approach with cascading harmonic relationships. All musical intelligence is now modular and tunable through constraint objects.

---

*Last Updated: July 11, 2025*