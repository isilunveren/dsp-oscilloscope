MAIN_STYLESHEET = """
    QMainWindow, QWidget { background-color: #101317; color: #d8dee9; font-family: "Segoe UI"; font-size: 10px; }
    QFrame#controlPanel { background-color: #171b21; border: 1px solid #292f38; border-radius: 6px; }
    QFrame#section { background-color: #1b2027; border: 1px solid #2b323c; border-radius: 5px; }
    QLabel#sectionTitle { color: #7f8b9b; font-size: 9px; font-weight: bold; }
    QLabel#statusTitle { color: #7f8b9b; font-size: 9px; font-weight: bold; }
    QLabel#statusValue { color: #d8dee9; font-size: 10px; font-weight: bold; }
    QComboBox, QDoubleSpinBox, QSpinBox { background-color: #242a32; color: #e6edf3; border: 1px solid #39414c; border-radius: 4px; padding: 4px 7px; min-height: 18px; }
    QComboBox:hover, QDoubleSpinBox:hover, QSpinBox:hover { border-color: #4f5b69; }
    QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus { border-color: #00aaff; }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox QAbstractItemView { background-color: #20262d; color: #e6edf3; selection-background-color: #245d78; border: 1px solid #39414c; }
    QCheckBox { color: #cbd5e1; spacing: 6px; }
    QCheckBox::indicator { width: 14px; height: 14px; border-radius: 3px; border: 1px solid #4a5563; background-color: #20262d; }
    QCheckBox::indicator:checked { background-color: #00a6d6; border-color: #00c7ff; }
    QCheckBox::indicator:hover { border-color: #00a6d6; }
    QLabel#title { color: #f1f5f9; font-size: 15px; font-weight: bold; }
    QLabel#subtitle { color: #6f7b89; font-size: 9px; }
    QLabel#led { color: #32d583; font-size: 10px; font-weight: bold; }
"""