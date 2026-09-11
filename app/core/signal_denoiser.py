import numpy as np
import torch
from df.enhance import enhance, init_df


class SignalDenoiser:
    def __init__(self):
        self.model, self.df_state, _ = init_df()
        self.sample_rate = self.df_state.sr()  # DeepFilterNet3's native rate: 48000 Hz

    def process(self, samples: np.ndarray) -> np.ndarray:
        samples = np.asarray(samples, dtype=np.float64)
        if len(samples) == 0:
            return samples

        mean = np.mean(samples)
        centered = samples - mean
        peak = np.max(np.abs(centered))
        scale = peak if peak > 1e-6 else 1.0
        normalized = (centered / scale).astype(np.float32)

        audio_tensor = torch.from_numpy(normalized).unsqueeze(0) 
        with torch.no_grad():
            enhanced_tensor = enhance(self.model, self.df_state, audio_tensor)

        enhanced = enhanced_tensor.squeeze(0).numpy().astype(np.float64)
        return enhanced * scale + mean