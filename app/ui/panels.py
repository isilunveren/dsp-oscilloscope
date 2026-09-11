from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QCheckBox
)
from app.ui.sections import create_section


def build_channel_panel(window):
    section = create_section("CHANNEL")
    grid = section.layout()

    window.channel_combo = QComboBox()
    for i in range(window.channel_manager.num_channels):
        window.channel_combo.addItem(f"CH{i + 1}", i)
    window.channel_combo.currentIndexChanged.connect(window.channel_changed)

    window.port_combo = QComboBox()
    window.refresh_ports()

    window.refresh_button = QPushButton("Refresh")
    window.refresh_button.clicked.connect(window.refresh_ports)

    window.connect_button = QPushButton("Connect")
    window.connect_button.clicked.connect(window.connect_clicked)

    window.channel_status_label = QLabel("● Disconnected")
    window.channel_status_label.setStyleSheet("color: #ef4444;")

    grid.addWidget(QLabel("Channel"), 1, 0)
    grid.addWidget(window.channel_combo, 1, 1)
    grid.addWidget(QLabel("Port"), 2, 0)
    grid.addWidget(window.port_combo, 2, 1)
    grid.addWidget(window.refresh_button, 3, 0)
    grid.addWidget(window.connect_button, 3, 1)
    grid.addWidget(window.channel_status_label, 4, 0, 1, 2)
    return section


def build_time_panel(window):
    section = create_section("TIME")
    grid = section.layout()
    window.time_combo = QComboBox()
    for value in window.TIME_PER_DIV:
        window.time_combo.addItem(window.format_time(value), value)
    window.time_combo.setCurrentIndex(3)
    window.time_combo.currentIndexChanged.connect(window.time_div_changed)
    grid.addWidget(QLabel("Time/Div"), 1, 0)
    grid.addWidget(window.time_combo, 1, 1)
    return section


def build_vertical_panel(window):
    section = create_section("VERTICAL")
    grid = section.layout()
    window.volt_combo = QComboBox()
    for value in window.VOLT_PER_DIV:
        window.volt_combo.addItem(f"{value:g} V/div", value)
    window.volt_combo.setCurrentIndex(3)
    window.volt_combo.currentIndexChanged.connect(window.volt_div_changed)

    window.offset_spin = QDoubleSpinBox()
    window.offset_spin.setRange(-10.0, 10.0)
    window.offset_spin.setSingleStep(0.1)
    window.offset_spin.setDecimals(2)
    window.offset_spin.setValue(0.0)
    window.offset_spin.setSuffix(" V")
    window.offset_spin.valueChanged.connect(window.offset_changed)

    window.auto_scale_button = QPushButton("Auto Scale")
    window.auto_scale_button.clicked.connect(window.auto_scale_clicked)

    grid.addWidget(QLabel("Scale"), 1, 0)
    grid.addWidget(window.volt_combo, 1, 1)
    grid.addWidget(QLabel("Offset"), 2, 0)
    grid.addWidget(window.offset_spin, 2, 1)
    grid.addWidget(window.auto_scale_button, 3, 0, 1, 2)
    return section


def build_trigger_panel(window):
    section = create_section("TRIGGER")
    grid = section.layout()

    window.trigger_level_spin = QSpinBox()
    window.trigger_level_spin.setRange(0, 4095)
    window.trigger_level_spin.setValue(2048)
    window.trigger_level_spin.valueChanged.connect(window.trigger_level_changed)

    window.trigger_edge_combo = QComboBox()
    window.trigger_edge_combo.addItem("Rising", "rising")
    window.trigger_edge_combo.addItem("Falling", "falling")
    window.trigger_edge_combo.currentIndexChanged.connect(window.trigger_edge_changed)

    window.trigger_position_spin = QSpinBox()
    window.trigger_position_spin.setRange(0, 100)
    window.trigger_position_spin.setValue(50)
    window.trigger_position_spin.setSuffix(" %")
    window.trigger_position_spin.valueChanged.connect(window.trigger_position_spin_changed)

    window.trigger_mode_combo = QComboBox()
    window.trigger_mode_combo.addItem("Auto", "auto")
    window.trigger_mode_combo.addItem("Normal", "normal")
    window.trigger_mode_combo.addItem("Single", "single")
    window.trigger_mode_combo.currentIndexChanged.connect(window.trigger_mode_changed)

    grid.addWidget(QLabel("Level"), 1, 0)
    grid.addWidget(window.trigger_level_spin, 1, 1)
    grid.addWidget(QLabel("Edge"), 2, 0)
    grid.addWidget(window.trigger_edge_combo, 2, 1)
    grid.addWidget(QLabel("Position"), 3, 0)
    grid.addWidget(window.trigger_position_spin, 3, 1)
    grid.addWidget(QLabel("Mode"), 4, 0)
    grid.addWidget(window.trigger_mode_combo, 4, 1)
    return section


