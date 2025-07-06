#!/usr/bin/env python3
"""
FIBRIL Real-Time Comb Visualizer

Interactive visualization of the FIBRIL comb algorithm with real-time OSC integration.
This visualizer listens for OSC messages from MaxMSP and updates the display in real-time.

Usage:
    python fibril_realtime_visualizer.py [--osc-port PORT]
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import threading
import time
import argparse
import queue
from typing import List, Dict, Optional

# Import FIBRIL components
from fibril_classes import Rank, Voice, SystemState
from fibril_algorithms import FibrilAlgorithm, ProbabilityCurve
from fibril_init import fibril_system

# OSC imports
try:
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
    OSC_AVAILABLE = True
except ImportError:
    OSC_AVAILABLE = False
    print("Warning: python-osc not available. Run 'pip install python-osc' for OSC support.")


class FibrilRealtimeVisualizer:
    """Real-time FIBRIL comb visualizer with OSC integration"""
    
    def __init__(self, osc_port: int = 1763):
        self.osc_port = osc_port
        self.running = True
        
        # Initialize FIBRIL system
        self.system_state = fibril_system.system_state
        self.algorithm = FibrilAlgorithm()
        
        # OSC message queue for thread-safe communication
        self.osc_queue = queue.Queue()
        
        # Animation state
        self.animation_step = 0
        self.animation_running = False
        self.allocated_voices = []
        
        # Create GUI
        self.setup_gui()
        
        # Start OSC server if available
        if OSC_AVAILABLE:
            self.start_osc_server()
        else:
            self.show_osc_warning()
        
        # Start update loop
        self.update_loop()
    
    def setup_gui(self):
        """Create the main GUI window"""
        self.root = tk.Tk()
        self.root.title(f"FIBRIL Real-Time Visualizer (OSC Port: {self.osc_port})")
        self.root.geometry("1400x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create left panel for controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Create right panel for visualization
        viz_frame = ttk.Frame(main_frame)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_control_panel(control_frame)
        self.setup_visualization_panel(viz_frame)
    
    def setup_control_panel(self, parent):
        """Create the control panel with rank controls"""
        # Title
        title_label = ttk.Label(parent, text="FIBRIL Real-Time Controls", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # OSC status
        self.osc_status = ttk.Label(parent, text="OSC: Connecting...", foreground="orange")
        self.osc_status.pack(pady=(0, 10))
        
        # Key center control
        key_frame = ttk.LabelFrame(parent, text="Global Settings")
        key_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(key_frame, text="Key Center:").pack(anchor=tk.W)
        self.key_center_var = tk.IntVar(value=self.system_state.key_center)
        key_scale = ttk.Scale(key_frame, from_=48, to=84, variable=self.key_center_var, 
                             orient=tk.HORIZONTAL, command=self.on_key_center_change)
        key_scale.pack(fill=tk.X, padx=5, pady=2)
        self.key_center_label = ttk.Label(key_frame, text=f"MIDI {self.system_state.key_center}")
        self.key_center_label.pack(anchor=tk.W)
        
        # Sustain control
        self.sustain_var = tk.BooleanVar()
        sustain_check = ttk.Checkbutton(key_frame, text="Sustain Pedal", 
                                       variable=self.sustain_var, command=self.on_sustain_change)
        sustain_check.pack(anchor=tk.W, pady=2)
        
        # Rank controls
        self.rank_controls = []
        for i in range(8):
            rank_frame = self.create_rank_control(parent, i + 1)
            rank_frame.pack(fill=tk.X, pady=2)
        
        # Animation controls
        anim_frame = ttk.LabelFrame(parent, text="Animation")
        anim_frame.pack(fill=tk.X, pady=(10, 0))
        
        button_frame = ttk.Frame(anim_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Step", command=self.step_animation).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Reset", command=self.reset_animation).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Auto", command=self.toggle_auto_animation).pack(side=tk.LEFT, padx=2)
        
        self.animation_label = ttk.Label(anim_frame, text="Step: 0")
        self.animation_label.pack(pady=2)
    
    def create_rank_control(self, parent, rank_num):
        """Create control widgets for a single rank"""
        rank = self.system_state.ranks[rank_num - 1]
        
        frame = ttk.LabelFrame(parent, text=f"Rank {rank_num}")
        
        # Priority control
        ttk.Label(frame, text="Priority:").pack(anchor=tk.W)
        priority_var = tk.IntVar(value=rank.priority)
        priority_scale = ttk.Scale(frame, from_=1, to=8, variable=priority_var, 
                                  orient=tk.HORIZONTAL, command=lambda v, r=rank_num-1: self.on_priority_change(r, v))
        priority_scale.pack(fill=tk.X, padx=5)
        
        # Tonicization control
        ttk.Label(frame, text="Tonicization:").pack(anchor=tk.W)
        tonic_var = tk.IntVar(value=rank.tonicization)
        tonic_combo = ttk.Combobox(frame, textvariable=tonic_var, values=list(range(1, 10)), state="readonly")
        tonic_combo.pack(fill=tk.X, padx=5)
        tonic_combo.bind("<<ComboboxSelected>>", lambda e, r=rank_num-1: self.on_tonicization_change(r, tonic_var.get()))
        
        # Grey code buttons
        grey_frame = ttk.Frame(frame)
        grey_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(grey_frame, text="Grey Code:").pack(anchor=tk.W)
        
        button_frame = ttk.Frame(grey_frame)
        button_frame.pack(fill=tk.X)
        
        grey_buttons = []
        for i in range(4):
            var = tk.BooleanVar(value=bool(rank.grey_code[i]))
            btn = ttk.Checkbutton(button_frame, text=str(i), variable=var,
                                 command=lambda i=i, r=rank_num-1, v=var: self.on_grey_code_change(r, i, v.get()))
            btn.pack(side=tk.LEFT, padx=1)
            grey_buttons.append(var)
        
        # Density display
        density_label = ttk.Label(frame, text=f"Density: {rank.density}")
        density_label.pack(anchor=tk.W, padx=5)
        
        control_data = {
            'frame': frame,
            'priority_var': priority_var,
            'tonic_var': tonic_var,
            'grey_buttons': grey_buttons,
            'density_label': density_label
        }
        self.rank_controls.append(control_data)
        
        return frame
    
    def setup_visualization_panel(self, parent):
        """Create the matplotlib visualization panel"""
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create subplots
        self.ax_curves = self.fig.add_subplot(2, 1, 1)
        self.ax_allocation = self.fig.add_subplot(2, 1, 2)
        
        self.fig.tight_layout()
        
        # Initial plot
        self.update_visualization()
    
    def start_osc_server(self):
        """Start the OSC server in a separate thread"""
        def osc_thread():
            try:
                # Create dispatcher
                dispatcher = Dispatcher()
                dispatcher.map("/R*", self.handle_rank_osc)
                dispatcher.map("/keyCenter", self.handle_key_center_osc)
                dispatcher.map("/sustain", self.handle_sustain_osc)
                
                # Create server
                self.osc_server = BlockingOSCUDPServer(("127.0.0.1", self.osc_port), dispatcher)
                self.osc_status.config(text=f"OSC: Listening on port {self.osc_port}", foreground="green")
                
                print(f"OSC server started on port {self.osc_port}")
                self.osc_server.serve_forever()
                
            except Exception as e:
                print(f"OSC server error: {e}")
                self.osc_status.config(text=f"OSC: Error - {e}", foreground="red")
        
        self.osc_thread = threading.Thread(target=osc_thread, daemon=True)
        self.osc_thread.start()
    
    def handle_rank_osc(self, address, *args):
        """Handle OSC messages for rank updates"""
        try:
            # Parse address like "/R3_0100" or "/R1_priority"
            parts = address.split('_')
            if len(parts) >= 2:
                rank_part = parts[0]  # "/R3"
                rank_num = int(rank_part[2:])  # Extract number
                
                if len(parts) == 2:
                    param = parts[1]
                    value = args[0] if args else 0
                    
                    message = {
                        'rank_num': rank_num,
                        'param': param,
                        'value': value
                    }
                    self.osc_queue.put(('rank_update', message))
                    
        except Exception as e:
            print(f"Error handling rank OSC: {e}")
    
    def handle_key_center_osc(self, address, *args):
        """Handle key center OSC messages"""
        if args:
            self.osc_queue.put(('key_center', args[0]))
    
    def handle_sustain_osc(self, address, *args):
        """Handle sustain OSC messages"""
        if args:
            self.osc_queue.put(('sustain', bool(args[0])))
    
    def show_osc_warning(self):
        """Show warning if OSC is not available"""
        self.osc_status.config(text="OSC: Not available (install python-osc)", foreground="red")
    
    def update_loop(self):
        """Main update loop - processes OSC messages and updates GUI"""
        if not self.running:
            return
            
        # Process OSC messages
        try:
            while not self.osc_queue.empty():
                msg_type, data = self.osc_queue.get_nowait()
                self.process_osc_message(msg_type, data)
        except queue.Empty:
            pass
        
        # Auto animation
        if self.animation_running:
            self.step_animation()
            time.sleep(0.1)  # Animation speed
        
        # Schedule next update
        self.root.after(50, self.update_loop)  # 20 FPS
    
    def process_osc_message(self, msg_type, data):
        """Process OSC messages and update the system state"""
        updated = False
        
        if msg_type == 'rank_update':
            rank_num = data['rank_num']
            param = data['param']
            value = data['value']
            
            if 1 <= rank_num <= 8:
                rank = self.system_state.ranks[rank_num - 1]
                
                if param == 'priority':
                    rank.priority = int(value)
                    self.rank_controls[rank_num - 1]['priority_var'].set(rank.priority)
                    updated = True
                    
                elif param == 'tonicization':
                    rank.tonicization = int(value)
                    self.rank_controls[rank_num - 1]['tonic_var'].set(rank.tonicization)
                    updated = True
                    
                elif len(param) == 4 and all(c in '01' for c in param):
                    # Grey code update like "0100"
                    bit_index = {'1000': 0, '0100': 1, '0010': 2, '0001': 3}.get(param)
                    if bit_index is not None:
                        rank.grey_code[bit_index] = 1 if value > 0 else 0
                        rank.__post_init__()  # Recalculate density
                        
                        # Update GUI
                        self.rank_controls[rank_num - 1]['grey_buttons'][bit_index].set(bool(value))
                        self.rank_controls[rank_num - 1]['density_label'].config(text=f"Density: {rank.density}")
                        updated = True
        
        elif msg_type == 'key_center':
            self.system_state.key_center = int(data)
            self.key_center_var.set(self.system_state.key_center)
            self.key_center_label.config(text=f"MIDI {self.system_state.key_center}")
            updated = True
            
        elif msg_type == 'sustain':
            self.system_state.sustain = bool(data)
            self.sustain_var.set(self.system_state.sustain)
            updated = True
        
        if updated:
            self.update_visualization()
            print(f"Updated from OSC: {msg_type} = {data}")
    
    def on_key_center_change(self, value):
        """Handle key center slider change"""
        self.system_state.key_center = int(float(value))
        self.key_center_label.config(text=f"MIDI {self.system_state.key_center}")
        self.update_visualization()
    
    def on_sustain_change(self):
        """Handle sustain checkbox change"""
        self.system_state.sustain = self.sustain_var.get()
        self.update_visualization()
    
    def on_priority_change(self, rank_idx, value):
        """Handle rank priority change"""
        self.system_state.ranks[rank_idx].priority = int(float(value))
        self.update_visualization()
    
    def on_tonicization_change(self, rank_idx, value):
        """Handle rank tonicization change"""
        self.system_state.ranks[rank_idx].tonicization = value
        self.update_visualization()
    
    def on_grey_code_change(self, rank_idx, bit_idx, value):
        """Handle grey code button change"""
        rank = self.system_state.ranks[rank_idx]
        rank.grey_code[bit_idx] = 1 if value else 0
        rank.__post_init__()  # Recalculate density
        
        # Update density label
        self.rank_controls[rank_idx]['density_label'].config(text=f"Density: {rank.density}")
        self.update_visualization()
    
    def update_visualization(self):
        """Update the matplotlib visualization"""
        self.ax_curves.clear()
        self.ax_allocation.clear()
        
        # Plot individual rank probability curves
        colors = plt.cm.Set3(np.linspace(0, 1, 8))
        midi_range = range(48, 85)  # Focus on useful range
        
        combined_curve = np.zeros(len(midi_range))
        
        for i, rank in enumerate(self.system_state.ranks):
            if rank.density > 0:  # Only show active ranks
                # Generate probability curve for this rank
                root_midi = self.get_rank_root_midi(rank)
                curve = ProbabilityCurve.gaussian(root_midi, width=12, midi_range=midi_range)
                
                # Weight by density
                weighted_curve = np.array(curve) * rank.density
                combined_curve += weighted_curve
                
                # Plot individual curve
                self.ax_curves.plot(midi_range, weighted_curve, 
                                  color=colors[i], alpha=0.7, linewidth=2,
                                  label=f'R{rank.number} (d={rank.density})')
        
        # Plot combined curve
        if np.any(combined_curve):
            self.ax_curves.plot(midi_range, combined_curve, 
                              color='black', linewidth=3, alpha=0.8,
                              label='Combined')
        
        self.ax_curves.set_title('Rank Probability Curves')
        self.ax_curves.set_xlabel('MIDI Note')
        self.ax_curves.set_ylabel('Probability Weight')
        self.ax_curves.legend()
        self.ax_curves.grid(True, alpha=0.3)
        
        # Plot voice allocation
        if hasattr(self, 'allocated_voices') and self.allocated_voices:
            voices_midi = [v.midi_note for v in self.allocated_voices if v.volume]
            if voices_midi:
                self.ax_allocation.hist(voices_midi, bins=range(48, 86), alpha=0.7, color='steelblue')
        
        self.ax_allocation.set_title(f'Voice Allocation (Step {self.animation_step})')
        self.ax_allocation.set_xlabel('MIDI Note')
        self.ax_allocation.set_ylabel('Voice Count')
        self.ax_allocation.grid(True, alpha=0.3)
        
        self.canvas.draw()
    
    def get_rank_root_midi(self, rank):
        """Get the root MIDI note for a rank based on its tonicization"""
        key_center = self.system_state.key_center
        scale_degrees = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11, 8: 11, 9: 10}  # 9 = subtonic
        semitone_offset = scale_degrees.get(rank.tonicization, 0)
        return key_center + semitone_offset
    
    def step_animation(self):
        """Step through the voice allocation animation"""
        try:
            # Run the algorithm
            new_state = self.algorithm.allocate_voices(self.system_state)
            self.allocated_voices = new_state.voices
            self.animation_step += 1
            
            self.animation_label.config(text=f"Step: {self.animation_step}")
            self.update_visualization()
            
        except Exception as e:
            print(f"Animation error: {e}")
    
    def reset_animation(self):
        """Reset the animation"""
        self.animation_step = 0
        self.allocated_voices = []
        self.animation_label.config(text="Step: 0")
        self.update_visualization()
    
    def toggle_auto_animation(self):
        """Toggle automatic animation"""
        self.animation_running = not self.animation_running
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        if hasattr(self, 'osc_server'):
            self.osc_server.shutdown()
        self.root.destroy()
    
    def run(self):
        """Start the visualizer"""
        self.root.mainloop()


def main():
    """Command line entry point"""
    parser = argparse.ArgumentParser(description='FIBRIL Real-Time Comb Visualizer')
    parser.add_argument('--osc-port', type=int, default=1763,
                        help='OSC port to listen for MaxMSP messages (default: 1763)')
    
    args = parser.parse_args()
    
    try:
        visualizer = FibrilRealtimeVisualizer(osc_port=args.osc_port)
        visualizer.run()
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
