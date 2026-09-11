import numpy as np

class TriggerDetector:

    def __init__( self, level: float = 2048.0, edge: str = "rising", ):
        self.level = level
        self.edge = edge

    def find_trigger(self, samples: np.ndarray) -> int | None:

        samples = np.asarray(samples)

        if len(samples) < 2:
            return None

        if self.edge == "rising":

            indices = np.where( (samples[:-1] < self.level) & (samples[1:] >= self.level) )[0]

        elif self.edge == "falling":

            indices = np.where( (samples[:-1] > self.level) & (samples[1:] <= self.level) )[0]

        else:
            raise ValueError( f"Unsupported trigger edge: {self.edge}" )

        if len(indices) == 0:
            return None

        return int(indices[0] + 1)
