#!/usr/bin/env python3
"""
Test SimpleUDPClient for sending messages to MaxMSP
"""

import time
from fibril_udp import SimpleUDPClient

def test_simple_udp_client():
    """Test SimpleUDPClient for MaxMSP communication"""
    print("🔗 Testing SimpleUDPClient for MaxMSP")
    print("=" * 40)
    
    try:
        # Create client for sending to MaxMSP on port 1762
        client = SimpleUDPClient("127.0.0.1", 1762)
        
        print("1. Testing OSC message sending...")
        
        # Send voice messages (typical FIBRIL output)
        client.send_message("/voice_1_MIDI", 60)
        print("✅ Sent: /voice_1_MIDI 60")
        time.sleep(0.1)
        
        client.send_message("/voice_1_Volume", 1)
        print("✅ Sent: /voice_1_Volume 1")
        time.sleep(0.1)
        
        client.send_message("/voice_2_MIDI", 64)
        print("✅ Sent: /voice_2_MIDI 64")
        time.sleep(0.1)
        
        client.send_message("/voice_2_Volume", 0)
        print("✅ Sent: /voice_2_Volume 0")
        time.sleep(0.1)
        
        client.send_message("/active_count", 1)
        print("✅ Sent: /active_count 1")
        
        print("\n2. Testing raw bytes sending...")
        
        # Test sending raw OSC bytes
        raw_osc = b'/test\x00\x00\x00,i\x00\x00\x00\x00\x00\x2A'  # "/test" with integer 42
        client.send_raw(raw_osc)
        print("✅ Sent raw OSC: /test 42")
        
        client.close()
        
        print("\n✅ SimpleUDPClient test completed!")
        print("📋 MaxMSP Check:")
        print("   - In MaxMSP: [udpreceive 1762] → [print]")
        print("   - You should see the OSC messages above")
        print("   - All messages sent to port 1762")
        
        return True
        
    except Exception as e:
        print(f"❌ SimpleUDPClient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_udp_client()
    exit(0 if success else 1)
