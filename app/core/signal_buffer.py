import numpy as np


class SignalBuffer:

    def __init__(self, size: int = 65536):
        self.size = size
        self.buffer = np.zeros(size, dtype=np.uint16)

    def add_samples(self, samples: np.ndarray):
        samples = np.asarray(samples, dtype=np.uint16)

        if len(samples) >= self.size:
            self.buffer[:] = samples[-self.size:]
            return

        self.buffer[:-len(samples)] = self.buffer[len(samples):]
        self.buffer[-len(samples):] = samples

    def get_samples(self) -> np.ndarray:
        return self.buffer.copy()