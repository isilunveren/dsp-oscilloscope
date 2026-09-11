import sys

from PySide6.QtWidgets import QApplication

from app.core.channel_manager import ChannelManager
from app.ui.main_window import OscilloscopeWindow

def main():

    app = QApplication(sys.argv)

    channel_manager = ChannelManager(num_channels=4, buffer_size=480_000, baudrate=115200)

    window = OscilloscopeWindow(channel_manager)
    window.show()

    exit_code = app.exec()

    channel_manager.shutdown()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()