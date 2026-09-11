import struct
import numpy as np

MAGIC = b"\xAA\x55"

PROTOCOL_VERSION = 0x01
PACKET_TYPE_ADC = 0x01

HEADER_SIZE = 10
CRC_SIZE = 2

MAX_SAMPLES = 512

def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF

    for byte in data:
        crc ^= byte << 8

        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF

    return crc

class ADCPacket:
    def __init__( self, sequence: int, samples: np.ndarray, crc: int, ):
        self.sequence = sequence
        self.samples = samples
        self.crc = crc

    @property
    def sample_count(self) -> int:
        return len(self.samples)


def parse_packet(packet: bytes) -> ADCPacket:

    if len(packet) < HEADER_SIZE + CRC_SIZE:
        raise ValueError("Packet too short")

    if packet[0:2] != MAGIC:
        raise ValueError("Invalid packet magic")

    version = packet[2]
    packet_type = packet[3]

    if version != PROTOCOL_VERSION:
        raise ValueError(f"Unsupported protocol version: {version}")

    if packet_type != PACKET_TYPE_ADC:
        raise ValueError(f"Unsupported packet type: {packet_type}")

    sample_count = struct.unpack_from("<H",packet,4,)[0]

    sequence = struct.unpack_from("<I",packet,6,)[0]

    if sample_count == 0 or sample_count > MAX_SAMPLES:
        raise ValueError(f"Invalid sample count: {sample_count}")

    expected_size = (HEADER_SIZE+ sample_count * 2+ CRC_SIZE)

    if len(packet) != expected_size:
        raise ValueError( f"Invalid packet size: " f"{len(packet)} != {expected_size}" )
    
    payload_end = HEADER_SIZE + sample_count * 2

    payload = packet[ HEADER_SIZE:payload_end ]

    received_crc = struct.unpack_from( "<H", packet, payload_end, )[0]

    crc_data = packet[ 2:payload_end ]

    calculated_crc = crc16_ccitt(
        crc_data
    )

    if received_crc != calculated_crc:
        raise ValueError( f"CRC mismatch: " f"received=0x{received_crc:04X}, " f"calculated=0x{calculated_crc:04X}" )
    
    samples = np.frombuffer( payload, dtype="<u2", ).copy()

    return ADCPacket( sequence=sequence, samples=samples, crc=received_crc, )