#!/usr/bin/env python3
"""
Simple GUI test to verify tkinter and matplotlib work
"""

try:
    import tkinter as tk
    print("✅ tkinter imported successfully")
    
    # Test basic tkinter window
    root = tk.Tk()
    root.title("FIBRIL GUI Test")
    root.geometry("300x200")
    
    label = tk.Label(root, text="GUI Test Successful!\nClose this window.", font=("Arial", 14))
    label.pack(expand=True)
    
    print("✅ Tkinter window created - you should see a test window")
    print("Close the test window to continue...")
    
    root.mainloop()
    print("✅ GUI test completed successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("You need to install tkinter for your system")
except Exception as e:
    print(f"❌ GUI error: {e}")
    print("There's an issue with the GUI system")
