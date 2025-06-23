# TO DO:
---
## Implement _run_dbn_algorithm()
- Create the functions for:
    - StateTransitionBypass()
    - SustainBypass()
        - if self.current_state.sustain: self.GlobalDensityBias()
        - else: ...
    - GlobalDensityBias()
    - ValidDestinationSelection()
        - Make this run theough all the other ranks' first 4 functions in the algorithm chain, then russian doll your way bsck out to here and continue
    - VoiceLeadingRule()
    - StateTransitionAlgorithm()
        - First implement this with a norbal distribution, then play arojnd kster with custom functions