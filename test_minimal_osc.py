#!/usr/bin/env python3
"""
Test our pythonosc-free UDP handler
"""

import time
import threading
from fibril_udp import SimpleOSCClient

def test_minimal_osc():
    """Test our minimal OSC implementation"""
    print("🧪 Testing minimal OSC implementation")
    print("=" * 40)
    
    try:
        # Create our minimal OSC client
        client = SimpleOSCClient("127.0.0.1", 1762)
        
        # Test sending various message types
        print("Sending OSC messages to port 1762...")
        
        client.send_message("/test", 42)
        print("  1. Sent: /test 42")
        time.sleep(0.1)
        
        client.send_message("/voice_1_MIDI", 60)
        print("  2. Sent: /voice_1_MIDI 60")
        time.sleep(0.1)
        
        client.send_message("/voice_1_Volume", 1)
        print("  3. Sent: /voice_1_Volume 1")
        time.sleep(0.1)
        
        client.send_message("/active_count", 5)
        print("  4. Sent: /active_count 5")
        time.sleep(0.1)
        
        # Test with different types
        client.send_message("/float_test", 3.14)
        print("  5. Sent: /float_test 3.14")
        time.sleep(0.1)
        
        client.send_message("/string_test", "hello")
        print("  6. Sent: /string_test hello")
        
        client.close()
        
        print("\n✅ Minimal OSC client test completed!")
        print("📋 MaxMSP Check:")
        print("   - In MaxMSP: [udpreceive 1762] → [print]")
        print("   - You should see OSC messages above")
        print("   - No pythonosc dependencies needed!")
        
    except Exception as e:
        print(f"❌ OSC test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal_osc()