def build_filter_panel(window):
    section = create_section("FILTER")
    section.setMinimumWidth(155)
    grid = section.layout()

    window.filter_combo = QComboBox()
    window.filter_combo.addItem("OFF", False)
    window.filter_combo.addItem("ON", True)
    window.filter_combo.setCurrentIndex(1)
    window.filter_combo.currentIndexChanged.connect(window.filter_changed)

    window.filter_family_combo = QComboBox()
    for label, value in [
        ("Butterworth", "butterworth"),
        ("Chebyshev I", "chebyshev1"),
        ("Chebyshev II", "chebyshev2"),
        ("Elliptic", "elliptic"),
    ]:
        window.filter_family_combo.addItem(label, value)
    window.filter_family_combo.currentIndexChanged.connect(window.filter_family_changed)

    window.filter_kind_combo = QComboBox()
    for label, value in [
        ("Lowpass", "lowpass"),
        ("Highpass", "highpass"),
        ("Bandpass", "bandpass"),
        ("Bandstop", "bandstop"),
    ]:
        window.filter_kind_combo.addItem(label, value)
    window.filter_kind_combo.currentIndexChanged.connect(window.filter_kind_changed)

    window.filter_cutoff_spin = QDoubleSpinBox()
    window.filter_cutoff_spin.setRange(0.1, window.SAMPLE_RATE / 2000 - 0.1)
    window.filter_cutoff_spin.setDecimals(2)
    window.filter_cutoff_spin.setSingleStep(0.5)
    window.filter_cutoff_spin.setSuffix(" kHz")
    window.filter_cutoff_spin.setValue(window.filter_cutoff / 1000.0)
    window.filter_cutoff_spin.valueChanged.connect(window.filter_cutoff_spin_changed)

    window.filter_center_spin = QDoubleSpinBox()
    window.filter_center_spin.setRange(0.2, window.SAMPLE_RATE / 2000 - 0.2)
    window.filter_center_spin.setDecimals(2)
    window.filter_center_spin.setSingleStep(0.5)
    window.filter_center_spin.setSuffix(" kHz")
    window.filter_center_spin.setValue(window.filter_center / 1000.0)
    window.filter_center_spin.valueChanged.connect(window.filter_center_changed)

    window.filter_bandwidth_spin = QDoubleSpinBox()
    window.filter_bandwidth_spin.setRange(0.1, window.SAMPLE_RATE / 1000 - 0.4)
    window.filter_bandwidth_spin.setDecimals(2)
    window.filter_bandwidth_spin.setSingleStep(0.5)
    window.filter_bandwidth_spin.setSuffix(" kHz")
    window.filter_bandwidth_spin.setValue(window.filter_bandwidth / 1000.0)
    window.filter_bandwidth_spin.valueChanged.connect(window.filter_bandwidth_changed)

    window.filter_order_combo = QComboBox()
    for value in window.FILTER_ORDERS:
        window.filter_order_combo.addItem(f"Order {value}", value)
    window.filter_order_combo.setCurrentIndex(window.FILTER_ORDERS.index(window.filter_order))
    window.filter_order_combo.currentIndexChanged.connect(window.filter_order_changed)

    window.filter_rp_spin = QDoubleSpinBox()
    window.filter_rp_spin.setRange(0.01, 10.0)
    window.filter_rp_spin.setDecimals(2)
    window.filter_rp_spin.setSingleStep(0.1)
    window.filter_rp_spin.setSuffix(" dB")
    window.filter_rp_spin.setValue(window.filter_rp)
    window.filter_rp_spin.valueChanged.connect(window.filter_rp_changed)

    window.filter_rs_spin = QDoubleSpinBox()
    window.filter_rs_spin.setRange(1.0, 120.0)
    window.filter_rs_spin.setDecimals(1)
    window.filter_rs_spin.setSingleStep(1.0)
    window.filter_rs_spin.setSuffix(" dB")
    window.filter_rs_spin.setValue(window.filter_rs)
    window.filter_rs_spin.valueChanged.connect(window.filter_rs_changed)

    window.coupling_combo = QComboBox()
    window.coupling_combo.addItem("DC", "DC")
    window.coupling_combo.addItem("AC", "AC")
    window.coupling_combo.currentIndexChanged.connect(window.coupling_changed)

    window.cutoff_label = QLabel("Cutoff")
    window.center_label = QLabel("Center")
    window.bandwidth_label = QLabel("Bandwidth")
    window.rp_label = QLabel("Ripple")
    window.rs_label = QLabel("Stopband")

    grid.addWidget(QLabel("Filter"), 1, 0)
    grid.addWidget(window.filter_combo, 1, 1)
    grid.addWidget(QLabel("Type"), 2, 0)
    grid.addWidget(window.filter_family_combo, 2, 1)
    grid.addWidget(QLabel("Kind"), 3, 0)
    grid.addWidget(window.filter_kind_combo, 3, 1)
    grid.addWidget(window.cutoff_label, 4, 0)
    grid.addWidget(window.filter_cutoff_spin, 4, 1)
    grid.addWidget(window.center_label, 5, 0)
    grid.addWidget(window.filter_center_spin, 5, 1)
    grid.addWidget(window.bandwidth_label, 6, 0)
    grid.addWidget(window.filter_bandwidth_spin, 6, 1)
    grid.addWidget(QLabel("Order"), 7, 0)
    grid.addWidget(window.filter_order_combo, 7, 1)
    grid.addWidget(window.rp_label, 8, 0)
    grid.addWidget(window.filter_rp_spin, 8, 1)
    grid.addWidget(window.rs_label, 9, 0)
    grid.addWidget(window.filter_rs_spin, 9, 1)
    grid.addWidget(QLabel("Coupling"), 10, 0)
    grid.addWidget(window.coupling_combo, 10, 1)

    window.denoise_combo = QComboBox()
    window.denoise_combo.addItem("OFF", False)
    window.denoise_combo.addItem("ON", True)
    window.denoise_combo.currentIndexChanged.connect(window.denoise_changed)
    grid.addWidget(QLabel("Denoise (AI)"), 11, 0)
    grid.addWidget(window.denoise_combo, 11, 1)

    return section


