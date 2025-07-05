#!/usr/bin/env python3
"""
Test script to verify grey code bit updates work correctly
"""

import sys
import importlib.util

# Import fibril_init
spec = importlib.util.spec_from_file_location("fibril_init", "fibril-init.py")
fibril_init = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fibril_init)

def test_grey_code_updates():
    """Test grey code bit updates"""
    print("Testing FIBRIL Grey Code Updates")
    print("=" * 40)
    
    system = fibril_init.fibril_system
    
    # Test scenario: /R1_1000 sends 1, /R1_0100 sends 0, /R1_0010 sends 0, /R1_0001 sends 1
    # Expected result: Rank 1 grey code should be [1, 0, 0, 1]
    
    print("\nInitial state:")
    rank1 = system.get_rank(1)
    print(f"Rank 1 grey code: {rank1.grey_code}")
    
    print("\nSimulating MaxMSP messages for Rank 1:")
    
    # /R1_1000 sends 1
    print("Received /R1_1000 with value 1")
    system.update_rank_grey_bit(1, '1000', 1)
    
    # /R1_0100 sends 0  
    print("Received /R1_0100 with value 0")
    system.update_rank_grey_bit(1, '0100', 0)
    
    # /R1_0010 sends 0
    print("Received /R1_0010 with value 0")
    system.update_rank_grey_bit(1, '0010', 0)
    
    # /R1_0001 sends 1
    print("Received /R1_0001 with value 1")
    system.update_rank_grey_bit(1, '0001', 1)
    
    print("\nFinal state:")
    print(f"Rank 1 grey code: {rank1.grey_code}")
    print(f"Expected: [1, 0, 0, 1]")
    print(f"Match: {rank1.grey_code == [1, 0, 0, 1]}")
    
    # Test another rank
    print("\n" + "=" * 40)
    print("Testing Rank 2 with different pattern:")
    
    # Set R2 to [0, 1, 1, 0]
    system.update_rank_grey_bit(2, '1000', 0)  # First bit = 0
    system.update_rank_grey_bit(2, '0100', 1)  # Second bit = 1
    system.update_rank_grey_bit(2, '0010', 1)  # Third bit = 1
    system.update_rank_grey_bit(2, '0001', 0)  # Fourth bit = 0
    
    rank2 = system.get_rank(2)
    print(f"Rank 2 grey code: {rank2.grey_code}")
    print(f"Expected: [0, 1, 1, 0]")
    print(f"Match: {rank2.grey_code == [0, 1, 1, 0]}")
    
    print("\n" + "=" * 40)
    print("Final system state:")
    system.print_system_state()

if __name__ == "__main__":
    test_grey_code_updates()
