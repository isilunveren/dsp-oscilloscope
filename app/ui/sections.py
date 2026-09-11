from PySide6.QtWidgets import QFrame, QGridLayout, QLabel


def create_section(title):
    section = QFrame()
    section.setObjectName("section")
    section.setMinimumWidth(135)
    layout = QGridLayout(section)
    layout.setContentsMargins(8, 5, 8, 7)
    layout.setHorizontalSpacing(6)
    layout.setVerticalSpacing(4)
    title_label = QLabel(title)
    title_label.setObjectName("sectionTitle")
    layout.addWidget(title_label, 0, 0, 1, 2)
    return section