def build_display_panel(window):
    section = create_section("DISPLAY")
    grid = section.layout()

    window.waveform_check = QCheckBox("Waveform")
    window.waveform_check.setChecked(True)
    window.waveform_check.toggled.connect(window.waveform_visibility_changed)

    window.fft_check = QCheckBox("FFT")
    window.fft_check.setChecked(True)
    window.fft_check.toggled.connect(window.fft_visibility_changed)

    window.fft_mode_combo = QComboBox()
    window.fft_mode_combo.addItem("Waveform", "waveform")
    window.fft_mode_combo.addItem("Columns", "columns")
    window.fft_mode_combo.currentIndexChanged.connect(window.fft_mode_changed)

    window.waterfall_check = QCheckBox("Waterfall")
    window.waterfall_check.setChecked(True)
    window.waterfall_check.toggled.connect(window.waterfall_visibility_changed)

    grid.addWidget(window.waveform_check, 1, 0, 1, 2)
    grid.addWidget(window.fft_check, 2, 0, 1, 2)
    grid.addWidget(QLabel("FFT View"), 3, 0)
    grid.addWidget(window.fft_mode_combo, 3, 1)
    grid.addWidget(window.waterfall_check, 4, 0, 1, 2)
    return section


def build_peaks_panel(window):
    section = create_section("PEAKS")
    grid = section.layout()

    window.peak_detect_combo = QComboBox()
    window.peak_detect_combo.addItem("OFF", False)
    window.peak_detect_combo.addItem("ON", True)
    window.peak_detect_combo.currentIndexChanged.connect(window.peak_detect_changed)

    window.peak_min_width_spin = QDoubleSpinBox()
    window.peak_min_width_spin.setRange(0.02, 50.0)
    window.peak_min_width_spin.setDecimals(2)
    window.peak_min_width_spin.setSingleStep(0.1)
    window.peak_min_width_spin.setSuffix(" ms")
    window.peak_min_width_spin.setValue(window.peak_detector.min_width_ms)
    window.peak_min_width_spin.valueChanged.connect(window.peak_min_width_changed)

    window.peak_max_width_spin = QDoubleSpinBox()
    window.peak_max_width_spin.setRange(0.05, 100.0)
    window.peak_max_width_spin.setDecimals(2)
    window.peak_max_width_spin.setSingleStep(0.5)
    window.peak_max_width_spin.setSuffix(" ms")
    window.peak_max_width_spin.setValue(window.peak_detector.max_width_ms)
    window.peak_max_width_spin.valueChanged.connect(window.peak_max_width_changed)

    window.peak_min_height_spin = QDoubleSpinBox()
    window.peak_min_height_spin.setRange(0.0, 10.0)
    window.peak_min_height_spin.setDecimals(3)
    window.peak_min_height_spin.setSingleStep(0.01)
    window.peak_min_height_spin.setSuffix(" V")
    window.peak_min_height_spin.setValue(window.peak_detector.min_height)
    window.peak_min_height_spin.valueChanged.connect(window.peak_min_height_changed)

    grid.addWidget(QLabel("Peak Detect"), 1, 0)
    grid.addWidget(window.peak_detect_combo, 1, 1)
    grid.addWidget(QLabel("Min Width"), 2, 0)
    grid.addWidget(window.peak_min_width_spin, 2, 1)
    grid.addWidget(QLabel("Max Width"), 3, 0)
    grid.addWidget(window.peak_max_width_spin, 3, 1)
    grid.addWidget(QLabel("Min Height"), 4, 0)
    grid.addWidget(window.peak_min_height_spin, 4, 1)
    return section


