#!/usr/bin/env python3
"""
FIBRIL Probability Comb Visualizer

Interactive test environment for the FIBRIL harmonic probability system.
Visualizes the step-by-step evolution of probability "combs" as voices are allocated.
"""

import math
import random
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
import time

@dataclass
class TestRank:
    """Simplified rank for testing the comb algorithm"""
    number: int
    grey_code: List[int]
    gci: int = 0
    density: int = 0
    priority: int = 1
    tonicization: int = 1
    previous_gci: int = 0
    owned_voices: List[int] = None  # MIDI notes this rank currently owns
    
    def __post_init__(self):
        if self.owned_voices is None:
            self.owned_voices = []
        self.calculate_gci_and_density()
    
    def calculate_gci_and_density(self):
        """Calculate GCI and density from grey code"""
        # GCI calculation (Gray Code Index)
        self.gci = 0
        for i, bit in enumerate(self.grey_code):
            if bit == 1:
                self.gci += 2 ** (3 - i)
        
        # Density calculation (number of 1s)
        self.density = sum(self.grey_code)

class ProbabilityCombGenerator:
    """Generates probability combs for individual ranks and global system"""
    
    def __init__(self, key_center: int = 60):
        self.key_center = key_center
        self.harmonic_degrees = [0, 4, 7, 11, 14]  # 1, 3, 5, 7, 9 in semitones
        self.extended_degrees = [17, 20, 6]  # 11, b13, #5 in semitones
        
    def generate_rank_comb(self, rank: TestRank, forbidden_notes: Set[int], 
                          sustained_notes: Set[int]) -> List[float]:
        """Generate probability comb for a single rank"""
        comb = [0.0] * 128
        
        if rank.density == 0:
            return comb
            
        # Get harmonic degree probabilities
        degree_probs = self._get_harmonic_degree_probabilities(rank, forbidden_notes, sustained_notes)
        
        # Apply octave distribution
        octave_curve = self._generate_octave_distribution()
        
        # Apply voice leading constraints
        voice_leading_mask = self._generate_voice_leading_mask(rank)
        
        # Build the comb
        for midi in range(128):
            octave = midi // 12
            note_class = midi % 12
            rank_tonic = self._get_rank_tonic(rank)
            
            # Check if this MIDI note corresponds to a harmonic degree
            harmonic_strength = 0.0
            for degree_offset, prob in degree_probs.items():
                target_note = (rank_tonic + degree_offset) % 12
                if note_class == target_note:
                    harmonic_strength += prob
            
            # Apply octave weighting
            octave_weight = octave_curve[midi] if midi < len(octave_curve) else 0.0
            
            # Apply voice leading mask
            voice_leading_weight = voice_leading_mask[midi]
            
            # Combine all factors
            comb[midi] = harmonic_strength * octave_weight * voice_leading_weight
            
        return comb
    
    def _get_harmonic_degree_probabilities(self, rank: TestRank, forbidden_notes: Set[int], 
                                         sustained_notes: Set[int]) -> Dict[int, float]:
        """Calculate probability weights for harmonic degrees"""
        # Base probabilities
        probs = {
            0: 0.24,   # Root (1st)
            7: 0.24,   # Fifth (5th)
            4: 0.16,   # Third (3rd)
            11: 0.12,  # Seventh (7th)
            14: 0.08,  # Ninth (9th) - spills to next octave
        }
        
        # Extended degrees share remaining probability
        remaining = 1.0 - sum(probs.values())
        extended_prob = remaining / len(self.extended_degrees)
        for degree in self.extended_degrees:
            probs[degree] = extended_prob
            
        # Check for root/fifth conflict and adjust
        rank_tonic = self._get_rank_tonic(rank)
        
        # Check if root or fifth (≤ key center) are already taken
        root_taken = False
        fifth_taken = False
        
        for midi in forbidden_notes.union(sustained_notes):
            if midi <= self.key_center:
                note_class = midi % 12
                if note_class == (rank_tonic % 12):
                    root_taken = True
                if note_class == ((rank_tonic + 7) % 12):
                    fifth_taken = True
        
        if root_taken or fifth_taken:
            # Halve root/fifth probabilities, double 3rd/7th/9th
            probs[0] *= 0.5  # Root
            probs[7] *= 0.5  # Fifth
            probs[4] *= 2.0  # Third
            probs[11] *= 2.0  # Seventh
            probs[14] *= 2.0  # Ninth
            
        return probs
    
    def _generate_octave_distribution(self) -> List[float]:
        """Generate normal distribution centered at key center"""
        curve = []
        sigma = 18.0  # 1.5 octaves in semitones
        
        for midi in range(128):
            exponent = -((midi - self.key_center) ** 2) / (2 * sigma ** 2)
            curve.append(math.exp(exponent))
            
        return curve
    
    def _generate_voice_leading_mask(self, rank: TestRank) -> List[float]:
        """Generate voice leading directional mask"""
        mask = [1.0] * 128
        
        if not rank.owned_voices:
            return mask
            
        gci_change = rank.gci - rank.previous_gci
        
        if gci_change > 0:  # GCI increasing - only above highest owned note
            highest_note = max(rank.owned_voices)
            for midi in range(highest_note + 1):
                mask[midi] = 0.0
                
        elif gci_change < 0:  # GCI decreasing - only below lowest owned note
            lowest_note = min(rank.owned_voices)
            for midi in range(lowest_note, 128):
                mask[midi] = 0.0
                
        return mask
    
    def _get_rank_tonic(self, rank: TestRank) -> int:
        """Get the tonic note for a rank based on its tonicization"""
        key_center_pc = self.key_center % 12
        scale_offsets = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11, 8: 0, 9: 6}
        offset = scale_offsets.get(rank.tonicization, 0)
        return (key_center_pc + offset) % 12

