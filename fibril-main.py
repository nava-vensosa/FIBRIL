# Main entry point for FIBRIL system (UDP listener only for now)
import importlib.util
import sys

# Import module with hyphens in filename
spec = importlib.util.spec_from_file_location("fibril_listen_udp", "fibril-listen-udp.py")
fibril_listen_udp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fibril_listen_udp)

if __name__ == "__main__":
    fibril_listen_udp.main()
