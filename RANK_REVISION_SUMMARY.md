# FIBRIL Rank Class Revision Summary

## Completed Changes ✅

### 1. Rank Class Updates
- **Renamed:** `position` → `priority` 
- **Updated initialization:** 
  - Ranks 1-7: `priority = rank_number`, `tonicization = rank_number`
  - Rank 8: `priority = 8`, `tonicization = 9` (subtonic/sharp 5th)
- **Updated display:** Now shows Priority and Tonicization columns

### 2. New UDP Message Handling
- **`/Rn_priority`**: Updates the priority value for rank n
- **`/Rn_tonicization`**: Updates the tonicization value for rank n
- **Example messages:**
  - `/R1_priority 5` → Sets Rank 1's priority to 5
  - `/R3_tonicization 7` → Sets Rank 3's tonicization to 7 (leading tone)

### 3. Updated Components

#### `fibril_classes.py`:
- Changed `position: int` to `priority: int`
- Updated tonicization logic (9 = subtonic for whole tone scale)
- Updated copy method to use `priority`

#### `fibril_init.py`:
- Ranks 1-7 initialize with priority and tonicization matching rank number
- Rank 8 initializes with priority=8, tonicization=9

#### `fibril_udp.py`:
- Added parsing for `/Rn_priority` messages
- Added parsing for `/Rn_tonicization` messages
- Removed old position message handling

#### `fibril_main.py`:
- Added handling for `rank_priority` message type
- Added handling for `rank_tonicization` message type
- Updated display to show Priority and Tonicization columns
- Removed old position update handling

#### `fibril_algorithms.py`:
- Updated all references from `rank.position` to `rank.priority`

### 4. Current Display Format
```
RANKS:
Number | Priority | Grey Code    | GCI | Density | Tonicization
-------|----------|--------------|-----|---------|-------------
   1   |     1    | [0,0,0,0]    |   0 |    0    |       1
   2   |     2    | [0,0,0,0]    |   0 |    0    |       2
   3   |     3    | [0,0,0,0]    |   0 |    0    |       3
   4   |     4    | [0,0,0,0]    |   0 |    0    |       4
   5   |     5    | [0,0,0,0]    |   0 |    0    |       5
   6   |     6    | [0,0,0,0]    |   0 |    0    |       6
   7   |     7    | [0,0,0,0]    |   0 |    0    |       7
   8   |     8    | [0,0,0,0]    |   0 |    0    |       9
```

### 5. MaxMSP Integration
- **Rank Numbers:** Fixed (1-8), not affected by MaxMSP
- **Priority Control:** Use `/R1_priority`, `/R2_priority`, etc.
- **Tonicization Control:** Use `/R1_tonicization`, `/R2_tonicization`, etc.
- **Grey Code Control:** Still via `/R1_1000`, `/R2_0100`, etc.

### 6. Tonicization Scale Degrees
- 1 = Tonic
- 2 = Supertonic  
- 3 = Mediant
- 4 = Subdominant
- 5 = Dominant
- 6 = Submediant
- 7 = Leading tone
- 8 = Octave
- 9 = Subtonic (sharp 5th, whole tone scale) - **Rank 8 default**

### 7. Test Results
- ✅ All 9 comprehensive tests passing (100% success rate)
- ✅ Updated voice allocation algorithm working correctly
- ✅ New UDP message parsing functional
- ✅ System state display showing priority and tonicization
- ✅ Rank 8 properly initialized with tonicization = 9

## Usage Examples

### Set Rank Priorities (MaxMSP)
```
/R1_priority 3    # Rank 1 gets priority 3
/R4_priority 1    # Rank 4 gets priority 1 (highest)
/R8_priority 7    # Rank 8 gets priority 7
```

### Set Rank Tonicizations (MaxMSP)
```
/R1_tonicization 5    # Rank 1 becomes dominant
/R3_tonicization 1    # Rank 3 becomes tonic
/R8_tonicization 9    # Rank 8 stays subtonic (whole tone)
```

The FIBRIL system now provides complete MaxMSP control over rank priorities and tonicizations while maintaining fixed rank numbers for consistent reference.
