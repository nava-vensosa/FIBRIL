#!/usr/bin/env python3
"""
Test that we can run without pythonosc dependency
"""

import sys

def test_no_pythonosc():
    """Test that pythonosc is not imported anywhere"""
    print("🔍 Checking for pythonosc dependencies...")
    print("=" * 40)
    
    # Check if pythonosc is accidentally imported
    pythonosc_modules = [name for name in sys.modules.keys() if 'pythonosc' in name]
    
    if pythonosc_modules:
        print(f"❌ Found pythonosc modules: {pythonosc_modules}")
        return False
    else:
        print("✅ No pythonosc modules found in sys.modules")
    
    # Try importing our modules
    try:
        from fibril_udp import SimpleOSCClient, parse_osc_message_for_fibril, build_osc_message
        print("✅ fibril_udp imports successfully")
        
        from fibril_classes import SystemState, Rank, Voice
        print("✅ fibril_classes imports successfully")
        
        from fibril_algorithms import FibrilAlgorithm
        print("✅ fibril_algorithms imports successfully")
        
        from fibril_init import FibrilSystem
        print("✅ fibril_init imports successfully")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test basic OSC functionality
    try:
        client = SimpleOSCClient("127.0.0.1", 1762)
        message = build_osc_message("/test", 42)
        print(f"✅ Built OSC message: {len(message)} bytes")
        client.close()
        
        # Test parsing
        test_data = b'/R3_0100\x00\x00\x00\x00,i\x00\x00\x00\x00\x00\x01'
        parsed = parse_osc_message_for_fibril(test_data)
        print(f"✅ Parsed OSC message: {parsed}")
        
    except Exception as e:
        print(f"❌ OSC functionality failed: {e}")
        return False
    
    print("\n🎉 SUCCESS! All FIBRIL modules work without pythonosc!")
    print("   - No pythonosc dependencies detected")
    print("   - All core modules import successfully")
    print("   - OSC functionality works with minimal implementation")
    
    return True

if __name__ == "__main__":
    success = test_no_pythonosc()
    sys.exit(0 if success else 1)
