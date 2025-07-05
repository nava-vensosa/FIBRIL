from pythonosc.udp_client import SimpleUDPClient
import time

if __name__ == "__main__":
    client = SimpleUDPClient("127.0.0.1", 1762)
    print("Sending OSC messages to 127.0.0.1:1762 every 100ms...")
    try:
        while True:
            client.send_message("/test", 0)
            print("Sent: /test 0")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped sending.")
