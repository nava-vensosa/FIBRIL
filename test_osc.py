#!/usr/bin/env python3
"""
Test OSC functionality to debug import issues
"""

print("Testing OSC imports...")

try:
    import pythonosc
    print(f"✅ pythonosc base module imported successfully")
    print(f"   Version info: {pythonosc.__file__}")
except ImportError as e:
    print(f"❌ Failed to import pythonosc: {e}")

try:
    from pythonosc.dispatcher import Dispatcher
    print("✅ Dispatcher imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Dispatcher: {e}")

try:
    from pythonosc.osc_server import BlockingOSCUDPServer
    print("✅ BlockingOSCUDPServer imported successfully")
except ImportError as e:
    print(f"❌ Failed to import BlockingOSCUDPServer: {e}")

try:
    from pythonosc.udp_client import SimpleUDPClient
    print("✅ SimpleUDPClient imported successfully")
except ImportError as e:
    print(f"❌ Failed to import SimpleUDPClient: {e}")

# Test basic functionality
try:
    dispatcher = Dispatcher()
    print("✅ Dispatcher created successfully")
    
    # Test server creation (but don't start it)
    server = BlockingOSCUDPServer(("127.0.0.1", 9999), dispatcher)
    print("✅ OSC Server created successfully")
    
    print("\n🎉 All OSC components working correctly!")
    
except Exception as e:
    print(f"❌ OSC functionality test failed: {e}")

print("\n" + "="*50)
print("If all tests pass, OSC should work in the visualizer.")
print("If any fail, try: pip install --upgrade python-osc")
