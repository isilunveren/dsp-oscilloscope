import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


def build_waveform_plot(window):
    window.waveform_widget = pg.PlotWidget()
    window.waveform_widget.setBackground("#080b0e")
    window.waveform_widget.showGrid(x=True, y=True, alpha=0.22)
    window.waveform_widget.setLabel("left", "Voltage", units="V", color="#8b96a5")
    window.waveform_widget.setLabel("bottom", "Time", units="ms", color="#8b96a5")
    window.waveform_widget.getAxis("left").setPen(pg.mkPen("#46505c"))
    window.waveform_widget.getAxis("bottom").setPen(pg.mkPen("#46505c"))
    window.waveform_widget.getAxis("left").setTextPen(pg.mkPen("#7f8b99"))
    window.waveform_widget.getAxis("bottom").setTextPen(pg.mkPen("#7f8b99"))
    window.waveform_curve = window.waveform_widget.plot(pen=pg.mkPen("#39ff88", width=2))
    window.waveform_curve.setDownsampling(auto=True, method="peak")
    window.waveform_curve.setClipToView(True)
    window.trigger_level_line = pg.InfiniteLine(
        pos=window.adc_to_voltage(2048), angle=0,
        pen=pg.mkPen("#ffc857", width=1, style=Qt.PenStyle.DashLine),
    )
    window.waveform_widget.addItem(window.trigger_level_line)
    window.trigger_position_line = pg.InfiniteLine(
        pos=0, angle=90, pen=pg.mkPen("#ffc857", width=1, style=Qt.PenStyle.DashLine)
    )
    window.waveform_widget.addItem(window.trigger_position_line)
    window.waveform_widget.setMouseEnabled(x=False, y=False)
    window.waveform_widget.setMenuEnabled(False)
    window.waveform_widget.viewport().installEventFilter(window)

    window.measure_marker_a = pg.ScatterPlotItem(size=10, brush=pg.mkBrush("#ffcc00"), pen=pg.mkPen("#000000", width=1))
    window.measure_marker_b = pg.ScatterPlotItem(size=10, brush=pg.mkBrush("#ffcc00"), pen=pg.mkPen("#000000", width=1))
    window.waveform_widget.addItem(window.measure_marker_a)
    window.waveform_widget.addItem(window.measure_marker_b)
    window.peak_markers = pg.ScatterPlotItem(size=8, brush=pg.mkBrush("#ff5d5d"), pen=pg.mkPen("#ffffff", width=1))
    window.waveform_widget.addItem(window.peak_markers)
    window.measure_marker_a.setVisible(False)
    window.measure_marker_b.setVisible(False)

    window.measure_label = QLabel(window.waveform_widget)
    window.measure_label.setStyleSheet(
        "background-color: rgba(20, 24, 30, 210); color: #ffcc00; "
        "padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;"
    )
    window.measure_label.move(10, 10)
    window.measure_label.hide()
    window.waveform_widget.scene().sigMouseClicked.connect(window.waveform_clicked)


def build_fft_waterfall(window):
    window.right_graphics = pg.GraphicsLayoutWidget()
    window.right_graphics.setBackground("#080b0e")
    window.right_graphics.ci.layout.setSpacing(0)
    window.right_graphics.ci.layout.setContentsMargins(0, 0, 0, 0)

    window.fft_widget = window.right_graphics.addPlot(row=0, col=0)
    window.fft_widget.showGrid(x=True, y=True, alpha=0.22)
    window.fft_widget.setLabel("left", "Magnitude", units="dBFS", color="#8b96a5")
    window.fft_widget.getAxis("left").setPen(pg.mkPen("#46505c"))
    window.fft_widget.getAxis("left").setTextPen(pg.mkPen("#7f8b99"))
    window.fft_widget.getAxis("left").setWidth(50)
    window.fft_widget.getAxis("bottom").setPen(pg.mkPen("#46505c"))
    window.fft_widget.getAxis("bottom").setTextPen(pg.mkPen("#7f8b99"))
    window.fft_curve = window.fft_widget.plot(pen=pg.mkPen("#22d3ee", width=2))
    window.fft_bars = pg.BarGraphItem(x=np.arange(24) + 0.5, height=np.zeros(24), width=0.4, brush="#22d3ee")
    window.fft_widget.addItem(window.fft_bars)
    window.fft_bars.setVisible(False)
    window.fft_widget.setXRange(0, 24, padding=0)
    window.fft_widget.setYRange(-100, 0, padding=0)
    window.fft_widget.setMouseEnabled(x=False, y=False)
    window.fft_widget.setMenuEnabled(False)

    window.waterfall_widget = window.right_graphics.addPlot(row=1, col=0)
    window.waterfall_widget.showGrid(x=False, y=False)
    window.waterfall_widget.setLabel("left", "Time", units="s", color="#8b96a5")
    window.waterfall_widget.getAxis("left").setPen(pg.mkPen("#46505c"))
    window.waterfall_widget.getAxis("left").setTextPen(pg.mkPen("#7f8b99"))
    window.waterfall_widget.getAxis("left").setWidth(50)
    window.waterfall_widget.getAxis("bottom").setPen(pg.mkPen("#46505c"))
    window.waterfall_widget.getAxis("bottom").setTextPen(pg.mkPen("#7f8b99"))
    window.waterfall_widget.showAxis("bottom", False)
    window.waterfall_image = pg.ImageItem(window.waterfall_data)
    window.waterfall_image.setColorMap(pg.colormap.get("inferno"))
    window.waterfall_image.setRect(0, 0, 24, window.WATERFALL_ROWS / 30.0)
    window.waterfall_widget.addItem(window.waterfall_image)
    window.waterfall_widget.setXRange(0, 24, padding=0)
    window.waterfall_widget.setYRange(0, window.WATERFALL_ROWS / 30, padding=0)
    window.waterfall_widget.setMouseEnabled(x=False, y=False)
    window.waterfall_widget.setMenuEnabled(False)

    window.waterfall_widget.setXLink(window.fft_widget)

    window.right_graphics.ci.layout.setRowStretchFactor(0, 1)
    window.right_graphics.ci.layout.setRowStretchFactor(1, 1)

    window.frequency_caption = QLabel("Frequency (kHz)")
    window.frequency_caption.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    window.frequency_caption.setStyleSheet("color: #7f8b99; font-size: 9px;")

    right_container = QWidget()
    right_container_layout = QVBoxLayout(right_container)
    right_container_layout.setContentsMargins(0, 0, 0, 0)
    right_container_layout.setSpacing(2)
    right_container_layout.addWidget(window.right_graphics, 1)
    right_container_layout.addWidget(window.frequency_caption, 0)
    return right_container