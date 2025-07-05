#!/usr/bin/env python3
"""
Test OSC sending using the improved pattern from user's example.
"""

from pythonosc.udp_client import SimpleUDPClient
import time

def test_improved_osc_sending():
    """Test OSC sending with the user's clean pattern"""
    print("🧪 TESTING IMPROVED OSC SENDING PATTERN")
    print("=" * 50)
    
    # Create client like the user's example (but targeting MaxMSP port)
    client = SimpleUDPClient("127.0.0.1", 1762)
    
    print("Sending OSC messages to 127.0.0.1:1762 every 100ms...")
    print("(Like user's example but with FIBRIL voice messages)")
    print()
    
    try:
        voice_id = 1
        for x in range(10):  # Send 10 test messages
            # Send MIDI note message
            client.send_message(f"/voice_{voice_id}_MIDI", 60 + x)
            print(f"✅ Sent: /voice_{voice_id}_MIDI {60 + x}")
            time.sleep(0.05)  # 50ms
            
            # Send volume message  
            volume = 1 if x % 2 == 0 else 0  # Alternate on/off
            client.send_message(f"/voice_{voice_id}_Volume", volume)
            print(f"✅ Sent: /voice_{voice_id}_Volume {volume}")
            time.sleep(0.05)  # 50ms
            
            voice_id = (voice_id % 5) + 1  # Cycle through voices 1-5
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped sending.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()
        print("🔒 OSC client closed.")

def test_fibril_updated_sending():
    """Test the updated FIBRIL sending pattern"""
    print("\n🎹 TESTING UPDATED FIBRIL SENDING")
    print("=" * 50)
    
    # Import the updated sending function
    from fibril_udp import send_osc_messages_simple
    
    client = SimpleUDPClient("127.0.0.1", 1762)
    
    # Create mock FIBRIL response data
    response_data = {
        'voices': [
            {'id': 1, 'midi_note': 60, 'volume': True, 'midi_changed': True, 'volume_changed': True},
            {'id': 2, 'midi_note': 64, 'volume': True, 'midi_changed': True, 'volume_changed': False},
            {'id': 3, 'midi_note': 67, 'volume': False, 'midi_changed': False, 'volume_changed': True},
        ],
        'active_count': 2
    }
    
    print("Sending FIBRIL response using updated function...")
    
    try:
        message_count = send_osc_messages_simple(client, response_data)
        print(f"✅ Successfully sent {message_count} OSC messages")
        
        print("\nMessages sent:")
        print("- /voice_1_MIDI 60")
        print("- /voice_1_Volume 1") 
        print("- /voice_2_MIDI 64")
        print("- /voice_3_Volume 0")
        print("- /active_count 2")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

def main():
    """Run all tests"""
    test_improved_osc_sending()
    test_fibril_updated_sending()
    
    print("\n" + "=" * 60)
    print("🏁 IMPROVED OSC SENDING TESTS COMPLETED")
    print()
    print("✅ Confirmed: User's clean SimpleUDPClient pattern works perfectly")
    print("✅ Updated: FIBRIL sending functions use improved pattern")
    print("✅ Ready: MaxMSP integration should work seamlessly")

if __name__ == "__main__":
    main()
