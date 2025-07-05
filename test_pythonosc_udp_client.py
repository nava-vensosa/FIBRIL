#!/usr/bin/env python3
"""
Test pythonosc SimpleUDPClient integration
"""

import time
from pythonosc.udp_client import SimpleUDPClient

def test_pythonosc_simple_udp_client():
    """Test pythonosc SimpleUDPClient for MaxMSP communication"""
    print("🔗 Testing pythonosc SimpleUDPClient")
    print("=" * 40)
    
    try:
        # Create pythonosc SimpleUDPClient for sending to MaxMSP on port 8998
        client = SimpleUDPClient("127.0.0.1", 8998)
        
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
        
        # Test different data types
        client.send_message("/test_float", 3.14)
        print("✅ Sent: /test_float 3.14")
        
        client.send_message("/test_string", "hello")
        print("✅ Sent: /test_string hello")
        
        print("\n✅ pythonosc SimpleUDPClient test completed!")
        print("📋 MaxMSP Check:")
        print("   - In MaxMSP: [udpreceive 8998] → [print]")
        print("   - You should see the OSC messages above")
        print("   - All messages sent to port 8998 via pythonosc")
        
        return True
        
    except Exception as e:
        print(f"❌ pythonosc SimpleUDPClient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pythonosc_simple_udp_client()
    exit(0 if success else 1)
