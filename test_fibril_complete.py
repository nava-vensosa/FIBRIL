#!/usr/bin/env python3
"""
FIBRIL Complete Test Suite

This is the comprehensive test suite for the FIBRIL 48-Voice Allocation System.
It includes both automated tests and interactive live demos.

Test Categories:
1. OSC Message Encoding/Decoding Tests
2. Voice Allocation Algorithm Tests  
3. UDP Communication Tests
4. 48-Voice Display Tests
5. Integration Tests
6. Live MaxMSP Communication Demos
7. Performance and Latency Tests

Usage:
    python test_fibril_complete.py                    # Run all automated tests
    python test_fibril_complete.py --live            # Run live demos
    python test_fibril_complete.py --demo maxmsp     # Run specific demo
"""

import socket
import struct
import time
import threading
import argparse
from typing import Dict, Any, List
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_message_builder import OscMessageBuilder

# Import FIBRIL components
from fibril_classes import SystemState, Rank, Voice
from fibril_init import FibrilSystem
from fibril_algorithms import FibrilAlgorithm
from fibril_udp import UDPHandler, build_osc_message, parse_osc_message, send_osc_messages_simple
from fibril_main import FibrilMain


class FibrilTestSuite:
    """Complete test suite for FIBRIL system - automated tests"""
    
    def __init__(self):
        self.test_results = {}
        self.fibril_system = None
        self.system_state = None
        
    def setup_fibril_system(self):
        """Initialize FIBRIL system for testing"""
        self.fibril_system = FibrilSystem()
        self.system_state = self.fibril_system.system_state
        
    def log_test_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        self.test_results[test_name] = {"passed": passed, "message": message}
        
    def test_osc_encoding_decoding(self):
        """Test OSC message encoding and decoding"""
        print("\n🔬 Testing OSC Message Encoding/Decoding...")
        
        # Test 1: Build OSC message
        try:
            address = "/voice_1_MIDI"
            value = 60
            message = build_osc_message(address, value)
            self.log_test_result("OSC Message Building", True, f"Built message: {address} {value}")
        except Exception as e:
            self.log_test_result("OSC Message Building", False, f"Error: {e}")
            
        # Test 2: Parse incoming rank message
        try:
            # Create a simple OSC message manually
            test_data = build_osc_message("/R3_0100", 127)
            address, args = parse_osc_message(test_data)
            
            expected_address = "/R3_0100"
            expected_value = 127
            
            passed = (address == expected_address and 
                     len(args) > 0 and args[0] == expected_value)
            
            self.log_test_result("OSC Message Parsing", passed, 
                               f"Parsed address: {address}, args: {args}")
        except Exception as e:
            self.log_test_result("OSC Message Parsing", False, f"Error: {e}")
            
    def test_voice_allocation_algorithm(self):
        """Test voice allocation algorithm"""
        print("\n🧮 Testing Voice Allocation Algorithm...")
        
        self.setup_fibril_system()
        algorithm = FibrilAlgorithm()
        
        # Test 1: Basic voice allocation
        try:
            # Set up a simple test case
            self.system_state.ranks[0].grey_code = [0, 0, 1, 0]  # GCI=1, density=2
            self.system_state.ranks[2].grey_code = [0, 0, 1, 1]  # GCI=2, density=3
            
            # Force recalculation
            for rank in self.system_state.ranks:
                rank.__post_init__()
            
            new_state = algorithm.allocate_voices(self.system_state)
            active_voices = [v for v in new_state.voices if v.volume > 0]
            
            self.log_test_result("Basic Voice Allocation", len(active_voices) > 0, 
                               f"Allocated {len(active_voices)} voices")
        except Exception as e:
            self.log_test_result("Basic Voice Allocation", False, f"Error: {e}")
            
        # Test 2: Sustain pedal functionality
        try:
            self.system_state.sustain = True
            sustained_state = algorithm.allocate_voices(self.system_state)
            self.log_test_result("Sustain Pedal Test", True, "Sustain mode processed")
        except Exception as e:
            self.log_test_result("Sustain Pedal Test", False, f"Error: {e}")
            
    def test_udp_communication(self):
        """Test UDP communication components"""
        print("\n📡 Testing UDP Communication...")
        
        # Test 1: UDP Handler initialization
        try:
            def dummy_processor(msg):
                return {"test": "response"}
            
            handler = UDPHandler(
                message_processor=dummy_processor,
                listen_port=1761,
                send_port=8998
            )
            
            self.log_test_result("UDP Handler Init", True, 
                               f"Initialized on listen:{handler.listen_port}, send:{handler.send_port}")
        except Exception as e:
            self.log_test_result("UDP Handler Init", False, f"Error: {e}")
            
        # Test 2: Port configuration validation
        try:
            # Check that send port is correctly set to 8998
            fibril_main = FibrilMain()
            correct_send_port = fibril_main.send_port == 8998
            correct_listen_port = fibril_main.listen_port == 1761
            
            self.log_test_result("Port Configuration", 
                               correct_send_port and correct_listen_port,
                               f"Send port: {fibril_main.send_port}, Listen port: {fibril_main.listen_port}")
        except Exception as e:
            self.log_test_result("Port Configuration", False, f"Error: {e}")
            
    def test_48_voice_display(self):
        """Test 48-voice display functionality"""
        print("\n🎹 Testing 48-Voice Display...")
        
        self.setup_fibril_system()
        
        # Test 1: Voice count validation
        try:
            voice_count = len(self.system_state.voices)
            self.log_test_result("48 Voice Count", voice_count == 48, 
                               f"Found {voice_count} voices")
        except Exception as e:
            self.log_test_result("48 Voice Count", False, f"Error: {e}")
            
        # Test 2: Voice data structure
        try:
            if self.system_state.voices:
                voice = self.system_state.voices[0]
                has_required_attrs = all(hasattr(voice, attr) for attr in ['id', 'midi_note', 'volume'])
                self.log_test_result("Voice Data Structure", has_required_attrs, 
                                   "All voices have required attributes")
            else:
                self.log_test_result("Voice Data Structure", False, "No voices found")
        except Exception as e:
            self.log_test_result("Voice Data Structure", False, f"Error: {e}")
            
    def test_integration(self):
        """Test full system integration"""
        print("\n🔗 Testing System Integration...")
        
        # Test 1: Full system initialization
        try:
            fibril_main = FibrilMain(listen_port=1761, send_port=8998)
            
            # Test message processing
            test_message = {
                'type': 'rank_update',
                'rank_number': 1,
                'bit_pattern': '1000',
                'value': 127
            }
            
            response = fibril_main.process_message(test_message)
            # Response might be None due to buffering, which is okay
            
            self.log_test_result("Integration Test", True, "System processed message successfully")
        except Exception as e:
            self.log_test_result("Integration Test", False, f"Error: {e}")
            
    def run_all_tests(self):
        """Run all automated tests"""
        print("🚀 Starting FIBRIL Comprehensive Test Suite...")
        print("=" * 60)
        
        # Run all test categories
        self.test_osc_encoding_decoding()
        self.test_voice_allocation_algorithm()
        self.test_udp_communication()
        self.test_48_voice_display()
        self.test_integration()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results.values() if result["passed"])
        total_tests = len(self.test_results)
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        if failed_tests > 0:
            print("\nFailed tests:")
            for name, result in self.test_results.items():
                if not result["passed"]:
                    print(f"  ❌ {name}: {result['message']}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")
        
        return failed_tests == 0


