# FIBRIL - Implementation Overview
**The system operates a 48-voice polyphonic Max/MSP patch, where each voice is defined by:**
- A **MIDI note** (0–127)
- A **Volume** (0 = off, 1 = on)
---
# Initialization
On startup, all 48 voices are initialized as follows:
- **MIDI Notes** are randomly chosen from: 48, 55, 60, 67, 72
- **Volumes** are set to 0
This ensures the initial voicing forms a **perfect fifth-based cluster**, centered within ±1 octave of Middle C, providing a harmonically consistent and contained starting chord.
---
# Computer Keyboard Interface
## Rank System
- The center of the computer keyboard is divided into **8 Ranks**.
- Each Rank outputs a **4-bit Grey Code**.
- Example: Pressing [F] yields Rank 3 → [0, 0, 0, 1]
## “Clavier” Layout Diagram
<pre>      R7                                         R8
[1] [2] [3] [4]                            [9] [0] [-] [=]
          R5                                 R6
    [Q] [W] [E] [R]                    [I] [O] [P] [[]
              R3                         R4
        [A] [S] [D] [F]            [J] [K] [L] [;]
                  R1                  R2
            [Z] [X] [C] [V]    [N] [M] [,] [.]
</pre>
## Key Terms
- **GCI (Grey Code Integer)**: The integer value of the Grey Code, used for internal **Voice Leading**.
- **Rank Density**: A function of GCI that determines how many voices a Rank contributes to the overall chord.
## Rank Density Mapping:
<pre>
GCI       Example      Voices
 0        [0000]         0
 1        [0010]         2
 2        [0011]         3
 3        [1101]         4
 4        [1111]         6
</pre>
## Tonicization & Priority
- Each Rank has:
    - A **Rank Number** (R1–R8)
    - A **Tonicization** (assigned scale degree)
    - A **Priority Order** (for evaluation in the algorithm)
Default Tonicization:
R1: supertonic
R2: mediant
R3: tonic
R4: dominant
R5: submediant
R6: subdominant
R7: subtonic (used for Key Substitution)
R8: leading tone

Default Priority Order:
[R3, R6, R1, R4, R5, R2, R8, R7]
---
# Added Controls
## General
- **Spacebar**: Sustain Pedal
- **Numpad [1–9, /, , -]**: Sets Key Center (e.g. 5 = C, 6 = G, 4 = F)
- **Numpad [0, .]**: Toggle Right-Hand Layout Mode:
    - R->L (identical to left)
    - Mirrored (horizontal reflection of left)
## Editing Ranks
- **Arrow Keys**:
    - **Up/Down** toggle edit mode between Priority and Tonicization
    - **Left/Right** select a Rank
    - **Numpad [+ / Enter]**: Increment/decrement values
---
# Grey Code Modes
<pre>
Mirrored Mode        R->L Mode <br />
 0001  1000         0001  0001<br />
 0011  1100         0011  0011<br />
 0010  0100         0010  0010<br />
 0110  0110         0110  0110<br />
 0111  1110         0111  0111<br />
 0101  1010         0101  0101<br />
 0100  0010         0100  0100<br />
 1100  0011         1100  1100<br />
 1101  1011         1101  1101<br />
 1111  1111         1111  1111<br />
 1110  0111         1110  1110<br />
 1010  0101         1010  1010<br />
 1011  1101         1011  1011<br />
 1001  1001         1001  1001<br />
 1000  0001         1000  1000<br />
</pre>
   ---
# Algorithm Overview
## Stored State
- **CurrentVoicingNotes**: MIDI/Volume pairs for currently active voices
- **Probability Maps**:
    - One per Rank per cycle
    - Values reset between keypress cycles
    - Aggregated into a **Global Probability Map** based on Rank Priority
---
# Rank Evaluation Cycle
## 1. StateTransitionBypass()
- Skip if the Rank has no keys pressed
## 2. SustainBypass()
- If sustain is active:
    - Notes currently playing **must not be released**
    - If >48 voices are held, **earliest notes are released**
    - Sustained notes are counted when fulfilling the **Rooted Note Requirement**
## 3. Rooted Note Requirement
Every active Rank **must voice its Root and Perfect Fifth** before any other chord tones.
- These can be in **any octave**
- Example:
    - If the tonic and dominant Ranks are active, the system must voice their respective roots and fifths
    - Once those are voiced (or sustained), other degrees can be added: 3rd, 2nd, 4th, 6th, 7th, 9th, b13th, #5th
---
# Global Heuristics
## GlobalDensityBias()
- Sum of all Rank Densities = **Total Number of Voices**
- If this + sustained voices > 48:
    - Release the lowest MIDI notes to meet the limit
- Notes already active cannot be selected again in this cycle
- However, they count toward the “Rooted” condition
- Lower priority Ranks will be biased toward **higher octaves** to avoid muddiness in midrange
    - Bias calculated from:
        - Rank Density
        - Global Density
        - Rank Priority
---
# Rank-Specific Heuristics
## ValidDestinationSelection()
- Once Root + Fifth are secured:
    - Determine available harmonic degrees:
        - 1, 5, 3, 2, 4, 6, 7, 9, 11, b13, #5
    - Assign probabilities to these notes for inclusion in Global Map
## VoiceLeadingRule()
- Compare current and previous GCI:
    - If **GCI ↑**, voices encouraged to move **upward**
        - Check if any of the currently voicing notes are within -1 or -2 MIDI values of a valid destination; if so, that  destination should be more probable
    - If **GCI ↓**, boost destination notes just **below** current voicings
        - Check if any of the currently voicing notes are within +1 or +2 MIDI values of a valid destination; if so, that  destination should be more probable
---
# StateTransitionAlgorithm()
- Combine:
    - Valid Destinations
    - VoiceLeadingRule biases
    - GlobalDensityBias
- Apply a shaping curve (e.g. Poisson, Gaussian) to set probability weights
    - Example:
        - If MIDI = 2x, Poisson centered at x = 40 maps best to MIDI ≈ 80
        - Edge values (20 or 127) get minimal bias

Final step selects notes based on this adjusted Global Probability Map.
---
**The keyboard I'm using is the Leopold FC900R. Pressing Fn+Home with this keyboard on MacOS enables NKRO, which works in Max 9 (where user input is being handled)**