import numpy as np
import json
import pyqtgraph as pg
import os
import time
from app.wav_recorder import WavRecorder
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from app.core.trigger_detector import TriggerDetector
from app.core.signal_filter import SignalFilter
from app.core.channel_manager import ChannelManager
from app.core.signal_denoiser import SignalDenoiser
from app.core.peak_detector import WaveletPeakDetector
from app.core.event_detector import EventDetector
from app.llm.tools import SYSTEM_PROMPT
from app.llm.worker import create_nvidia_client, LLMWorker
from app.llm.handlers import LLMSettingsController
from app.ui.styles import MAIN_STYLESHEET
from app.ui.interaction import PlotInteractionMixin
from app.core.function_generator import FunctionGenerator
from app.ui.panels import (
    build_channel_panel, build_time_panel, build_vertical_panel,
    build_trigger_panel, build_filter_panel, build_display_panel,
    build_peaks_panel, build_events_panel, build_record_panel, build_llm_panel,
    build_source_panel,
)
from app.ui.plots import build_waveform_plot, build_fft_waterfall


class OscilloscopeWindow(PlotInteractionMixin, QMainWindow):
    SAMPLE_RATE = 48_000
    BUFFER_SIZE = 480_000
    HORIZONTAL_DIVISIONS = 10
    VERTICAL_DIVISIONS = 8
    ADC_MAX = 4095
    ADC_VREF = 3.3
    TIME_PER_DIV = [0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 1.0]
    VOLT_PER_DIV = [0.05, 0.1, 0.2, 0.5, 1.0]
    FILTER_CUTOFFS = [1000, 2000, 5000, 10000, 15000]
    FILTER_ORDERS = [1, 2, 4, 6, 8]
    WATERFALL_ROWS = 150
    RECORDINGS_DIR = "recordings"

    def __init__(self, channel_manager):
        super().__init__()
        self.channel_manager = channel_manager
        self.function_generator = FunctionGenerator(sample_rate=self.SAMPLE_RATE)
        self.last_generator_push_time = None
        self.source_mode = "hardware"
        self.channel_manager.on_status_changed = self.channel_status_changed
        self.channel_manager.on_samples = self.on_samples_received

        self.is_recording = False
        self.recording_channel = None
        self.wav_recorder = None
        self.selected_channel = 0
        self.is_running = True
        self.measure_start = None
        self.pan_offset_samples = 0
        self._panning = False
        self._pan_start_x = None
        self._pan_start_offset = 0
        self.measure_end = None
        self._measuring = False
        self._last_display_time = np.array([])
        self._last_display_voltage = np.array([])
        self.trigger_detector = TriggerDetector(level=2048, edge="rising")
        self.trigger_position = 0.5
        self.trigger_mode = "auto"
        self.single_triggered = False
        self.volt_per_div = 0.5
        self.voltage_offset = 0.0
        self.coupling = "DC"
        self.filter_enabled = True
        self.filter_family = "butterworth"
        self.filter_kind = "lowpass"
        self.filter_cutoff = 5000
        self.filter_center = 5000
        self.filter_bandwidth = 2000
        self.filter_order = 4
        self.filter_rp = 1.0
        self.filter_rs = 40.0
        self.denoise_enabled = False
        self.signal_denoiser = None
        self.peak_detector = WaveletPeakDetector(
            sample_rate=self.SAMPLE_RATE,
            min_width_ms=0.2,
            max_width_ms=5.0,
            min_height=0.05,
        )
        self.event_detector = EventDetector(
            sample_rate=self.SAMPLE_RATE,
            window_ms=200.0,
            poll_interval_ms=100.0,
            cluster_gap_ms=60.0,
            min_event_duration_ms=20.0,
            peak_min_height=250.0,
        )
        try:
            self.llm_client = create_nvidia_client()
        except RuntimeError as exc:
            self.llm_client = None
            print(f"LLM assistant disabled: {exc}")

        self.llm_model = "nvidia/nemotron-3-super-120b-a12b"
        self.llm_conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.llm_worker = None
        self.llm_controller = LLMSettingsController(self)
        self.llm_tool_registry = self.llm_controller.build_llm_tool_registry()
        self.LLM_MAX_TOOL_ITERATIONS = 5
        self.llm_tool_iteration_count = 0
        self.event_detect_enabled = False
        self.event_auto_record_enabled = False
        self.recording_is_auto = False
        self.active_event_start = None
        self.active_event_region = None
        self.closed_event_regions = []
        self.MAX_CLOSED_EVENT_REGIONS = 5
        self.peak_detect_enabled = False
        self._cached_peak_times = np.array([])
        self._cached_peak_voltages = np.array([])
        self._peak_frame_counter = 0
        self.fft_mode = "waveform"
        self.waterfall_enabled = True
        self.print_fft_to_terminal = True
        self.signal_filter = SignalFilter(
            self.SAMPLE_RATE,
            family=self.filter_family,
            kind=self.filter_kind,
            cutoff=self.filter_cutoff,
            center=self.filter_center,
            bandwidth=self.filter_bandwidth,
            order=self.filter_order,
            rp=self.filter_rp,
            rs=self.filter_rs,
        )
        self.waterfall_data = np.full((24, self.WATERFALL_ROWS), -100.0)

        self.setWindowTitle("STM32 Oscilloscope")
        self.resize(1200, 900)
        self.setMinimumSize(900, 650)
        self.setStyleSheet(MAIN_STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(7)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 0)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title = QLabel("STM32 OSCILLOSCOPE")
        title.setObjectName("title")
        subtitle = QLabel("12-bit ADC  •  48 kHz  •  USB-CDC")
        subtitle.setObjectName("subtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        self.status_led = QLabel("● RUNNING")
        self.status_led.setObjectName("led")
        header_layout.addWidget(self.status_led, 0, Qt.AlignmentFlag.AlignVCenter)
        from PySide6.QtWidgets import QPushButton
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_resume_clicked)
        header_layout.addWidget(self.stop_button, 0, Qt.AlignmentFlag.AlignVCenter)
        main_layout.addLayout(header_layout)

        control_panel = QFrame()
        control_panel.setObjectName("controlPanel")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(8, 7, 8, 7)
        control_layout.setSpacing(6)
        control_layout.addWidget(build_source_panel(self))
        control_layout.addWidget(build_channel_panel(self))
        control_layout.addWidget(build_time_panel(self))
        control_layout.addWidget(build_vertical_panel(self))
        control_layout.addWidget(build_trigger_panel(self))
        control_layout.addWidget(build_filter_panel(self))
        self.update_filter_field_visibility()
        control_layout.addWidget(build_display_panel(self))
        control_layout.addWidget(build_peaks_panel(self))
        control_layout.addWidget(build_events_panel(self))
        control_layout.addStretch()
        control_layout.addWidget(build_record_panel(self))

        main_layout.addWidget(control_panel)
        main_layout.addWidget(control_panel)

        build_waveform_plot(self)
        right_container = build_fft_waterfall(self)

        status_panel = QFrame()
        status_panel.setObjectName("section")
        status_layout = QHBoxLayout(status_panel)
        status_layout.setContentsMargins(10, 5, 10, 5)
        status_layout.setSpacing(18)
        status_layout.addStretch()

        llm_panel = build_llm_panel(self)

        content_grid = QGridLayout()
        content_grid.setHorizontalSpacing(7)
        content_grid.setVerticalSpacing(7)

        content_grid.addWidget(self.waveform_widget, 0, 0)
        content_grid.addWidget(status_panel, 1, 0)
        content_grid.addWidget(llm_panel, 2, 0)
        content_grid.addWidget(right_container, 0, 1, 3, 1)
        content_grid.setColumnStretch(0, 3)
        content_grid.setColumnStretch(1, 2)
        content_grid.setRowStretch(0, 6)
        content_grid.setRowStretch(1, 0)
        content_grid.setRowStretch(2, 2)

        main_layout.addLayout(content_grid, 1)

        self.update_time_range()
        self.update_voltage_range()
        self.update_plot_layout()
        self.update_shared_frequency_axis()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.update_timer_interval()
        self.timer.start(33)
        self.event_timer = QTimer()
        self.event_timer.timeout.connect(self.poll_event_detector)
        self.event_timer.start(int(self.event_detector.poll_interval_ms))
        self.generator_timer = QTimer()
        self.generator_timer.timeout.connect(self.push_generator_samples)

    def adc_to_voltage(self, adc): return np.asarray(adc, dtype=np.float64) * self.ADC_VREF / self.ADC_MAX

    def trigger_level_changed(self, value):
        self.trigger_detector.level = float(value)
        self.trigger_level_line.setPos(self.adc_to_voltage(value))

    def trigger_edge_changed(self): self.trigger_detector.edge = self.trigger_edge_combo.currentData()

    def trigger_position_changed(self):
        self.trigger_position = self.trigger_position_combo.currentData()
        self.update_time_range()

    def trigger_position_spin_changed(self, value):
        self.trigger_position = value / 100.0
        self.update_time_range()

    def trigger_mode_changed(self):
        self.trigger_mode = self.trigger_mode_combo.currentData()
        self.single_triggered = False
        self.pan_offset_samples = 0

    def time_div_changed(self):
        self.update_time_range()
        self.update_timer_interval()
        if self.is_frozen():
            self.render_panned()

    def update_timer_interval(self):
        time_per_div = self.time_combo.currentData()
        total_time = time_per_div * self.HORIZONTAL_DIVISIONS
        interval_ms = int(np.clip(total_time * 1000 / 10, 33, 100))
        self.timer.setInterval(interval_ms)

    def volt_div_changed(self):
        self.volt_per_div = self.volt_combo.currentData()
        self.update_voltage_range()

    def offset_changed(self, value):
        self.voltage_offset = value
        self.update_voltage_range()
        self.trigger_level_changed(self.trigger_level_spin.value())

    def coupling_changed(self): self.coupling = self.coupling_combo.currentData()

    def filter_changed(self):
        self.filter_enabled = self.filter_combo.currentData()
        self.signal_filter.update()

    def filter_family_changed(self):
        self.filter_family = self.filter_family_combo.currentData()
        self.signal_filter.family = self.filter_family
        self.update_filter_field_visibility()
        self.signal_filter.update()

    def filter_kind_changed(self):
        self.filter_kind = self.filter_kind_combo.currentData()
        self.signal_filter.kind = self.filter_kind
        self.update_filter_field_visibility()
        self.signal_filter.update()

    def filter_cutoff_spin_changed(self, value):
        self.filter_cutoff = value * 1000.0
        self.signal_filter.cutoff = self.filter_cutoff
        self.signal_filter.update()

    def filter_center_changed(self, value):
        self.filter_center = value * 1000.0
        self.signal_filter.center = self.filter_center
        self.signal_filter.update()

    def filter_bandwidth_changed(self, value):
        self.filter_bandwidth = value * 1000.0
        self.signal_filter.bandwidth = self.filter_bandwidth
        self.signal_filter.update()

    def filter_order_changed(self):
        self.filter_order = self.filter_order_combo.currentData()
        self.signal_filter.order = self.filter_order
        self.signal_filter.update()

    def filter_rp_changed(self, value):
        self.filter_rp = value
        self.signal_filter.rp = value
        self.signal_filter.update()

    def filter_rs_changed(self, value):
        self.filter_rs = value
        self.signal_filter.rs = value
        self.signal_filter.update()

    def update_filter_field_visibility(self):
        is_lp_hp = self.filter_kind in ("lowpass", "highpass")
        is_bp_bs = self.filter_kind in ("bandpass", "bandstop")
        self.cutoff_label.setVisible(is_lp_hp)
        self.filter_cutoff_spin.setVisible(is_lp_hp)
        self.center_label.setVisible(is_bp_bs)
        self.filter_center_spin.setVisible(is_bp_bs)
        self.bandwidth_label.setVisible(is_bp_bs)
        self.filter_bandwidth_spin.setVisible(is_bp_bs)

        needs_rp = self.filter_family in ("chebyshev1", "elliptic")
        needs_rs = self.filter_family in ("chebyshev2", "elliptic")
        self.rp_label.setVisible(needs_rp)
        self.filter_rp_spin.setVisible(needs_rp)
        self.rs_label.setVisible(needs_rs)
        self.filter_rs_spin.setVisible(needs_rs)

    def fft_mode_changed(self):
        self.fft_mode = self.fft_mode_combo.currentData()
        columns = self.fft_mode == "columns"
        self.fft_curve.setVisible(not columns)
        self.fft_bars.setVisible(columns)

    def waveform_visibility_changed(self, checked):
        self.waveform_widget.setVisible(checked)
        self.update_plot_layout()

    def fft_visibility_changed(self, checked):
        self.fft_widget.setVisible(checked)
        self.update_plot_layout()
        self.update_shared_frequency_axis()

    def waterfall_visibility_changed(self, checked):
        self.waterfall_enabled = checked
        self.waterfall_widget.setVisible(checked)
        self.update_plot_layout()
        self.update_shared_frequency_axis()

    def update_plot_layout(self):
        waveform_visible = self.waveform_check.isChecked()
        fft_visible = self.fft_check.isChecked()
        waterfall_visible = self.waterfall_check.isChecked()
        self.waveform_widget.setVisible(waveform_visible)
        self.fft_widget.setVisible(fft_visible)
        self.waterfall_widget.setVisible(waterfall_visible)

    def update_voltage_range(self):
        total_range = self.volt_per_div * self.VERTICAL_DIVISIONS
        self.waveform_widget.setYRange(
            self.voltage_offset - total_range / 2,
            self.voltage_offset + total_range / 2,
            padding=0,
        )

    def update_time_range(self):
        time_per_div = self.time_combo.currentData()
        total_time_ms = time_per_div * self.HORIZONTAL_DIVISIONS * 1000.0
        start_time_ms = -total_time_ms * self.trigger_position
        end_time_ms = total_time_ms * (1.0 - self.trigger_position)
        self.waveform_widget.setXRange(start_time_ms, end_time_ms, padding=0)
        self.trigger_position_line.setPos(0)

    def calculate_fft(self, samples):
        samples = np.asarray(samples, dtype=np.float64)
        if len(samples) < 2: return np.array([]), np.array([])
        samples -= np.mean(samples)
        window = np.hanning(len(samples))
        coherent_gain = np.sum(window)
        fft = np.fft.rfft(samples * window)
        magnitude = np.abs(fft) / coherent_gain
        if len(magnitude) > 2: magnitude[1:-1] *= 2.0
        magnitude = np.maximum(magnitude / self.ADC_MAX, 1e-12)
        return np.fft.rfftfreq(len(samples), 1 / self.SAMPLE_RATE), 20.0 * np.log10(magnitude)

    def update_fft(self, samples):
        frequency, magnitude_dbfs = self.calculate_fft(samples)
        if len(frequency) == 0: return

        if self.fft_mode == "waveform":
            self.fft_curve.setData(frequency / 1000.0, magnitude_dbfs)
        else:
            columns = np.zeros(24)
            for i in range(24):
                mask = (frequency >= i * 1000) & (frequency < (i + 1) * 1000)
                columns[i] = np.max(magnitude_dbfs[mask]) if np.any(mask) else -100
            self.fft_bars.setOpts(x=np.arange(24) + 0.5, y0=-100, height=columns + 100, width=0.4)
        if self.waterfall_enabled:
            columns = np.zeros(24)
            for i in range(24):
                mask = (frequency >= i * 1000) & (frequency < (i + 1) * 1000)
                columns[i] = np.max(magnitude_dbfs[mask]) if np.any(mask) else -100
            self.waterfall_data[:, :-1] = self.waterfall_data[:, 1:]
            self.waterfall_data[:, -1] = np.round(columns)
            self.waterfall_image.setImage(self.waterfall_data, autoLevels=False, levels=(-100, 0))

    def update_plot(self):
        if self.is_recording and self.wav_recorder is not None:
            self.record_status_label.setText(
                f"Recording to\n{os.path.basename(self.wav_recorder.filepath)}\n"
                f"{self.wav_recorder.duration_seconds:.1f}s"
            )
        if self.trigger_mode == "single" and self.single_triggered: return
        time_per_div = self.time_combo.currentData()
        total_time = time_per_div * self.HORIZONTAL_DIVISIONS
        sample_count = max(2, min(int(total_time * self.SAMPLE_RATE), self.BUFFER_SIZE))
        samples = np.asarray(self.channel_manager.get_buffer(self.selected_channel).get_samples())
        if len(samples) < sample_count: return
        if self.filter_enabled: samples = self.signal_filter.process(samples)
        search_window = min(len(samples), sample_count * 3)
        search_samples = samples[-search_window:]
        search_offset = len(samples) - search_window
        trigger_index_local = self.trigger_detector.find_trigger(search_samples)
        trigger_index = None if trigger_index_local is None else trigger_index_local + search_offset
        if trigger_index is not None:
            pre_trigger_samples = int(sample_count * self.trigger_position)
            start_index = trigger_index - pre_trigger_samples
            end_index = start_index + sample_count
            if start_index >= 0 and end_index <= len(samples):
                display_samples = samples[start_index:end_index]
                trigger_sample = pre_trigger_samples
                if self.trigger_mode == "single":
                    self.single_triggered = True
                    self.pan_offset_samples = 0
            elif self.trigger_mode == "normal": return
            else:
                display_samples = samples[-sample_count:]
                trigger_sample = int(len(display_samples) * self.trigger_position)
        elif self.trigger_mode == "normal": return
        else:
            display_samples = samples[-sample_count:]
            trigger_sample = int(len(display_samples) * self.trigger_position)
        if self.denoise_enabled and self.signal_denoiser is not None:
            display_samples = self.signal_denoiser.process(display_samples)
        self.draw_frame(display_samples, trigger_sample, sample_count, time_per_div)
        
    def source_mode_changed(self):
        self.source_mode = self.source_mode_combo.currentData()
        is_generator = self.source_mode == "generator"
        self.generator_freq_combo.setVisible(is_generator)

        if is_generator:
            self.channel_manager.assign_port(self.selected_channel, None)
            self.connect_button.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self.channel_status_label.setText("● Generating")
            self.channel_status_label.setStyleSheet("color: #22d3ee;")
            self.generator_timer.start(20)
        else:
            self.generator_timer.stop()
            self.connect_button.setEnabled(True)
            self.refresh_button.setEnabled(True)
            self.channel_status_label.setText("● Disconnected")
            self.channel_status_label.setStyleSheet("color: #ef4444;")

    def generator_frequency_changed(self):
        self.function_generator.frequency = self.generator_freq_combo.currentData()

    def push_generator_samples(self):
            now = time.perf_counter()
            if self.last_generator_push_time is None:
                elapsed = self.generator_timer.interval() / 1000.0
            else:
                elapsed = now - self.last_generator_push_time
            self.last_generator_push_time = now

            count = max(1, int(elapsed * self.SAMPLE_RATE))
            samples = self.function_generator.generate_samples(count)
            self.channel_manager.inject_samples(self.selected_channel, samples)

    def refresh_ports(self):
        current_selection = self.port_combo.currentData()
        self.port_combo.clear()
        self.port_combo.addItem("— Select port —", None)
        for port_name in self.channel_manager.list_available_ports():
            self.port_combo.addItem(port_name, port_name)
        if current_selection is not None:
            index = self.port_combo.findData(current_selection)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

    def channel_changed(self):
        if not self.is_running:
            self.stop_resume_clicked()
        self.selected_channel = self.channel_combo.currentData()
        self.single_triggered = False
        self.pan_offset_samples = 0
        assigned_port = self.channel_manager.channel_ports[self.selected_channel]
        index = self.port_combo.findData(assigned_port)
        self.port_combo.setCurrentIndex(index if index >= 0 else 0)

        self.channel_manager.activate(self.selected_channel)

    def connect_clicked(self):
        port_name = self.port_combo.currentData()
        if port_name is None:
            return
        self.channel_manager.assign_port(self.selected_channel, port_name)

    def channel_status_changed(self, channel, connected, error):
        if channel != self.selected_channel:
            return
        if connected:
            self.channel_status_label.setText("● Connected")
            self.channel_status_label.setStyleSheet("color: #32d583;")
        else:
            text = "● Disconnected" if error is None else f"● Error: {error}"
            self.channel_status_label.setText(text)
            self.channel_status_label.setStyleSheet("color: #ef4444;")

    def auto_scale_clicked(self):
        samples = np.asarray(self.channel_manager.get_buffer(self.selected_channel).get_samples())
        if len(samples) == 0:
            return

        if self.filter_enabled:
            samples = self.signal_filter.process(samples)

        voltage = self.adc_to_voltage(samples)
        if self.coupling == "AC":
            voltage = voltage - np.mean(voltage)

        v_min = float(np.min(voltage))
        v_max = float(np.max(voltage))
        span = v_max - v_min

        if span < 1e-6:
            span = 0.05

        total_range = span * 1.1

        self.volt_per_div = total_range / self.VERTICAL_DIVISIONS
        self.voltage_offset = (v_min + v_max) / 2.0

        self.offset_spin.blockSignals(True)
        self.offset_spin.setValue(round(self.voltage_offset, 2))
        self.offset_spin.blockSignals(False)

        self.update_voltage_range()

    def denoise_changed(self):
        self.denoise_enabled = self.denoise_combo.currentData()
        if self.denoise_enabled and self.signal_denoiser is None:
            self.denoise_combo.setEnabled(False)
            QApplication.processEvents()
            self.signal_denoiser = SignalDenoiser()
            self.denoise_combo.setEnabled(True)

    def stop_resume_clicked(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.timer.start(33)
            self.stop_button.setText("Stop")
            self.status_led.setText("● RUNNING")
            self.status_led.setStyleSheet("")
            self.measure_marker_a.setVisible(False)
            self.measure_marker_b.setVisible(False)
            self.measure_label.hide()
            self.measure_start = None
            self.measure_end = None
            self.pan_offset_samples = 0
        else:
            self.timer.stop()
            self.stop_button.setText("Resume")
            self.status_led.setText("● STOPPED")
            self.status_led.setStyleSheet("color: #ef4444;")

    def get_panned_window(self):
        time_per_div = self.time_combo.currentData()
        total_time = time_per_div * self.HORIZONTAL_DIVISIONS
        sample_count = max(2, min(int(total_time * self.SAMPLE_RATE), self.BUFFER_SIZE))
        samples = np.asarray(self.channel_manager.get_buffer(self.selected_channel).get_samples())

        max_offset = max(0, len(samples) - sample_count)
        self.pan_offset_samples = int(np.clip(self.pan_offset_samples, 0, max_offset))

        end_index = len(samples) - self.pan_offset_samples
        start_index = end_index - sample_count
        display_samples = samples[start_index:end_index]

        if self.filter_enabled:
            display_samples = self.signal_filter.process(display_samples)
        if self.denoise_enabled and self.signal_denoiser is not None:
            display_samples = self.signal_denoiser.process(display_samples)

        trigger_sample = int(sample_count * self.trigger_position)
        return display_samples, trigger_sample, sample_count, time_per_div

    def render_panned(self):
        display_samples, trigger_sample, sample_count, time_per_div = self.get_panned_window()
        self.draw_frame(display_samples, trigger_sample, sample_count, time_per_div)

    def draw_frame(self, display_samples, trigger_sample, sample_count, time_per_div):
        if self.waveform_check.isChecked():
            display_voltage = self.adc_to_voltage(display_samples)
            if self.coupling == "AC": display_voltage -= np.mean(display_voltage)
            self._last_display_time = (np.arange(len(display_samples)) - trigger_sample) / self.SAMPLE_RATE * 1000.0
            self._last_display_voltage = display_voltage
            self.last_frame_wall_time = time.time()
            self.waveform_curve.setData(self._last_display_time, display_voltage)
            total_time_ms = time_per_div * self.HORIZONTAL_DIVISIONS * 1000.0
            self.waveform_widget.setXRange(-total_time_ms * self.trigger_position, total_time_ms * (1.0 - self.trigger_position), padding=0)

        if self.peak_detect_enabled:
            if self.is_frozen():
                self._peak_frame_counter += 1
                if self._peak_frame_counter % 4 == 0 or len(self._cached_peak_times) == 0:
                    peak_indices = self.peak_detector.find_peaks(display_voltage)
                    if len(peak_indices) > 0:
                        self._cached_peak_times = self._last_display_time[peak_indices]
                        self._cached_peak_voltages = self._last_display_voltage[peak_indices]
                    else:
                        self._cached_peak_times = np.array([])
                        self._cached_peak_voltages = np.array([])
            else:
                peak_indices = self.peak_detector.find_peaks(display_voltage)
                if len(peak_indices) > 0:
                    self._cached_peak_times = self._last_display_time[peak_indices]
                    self._cached_peak_voltages = self._last_display_voltage[peak_indices]
                else:
                    self._cached_peak_times = np.array([])
                    self._cached_peak_voltages = np.array([])

            self.peak_markers.setData(self._cached_peak_times, self._cached_peak_voltages)
        else:
            self.peak_markers.setData([], [])
            if self.event_detect_enabled:
                self.update_event_regions()

        if self.fft_check.isChecked() or self.waterfall_enabled:
            self.update_fft(display_samples)

    def record_button_clicked(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self, auto: bool = False):
        channel = self.selected_channel
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        prefix = "event" if auto else "capture"
        filename = os.path.join(
            self.RECORDINGS_DIR, f"{prefix}_ch{channel + 1}_{timestamp}.wav"
        )

        self.wav_recorder = WavRecorder(filename, sample_rate=self.SAMPLE_RATE)
        self.recording_channel = channel
        self.is_recording = True
        self._recording_is_auto = auto

        self.record_button.setText("■ Stop Recording")
        self.record_button.setStyleSheet(
            "background-color: #ef4444; color: white; font-weight: bold;"
        )
        self.record_status_label.setText(f"Recording to\n{os.path.basename(filename)}")

        self.channel_combo.setEnabled(False)
        self.connect_button.setEnabled(False)
        self.refresh_button.setEnabled(False)

    def stop_recording(self):
        if self.wav_recorder is not None:
            self.wav_recorder.close()

        self.is_recording = False
        self.wav_recorder = None
        self.recording_channel = None
        self._recording_is_auto = False

        self.record_button.setText("● Record")
        self.record_button.setStyleSheet("")
        self.record_status_label.setText("Not recording")

        self.channel_combo.setEnabled(True)
        self.connect_button.setEnabled(True)
        self.refresh_button.setEnabled(True)

    def on_samples_received(self, channel, samples):
        if self.is_recording and channel == self.recording_channel and self.wav_recorder is not None:
            self.wav_recorder.write_samples(samples)

    def peak_detect_changed(self):
        self.peak_detect_enabled = self.peak_detect_combo.currentData()
        if not self.peak_detect_enabled:
            self.peak_markers.setData([], [])

    def peak_min_width_changed(self, value):
        self.peak_detector.min_width_ms = value

    def peak_max_width_changed(self, value):
        self.peak_detector.max_width_ms = value

    def peak_min_height_changed(self, value):
        self.peak_detector.min_height = value

    def event_detect_toggled(self):
        self.event_detect_enabled = self.event_detect_combo.currentData()
        if not self.event_detect_enabled:
            self.clear_event_regions()
            self.event_active_label.setText("○ No Event")
            self.event_active_label.setStyleSheet("color: #7f8b9b; font-weight: bold;")

    def event_auto_record_toggled(self, checked):
        self.event_auto_record_enabled = checked

    def event_cluster_gap_changed(self, value):
        self.event_detector.cluster_gap_ms = float(value)

    def event_min_duration_changed(self, value):
        self.event_detector.min_event_duration_ms = float(value)

    def event_min_height_changed(self, value):
        self.event_detector.peak_detector.min_height = value * self.ADC_MAX / self.ADC_VREF

    def poll_event_detector(self):
        if not self.event_detect_enabled or not self.is_running:
            return
        if not self.event_detect_enabled:
            return

        channel = self.selected_channel
        buffer = self.channel_manager.get_buffer(channel)

        def get_window(n):
            samples = buffer.get_samples()
            return samples[-n:] if len(samples) >= n else samples

        result = self.event_detector.poll(get_window)

        if result.cluster_ended:
            self.on_cluster_ended(channel, result.closed_events)

        if result.started:
            self.on_event_started(result.started_time)

        if result.is_active:
            self.event_active_label.setText("● EVENT ACTIVE")
            self.event_active_label.setStyleSheet("color: #ef4444; font-weight: bold;")
        elif not result.cluster_ended:
            self.event_active_label.setText("○ No Event")
            self.event_active_label.setStyleSheet("color: #7f8b9b; font-weight: bold;")

    def on_event_started(self, start_time):
        self.active_event_start = start_time
        if self.event_auto_record_enabled and not self.is_recording:
            self.start_recording(auto=True)

    def on_cluster_ended(self, channel, closed_events):
        self.archive_active_region()
        for event in closed_events:
            timestamp_str = time.strftime("%H:%M:%S", time.localtime(event.start_time))
            self.event_log_list.addItem(
                f"{timestamp_str}  CH{channel + 1}  {event.duration * 1000.0:.0f} ms  {event.peak_count} peaks"
            )
        if closed_events:
            self.event_log_list.scrollToBottom()

        self.active_event_start = None

        if self.event_auto_record_enabled and self.is_recording and self.recording_is_auto:
            self.stop_recording()

    def archive_active_region(self):
        if self.active_event_region is not None:
            self.waveform_widget.removeItem(self.active_event_region)
            self.active_event_region = None

    def clear_event_regions(self):
        if self.active_event_region is not None:
            self.waveform_widget.removeItem(self.active_event_region)
            self.active_event_region = None
        self.active_event_start = None

    def update_event_regions(self):
        if len(self._last_display_time) == 0:
            return

        now = self.last_frame_wall_time
        right_edge_ms = self._last_display_time[-1]

        def to_x_ms(wall_time):
            delta_seconds = now - wall_time
            return right_edge_ms - delta_seconds * 1000.0

        if self.active_event_start is not None:
            x0 = to_x_ms(self.active_event_start)
            x1 = right_edge_ms
            if self.active_event_region is None:
                self.active_event_region = pg.LinearRegionItem(
                    values=[x0, x1],
                    movable=False,
                    brush=pg.mkBrush(255, 93, 93, 60),
                    pen=pg.mkPen("#ff5d5d", width=1),
                )
                self.waveform_widget.addItem(self.active_event_region)
            else:
                self.active_event_region.setRegion([x0, x1])

    def llm_send_message(self):
        if self.llm_client is None:
            self.llm_log.append("<i>LLM asistanı devre dışı (NVIDIA_API_KEY ayarlı değil).</i>")
            return

        text = self.llm_input.text().strip()
        if not text:
            return

        self.llm_input.clear()
        self.llm_log.append(f"<b>Sen:</b> {text}")
        self.llm_conversation.append({"role": "user", "content": text})
        self.llm_tool_iteration_count = 0
        self.llm_input.setEnabled(False)
        self.llm_send_button.setEnabled(False)
        self.llm_run_worker()

    def llm_run_worker(self):
        self.llm_worker = LLMWorker(self.llm_client, self.llm_model, list(self.llm_conversation))
        self.llm_worker.result_ready.connect(self.llm_handle_result)
        self.llm_worker.error.connect(self.llm_handle_error)
        self.llm_worker.start()

    def llm_handle_error(self, message):
        self.llm_log.append(f"<i>Hata: {message}</i>")
        self.llm_input.setEnabled(True)
        self.llm_send_button.setEnabled(True)

    def llm_handle_result(self, message):
        self.llm_conversation.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls,
        })

        if message.tool_calls:
            self.llm_tool_iteration_count += 1
            if self.llm_tool_iteration_count > self.LLM_MAX_TOOL_ITERATIONS:
                self.llm_log.append("<i>Çok fazla ardışık işlem, döngü durduruldu.</i>")
                self.llm_input.setEnabled(True)
                self.llm_send_button.setEnabled(True)
                return

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                handler = self.llm_tool_registry.get(tool_name)
                if handler is None:
                    result_text = f"unknown tool: {tool_name}"
                else:
                    try:
                        result_text = handler(args)
                    except Exception as exc:
                        result_text = f"error executing {tool_name}: {exc}"

                self.llm_log.append(f"<i>→ {tool_name}({args}) : {result_text}</i>")
                self.llm_conversation.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_text,
                })

            self.llm_run_worker()
        else:
            self.llm_log.append(f"<b>Asistan:</b> {message.content}")
            self.llm_input.setEnabled(True)
            self.llm_send_button.setEnabled(True)

    def update_shared_frequency_axis(self):
        fft_visible = self.fft_check.isChecked()
        waterfall_visible = self.waterfall_check.isChecked()

        if fft_visible:
            self.waterfall_widget.showAxis("bottom", False)
        elif waterfall_visible:
            self.waterfall_widget.showAxis("bottom", True)

    def closeEvent(self, event):
        if self.llm_worker is not None and self.llm_worker.isRunning():
            self.llm_worker.wait(2000)
        self.event_timer.stop()
        if self.is_recording:
            self.stop_recording()
        self.channel_manager.shutdown()
        super().closeEvent(event)

    @staticmethod
    def format_time(seconds):
        if seconds < 0.001: return f"{seconds * 1_000_000:g} µs/div"
        if seconds < 1: return f"{seconds * 1000:g} ms/div"
        return f"{seconds:g} s/div"