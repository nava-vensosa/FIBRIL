#!/usr/bin/env python3
"""
Test the new density mapping
"""

import sys
import importlib.util

# Import fibril_classes
spec = importlib.util.spec_from_file_location("fibril_classes", "fibril-classes.py")
fibril_classes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fibril_classes)

def test_density_mapping():
    """Test the new density mapping: 1->2, 2->3, 3->4, 4->6"""
    print("Testing New Density Mapping")
    print("=" * 40)
    
    test_cases = [
        ([0, 0, 0, 0], 0, 0),  # 0 ones -> density 0
        ([1, 0, 0, 0], 1, 2),  # 1 one -> density 2
        ([1, 1, 0, 0], 2, 3),  # 2 ones -> density 3
        ([1, 1, 1, 0], 3, 4),  # 3 ones -> density 4
        ([1, 1, 1, 1], 4, 6),  # 4 ones -> density 6
    ]
    
    for grey_code, expected_ones, expected_density in test_cases:
        rank = fibril_classes.Rank(number=1, position=1, grey_code=grey_code)
        ones_count = sum(grey_code)
        
        print(f"Grey code: {grey_code}")
        print(f"  Ones count: {ones_count} (expected: {expected_ones})")
        print(f"  Density: {rank.density} (expected: {expected_density})")
        print(f"  GCI: {rank.gci}")
        print(f"  ✓ Correct" if rank.density == expected_density else "  ✗ ERROR")
        print()

if __name__ == "__main__":
    test_density_mapping()
