TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_settings",
            "description": "Returns the oscilloscope's current settings (time/div, volt/div, trigger, filter, peak/event detection, recording state). Call this before making relative changes (e.g. 'double the cutoff') or when the user asks about current state.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_time_per_div",
            "description": "Sets the horizontal time/div scale. Snaps to the nearest available value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "description": "Desired time per division, in seconds (e.g. 0.001 for 1ms)."}
                },
                "required": ["seconds"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_volt_per_div",
            "description": "Sets the vertical volt/div scale. Snaps to the nearest available value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "volts": {"type": "number", "description": "Desired volts per division."}
                },
                "required": ["volts"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "auto_scale",
            "description": "Automatically fits the vertical scale and offset to the current signal.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_trigger",
            "description": "Configures the trigger. Any omitted field is left unchanged.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Trigger level as a raw ADC code, 0-4095."},
                    "edge": {"type": "string", "enum": ["rising", "falling"]},
                    "mode": {"type": "string", "enum": ["auto", "normal", "single"]},
                    "position_percent": {"type": "integer", "description": "Pre-trigger position, 0-100."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_filter",
            "description": "Configures the digital IIR filter. Any omitted field is left unchanged.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean"},
                    "family": {"type": "string", "enum": ["butterworth", "chebyshev1", "chebyshev2", "elliptic"]},
                    "kind": {"type": "string", "enum": ["lowpass", "highpass", "bandpass", "bandstop"]},
                    "cutoff_khz": {"type": "number", "description": "Cutoff frequency in kHz, used for lowpass/highpass."},
                    "center_khz": {"type": "number", "description": "Center frequency in kHz, used for bandpass/bandstop."},
                    "bandwidth_khz": {"type": "number", "description": "Bandwidth in kHz, used for bandpass/bandstop."},
                    "order": {"type": "integer", "enum": [1, 2, 4, 6, 8]},
                    "rp_db": {"type": "number", "description": "Passband ripple in dB (Chebyshev I / Elliptic)."},
                    "rs_db": {"type": "number", "description": "Stopband attenuation in dB (Chebyshev II / Elliptic)."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_coupling",
            "description": "Sets AC or DC coupling.",
            "parameters": {
                "type": "object",
                "properties": {"mode": {"type": "string", "enum": ["AC", "DC"]}},
                "required": ["mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_denoise",
            "description": "Enables or disables the AI-based (DeepFilterNet3) noise reduction. Note: first activation loads the model and may take a few seconds.",
            "parameters": {
                "type": "object",
                "properties": {"enabled": {"type": "boolean"}},
                "required": ["enabled"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_peak_detection",
            "description": "Configures wavelet-based peak detection. Any omitted field is left unchanged.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean"},
                    "min_width_ms": {"type": "number"},
                    "max_width_ms": {"type": "number"},
                    "min_height_v": {"type": "number", "description": "Minimum prominence in volts."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_event_detection",
            "description": "Configures event clustering. Any omitted field is left unchanged.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean"},
                    "cluster_gap_ms": {"type": "integer"},
                    "min_duration_ms": {"type": "integer"},
                    "min_height_v": {"type": "number"},
                    "auto_record": {"type": "boolean"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_recording",
            "description": "Starts or stops manual WAV recording.",
            "parameters": {
                "type": "object",
                "properties": {"action": {"type": "string", "enum": ["start", "stop"]}},
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_channel",
            "description": "Selects the active channel.",
            "parameters": {
                "type": "object",
                "properties": {"channel": {"type": "integer", "description": "1-based channel number."}},
                "required": ["channel"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_run_state",
            "description": "Runs or stops (freezes) live acquisition.",
            "parameters": {
                "type": "object",
                "properties": {"state": {"type": "string", "enum": ["run", "stop"]}},
                "required": ["state"],
            },
        },
    },
]

SYSTEM_PROMPT = """You control a real-time digital oscilloscope application via tool calls.
Always use the provided tools to make changes - never claim to have changed a setting without calling
the corresponding tool. If a request is ambiguous or a value is out of reasonable range, ask for
clarification instead of guessing. After making changes, give the user a brief confirmation in Turkish.
Call get_current_settings first if you need to know the current state before making a relative change."""