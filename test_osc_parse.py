#!/usr/bin/env python3
"""Test OSC parsing"""

import struct
import sys
sys.path.append('.')

from fibril_udp import parse_osc_message

# Test with the actual OSC data from MaxMSP
test_data = b'/R3_0100\x00\x00\x00\x00,i\x00\x00\x00\x00\x00\x01'
print(f"Test data length: {len(test_data)}")
print(f"Test data hex: {test_data.hex()}")

result = parse_osc_message(test_data)
print('Parsed OSC message:', result)

# Test with the second message too
test_data2 = b'/R3_0100\x00\x00\x00\x00,i\x00\x00\x00\x00\x00\x00'
result2 = parse_osc_message(test_data2)
print('Parsed OSC message 2:', result2)
