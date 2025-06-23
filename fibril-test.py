import asyncio
import socket
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Callable, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---

@dataclass
class Config:
    listen_port: int = 1761
    send_port: int = 1762
    host: str = "127.0.0.1"
    buffer_time_ms: int = 18
    input_timeout_ms: int = 50
    num_ranks: int = 8
    rank_size: int = 4
    # The set below is not used anymore, but kept for compatibility
    expected_input_flags: Set[str] = field(default_factory=lambda: set())

# --- SYSTEM STATE ---

@dataclass
class RankState:
    grey_code: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    gci: int = 0
    density: int = 0

@dataclass
class SystemState:
    sustain: int = 0
    global_density: int = 0
    key_center: int = 0
    rank_priority: List[int] = field(default_factory=lambda: list(range(8)))
    ranks: List[RankState] = field(default_factory=lambda: [RankState() for _ in range(8)])

    def copy(self) -> 'SystemState':
        return SystemState(
            sustain=self.sustain,
            global_density=self.global_density,
            key_center=self.key_center,
            rank_priority=self.rank_priority.copy(),
            ranks=[RankState(
                grey_code=rank.grey_code.copy(),
                gci=rank.gci,
                density=rank.density
            ) for rank in self.ranks]
        )

    def get_changes(self, previous_state: 'SystemState') -> Dict[str, Any]:
        changes = {}
        if self.sustain != previous_state.sustain:
            changes['sustain'] = self.sustain
        if self.global_density != previous_state.global_density:
            changes['global_density'] = self.global_density
        if self.key_center != previous_state.key_center:
            changes['key_center'] = self.key_center
        if self.rank_priority != previous_state.rank_priority:
            changes['rank_priority'] = self.rank_priority
        for i, (curr, prev) in enumerate(zip(self.ranks, previous_state.ranks)):
            if curr.grey_code != prev.grey_code or curr.gci != prev.gci or curr.density != prev.density:
                changes[f'rank_{i+1}'] = {
                    "grey_code": curr.grey_code,
                    "gci": curr.gci,
                    "density": curr.density
                }
        return changes

# --- UDP HANDLER ---

