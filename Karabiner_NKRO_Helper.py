import time
import json
from pathlib import Path
from pythonosc.udp_client import SimpleUDPClient

log_path = Path.home() / ".karabiner" / "log" / "karabiner_grabber_log.txt"
client = SimpleUDPClient("127.0.0.1", 7400)

pressed_keys = set()

with open(log_path, "r") as file:
    file.seek(0, 2)  # move to end of file
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.01)
            continue
        if "key_down" in line or "key_up" in line:
            try:
                event = json.loads(line[line.index('{'):])
                if "event_type" in event and "key_code" in event:
                    key = event["key_code"]
                    if event["event_type"] == "key_down":
                        pressed_keys.add(key)
                    elif event["event_type"] == "key_up":
                        pressed_keys.discard(key)
                    client.send_message("/keys", list(pressed_keys))
            except Exception:
                pass
