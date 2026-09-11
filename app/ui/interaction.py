import numpy as np
from PySide6.QtCore import Qt, QEvent


class PlotInteractionMixin:

    def eventFilter(self, obj, event):
        if obj is self.waveform_widget.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton and not self.is_running:
                    self.start_measure_drag(event.position())
                    return True
                elif event.button() == Qt.MouseButton.RightButton and self.is_frozen():
                    self.start_pan_drag(event.position())
                    return True
            elif event.type() == QEvent.Type.MouseMove:
                if self._measuring:
                    self.update_measure_drag(event.position())
                    return True
                elif self._panning:
                    self.update_pan_drag(event.position())
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if self._measuring and event.button() == Qt.MouseButton.LeftButton:
                    self.update_measure_drag(event.position())
                    self._measuring = False
                    return True
                elif self._panning and event.button() == Qt.MouseButton.RightButton:
                    self._panning = False
                    return True
            elif event.type() == QEvent.Type.Wheel:
                self.handle_wheel_zoom(event)
                return True
        return super().eventFilter(obj, event)

    def widget_pos_to_data(self, pos):
        scene_pos = self.waveform_widget.mapToScene(pos.toPoint())
        view_box = self.waveform_widget.getPlotItem().vb
        data_pos = view_box.mapSceneToView(scene_pos)
        return data_pos.x()

    def nearest_point(self, t_click):
        if len(self._last_display_time) == 0:
            return None
        idx = int(np.argmin(np.abs(self._last_display_time - t_click)))
        return float(self._last_display_time[idx]), float(self._last_display_voltage[idx])

    def start_measure_drag(self, pos):
        point = self.nearest_point(self.widget_pos_to_data(pos))
        if point is None:
            return
        self._measuring = True
        self.measure_start = point
        self.measure_end = point
        self.measure_marker_a.setData([point[0]], [point[1]])
        self.measure_marker_a.setVisible(True)
        self.measure_marker_b.setVisible(False)
        self.measure_label.hide()

    def update_measure_drag(self, pos):
        point = self.nearest_point(self.widget_pos_to_data(pos))
        if point is None:
            return
        self.measure_end = point
        self.measure_marker_b.setData([point[0]], [point[1]])
        self.measure_marker_b.setVisible(True)
        self.update_measure_label()

    def update_measure_label(self):
        if self.measure_start is None or self.measure_end is None:
            return
        dt = self.measure_end[0] - self.measure_start[0]
        dv = self.measure_end[1] - self.measure_start[1]
        self.measure_label.setText(f"ΔT: {dt:+.3f} ms   ΔV: {dv:+.3f} V")
        self.measure_label.adjustSize()
        self.measure_label.show()

    def is_frozen(self):
        return (not self.is_running) or (self.trigger_mode == "single" and self.single_triggered)

    def start_pan_drag(self, pos):
        self._panning = True
        self._pan_start_x = pos.x()
        self._pan_start_offset = self.pan_offset_samples

    def update_pan_drag(self, pos):
        dx_pixels = pos.x() - self._pan_start_x
        widget_width = self.waveform_widget.width()
        if widget_width <= 0:
            return
        xmin, xmax = self.waveform_widget.getPlotItem().vb.viewRange()[0]
        ms_per_pixel = (xmax - xmin) / widget_width
        ms_delta = dx_pixels * ms_per_pixel
        samples_delta = int(ms_delta / 1000.0 * self.SAMPLE_RATE)
        self.pan_offset_samples = self._pan_start_offset + samples_delta
        self.render_panned()

    def waveform_clicked(self, event):
        view_box = self.waveform_widget.getPlotItem().vb
        scene_pos = event.scenePos()

        if not view_box.sceneBoundingRect().contains(scene_pos):
            return

        data_pos = view_box.mapSceneToView(scene_pos)
        t_click = data_pos.x()

        xmin, xmax = view_box.viewRange()[0]
        if xmax <= xmin:
            return

        fraction = (t_click - xmin) / (xmax - xmin)
        fraction = float(np.clip(fraction, 0.0, 1.0))

        self.trigger_position = fraction

        self.trigger_position_spin.blockSignals(True)
        self.trigger_position_spin.setValue(round(fraction * 100))
        self.trigger_position_spin.blockSignals(False)

        self.update_time_range()

    def handle_wheel_zoom(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            return
        direction = -1 if delta > 0 else 1

        time_index = self.time_combo.currentIndex()
        new_time_index = int(np.clip(time_index + direction, 0, len(self.TIME_PER_DIV) - 1))
        if new_time_index != time_index:
            self.time_combo.setCurrentIndex(new_time_index)

        volt_index = self.volt_combo.currentIndex()
        new_volt_index = int(np.clip(volt_index + direction, 0, len(self.VOLT_PER_DIV) - 1))
        if new_volt_index != volt_index:
            self.volt_combo.setCurrentIndex(new_volt_index)