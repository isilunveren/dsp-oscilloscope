import serial.tools.list_ports
from device.reader import SerialReader
from app.core.signal_buffer import SignalBuffer

class ChannelManager:
    def __init__(self, num_channels: int = 4, buffer_size: int = 480_000, baudrate: int = 115200):
        self.num_channels = num_channels
        self.baudrate = baudrate

        self.channel_ports = [None] * num_channels
        self.channel_buffers = [SignalBuffer(size=buffer_size) for _ in range(num_channels)]

        self.active_channel = None
        self.active_reader: SerialReader | None = None

        self.on_status_changed = None
        
        self.on_status_changed = None
        self.on_samples = None

    @staticmethod
    def list_available_ports() -> list[str]:
        return [p.device for p in serial.tools.list_ports.comports()]

    def assign_port(self, channel: int, port_name: str | None):
        self.channel_ports[channel] = port_name
        if channel == self.active_channel:
            self.activate(channel)

    def activate(self, channel: int):
        self._disconnect_active()
        self.active_channel = channel

        port_name = self.channel_ports[channel]
        if port_name is None:
            self._notify(channel, connected=False, error=None)
            return

        reader = SerialReader(
            port=port_name,
            baudrate=self.baudrate,
            on_packet=lambda packet, ch=channel: self._on_packet(ch, packet),
            on_error=lambda msg, ch=channel: self._notify(ch, connected=False, error=msg),
        )
        try:
            reader.connect()
            self.active_reader = reader
            self._notify(channel, connected=True, error=None)
        except Exception as exc:
            self.active_reader = None
            self._notify(channel, connected=False, error=str(exc))

    def _disconnect_active(self):
        if self.active_reader is not None:
            self.active_reader.disconnect()
            self.active_reader = None

    def _on_packet(self, channel: int, packet):
        self.channel_buffers[channel].add_samples(packet.samples)

    def _notify(self, channel: int, connected: bool, error: str | None):
        if self.on_status_changed is not None:
            self.on_status_changed(channel, connected, error)

    def get_buffer(self, channel: int) -> SignalBuffer:
        return self.channel_buffers[channel]
    
    def inject_samples(self, channel: int, samples):
        self.channel_buffers[channel].add_samples(samples)
        if self.on_samples is not None:
            self.on_samples(channel, samples)
    
    def _on_packet(self, channel: int, packet):
        self.channel_buffers[channel].add_samples(packet.samples)
        if self.on_samples is not None:
            self.on_samples(channel, packet.samples)

    def shutdown(self):
        self._disconnect_active()