#!/usr/bin/env python3
"""
Integration test to demonstrate both features working together:
1. OSC message encoding verification
2. Real-time 48-voice display during system operation
"""

import socket
import struct
import time
import threading
from fibril_main import main as fibril_main

def send_test_rank_message(rank_num, value):
    """Send a rank update message to FIBRIL"""
    try:
        # Build OSC message for rank update
        def encode_string(s):
            data = s.encode('utf-8') + b'\x00'
            while len(data) % 4 != 0:
                data += b'\x00'
            return data

        def encode_int(value):
            return struct.pack('>i', value)

        # Create rank message pattern like MaxMSP would send
        address = f"/R{rank_num}_0100"  # Standard bit pattern
        
        message = encode_string(address)
        message += encode_string(',i')  # type tag for integer
        message += encode_int(value)

        # Send to FIBRIL
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message, ('localhost', 1761))
        sock.close()
        
        print(f"✅ Sent rank update: {address} {value}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def main():
    """Run integration test"""
    print("🧪 FIBRIL INTEGRATION TEST: OSC + 48-VOICE DISPLAY")
    print("=" * 60)
    print()
    
    print("📋 Test Plan:")
    print("1. Start FIBRIL system")
    print("2. Send test rank updates")
    print("3. Observe OSC message encoding and 48-voice display")
    print("4. Verify both features work together")
    print()
    
    print("Starting FIBRIL system in background...")
    
    # Start FIBRIL in a separate thread
    fibril_thread = threading.Thread(target=fibril_main, daemon=True)
    fibril_thread.start()
    
    # Give FIBRIL time to start
    time.sleep(2)
    
    print("✅ FIBRIL system started")
    print("\nSending test messages...")
    print("─" * 40)
    
    # Send a series of test messages
    test_messages = [
        (1, 50),   # Rank 1 = 50
        (3, 75),   # Rank 3 = 75  
        (5, 100),  # Rank 5 = 100
        (2, 25),   # Rank 2 = 25
    ]
    
    for i, (rank_num, value) in enumerate(test_messages, 1):
        print(f"\n📤 Test {i}: Updating Rank {rank_num} to {value}")
        success = send_test_rank_message(rank_num, value)
        
        if success:
            print(f"   Message sent successfully")
            print(f"   Watch for OSC encoding info and 48-voice display...")
            time.sleep(3)  # Give time for processing and display
        else:
            print(f"   ❌ Message failed")
    
    print("\n" + "=" * 60)
    print("🏁 Integration test completed!")
    print()
    print("Expected results:")
    print("✅ OSC messages properly encoded (verified by pythonosc)")
    print("✅ 48-voice display shows real-time status of all voices")
    print("✅ Changed voices highlighted with '→' marker")
    print("✅ Active/inactive status shown with 🔊/🔇 icons")
    print("✅ No manual encoding/decoding needed for MaxMSP")
    print()
    print("Press Ctrl+C to stop FIBRIL system")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping test...")

if __name__ == "__main__":
    main()
