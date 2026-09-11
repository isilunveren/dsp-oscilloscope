import serial
import threading
import time

from device.protocol import parse_packet, ADCPacket


class SerialReader:

    MAGIC = b"\xAA\x55"

    HEADER_SIZE = 10
    CRC_SIZE = 2

    def __init__( self, port: str, baudrate: int = 115200, on_packet=None, on_error=None, ):
        self.port = port
        self.baudrate = baudrate

        self.on_packet = on_packet
        self.on_error = on_error

        self.serial = None

        self.running = False
        self.thread = None

        self.buffer = bytearray()

        self.packets_received = 0
        self.packets_valid = 0
        self.packets_invalid = 0
        self.crc_errors = 0

        self.last_sequence = None
        self.sequence_errors = 0


    def connect(self):
        if self.running:
            return

        try:
            self.serial = serial.Serial( port=self.port, baudrate=self.baudrate, timeout=0.1, )
            self.buffer.clear()

            self.running = True

            self.thread = threading.Thread( target=self._read_loop, daemon=True, )

            self.thread.start()

        except serial.SerialException as exc:
            self._report_error( f"Could not open serial port {self.port}: {exc}" )

            self.serial = None
            self.running = False

            raise

    def disconnect(self):

        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None

        if self.serial is not None:

            try:
                if self.serial.is_open:
                    self.serial.close()

            except serial.SerialException:
                pass

            self.serial = None

    @property
    def is_connected(self) -> bool:
        return ( self.serial is not None and self.serial.is_open and self.running )
    
    def _read_loop(self):

        while self.running:

            try:

                if self.serial is None:
                    break

                data = self.serial.read( self.serial.in_waiting or 1 )

                if data:
                    self.buffer.extend(data)
                    self._process_buffer()

            except serial.SerialException as exc:

                self._report_error( f"Serial communication error: {exc}" )

                self.running = False
                break

            except Exception as exc:

                self._report_error( f"Reader error: {exc}" )

                time.sleep(0.01)


    def _process_buffer(self):

        while True:

            magic_index = self.buffer.find(self.MAGIC)

            if magic_index < 0:

                if self.buffer[-1:] == b"\xAA":
                    self.buffer = bytearray(b"\xAA")
                else:
                    self.buffer.clear()

                return

            if magic_index > 0:
                del self.buffer[:magic_index]

            if len(self.buffer) < self.HEADER_SIZE:
                return

            sample_count = ( self.buffer[4] | (self.buffer[5] << 8) )

            if sample_count == 0 or sample_count > 512:

                self.packets_invalid += 1
                del self.buffer[0]
                continue

            packet_size = ( self.HEADER_SIZE + sample_count * 2 + self.CRC_SIZE )

            if len(self.buffer) < packet_size:
                return

            packet_data = bytes( self.buffer[:packet_size] )

            try:

                packet = parse_packet(packet_data)

            except ValueError as exc:

                self.packets_invalid += 1

                error_text = str(exc)

                if "CRC mismatch" in error_text:
                    self.crc_errors += 1

                self._report_error( f"Invalid packet: {error_text}" )

                del self.buffer[0]
                continue

            del self.buffer[:packet_size]

            self.packets_received += 1
            self.packets_valid += 1

            self._check_sequence(packet)

            if self.on_packet is not None:
                self.on_packet(packet)


    def _check_sequence(self, packet: ADCPacket):
        if self.last_sequence is not None:

            expected = ( self.last_sequence + 1 ) & 0xFFFFFFFF

            if packet.sequence != expected:

                self.sequence_errors += 1

                self._report_error( "Sequence error: " f"expected={expected}, " f"received={packet.sequence}" )

        self.last_sequence = packet.sequence

    def _report_error(self, message: str):

        if self.on_error is not None:
            self.on_error(message)

    def get_statistics(self) -> dict:
        return {
            "packets_received": self.packets_received,
            "packets_valid": self.packets_valid,
            "packets_invalid": self.packets_invalid,
            "crc_errors": self.crc_errors,
            "sequence_errors": self.sequence_errors,
        }
