#!/usr/bin/env python3
"""
Quick OSC test client to send messages to FIBRIL system
This simulates MaxMSP sending rank data to trigger voice allocation
"""

import time
from pythonosc.udp_client import SimpleUDPClient

def test_fibril_osc():
    """Send test OSC messages to FIBRIL system"""
    client = SimpleUDPClient("127.0.0.1", 1761)
    
    print("🎛️ OSC Test Client - Sending test data to FIBRIL...")
    print("   Target: 127.0.0.1:1761")
    
    # Test 1: Activate rank 1 with some density
    print("\n📤 Test 1: Activating Rank 1 with density 2")
    client.send_message("/fibril/rank/1/density", 2.0)
    time.sleep(0.5)
    
    # Test 2: Activate rank 3 as well
    print("📤 Test 2: Activating Rank 3 with density 1")
    client.send_message("/fibril/rank/3/density", 1.0)
    time.sleep(0.5)
    
    # Test 3: Add more density to create interesting spatial clustering
    print("📤 Test 3: Activating Rank 2 with density 1")
    client.send_message("/fibril/rank/2/density", 1.0)
    time.sleep(0.5)
    
    # Test 4: Turn on sustain
    print("📤 Test 4: Enabling sustain")
    client.send_message("/fibril/sustain", 1)
    time.sleep(0.5)
    
    # Test 5: Change key center
    print("📤 Test 5: Setting key center to D (62)")
    client.send_message("/fibril/key_center", 62)
    time.sleep(0.5)
    
    # Test 6: Reduce density gradually
    print("📤 Test 6: Reducing densities gradually...")
    client.send_message("/fibril/rank/1/density", 1.0)
    time.sleep(0.3)
    client.send_message("/fibril/rank/3/density", 0.5)
    time.sleep(0.3)
    client.send_message("/fibril/rank/2/density", 0.0)
    time.sleep(0.3)
    
    # Test 7: Turn off everything
    print("📤 Test 7: Turning off all ranks")
    client.send_message("/fibril/rank/1/density", 0.0)
    client.send_message("/fibril/rank/3/density", 0.0)
    time.sleep(0.5)
    
    print("✅ OSC test sequence complete!")
    print("   Check FIBRIL main terminal for voice allocation results")

if __name__ == "__main__":
    test_fibril_osc()
