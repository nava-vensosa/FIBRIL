#!/usr/bin/env python3
"""
Send test UDP sustain messages to verify the UDP listener works
"""

import socket
import json
import time

def send_sustain_messages():
    print("Sending UDP Sustain Test Messages")
    print("=" * 40)
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Send sustain ON message
        sustain_on = {'type': 'sustain', 'value': 1}
        message_json = json.dumps(sustain_on).encode('utf-8')
        
        print(f"Sending: {sustain_on}")
        sock.sendto(message_json, ('127.0.0.1', 1761))
        time.sleep(1)
        
        # Send sustain OFF message  
        sustain_off = {'type': 'sustain', 'value': 0}
        message_json = json.dumps(sustain_off).encode('utf-8')
        
        print(f"Sending: {sustain_off}")
        sock.sendto(message_json, ('127.0.0.1', 1761))
        time.sleep(1)
        
        print("Messages sent successfully!")
        print("Check FIBRIL logs for 'Sustain pedal: ON/OFF' messages")
        
    except Exception as e:
        print(f"Error sending messages: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    send_sustain_messages()
