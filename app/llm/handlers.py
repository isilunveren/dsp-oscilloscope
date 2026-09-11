import json
import numpy as np


class LLMSettingsController:
    def __init__(self, window):
        self.window = window

    def build_llm_tool_registry(self):
        return {
            "get_current_settings": self.get_current_settings,
            "set_time_per_div": self.set_time_per_div,
            "set_volt_per_div": self.set_volt_per_div,
            "auto_scale": self.auto_scale,
            "set_trigger": self.set_trigger,
            "set_filter": self.set_filter,
            "set_coupling": self.set_coupling,
            "set_denoise": self.set_denoise,
            "set_peak_detection": self.set_peak_detection,
            "set_event_detection": self.set_event_detection,
            "control_recording": self.control_recording,
            "set_channel": self.set_channel,
            "set_run_state": self.set_run_state,
        }

    def get_current_settings(self, args):
        w = self.window
        return json.dumps({
            "time_per_div_s": w.time_combo.currentData(),
            "volt_per_div": w.volt_per_div,
            "trigger": {
                "level": w.trigger_detector.level,
                "edge": w.trigger_detector.edge,
                "mode": w.trigger_mode,
                "position_percent": int(w.trigger_position * 100),
            },
            "filter": {
                "enabled": w.filter_enabled,
                "family": w.filter_family,
                "kind": w.filter_kind,
                "cutoff_khz": w.filter_cutoff / 1000.0,
                "center_khz": w.filter_center / 1000.0,
                "bandwidth_khz": w.filter_bandwidth / 1000.0,
                "order": w.filter_order,
            },
            "coupling": w.coupling,
            "denoise_enabled": w.denoise_enabled,
            "peak_detect_enabled": w.peak_detect_enabled,
            "event_detect_enabled": w.event_detect_enabled,
            "is_recording": w.is_recording,
            "is_running": w.is_running,
            "selected_channel": w.selected_channel + 1,
        })

    def set_time_per_div(self, args):
        w = self.window
        seconds = args["seconds"]
        nearest = min(w.TIME_PER_DIV, key=lambda v: abs(v - seconds))
        idx = w.TIME_PER_DIV.index(nearest)
        w.time_combo.setCurrentIndex(idx)
        return f"time/div set to {w.format_time(nearest)}"

    def set_volt_per_div(self, args):
        w = self.window
        volts = args["volts"]
        nearest = min(w.VOLT_PER_DIV, key=lambda v: abs(v - volts))
        idx = w.VOLT_PER_DIV.index(nearest)
        w.volt_combo.setCurrentIndex(idx)
        return f"volt/div set to {nearest}"

    def auto_scale(self, args):
        w = self.window
        w.auto_scale_clicked()
        return "auto scale applied"

    def set_trigger(self, args):
        w = self.window
        changes = []
        if "level" in args:
            level = int(np.clip(args["level"], 0, 4095))
            w.trigger_level_spin.setValue(level)
            changes.append(f"level={level}")
        if "edge" in args:
            idx = w.trigger_edge_combo.findData(args["edge"])
            if idx >= 0:
                w.trigger_edge_combo.setCurrentIndex(idx)
                changes.append(f"edge={args['edge']}")
        if "mode" in args:
            idx = w.trigger_mode_combo.findData(args["mode"])
            if idx >= 0:
                w.trigger_mode_combo.setCurrentIndex(idx)
                changes.append(f"mode={args['mode']}")
        if "position_percent" in args:
            pos = int(np.clip(args["position_percent"], 0, 100))
            w.trigger_position_spin.setValue(pos)
            changes.append(f"position={pos}%")
        return "trigger updated: " + ", ".join(changes) if changes else "no changes requested"

    def set_filter(self, args):
        w = self.window
        changes = []
        if "enabled" in args:
            idx = w.filter_combo.findData(args["enabled"])
            if idx >= 0:
                w.filter_combo.setCurrentIndex(idx)
                changes.append(f"enabled={args['enabled']}")
        if "family" in args:
            idx = w.filter_family_combo.findData(args["family"])
            if idx >= 0:
                w.filter_family_combo.setCurrentIndex(idx)
                changes.append(f"family={args['family']}")
        if "kind" in args:
            idx = w.filter_kind_combo.findData(args["kind"])
            if idx >= 0:
                w.filter_kind_combo.setCurrentIndex(idx)
                changes.append(f"kind={args['kind']}")
        if "cutoff_khz" in args:
            w.filter_cutoff_spin.setValue(args["cutoff_khz"])
            changes.append(f"cutoff={args['cutoff_khz']}kHz")
        if "center_khz" in args:
            w.filter_center_spin.setValue(args["center_khz"])
            changes.append(f"center={args['center_khz']}kHz")
        if "bandwidth_khz" in args:
            w.filter_bandwidth_spin.setValue(args["bandwidth_khz"])
            changes.append(f"bandwidth={args['bandwidth_khz']}kHz")
        if "order" in args:
            idx = w.filter_order_combo.findData(args["order"])
            if idx >= 0:
                w.filter_order_combo.setCurrentIndex(idx)
                changes.append(f"order={args['order']}")
        if "rp_db" in args:
            w.filter_rp_spin.setValue(args["rp_db"])
            changes.append(f"rp={args['rp_db']}dB")
        if "rs_db" in args:
            w.filter_rs_spin.setValue(args["rs_db"])
            changes.append(f"rs={args['rs_db']}dB")
        return "filter updated: " + ", ".join(changes) if changes else "no changes requested"

    def set_coupling(self, args):
        w = self.window
        idx = w.coupling_combo.findData(args["mode"])
        if idx >= 0:
            w.coupling_combo.setCurrentIndex(idx)
            return f"coupling set to {args['mode']}"
        return "invalid coupling mode"

    def set_denoise(self, args):
        w = self.window
        idx = w.denoise_combo.findData(args["enabled"])
        if idx >= 0:
            w.denoise_combo.setCurrentIndex(idx)
            return f"denoise {'enabled' if args['enabled'] else 'disabled'}"
        return "invalid value"

    def set_peak_detection(self, args):
        w = self.window
        changes = []
        if "enabled" in args:
            idx = w.peak_detect_combo.findData(args["enabled"])
            if idx >= 0:
                w.peak_detect_combo.setCurrentIndex(idx)
                changes.append(f"enabled={args['enabled']}")
        if "min_width_ms" in args:
            w.peak_min_width_spin.setValue(args["min_width_ms"])
            changes.append(f"min_width={args['min_width_ms']}ms")
        if "max_width_ms" in args:
            w.peak_max_width_spin.setValue(args["max_width_ms"])
            changes.append(f"max_width={args['max_width_ms']}ms")
        if "min_height_v" in args:
            w.peak_min_height_spin.setValue(args["min_height_v"])
            changes.append(f"min_height={args['min_height_v']}V")
        return "peak detection updated: " + ", ".join(changes) if changes else "no changes requested"

    def set_event_detection(self, args):
        w = self.window
        changes = []
        if "enabled" in args:
            idx = w.event_detect_combo.findData(args["enabled"])
            if idx >= 0:
                w.event_detect_combo.setCurrentIndex(idx)
                changes.append(f"enabled={args['enabled']}")
        if "cluster_gap_ms" in args:
            w.event_cluster_gap_spin.setValue(args["cluster_gap_ms"])
            changes.append(f"cluster_gap={args['cluster_gap_ms']}ms")
        if "min_duration_ms" in args:
            w.event_min_duration_spin.setValue(args["min_duration_ms"])
            changes.append(f"min_duration={args['min_duration_ms']}ms")
        if "min_height_v" in args:
            w.event_min_height_spin.setValue(args["min_height_v"])
            changes.append(f"min_height={args['min_height_v']}V")
        if "auto_record" in args:
            w.event_auto_record_check.setChecked(args["auto_record"])
            changes.append(f"auto_record={args['auto_record']}")
        return "event detection updated: " + ", ".join(changes) if changes else "no changes requested"

    def control_recording(self, args):
        w = self.window
        if args["action"] == "start":
            if w.is_recording:
                return "already recording"
            w.start_recording(auto=False)
            return "recording started"
        else:
            if not w.is_recording:
                return "not currently recording"
            w.stop_recording()
            return "recording stopped"

    def set_channel(self, args):
        w = self.window
        channel_1based = args["channel"]
        idx = channel_1based - 1
        if 0 <= idx < w.channel_manager.num_channels:
            if w.is_recording:
                return "cannot switch channel while recording is active"
            w.channel_combo.setCurrentIndex(idx)
            return f"channel switched to CH{channel_1based}"
        return f"invalid channel: {channel_1based}"

    def set_run_state(self, args):
        w = self.window
        should_run = args["state"] == "run"
        if should_run != w.is_running:
            w.stop_resume_clicked()
        return f"acquisition {'running' if should_run else 'stopped'}"