import os
import wave
import numpy as np


class WavRecorder:

    def __init__(self, filepath: str, sample_rate: int = 48000):
        self.filepath = filepath
        self.sample_rate = sample_rate

        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

        self._wav = wave.open(filepath, "wb")
        self._wav.setnchannels(1)
        self._wav.setsampwidth(2)
        self._wav.setframerate(sample_rate)

        self.samples_written = 0
        self._closed = False

    def write_samples(self, samples: np.ndarray):
        if self._closed or len(samples) == 0:
            return

        signed = samples.astype(np.int32) - 2048
        pcm = np.clip(signed << 4, -32768, 32767).astype("<i2")

        self._wav.writeframes(pcm.tobytes())
        self.samples_written += len(samples)

    def close(self):
        if not self._closed:
            self._wav.close()
            self._closed = True

    @property
    def duration_seconds(self) -> float:
        return self.samples_written / self.sample_rate