def build_events_panel(window):
    section = create_section("EVENTS")
    section.setMinimumWidth(160)
    grid = section.layout()

    window.event_detect_combo = QComboBox()
    window.event_detect_combo.addItem("OFF", False)
    window.event_detect_combo.addItem("ON", True)
    window.event_detect_combo.currentIndexChanged.connect(window.event_detect_toggled)

    window.event_auto_record_check = QCheckBox("Auto-record")
    window.event_auto_record_check.toggled.connect(window.event_auto_record_toggled)

    window.event_cluster_gap_spin = QSpinBox()
    window.event_cluster_gap_spin.setRange(10, 2000)
    window.event_cluster_gap_spin.setSuffix(" ms")
    window.event_cluster_gap_spin.setValue(int(window.event_detector.cluster_gap_ms))
    window.event_cluster_gap_spin.valueChanged.connect(window.event_cluster_gap_changed)

    window.event_min_duration_spin = QSpinBox()
    window.event_min_duration_spin.setRange(0, 1000)
    window.event_min_duration_spin.setSuffix(" ms")
    window.event_min_duration_spin.setValue(int(window.event_detector.min_event_duration_ms))
    window.event_min_duration_spin.valueChanged.connect(window.event_min_duration_changed)

    window.event_min_height_spin = QDoubleSpinBox()
    window.event_min_height_spin.setRange(0.0, 3.3)
    window.event_min_height_spin.setDecimals(3)
    window.event_min_height_spin.setSingleStep(0.01)
    window.event_min_height_spin.setSuffix(" V")
    window.event_min_height_spin.setValue(
        window.event_detector.peak_detector.min_height * window.ADC_VREF / window.ADC_MAX
    )
    window.event_min_height_spin.valueChanged.connect(window.event_min_height_changed)

    window.event_active_label = QLabel("○ No Event")
    window.event_active_label.setStyleSheet("color: #7f8b9b; font-weight: bold;")

    window.event_log_list = QListWidget()
    window.event_log_list.setMaximumHeight(90)
    window.event_log_list.setStyleSheet(
        "background-color: #0d1013; border: 1px solid #2b323c; font-size: 9px;"
    )

    grid.addWidget(QLabel("Detect"), 1, 0)
    grid.addWidget(window.event_detect_combo, 1, 1)
    grid.addWidget(window.event_auto_record_check, 2, 0, 1, 2)
    grid.addWidget(QLabel("Cluster Gap"), 3, 0)
    grid.addWidget(window.event_cluster_gap_spin, 3, 1)
    grid.addWidget(QLabel("Min Duration"), 4, 0)
    grid.addWidget(window.event_min_duration_spin, 4, 1)
    grid.addWidget(QLabel("Min Height"), 5, 0)
    grid.addWidget(window.event_min_height_spin, 5, 1)
    grid.addWidget(window.event_active_label, 6, 0, 1, 2)
    grid.addWidget(window.event_log_list, 7, 0, 1, 2)
    return section


