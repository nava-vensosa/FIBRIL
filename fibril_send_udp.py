from pythonosc.udp_client import SimpleUDPClient
import time

def main():
    x = 0 
    client = SimpleUDPClient("127.0.0.1", 1762)
    print("Sending OSC messages to 127.0.0.1:1762 every 100ms...")
    try:
        while True:
            client.send_message("/test", x)
            print(f"Sent: /test {x}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped sending.")


if __name__ == "__main__":
    main()
