#!/usr/bin/env python3
"""
Test FIBRIL voice response generation
"""

import time
import socket
import threading
import subprocess
from fibril_udp import build_osc_message

def create_maxmsp_listener(port=1762):
    """Create a MaxMSP-like listener to see what FIBRIL is sending"""
    messages_received = []
    
    def listen():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", port))
        sock.settimeout(10.0)  # 10 second timeout
        
        print(f"🎧 MaxMSP Listener on port {port}...")
        
        try:
            while True:
                data, addr = sock.recvfrom(1024)
                messages_received.append(data)
                
                # Try to parse the OSC message
                try:
                    # Simple OSC parsing to show address
                    null_idx = data.find(b'\x00')
                    if null_idx > 0:
                        address = data[:null_idx].decode('utf-8')
                        print(f"📨 Received OSC: {address} ({len(data)} bytes)")
                    else:
                        print(f"📨 Received: {len(data)} bytes (not OSC?)")
                except:
                    print(f"📨 Received: {len(data)} bytes (parse error)")
                    
        except socket.timeout:
            print("🔇 MaxMSP listener timeout")
        except Exception as e:
            print(f"❌ MaxMSP listener error: {e}")
        finally:
            sock.close()
    
    listener_thread = threading.Thread(target=listen, daemon=True)
    return listener_thread, messages_received

def test_fibril_voice_responses():
    """Test if FIBRIL actually sends voice responses"""
    print("🎵 FIBRIL Voice Response Test")
    print("=" * 35)
    
    # Start MaxMSP listener
    listener, messages = create_maxmsp_listener(1762)
    listener.start()
    time.sleep(0.5)
    
    try:
        print("1. Starting FIBRIL system...")
        fibril_process = subprocess.Popen(
            ["python", "fibril_main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give FIBRIL time to start
        time.sleep(2)
        
        if fibril_process.poll() is not None:
            stdout, stderr = fibril_process.communicate()
            print(f"❌ FIBRIL failed to start:")
            print(f"STDERR: {stderr}")
            return False
        
        print("✅ FIBRIL started successfully")
        
        print("\n2. Sending rank update to trigger voice allocation...")
        
        # Send a rank update that should trigger voice allocation
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # This should turn ON rank 3 bit pattern 0100 (middle C area)
        rank_msg = build_osc_message("/R3_0100", 1)
        sock.sendto(rank_msg, ("127.0.0.1", 1761))
        print("✅ Sent: /R3_0100 1 (should trigger voice allocation)")
        
        time.sleep(0.5)
        
        # Send another to change the allocation
        rank_msg2 = build_osc_message("/R3_1000", 1)
        sock.sendto(rank_msg2, ("127.0.0.1", 1761))
        print("✅ Sent: /R3_1000 1 (different allocation)")
        
        time.sleep(0.5)
        
        # Turn off the first one
        rank_msg3 = build_osc_message("/R3_0100", 0)
        sock.sendto(rank_msg3, ("127.0.0.1", 1761))
        print("✅ Sent: /R3_0100 0 (should change voices)")
        
        sock.close()
        
        print("\n3. Waiting for voice responses...")
        time.sleep(3)  # Wait for buffer processing
        
        print(f"\n4. Results: Received {len(messages)} OSC messages")
        
        if len(messages) == 0:
            print("❌ No messages received from FIBRIL!")
            print("   This suggests FIBRIL is not sending voice responses.")
            print("   Possible issues:")
            print("   - Voice allocation not triggered")
            print("   - Buffer timing preventing immediate response")
            print("   - Error in _send_response method")
        else:
            print("✅ FIBRIL is sending messages!")
            print("   Voice allocation system is working.")
        
        # Stop FIBRIL
        print("\n5. Stopping FIBRIL...")
        fibril_process.terminate()
        fibril_process.wait(timeout=5)
        
        return len(messages) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        try:
            fibril_process.terminate()
        except:
            pass
        return False

if __name__ == "__main__":
    success = test_fibril_voice_responses()
    if success:
        print("\n🎉 FIBRIL voice responses are working!")
    else:
        print("\n🔧 FIBRIL voice responses need debugging")
    exit(0 if success else 1)
