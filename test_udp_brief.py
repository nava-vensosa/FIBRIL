#!/usr/bin/env python3
"""
Test FIBRIL UDP server briefly
"""

import asyncio
import json
import socket
import time
from fibril_main import FibrilMain

async def test_udp_server():
    """Test the UDP server for a few seconds"""
    print("Starting FIBRIL UDP server test...")
    
    # Create FIBRIL system
    fibril = FibrilMain()
    
    # Start server task
    server_task = asyncio.create_task(fibril.run())
    
    # Wait a moment for server to start
    await asyncio.sleep(0.5)
    
    # Send a test message
    test_message = {
        'sustain': False,
        'key_center': 0,
        'ranks': [
            {'number': 1, 'grey_code': [0, 0, 1, 0]},  # GCI=1, density=2
        ]
    }
    
    # Create client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1.0)
    
    try:
        # Send message
        message_data = json.dumps(test_message).encode('utf-8')
        client_socket.sendto(message_data, ("127.0.0.1", 1761))
        print("Sent test message to FIBRIL server")
        
        # Try to receive response
        try:
            response_data, addr = client_socket.recvfrom(4096)
            response = json.loads(response_data.decode('utf-8'))
            print(f"Received response with {response['active_count']} active voices")
        except socket.timeout:
            print("No response received (timeout)")
        
    except Exception as e:
        print(f"Error in client: {e}")
    finally:
        client_socket.close()
    
    # Stop server
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
    
    print("UDP server test completed")

if __name__ == "__main__":
    asyncio.run(test_udp_server())
