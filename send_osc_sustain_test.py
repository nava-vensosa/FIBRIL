#!/usr/bin/env python3
"""
Send proper OSC sustain messages to test the UDP listener
"""

try:
    from pythonosc.udp_client import SimpleUDPClient
    OSC_AVAILABLE = True
except ImportError:
    OSC_AVAILABLE = False
    print("Warning: python-osc not available. Install with: pip install python-osc")

import time

def send_osc_sustain_test():
    if not OSC_AVAILABLE:
        print("Cannot send OSC messages - python-osc not installed")
        return
        
    print("Sending OSC Sustain Test Messages")
    print("=" * 40)
    
    # Create OSC client
    client = SimpleUDPClient("127.0.0.1", 1761)  # FIBRIL listen port
    
    try:
        print("Sending: /sustain 1 (ON)")
        client.send_message("/sustain", 1)
        time.sleep(2)
        
        print("Sending: /sustain 0 (OFF)")
        client.send_message("/sustain", 0)
        time.sleep(1)
        
        print("Messages sent successfully!")
        print("Check FIBRIL console for 'RECEIVED OSC MESSAGE' logs")
        
    except Exception as e:
        print(f"Error sending OSC messages: {e}")

if __name__ == "__main__":
    send_osc_sustain_test()
