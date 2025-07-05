#!/usr/bin/env python3
"""
Simple test to verify FIBRIL runs without pythonosc
"""

import subprocess
import time
import socket
from fibril_udp import build_osc_message

def test_fibril_no_pythonosc():
    """Test FIBRIL system without pythonosc dependencies"""
    print("🔬 FIBRIL No-pythonosc Test")
    print("=" * 30)
    
    print("1. Testing OSC message building...")
    try:
        # Test our minimal OSC implementation
        msg = build_osc_message("/test", 42)
        print(f"✅ Built OSC message: {len(msg)} bytes")
    except Exception as e:
        print(f"❌ OSC building failed: {e}")
        return False
    
    print("2. Starting FIBRIL system...")
    try:
        # Start FIBRIL in background
        process = subprocess.Popen(
            ["python", "fibril_main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for startup
        time.sleep(2)
        
        # Check if it's still running (no crash)
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"❌ FIBRIL crashed on startup:")
            print(f"Error: {stderr}")
            return False
        
        print("✅ FIBRIL started successfully")
        
        print("3. Testing message sending...")
        # Send a test message
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        rank_msg = build_osc_message("/R3_0100", 1)
        sock.sendto(rank_msg, ("127.0.0.1", 1761))
        sock.close()
        print("✅ Sent test OSC message")
        
        # Let it run briefly
        time.sleep(1)
        
        print("4. Stopping FIBRIL...")
        process.terminate()
        process.wait(timeout=5)
        print("✅ FIBRIL stopped cleanly")
        
        print("\n🎉 SUCCESS: FIBRIL works without pythonosc!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        try:
            process.terminate()
        except:
            pass
        return False

if __name__ == "__main__":
    success = test_fibril_no_pythonosc()
    exit(0 if success else 1)
