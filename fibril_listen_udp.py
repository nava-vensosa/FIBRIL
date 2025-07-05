from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

def print_handler(address, *args):
    print(f"Received: {address} {args}")

def main():
    dispatcher = Dispatcher()
    dispatcher.set_default_handler(print_handler)
    server = BlockingOSCUDPServer(("127.0.0.1", 1761), dispatcher)
    print("Listening for OSC messages on 127.0.0.1:1761...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Listener stopped.")

if __name__ == "__main__":
    main()
