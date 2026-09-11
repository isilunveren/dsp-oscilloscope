# import numpy as np
# from scipy.signal import butter, sosfilt

# class SignalFilter:
#     def __init__(self, sample_rate, cutoff=5000, order=4):
#         self.sample_rate = sample_rate
#         self.cutoff = cutoff
#         self.order = order
#         self.update()

#     def update(self):
#         self.sos = butter(self.order, self.cutoff, btype="lowpass", fs=self.sample_rate, output="sos")

#     def process(self, samples):
#         samples = np.asarray(samples, dtype=np.float64)
#         if len(samples) == 0: return samples
#         return sosfilt(self.sos, samples)

import numpy as np
from scipy.signal import iirfilter, sosfilt

# Maps UI-facing family names to scipy's ftype strings
FILTER_FAMILIES = {
    "butterworth": "butter",
    "chebyshev1": "cheby1",
    "chebyshev2": "cheby2",
    "elliptic": "ellip",
}

# Maps UI-facing kind names to scipy's btype strings
FILTER_KINDS = {
    "lowpass": "lowpass",
    "highpass": "highpass",
    "bandpass": "bandpass",
    "bandstop": "bandstop",
}


class SignalFilter:
    def __init__(
        self,
        sample_rate,
        family="butterworth",
        kind="lowpass",
        cutoff=5000, # Hz, used for lowpass / highpass
        center=5000, # Hz, used for bandpass / bandstop
        bandwidth=2000,   # Hz, used for bandpass / bandstop
        order=4,
        rp=1.0,  # dB, passband ripple (cheby1 / elliptic)
        rs=40.0,  # dB, stopband attenuation (cheby2 / elliptic)
    ):
        self.sample_rate = sample_rate
        self.family = family
        self.kind = kind
        self.cutoff = cutoff
        self.center = center
        self.bandwidth = bandwidth
        self.order = order
        self.rp = rp
        self.rs = rs
        self.sos = None
        self.update()

    def _wn(self):
        # Builds the Wn argument for iirfilter, clamped to valid Nyquist range
        nyquist = self.sample_rate / 2.0

        if self.kind in ("lowpass", "highpass"):
            return float(np.clip(self.cutoff, 1.0, nyquist - 1.0))

        # bandpass / bandstop: derive edges from center + bandwidth
        low = self.center - self.bandwidth / 2.0
        high = self.center + self.bandwidth / 2.0
        low = float(np.clip(low, 1.0, nyquist - 2.0))
        high = float(np.clip(high, low + 1.0, nyquist - 1.0))
        return [low, high]

    def update(self):
        ftype = FILTER_FAMILIES[self.family]
        btype = FILTER_KINDS[self.kind]
        wn = self._wn()

        # rp/rs are only accepted by the families that need them
        kwargs = {}
        if ftype in ("cheby1", "ellip"):
            kwargs["rp"] = self.rp
        if ftype in ("cheby2", "ellip"):
            kwargs["rs"] = self.rs

        self.sos = iirfilter(
            self.order,
            wn,
            btype=btype,
            ftype=ftype,
            fs=self.sample_rate,
            output="sos",
            **kwargs,
        )

    def process(self, samples):
        samples = np.asarray(samples, dtype=np.float64)
        if len(samples) == 0 or self.sos is None:
            return samples
        return sosfilt(self.sos, samples)