class UDPHandler:
    """Handles UDP communication with MaxMSP"""

    def __init__(self, config: Config, message_processor: Callable[[SystemState], None]):
        self.config = config
        self.message_processor = message_processor
        self.socket: Optional[socket.socket] = None
        self.send_socket: Optional[socket.socket] = None
        self.system_state = SystemState()
        self.last_state = self.system_state.copy()

    async def start_listener(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.config.host, self.config.listen_port))
        self.socket.setblocking(False)
        logger.info(f"UDP Listener started on {self.config.host}:{self.config.listen_port}")
        while True:
            try:
                data, addr = await asyncio.get_event_loop().sock_recvfrom(self.socket, 1024)
                if data:
                    await self.process_received_message(data, addr)
            except Exception as e:
                logger.error(f"Error in UDP listener: {e}")
                await asyncio.sleep(0.001)

    async def process_received_message(self, data: bytes, addr: tuple) -> None:
        try:
            address, input_data = self._decode_osc_message(data)
            logger.debug(f"Received message: address='{address}', data='{input_data}'")
            updated = False

            if address == "/sustain":
                self.system_state.sustain = int(input_data)
                updated = True
            elif address == "/globalDensity":
                self.system_state.global_density = int(input_data)
                updated = True
            elif address == "/keyCenter":
                self.system_state.key_center = int(input_data)
                updated = True
            elif address == "/rankPriority":
                # Accepts space-separated or comma-separated ints
                self.system_state.rank_priority = [int(x) for x in input_data.replace(',', ' ').split()]
                updated = True
            elif address in [f"/R{i+1}" for i in range(8)]:
                rank_idx = int(address[2:]) - 1
                grey_code = [int(x) for x in input_data.replace(',', ' ').split()]
                if len(grey_code) != 4:
                    logger.warning(f"Rank {rank_idx+1} grey code must have 4 bits, got: {grey_code}")
                    return
                gci = self._grey_to_int(grey_code)
                density = self._gci_to_density(gci)
                self.system_state.ranks[rank_idx] = RankState(grey_code=grey_code, gci=gci, density=density)
                updated = True
            else:
                logger.debug(f"Ignoring message with address: {address}")

            if updated:
                # Only process if something changed
                await self.message_processor(self.system_state.copy())
        except Exception as e:
            logger.error(f"Error processing message from {addr}: {e}")

    def _grey_to_int(self, grey: List[int]) -> int:
        # Convert 4-bit grey code to int
        b = 0
        for bit in grey:
            b = (b << 1) | bit
        mask = b
        res = 0
        while mask:
            res ^= mask
            mask >>= 1
        return res

    def _gci_to_density(self, gci: int) -> int:
        # Example mapping from README
        mapping = {0: 0, 1: 2, 2: 3, 3: 4, 4: 6}
        return mapping.get(gci, gci)  # fallback: density = gci

    def _decode_osc_message(self, data: bytes) -> Tuple[str, str]:
        try:
            address_end = data.find(b'\x00')
            if address_end == -1:
                raise ValueError("No null terminator found for address")
            address = data[:address_end].decode('utf-8', errors='replace')
            data_offset = (address_end + 4) & ~0x03
            if data_offset >= len(data):
                raise ValueError("Insufficient data for type tags")
            data_tag_end = data.find(b'\x00', data_offset)
            if data_tag_end == -1:
                data_tag_end = len(data)
            input_offset = (data_tag_end + 4) & ~0x03
            if input_offset >= len(data):
                return address, ""
            input_data_bytes = data[input_offset:]
            try:
                input_data = input_data_bytes.decode('utf-8').strip('\x00')
            except UnicodeDecodeError:
                try:
                    input_data = input_data_bytes.decode('latin-1').strip('\x00')
                except UnicodeDecodeError:
                    input_data = input_data_bytes.hex()
                    logger.warning(f"Binary data received, converted to hex: {input_data}")
            return address, input_data
        except Exception as e:
            logger.error(f"Error decoding OSC message: {e}")
            logger.debug(f"Raw data: {data.hex()}")
            return "", ""

    async def send_message(self, address: str, data: int) -> None:
        try:
            if not self.send_socket:
                self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.send_socket.setblocking(False)
            message = self._encode_osc_message(address, data)
            await asyncio.get_event_loop().sock_sendto(
                self.send_socket, message, (self.config.host, self.config.send_port)
            )
            logger.debug(f"Sent message: {address} -> {data}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    def _encode_osc_message(self, address: str, data: int) -> bytes:
        encoded_addr = address.encode('utf-8') + b'\x00'
        padding = (4 - len(encoded_addr) % 4) % 4
        encoded_addr += b'\x00' * padding
        encoded_data = b",i\x00\x00"
        encoded_data += data.to_bytes(4, byteorder='big', signed=True)
        return encoded_addr + encoded_data

    def close(self) -> None:
        if self.socket:
            self.socket.close()
        if self.send_socket:
            self.send_socket.close()

# --- INPUT BUFFER ---

class InputBuffer:
    def __init__(self, buffer_time_ms: int, processor: Callable[[SystemState], None]):
        self.buffer_time_ms = buffer_time_ms
        self.processor = processor
        self.buffer = []
        self.buffer_lock = asyncio.Lock()
        self.buffer_event = asyncio.Event()

    async def add_state(self, state: SystemState) -> None:
        async with self.buffer_lock:
            self.buffer.append({
                'state': state,
                'timestamp': time.time()
            })
            self.buffer_event.set()

    async def process_buffer(self) -> None:
        while True:
            try:
                await self.buffer_event.wait()
                await asyncio.sleep(self.buffer_time_ms / 1000.0)
                async with self.buffer_lock:
                    if self.buffer:
                        latest_state = self.buffer[-1]['state']
                        self.buffer.clear()
                        self.buffer_event.clear()
                        await self.processor(latest_state)
            except Exception as e:
                logger.error(f"Error in buffer processor: {e}")
                await asyncio.sleep(0.001)

# --- DBN ENGINE (ALGORITHM PLACEHOLDER) ---

class DBNEngine:
    def __init__(self, udp_handler: UDPHandler):
        self.udp_handler = udp_handler
        self.current_state = SystemState()
        self.previous_state = SystemState()

    async def process_state(self, state: SystemState) -> None:
        try:
            self.previous_state = self.current_state.copy()
            self.current_state = state.copy()
            self._print_system_state()
            messages = await self._run_dbn_algorithm()
            for address, data in messages:
                await self.udp_handler.send_message(address, data)
        except Exception as e:
            logger.error(f"Error processing state: {e}")

    def _print_system_state(self) -> None:
        print("\n" + "="*60)
        print("NEW SIGNAL RECEIVED FROM MaxMSP")
        print("="*60)
        print(f"Sustain:         {self.current_state.sustain}")
        print(f"Global Density:  {self.current_state.global_density}")
        print(f"Key Center:      {self.current_state.key_center}")
        print(f"Rank Priority:   {self.current_state.rank_priority}")
        print("-"*60)
        print("RANK DATA:")
        for i, rank in enumerate(self.current_state.ranks, 1):
            print(f"  Rank {i}: Grey={rank.grey_code} GCI={rank.gci} Density={rank.density}")
        changes = self.current_state.get_changes(self.previous_state)
        if changes:
            print("-"*60)
            print("CHANGES FROM PREVIOUS STATE:")
            for key, value in changes.items():
                print(f"  {key}: {value}")
        else:
            print("-"*60)
            print("NO CHANGES FROM PREVIOUS STATE")
        print("="*60)
        print()

    async def _run_dbn_algorithm(self) -> List[Tuple[str, int]]:
        # Placeholder: just echo back the state for now
        messages = [
            ("/sustain", self.current_state.sustain),
            ("/globalDensity", self.current_state.global_density),
            ("/keyCenter", self.current_state.key_center)
        ]
        for i, rank in enumerate(self.current_state.ranks, 1):
            messages.append((f"/R{i}_density", rank.density))
            messages.append((f"/R{i}_gci", rank.gci))
        return

        
async def main():
    config = Config()
    controller = NecromoireController(config)
    try:
        await controller.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await controller.shutdown()

if __name__ == "__main__":
    asyncio.run(main())