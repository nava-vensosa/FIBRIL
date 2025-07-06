#!/usr/bin/env python3
"""
Test key center updates in the FIBRIL system.
This test verifies that the system correctly handles key center changes via 
both OSC and legacy message formats, using full MIDI values.
"""

import time
import socket
import json
import logging
from threading import Thread
from fibril_main import FibrilMain

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_udp_message(message, port=8998):
    """Send a UDP message to the FIBRIL system"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(json.dumps(message).encode(), ('localhost', port))
        logger.info(f"Sent: {message}")
    finally:
        sock.close()
    time.sleep(0.1)  # Small delay between messages

def test_key_center():
    """Test key center updates with full MIDI values"""
    
    logger.info("Starting FIBRIL system for key center testing...")
    
    # Create and start FIBRIL system in a separate thread
    fibril = FibrilMain()
    fibril_thread = Thread(target=fibril.run, daemon=True)
    fibril_thread.start()
    
    # Give the system time to start
    time.sleep(2)
    
    # Test 1: OSC format key center updates
    logger.info("\n=== TEST 1: OSC Format Key Center Updates ===")
    
    test_key_centers = [60, 67, 72, 48, 84]  # C4, G4, C5, C3, C6
    
    for key_center in test_key_centers:
        message = {
            'address': '/keyCenter',
            'value': key_center
        }
        logger.info(f"Testing key center: MIDI {key_center}")
        send_udp_message(message)
        time.sleep(0.5)
    
    # Test 2: Legacy format key center updates
    logger.info("\n=== TEST 2: Legacy Format Key Center Updates ===")
    
    for key_center in [55, 77, 36]:  # G3, F5, C2
        message = {
            'key_center': key_center
        }
        logger.info(f"Testing legacy key center: MIDI {key_center}")
        send_udp_message(message)
        time.sleep(0.5)
    
    # Test 3: Type-based key center updates
    logger.info("\n=== TEST 3: Type-based Key Center Updates ===")
    
    for key_center in [64, 69, 74]:  # E4, A4, D5
        message = {
            'type': 'key_center',
            'value': key_center
        }
        logger.info(f"Testing type-based key center: MIDI {key_center}")
        send_udp_message(message)
        time.sleep(0.5)
    
    # Test 4: Edge cases
    logger.info("\n=== TEST 4: Edge Cases ===")
    
    # Very low MIDI note
    send_udp_message({'address': '/keyCenter', 'value': 21})  # A0
    time.sleep(0.3)
    
    # Very high MIDI note
    send_udp_message({'address': '/keyCenter', 'value': 108})  # C8
    time.sleep(0.3)
    
    # Test with rank updates to create some density
    logger.info("\n=== TEST 5: Key Center Effect on Voice Allocation ===")
    
    # Set up some ranks with different patterns
    send_udp_message({
        'type': 'rank_update',
        'rank_number': 1,
        'bit_pattern': '0001',
        'value': 1
    })
    time.sleep(0.1)
    
    send_udp_message({
        'type': 'rank_update', 
        'rank_number': 2,
        'bit_pattern': '0010',
        'value': 1
    })
    time.sleep(0.1)
    
    send_udp_message({
        'type': 'rank_update',
        'rank_number': 3, 
        'bit_pattern': '0100',
        'value': 1
    })
    time.sleep(0.5)
    
    # Set key center to C4 and observe allocation
    logger.info("Setting key center to C4 (60) and observing allocation...")
    send_udp_message({'address': '/keyCenter', 'value': 60})  # C4
    time.sleep(1)
    
    # Change key center to F# and see if allocation updates
    logger.info("Changing key center to F#4 (66) and observing allocation changes...")
    send_udp_message({'address': '/keyCenter', 'value': 66})  # F#4
    time.sleep(1)
    
    # Change to a high key center
    logger.info("Changing key center to C6 (84) and observing allocation changes...")
    send_udp_message({'address': '/keyCenter', 'value': 84})  # C6
    time.sleep(1)
    
    # Change to a low key center  
    logger.info("Changing key center to C2 (36) and observing allocation changes...")
    send_udp_message({'address': '/keyCenter', 'value': 36})  # C2
    time.sleep(1)
    
    # Test 6: Multiple format consistency
    logger.info("\n=== TEST 6: Multiple Format Consistency ===")
    
    test_midi = 65  # F4
    
    # OSC format
    send_udp_message({'address': '/keyCenter', 'value': test_midi})
    time.sleep(0.2)
    
    # Legacy format  
    send_udp_message({'key_center': test_midi})
    time.sleep(0.2)
    
    # Type format
    send_udp_message({'type': 'key_center', 'value': test_midi})
    time.sleep(0.2)
    
    logger.info("\n=== Key Center Testing Complete ===")
    logger.info("All key center values should be stored as full MIDI values, not modulo 12.")
    logger.info("Check the FIBRIL system logs to verify correct handling of all updates.")
    
    # Give some time for final processing
    time.sleep(2)

if __name__ == "__main__":
    try:
        test_key_center()
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        raise
