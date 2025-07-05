#!/usr/bin/env python3
"""
Simple UDP test to verify MaxMSP can receive data
"""

import socket
import time
import struct

def test_simple_udp():
    """Send simple UDP packets to test MaxMSP connectivity"""
    print("🔌 Testing UDP connectivity to MaxMSP")
    print("=" * 35)
    
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Test messages
        messages = [
            b"Hello MaxMSP",
            b"Test message 2", 
            b"FIBRIL UDP test"
        ]
        
        print("Sending test UDP packets to port 1762...")
        
        for i, msg in enumerate(messages):
            sock.sendto(msg, ("127.0.0.1", 1762))
            print(f"  {i+1}. Sent: {msg.decode()}")
            time.sleep(0.5)
        
        # Try sending a simple OSC-like message
        osc_test = b"/test\x00\x00\x00,i\x00\x00\x00\x00\x00\x2A"  # "/test" with integer 42
        sock.sendto(osc_test, ("127.0.0.1", 1762))
        print(f"  4. Sent simple OSC message: /test 42")
        
        sock.close()
        
        print("\n✅ UDP packets sent successfully!")
        print("📋 MaxMSP Check:")
        print("   - In MaxMSP: [udpreceive 1762] → [print]")
        print("   - You should see the test messages above")
        print("   - If you see them, UDP is working!")
        print("   - If not, check port/firewall settings")
        
    except Exception as e:
        print(f"❌ UDP test failed: {e}")
        print("   Check if port 1762 is available")

if __name__ == "__main__":
    test_simple_udp()
