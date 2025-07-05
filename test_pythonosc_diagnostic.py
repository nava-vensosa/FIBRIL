#!/usr/bin/env python3
"""
Diagnostic test for pythonosc SimpleUDPClient sending
"""

import time
import socket
import threading
from pythonosc.udp_client import SimpleUDPClient

def create_udp_listener(port=1762):
    """Create a simple UDP listener to see what we're actually receiving"""
    def listen():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", port))
        sock.settimeout(5.0)  # 5 second timeout
        
        print(f"🎧 Listening on port {port} for incoming messages...")
        
        try:
            while True:
                data, addr = sock.recvfrom(1024)
                print(f"📨 Received {len(data)} bytes from {addr}:")
                print(f"   Raw: {data}")
                print(f"   Hex: {data.hex()}")
                try:
                    # Try to decode as string
                    decoded = data.decode('utf-8', errors='ignore')
                    print(f"   String: {repr(decoded)}")
                except:
                    pass
                print()
        except socket.timeout:
            print("🔇 Listener timeout - no more messages")
        except Exception as e:
            print(f"❌ Listener error: {e}")
        finally:
            sock.close()
    
    return threading.Thread(target=listen, daemon=True)

def test_pythonosc_sending():
    """Test if pythonosc SimpleUDPClient is actually sending"""
    print("🔍 Diagnostic Test: pythonosc SimpleUDPClient Sending")
    print("=" * 55)
    
    # Start listener
    listener = create_udp_listener(1762)
    listener.start()
    time.sleep(0.5)  # Give listener time to start
    
    try:
        print("1. Creating pythonosc SimpleUDPClient...")
        client = SimpleUDPClient("127.0.0.1", 1762)
        print("✅ Client created successfully")
        
        print("\n2. Testing basic send_message...")
        client.send_message("/test", 42)
        print("✅ Sent: /test 42")
        time.sleep(0.2)
        
        print("\n3. Testing voice messages (FIBRIL format)...")
        client.send_message("/voice_1_MIDI", 60)
        print("✅ Sent: /voice_1_MIDI 60")
        time.sleep(0.1)
        
        client.send_message("/voice_1_Volume", 1)
        print("✅ Sent: /voice_1_Volume 1")
        time.sleep(0.1)
        
        client.send_message("/active_count", 5)
        print("✅ Sent: /active_count 5")
        time.sleep(0.1)
        
        print("\n4. Testing different data types...")
        client.send_message("/test_float", 3.14159)
        print("✅ Sent: /test_float 3.14159")
        time.sleep(0.1)
        
        client.send_message("/test_string", "hello_maxmsp")
        print("✅ Sent: /test_string hello_maxmsp")
        time.sleep(0.1)
        
        print("\n5. Waiting for messages to be received...")
        time.sleep(2)
        
        print("\n📋 Test completed!")
        print("If you see 'Received X bytes' messages above,")
        print("then pythonosc SimpleUDPClient is working correctly.")
        print("If not, there might be a network or client issue.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pythonosc_sending()
    exit(0 if success else 1)
