import numpy as np
from scipy.signal import find_peaks_cwt, find_peaks


class WaveletPeakDetector:

    MAX_ANALYSIS_SAMPLES = 20_000

    def __init__(self, sample_rate: float, min_width_ms: float = 0.2,
                 max_width_ms: float = 5.0, min_height: float = 0.05):
        self.sample_rate = sample_rate
        self.min_width_ms = min_width_ms
        self.max_width_ms = max_width_ms
        self.min_height = min_height  # interpreted as prominence, same units as samples

    def find_peaks(self, samples: np.ndarray) -> np.ndarray:
        n = len(samples)
        if n < 8:
            return np.array([], dtype=int)

        stride = max(1, n // self.MAX_ANALYSIS_SAMPLES)
        analysis_samples = samples[::stride]

        min_width_samples = max(1.0, self.min_width_ms * 1e-3 * self.sample_rate / stride)
        max_width_samples = max(min_width_samples + 1.0, self.max_width_ms * 1e-3 * self.sample_rate / stride)
        widths = np.linspace(min_width_samples, max_width_samples, num=8)

        try:
            candidate_indices = find_peaks_cwt(analysis_samples, widths)
        except ValueError:
            return np.array([], dtype=int)

        if len(candidate_indices) == 0:
            return np.array([], dtype=int)
        candidate_indices = np.clip(np.asarray(candidate_indices) * stride, 0, n - 1)

        min_width_samples_full = max(1, int(self.min_width_ms * 1e-3 * self.sample_rate))
        search_radius = max(stride, int(max_width_samples * stride / 2), 1)

        return self.match_to_global_peaks(
            samples, candidate_indices, search_radius, min_width_samples_full
        )

    def match_to_global_peaks(self, samples: np.ndarray, candidate_indices: np.ndarray,
                               search_radius: int, min_distance: int) -> np.ndarray:
        global_peak_indices, _properties = find_peaks(
            samples,
            prominence=self.min_height,
            distance=max(1, min_distance),
        )

        if len(global_peak_indices) == 0:
            return np.array([], dtype=int)

        refined = []
        for idx in candidate_indices:
            distances = np.abs(global_peak_indices - int(idx))
            nearest_pos = np.argmin(distances)
            if distances[nearest_pos] <= search_radius:
                refined.append(int(global_peak_indices[nearest_pos]))

        if len(refined) == 0:
            return np.array([], dtype=int)

        return np.unique(np.asarray(refined, dtype=int))