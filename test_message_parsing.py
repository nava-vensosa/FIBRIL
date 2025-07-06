#!/usr/bin/env python3
"""
Simple test to verify key center message handling logic without starting the full system.
"""

import logging
from fibril_main import FibrilMain

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_message_parsing():
    """Test key center message parsing logic"""
    
    logger.info("Testing key center message parsing...")
    
    # Create FIBRIL system but don't start it
    fibril = FibrilMain()
    
    # Test different message formats
    test_messages = [
        # OSC format
        {'address': '/keyCenter', 'value': 60},
        {'address': '/keyCenter', 'value': 67},
        {'address': '/keyCenter', 'value': 84},
        
        # Type format  
        {'type': 'key_center', 'value': 55},
        {'type': 'key_center', 'value': 72},
        
        # Legacy format
        {'key_center': 48},
        {'key_center': 77},
        
        # Edge cases
        {'address': '/keyCenter', 'value': 21},  # A0
        {'address': '/keyCenter', 'value': 108}, # C8
    ]
    
    logger.info("Initial key center: {}".format(fibril.system_state.key_center))
    
    for i, message in enumerate(test_messages):
        logger.info(f"\n--- Test {i+1}: {message} ---")
        old_key = fibril.system_state.key_center
        
        # Test the message parsing logic
        state_changed = fibril._update_system_state(message)
        new_key = fibril.system_state.key_center
        
        logger.info(f"State changed: {state_changed}")
        logger.info(f"Key center: {old_key} -> {new_key}")
        
        # Verify the key center was updated correctly
        if 'address' in message and message['address'] == '/keyCenter':
            expected = message['value']
        elif 'type' in message and message['type'] == 'key_center':
            expected = message['value']
        elif 'key_center' in message:
            expected = message['key_center']
        else:
            expected = old_key
            
        if new_key == expected:
            logger.info("✅ Key center updated correctly")
        else:
            logger.error(f"❌ Key center mismatch: expected {expected}, got {new_key}")
    
    logger.info("\n=== Message Parsing Test Complete ===")

if __name__ == "__main__":
    test_message_parsing()
