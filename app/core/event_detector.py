import time
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Callable

from app.core.peak_detector import WaveletPeakDetector


@dataclass
class DetectedEvent:
    start_time: float
    end_time: float
    peak_count: int

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class EventPollResult:
    started: bool
    started_time: Optional[float]
    closed_events: List[DetectedEvent]
    cluster_ended: bool
    is_active: bool
    active_since: Optional[float]


class EventDetector:
    def __init__(
        self,
        sample_rate: float,
        window_ms: float = 200.0,
        poll_interval_ms: float = 100.0,
        cluster_gap_ms: float = 150.0,
        min_event_duration_ms: float = 20.0,
        peak_min_width_ms: float = 0.2,
        peak_max_width_ms: float = 5.0,
        peak_min_height: float = 60.0,
    ):
        self.sample_rate = sample_rate
        self.window_ms = window_ms
        self.poll_interval_ms = poll_interval_ms
        self.cluster_gap_ms = cluster_gap_ms
        self.min_event_duration_ms = min_event_duration_ms

        self.peak_detector = WaveletPeakDetector(
            sample_rate=sample_rate,
            min_width_ms=peak_min_width_ms,
            max_width_ms=peak_max_width_ms,
            min_height=peak_min_height,
        )

        self.in_event = False
        self.event_start_time: Optional[float] = None
        self.last_peak_time: Optional[float] = None
        self.peak_count = 0

    @property
    def window_samples(self) -> int:
        return max(8, int(self.window_ms * 1e-3 * self.sample_rate))

    def poll(self, get_window_fn: Callable[[int], np.ndarray]) -> EventPollResult:
        now = time.time()
        window = np.asarray(get_window_fn(self.window_samples), dtype=np.float64)

        started_time: Optional[float] = None
        closed_events: List[DetectedEvent] = []
        cluster_ended = False

        if len(window) >= 8:
            peak_indices = self.peak_detector.find_peaks(window)

            new_sample_count = int(self.poll_interval_ms * 1e-3 * self.sample_rate)
            cutoff_index = max(0, len(window) - new_sample_count)
            new_peak_indices = np.sort(peak_indices[peak_indices >= cutoff_index])

            for idx in new_peak_indices:
                samples_from_end = len(window) - 1 - int(idx)
                peak_time = now - samples_from_end / self.sample_rate

                started, closed_event, this_cluster_ended = self.feed_peak(peak_time)

                if started and started_time is None:
                    started_time = peak_time
                if closed_event is not None:
                    closed_events.append(closed_event)
                if this_cluster_ended:
                    cluster_ended = True

        timeout_event, timeout_cluster_ended = self.check_timeout(now)
        if timeout_event is not None:
            closed_events.append(timeout_event)
        if timeout_cluster_ended:
            cluster_ended = True

        return EventPollResult(
            started=started_time is not None,
            started_time=started_time,
            closed_events=closed_events,
            cluster_ended=cluster_ended,
            is_active=self.in_event,
            active_since=self.event_start_time if self.in_event else None,
        )

    def feed_peak(self, peak_time: float):
        closed_event = None
        cluster_ended = False
        started = False

        if not self.in_event:
            self.in_event = True
            self.event_start_time = peak_time
            self.peak_count = 1
            started = True
        else:
            gap_ms = (peak_time - self.last_peak_time) * 1000.0
            if gap_ms > self.cluster_gap_ms:
                closed_event = self.close_event(self.last_peak_time)
                cluster_ended = True
                self.in_event = True
                self.event_start_time = peak_time
                self.peak_count = 1
                started = True
            else:
                self.peak_count += 1

        self.last_peak_time = peak_time
        return started, closed_event, cluster_ended

    def check_timeout(self, now: float):
        if not self.in_event or self.last_peak_time is None:
            return None, False
        gap_ms = (now - self.last_peak_time) * 1000.0
        if gap_ms > self.cluster_gap_ms:
            return self.close_event(self.last_peak_time), True
        return None, False

    def close_event(self, end_time: float) -> Optional[DetectedEvent]:
        duration_ms = (end_time - self.event_start_time) * 1000.0
        event = None
        if duration_ms >= self.min_event_duration_ms:
            event = DetectedEvent(
                start_time=self.event_start_time,
                end_time=end_time,
                peak_count=self.peak_count,
            )
        self.in_event = False
        self.event_start_time = None
        self.last_peak_time = None
        self.peak_count = 0
        return event