def build_record_panel(window):
    section = create_section("RECORD")
    grid = section.layout()

    window.record_button = QPushButton("● Record")
    window.record_button.clicked.connect(window.record_button_clicked)

    window.record_status_label = QLabel("Not recording")
    window.record_status_label.setWordWrap(True)
    window.record_status_label.setStyleSheet("color: #7f8b9b;")

    grid.addWidget(window.record_button, 1, 0, 1, 2)
    grid.addWidget(window.record_status_label, 2, 0, 1, 2)
    return section


def build_llm_panel(window):
    panel = QFrame()
    panel.setObjectName("section")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(10, 6, 10, 6)

    window.llm_log = QTextEdit()
    window.llm_log.setReadOnly(True)
    window.llm_log.setMaximumHeight(100)
    window.llm_log.setStyleSheet("background-color: #0d1013; border: 1px solid #2b323c; font-size: 10px;")

    input_row = QHBoxLayout()
    window.llm_input = QLineEdit()
    window.llm_input.setPlaceholderText("Örn: filtreyi 2kHz lowpass yap, time/div'i 1ms'e getir...")
    window.llm_input.returnPressed.connect(window.llm_send_message)
    window.llm_send_button = QPushButton("Gönder")
    window.llm_send_button.clicked.connect(window.llm_send_message)
    input_row.addWidget(window.llm_input)
    input_row.addWidget(window.llm_send_button)

    layout.addWidget(window.llm_log)
    layout.addLayout(input_row)
    return panel

def build_source_panel(window):
    section = create_section("SOURCE")
    grid = section.layout()

    window.source_mode_combo = QComboBox()
    window.source_mode_combo.addItem("Hardware", "hardware")
    window.source_mode_combo.addItem("Function Generator", "generator")
    window.source_mode_combo.currentIndexChanged.connect(window.source_mode_changed)

    window.generator_freq_combo = QComboBox()
    for label, value in [
        ("100 Hz", 100.0),
        ("440 Hz", 440.0),
        ("1 kHz", 1000.0),
        ("2 kHz", 2000.0),
        ("5 kHz", 5000.0),
        ("10 kHz", 10000.0),
        ("12 kHz", 12000.0),
        ("20 kHz", 20000.0),
    ]:
        window.generator_freq_combo.addItem(label, value)
    window.generator_freq_combo.setCurrentIndex(2)
    window.generator_freq_combo.currentIndexChanged.connect(window.generator_frequency_changed)
    window.generator_freq_combo.setVisible(False)

    grid.addWidget(QLabel("Source"), 1, 0)
    grid.addWidget(window.source_mode_combo, 1, 1)
    grid.addWidget(QLabel("Frequency"), 2, 0)
    grid.addWidget(window.generator_freq_combo, 2, 1)
    return section