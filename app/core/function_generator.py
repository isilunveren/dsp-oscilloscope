import numpy as np


class FunctionGenerator:
    def __init__(self, sample_rate: int, adc_max: int = 4095, adc_vref: float = 3.3):
        self.sample_rate = sample_rate
        self.adc_max = adc_max
        self.adc_vref = adc_vref
        self.frequency = 1000.0
        self.amplitude_v = 1.0
        self._sample_index = 0

    def generate_samples(self, count: int) -> np.ndarray:
        n = np.arange(self._sample_index, self._sample_index + count)
        self._sample_index += count
        t = n / self.sample_rate
        jitter = np.random.normal(0, 0.0, size=count)
        voltage = self.amplitude_v * np.sin(2.0 * np.pi * self.frequency * t + jitter) + self.adc_vref / 2.0
        adc_codes = np.clip(voltage / self.adc_vref * self.adc_max, 0, self.adc_max)
        return adc_codes.astype(np.uint16)