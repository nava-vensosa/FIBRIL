#!/usr/bin/env python3

import struct

def encode_string(s):
    data = s.encode('utf-8') + b'\x00'
    while len(data) % 4 != 0:
        data += b'\x00'
    return data

def encode_int(value):
    return struct.pack('>i', value)

# Test the parsing logic manually
address = "/R1_priority"
print(f"Testing address: {address}")

# Check the parsing logic
if address.startswith('/R') and address.endswith('_priority'):
    rank_part = address[1:].split('_')[0]  # Remove '/' prefix, split on '_', take first part
    print(f"rank_part: '{rank_part}'")
    
    if rank_part.startswith('R') and rank_part[1:].isdigit():
        rank_number = int(rank_part[1:])
        print(f"rank_number: {rank_number}")
        print("Parsing should work!")
    else:
        print("Rank part validation failed")
else:
    print("Address format check failed")

# Also test tonicization
address2 = "/R3_tonicization"
print(f"\nTesting address: {address2}")

if address2.startswith('/R') and address2.endswith('_tonicization'):
    rank_part = address2[1:].split('_')[0]
    print(f"rank_part: '{rank_part}'")
    
    if rank_part.startswith('R') and rank_part[1:].isdigit():
        rank_number = int(rank_part[1:])
        print(f"rank_number: {rank_number}")
        print("Parsing should work!")
    else:
        print("Rank part validation failed")
else:
    print("Address format check failed")