class FibrilCombVisualizer:
    """Main application for visualizing FIBRIL probability combs"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FIBRIL Probability Comb Visualizer")
        self.root.geometry("1400x900")
        
        # Algorithm state
        self.key_center = 60  # Middle C
        self.ranks = [TestRank(i+1, [0,0,0,0], priority=i+1, tonicization=i+1) for i in range(8)]
        self.comb_generator = ProbabilityCombGenerator(self.key_center)
        self.current_step = 0
        self.animation_steps = []
        self.forbidden_notes = set()
        self.sustained_notes = set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Right panel for visualization
        viz_frame = ttk.Frame(main_frame)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_control_panel(control_frame)
        self.setup_visualization_panel(viz_frame)
        
    def setup_control_panel(self, parent):
        """Setup the control panel with rank inputs and parameters"""
        # Key Center control
        key_frame = ttk.LabelFrame(parent, text="Key Center", padding=10)
        key_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(key_frame, text="MIDI Note:").pack()
        self.key_center_var = tk.IntVar(value=self.key_center)
        key_spinbox = ttk.Spinbox(key_frame, from_=0, to=127, textvariable=self.key_center_var,
                                 command=self.update_key_center, width=10)
        key_spinbox.pack()
        
        # Rank controls
        ranks_frame = ttk.LabelFrame(parent, text="Rank Grey Codes", padding=10)
        ranks_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.rank_buttons = []
        for i in range(8):
            rank_frame = ttk.Frame(ranks_frame)
            rank_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(rank_frame, text=f"R{i+1}:", width=3).pack(side=tk.LEFT)
            
            rank_bits = []
            for j in range(4):
                var = tk.IntVar()
                btn = ttk.Checkbutton(rank_frame, variable=var, 
                                    command=lambda r=i, b=j: self.toggle_bit(r, b))
                btn.pack(side=tk.LEFT, padx=2)
                rank_bits.append(var)
            
            # Priority and Tonicization
            ttk.Label(rank_frame, text="P:").pack(side=tk.LEFT, padx=(10, 0))
            priority_var = tk.IntVar(value=i+1)
            ttk.Spinbox(rank_frame, from_=1, to=8, textvariable=priority_var, 
                       width=3, command=lambda r=i: self.update_priority(r)).pack(side=tk.LEFT)
            
            ttk.Label(rank_frame, text="T:").pack(side=tk.LEFT, padx=(5, 0))
            tonic_var = tk.IntVar(value=i+1 if i < 7 else 9)
            ttk.Spinbox(rank_frame, from_=1, to=9, textvariable=tonic_var, 
                       width=3, command=lambda r=i: self.update_tonicization(r)).pack(side=tk.LEFT)
            
            self.rank_buttons.append({
                'bits': rank_bits,
                'priority': priority_var,
                'tonicization': tonic_var
            })
        
        # Animation controls
        anim_frame = ttk.LabelFrame(parent, text="Animation", padding=10)
        anim_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(anim_frame, text="Step Through Algorithm", 
                  command=self.start_animation).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(anim_frame, text="Reset", command=self.reset_system).pack(fill=tk.X)
        
        # Status display
        status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(status_frame, height=15, width=40)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_visualization_panel(self, parent):
        """Setup the matplotlib visualization panel"""
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.update_visualization()
        
    def toggle_bit(self, rank_idx, bit_idx):
        """Toggle a bit in a rank's grey code"""
        current_value = self.rank_buttons[rank_idx]['bits'][bit_idx].get()
        self.ranks[rank_idx].grey_code[bit_idx] = current_value
        self.ranks[rank_idx].previous_gci = self.ranks[rank_idx].gci
        self.ranks[rank_idx].calculate_gci_and_density()
        self.update_status()
        
    def update_priority(self, rank_idx):
        """Update rank priority"""
        priority = self.rank_buttons[rank_idx]['priority'].get()
        self.ranks[rank_idx].priority = priority
        self.update_status()
        
    def update_tonicization(self, rank_idx):
        """Update rank tonicization"""
        tonicization = self.rank_buttons[rank_idx]['tonicization'].get()
        self.ranks[rank_idx].tonicization = tonicization
        self.update_status()
        
    def update_key_center(self):
        """Update the key center"""
        self.key_center = self.key_center_var.get()
        self.comb_generator.key_center = self.key_center
        self.update_status()
        
    def update_status(self):
        """Update the status display"""
        self.status_text.delete(1.0, tk.END)
        
        # Key center info
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = self.key_center // 12 - 1
        note_name = note_names[self.key_center % 12]
        
        self.status_text.insert(tk.END, f"Key Center: MIDI {self.key_center} ({note_name}{octave})\n\n")
        
        # Rank information
        self.status_text.insert(tk.END, "RANKS:\n")
        self.status_text.insert(tk.END, "Num | Grey Code | GCI | Density | Priority | Tonic\n")
        self.status_text.insert(tk.END, "----|-----------|-----|---------|----------|------\n")
        
        for rank in self.ranks:
            grey_str = ''.join(map(str, rank.grey_code))
            self.status_text.insert(tk.END, 
                f" {rank.number:2d} |    {grey_str}   | {rank.gci:3d} |   {rank.density:3d}   |    {rank.priority:2d}    |  {rank.tonicization:2d}\n")
        
        # Active voices count
        total_density = sum(rank.density for rank in self.ranks if rank.density > 0)
        self.status_text.insert(tk.END, f"\nTotal Active Density: {total_density}\n")
        
    def start_animation(self):
        """Start the step-by-step animation"""
        try:
            self.reset_system()
            self.generate_animation_steps()
            self.animate_step()
        except Exception as e:
            messagebox.showerror("Error", f"Animation failed: {str(e)}")
            
    def generate_animation_steps(self):
        """Generate all animation steps"""
        self.animation_steps = []
        self.forbidden_notes = set()
        self.sustained_notes = set()
        
        # Get active ranks sorted by priority
        active_ranks = [rank for rank in self.ranks if rank.density > 0]
        active_ranks.sort(key=lambda r: r.priority)
        
        if not active_ranks:
            self.animation_steps.append({
                'step_name': 'No Active Ranks',
                'global_comb': [0.0] * 128,
                'rank_combs': {},
                'selected_notes': [],
                'forbidden_notes': set()
            })
            return
            
        step_num = 0
        
        # Initial global comb
        rank_combs = {}
        global_comb = [0.0] * 128
        
        for rank in active_ranks:
            rank_comb = self.comb_generator.generate_rank_comb(rank, self.forbidden_notes, self.sustained_notes)
            rank_combs[rank.number] = rank_comb
            
            # Weight by priority and add to global
            weight = (9 - rank.priority) / 8.0
            for i in range(128):
                global_comb[i] += rank_comb[i] * weight
                
        # Normalize global comb
        total_prob = sum(global_comb)
        if total_prob > 0:
            global_comb = [p / total_prob for p in global_comb]
            
        self.animation_steps.append({
            'step_name': f'Step {step_num}: Initial Global Comb',
            'global_comb': global_comb.copy(),
            'rank_combs': rank_combs.copy(),
            'selected_notes': [],
            'forbidden_notes': self.forbidden_notes.copy()
        })
        step_num += 1
        
        # Now allocate voices rank by rank
        for rank in active_ranks:
            for voice_num in range(rank.density):
                # Select a note from the current global comb
                selected_midi = self.sample_from_comb(global_comb, self.forbidden_notes)
                
                if selected_midi is not None:
                    # Add to rank's owned voices
                    rank.owned_voices.append(selected_midi)
                    self.forbidden_notes.add(selected_midi)
                    
                    self.animation_steps.append({
                        'step_name': f'Step {step_num}: Rank {rank.number} selects MIDI {selected_midi}',
                        'global_comb': global_comb.copy(),
                        'rank_combs': rank_combs.copy(),
                        'selected_notes': [selected_midi],
                        'forbidden_notes': self.forbidden_notes.copy()
                    })
                    step_num += 1
                    
                    # Regenerate all combs for next selection
                    rank_combs = {}
                    global_comb = [0.0] * 128
                    
                    for r in active_ranks:
                        rank_comb = self.comb_generator.generate_rank_comb(r, self.forbidden_notes, self.sustained_notes)
                        rank_combs[r.number] = rank_comb
                        
                        weight = (9 - r.priority) / 8.0
                        for i in range(128):
                            global_comb[i] += rank_comb[i] * weight
                            
                    # Normalize
                    total_prob = sum(global_comb)
                    if total_prob > 0:
                        global_comb = [p / total_prob for p in global_comb]
                        
                    self.animation_steps.append({
                        'step_name': f'Step {step_num}: Recomputed Global Comb',
                        'global_comb': global_comb.copy(),
                        'rank_combs': rank_combs.copy(),
                        'selected_notes': [],
                        'forbidden_notes': self.forbidden_notes.copy()
                    })
                    step_num += 1
                    
    def sample_from_comb(self, comb: List[float], forbidden: Set[int]) -> int:
        """Sample a MIDI note from the probability comb"""
        # Filter out forbidden notes
        valid_probs = []
        valid_indices = []
        
        for i, prob in enumerate(comb):
            if i not in forbidden and prob > 0:
                valid_probs.append(prob)
                valid_indices.append(i)
                
        if not valid_probs:
            return None
            
        # Weighted random selection
        total_weight = sum(valid_probs)
        if total_weight == 0:
            return random.choice(valid_indices) if valid_indices else None
            
        rand_val = random.random() * total_weight
        cumulative = 0
        
        for i, weight in enumerate(valid_probs):
            cumulative += weight
            if rand_val <= cumulative:
                return valid_indices[i]
                
        return valid_indices[-1] if valid_indices else None
        
    def animate_step(self):
        """Animate one step of the algorithm"""
        if self.current_step >= len(self.animation_steps):
            self.status_text.insert(tk.END, "\nAnimation Complete!\n")
            return
            
        step_data = self.animation_steps[self.current_step]
        self.update_visualization(step_data)
        
        # Update status
        self.status_text.insert(tk.END, f"\n{step_data['step_name']}\n")
        if step_data['selected_notes']:
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            for midi in step_data['selected_notes']:
                octave = midi // 12 - 1
                note_name = note_names[midi % 12]
                self.status_text.insert(tk.END, f"  Selected: MIDI {midi} ({note_name}{octave})\n")
        
        self.status_text.see(tk.END)
        self.current_step += 1
        
        # Schedule next step
        self.root.after(1500, self.animate_step)  # 1.5 second delay
        
    def update_visualization(self, step_data=None):
        """Update the matplotlib visualization"""
        self.ax.clear()
        
        if step_data is None:
            # Show initial state
            self.ax.plot(range(128), [0] * 128, 'k-', linewidth=1)
            self.ax.set_title("FIBRIL Probability Combs - No Active Ranks")
        else:
            # Plot global comb
            self.ax.plot(range(128), step_data['global_comb'], 'k-', linewidth=2, 
                        label='Global Comb', alpha=0.8)
            
            # Plot individual rank combs
            colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
            for rank_num, rank_comb in step_data['rank_combs'].items():
                if any(p > 0 for p in rank_comb):  # Only plot if non-zero
                    color = colors[(rank_num - 1) % len(colors)]
                    self.ax.plot(range(128), rank_comb, color=color, linewidth=1, 
                               alpha=0.6, label=f'Rank {rank_num}')
            
            # Highlight selected notes
            for midi in step_data['selected_notes']:
                self.ax.axvline(x=midi, color='red', linestyle='--', linewidth=2, alpha=0.8)
                
            # Highlight forbidden notes
            for midi in step_data['forbidden_notes']:
                self.ax.axvline(x=midi, color='gray', linestyle=':', linewidth=1, alpha=0.5)
                
            self.ax.set_title(step_data['step_name'])
            
        # Formatting
        self.ax.set_xlabel('MIDI Note')
        self.ax.set_ylabel('Probability')
        self.ax.set_xlim(0, 127)
        self.ax.grid(True, alpha=0.3)
        
        # Add key center line
        self.ax.axvline(x=self.key_center, color='gold', linestyle='-', linewidth=2, alpha=0.7, label='Key Center')
        
        self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        self.fig.tight_layout()
        self.canvas.draw()
        
    def reset_system(self):
        """Reset the system to initial state"""
        self.current_step = 0
        self.animation_steps = []
        self.forbidden_notes = set()
        self.sustained_notes = set()
        
        # Reset rank owned voices
        for rank in self.ranks:
            rank.owned_voices = []
            rank.previous_gci = 0
            
        self.update_visualization()
        self.update_status()
        
    def run(self):
        """Start the application"""
        self.update_status()
        self.root.mainloop()

if __name__ == "__main__":
    app = FibrilCombVisualizer()
    app.run()