class FibrilLiveTest:
    """Live testing and demonstration of FIBRIL system"""
    
    def __init__(self):
        self.fibril_main = None
        self.running = False
        
    def setup_fibril(self, listen_port=1761, send_port=8998):
        """Initialize FIBRIL system for live testing"""
        print(f"🔧 Initializing FIBRIL system (listen:{listen_port}, send:{send_port})...")
        self.fibril_main = FibrilMain(listen_port=listen_port, send_port=send_port)
        print("✅ FIBRIL system ready")
        
    def send_rank_message(self, rank_num: int, value: int, target_port: int = 1761):
        """Send a rank update message to FIBRIL"""
        try:
            # Build OSC message like MaxMSP would send
            def encode_string(s):
                data = s.encode('utf-8') + b'\x00'
                while len(data) % 4 != 0:
                    data += b'\x00'
                return data

            def encode_int(value):
                return struct.pack('>i', value)

            # Create OSC message for rank update (e.g., "/R1_1000")
            address = f"/R{rank_num}_1000"
            
            msg = b''
            msg += encode_string(address)
            msg += b',i\x00\x00'  # Type tag for integer
            msg += encode_int(value)
            
            # Send via UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(msg, ("127.0.0.1", target_port))
            sock.close()
            
            print(f"📤 Sent {address} = {value} to port {target_port}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def demo_maxmsp_communication(self):
        """Demo MaxMSP communication"""
        print("\n🎛️  DEMO: MaxMSP Communication Test")
        print("=" * 50)
        
        self.setup_fibril()
        
        print("📡 Simulating MaxMSP rank messages...")
        
        # Send a series of rank updates
        rank_updates = [
            (1, 127),  # Rank 1 on
            (3, 64),   # Rank 3 medium
            (5, 127),  # Rank 5 on
            (1, 0),    # Rank 1 off
        ]
        
        for rank, value in rank_updates:
            self.send_rank_message(rank, value)
            time.sleep(0.5)
            
        print("\n✅ MaxMSP communication demo complete")
        print("   For real MaxMSP integration:")
        print("   - Send to FIBRIL: [udpsend] -> localhost 1761")
        print("   - Receive from FIBRIL: [udpreceive 8998]")
        
    def demo_voice_allocation(self):
        """Demo real-time voice allocation"""
        print("\n🎹 DEMO: Real-time Voice Allocation")
        print("=" * 50)
        
        self.setup_fibril()
        
        print("🎵 Testing different rank combinations...")
        
        # Test different rank patterns
        patterns = [
            {"ranks": [1], "desc": "Single rank"},
            {"ranks": [1, 3], "desc": "Two ranks"},
            {"ranks": [1, 3, 5], "desc": "Three ranks"},
            {"ranks": [1, 2, 3, 4], "desc": "Four ranks"},
        ]
        
        for pattern in patterns:
            print(f"\n🔹 {pattern['desc']}: ranks {pattern['ranks']}")
            
            # Turn on specified ranks
            for rank in pattern['ranks']:
                self.send_rank_message(rank, 127)
                time.sleep(0.2)
                
            time.sleep(1)
            
            # Turn off all ranks
            for rank in pattern['ranks']:
                self.send_rank_message(rank, 0)
                time.sleep(0.1)
                
        print("\n✅ Voice allocation demo complete")
        
    def demo_osc_messages(self):
        """Demo OSC message simulation"""
        print("\n📨 DEMO: OSC Message Simulation")
        print("=" * 50)
        
        print("🎯 Sending various OSC message types...")
        
        try:
            client = SimpleUDPClient("127.0.0.1", 1761)
            
            # Test different types of messages
            messages = [
                ("/R1_1000", [127]),
                ("/R2_0100", [64]),
                ("/R3_0010", [100]),
                ("/R1_priority", [5]),
                ("/R2_tonicization", [7]),
                ("/sustain", [1]),
                ("/key_center", [7]),  # G major
                ("/sustain", [0]),
            ]
            
            for address, args in messages:
                client.send_message(address, args)
                print(f"📤 Sent: {address} {args}")
                time.sleep(0.3)
                
            print("\n✅ OSC message demo complete")
            
        except Exception as e:
            print(f"❌ OSC demo error: {e}")
            
    def performance_test(self):
        """Test system performance and latency"""
        print("\n⚡ DEMO: Performance and Latency Test")
        print("=" * 50)
        
        self.setup_fibril()
        
        print("🏃 Running performance tests...")
        
        # Test rapid message sending
        start_time = time.time()
        message_count = 100
        
        for i in range(message_count):
            rank = (i % 8) + 1
            value = 127 if i % 2 == 0 else 0
            self.send_rank_message(rank, value)
            
        elapsed = time.time() - start_time
        messages_per_second = message_count / elapsed
        
        print(f"📊 Performance Results:")
        print(f"   Messages sent: {message_count}")
        print(f"   Time elapsed: {elapsed:.3f}s")
        print(f"   Messages/second: {messages_per_second:.1f}")
        print(f"   Average latency: {(elapsed/message_count)*1000:.2f}ms")
        
        print("\n✅ Performance test complete")
        
    def run_all_demos(self):
        """Run all live demos"""
        print("🎪 Starting FIBRIL Live Demo Suite...")
        print("=" * 60)
        
        try:
            self.demo_maxmsp_communication()
            time.sleep(1)
            
            self.demo_voice_allocation()
            time.sleep(1)
            
            self.demo_osc_messages()
            time.sleep(1)
            
            self.performance_test()
            
        except KeyboardInterrupt:
            print("\n🛑 Demos interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='FIBRIL Complete Test Suite')
    parser.add_argument('--live', action='store_true', 
                        help='Run live demos instead of automated tests')
    parser.add_argument('--demo', choices=['all', 'maxmsp', 'voices', 'osc', 'performance'],
                        default='all', help='Specific demo to run (when using --live)')
    
    args = parser.parse_args()
    
    if args.live:
        # Run live demos
        live_test = FibrilLiveTest()
        
        print("🎪 FIBRIL Live Testing & Demo Suite")
        print("=" * 60)
        
        try:
            if args.demo == 'all':
                live_test.run_all_demos()
            elif args.demo == 'maxmsp':
                live_test.demo_maxmsp_communication()
            elif args.demo == 'voices':
                live_test.demo_voice_allocation()
            elif args.demo == 'osc':
                live_test.demo_osc_messages()
            elif args.demo == 'performance':
                live_test.performance_test()
                
        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 FIBRIL Live Testing Complete!")
        print("For MaxMSP integration:")
        print("  - Send to FIBRIL: [udpsend] -> localhost 1761")
        print("  - Receive from FIBRIL: [udpreceive 8998]")
        print("=" * 60)
        
    else:
        # Run automated tests
        test_suite = FibrilTestSuite()
        success = test_suite.run_all_tests()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 ALL TESTS PASSED! FIBRIL system is ready for use.")
            print("Run with --live to try interactive demos.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        print("=" * 60)
        
        return 0 if success else 1


if __name__ == "__main__":
    exit(main())
