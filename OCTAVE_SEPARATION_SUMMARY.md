# FIBRIL Octave Separation Heuristic

## ✅ Implementation Complete

The octave separation heuristic has been successfully implemented in the FIBRIL algorithm.

## 🎯 **Formula**

```
octave_number = (rank.priority + 7) / 2
center_midi = key_center + (octave_number - 4) * 12
```

## 📊 **Priority to Octave Mapping**

| Priority | Octave Number | Relative to Key Center | Example (Key = C4) |
|----------|---------------|------------------------|-------------------|
| 1        | 4.0           | At key center         | C4 (MIDI 60)      |
| 2        | 4.5           | 0.5 octaves above     | F#4 (MIDI 66)     |
| 3        | 5.0           | 1 octave above        | C5 (MIDI 72)      |
| 4        | 5.5           | 1.5 octaves above     | F#5 (MIDI 78)     |
| 5        | 6.0           | 2 octaves above       | C6 (MIDI 84)      |
| 6        | 6.5           | 2.5 octaves above     | F#6 (MIDI 90)     |
| 7        | 7.0           | 3 octaves above       | C7 (MIDI 96)      |
| 8        | 7.5           | 3.5 octaves above     | F#7 (MIDI 102)    |

## 🎵 **Musical Benefits**

### **Voice Distribution**
- **High priority ranks (1-2)**: Voice around the key center
- **Medium priority ranks (3-4)**: Voice 1-1.5 octaves above
- **Low priority ranks (5-8)**: Voice 2-3.5 octaves above

### **Prevents Clustering**
- No more "muddy" harmonies with all voices in the same octave
- Each rank has its own preferred octave range
- Natural voice leading and separation

### **Dynamic Behavior**
- When a single rank is active, it voices in its preferred octave
- Multiple ranks create layered harmony across octaves
- Priority changes instantly affect octave placement

## 🔧 **Implementation Details**

### **Algorithm Integration**
- Added to `_build_global_probability_map()` in `fibril_algorithms.py`
- Applied as Gaussian curve multiplier to rank probability curves
- Works alongside existing voice leading and harmonic constraints

### **Real-Time Updates**
- Changes take effect immediately when priorities are updated via OSC
- Visualizer shows octave separation in real-time
- Debug output shows octave centers for each rank

## 🎹 **Usage Example**

```python
# Set different priorities for octave separation
system.ranks[0].priority = 1  # R1 voices around key center
system.ranks[1].priority = 3  # R2 voices 1 octave above
system.ranks[2].priority = 7  # R3 voices 3 octaves above

# Algorithm automatically applies octave separation
new_state = algorithm.allocate_voices(system)
```

## 📡 **OSC Control**

Update rank priorities from MaxMSP to control octave placement:

```
/R1_priority 1    # R1 at key center (octave 4)
/R2_priority 5    # R2 two octaves above (octave 6)
/R3_priority 8    # R3 high octaves (octave 7.5)
```

This creates a **dynamic octave allocation system** where ranks naturally separate into different octave ranges based on their priority, resulting in clearer, more musical voice distributions! 🎵✨
