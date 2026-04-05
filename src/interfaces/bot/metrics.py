from collections import deque
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    requests_total: int
    failures_total: int
    quota_blocked_total: int
    avg_response_ms: float
    p95_response_ms: float


class BotMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests_total = 0
        self._failures_total = 0
        self._quota_blocked_total = 0
        self._latencies_ms: deque[float] = deque(maxlen=1000)

    def record_request(self, latency_ms: float, success: bool) -> None:
        with self._lock:
            self._requests_total += 1
            if not success:
                self._failures_total += 1
            self._latencies_ms.append(latency_ms)

    def record_quota_blocked(self) -> None:
        with self._lock:
            self._quota_blocked_total += 1

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            latencies = list(self._latencies_ms)
            if not latencies:
                avg = 0.0
                p95 = 0.0
            else:
                avg = round(sum(latencies) / len(latencies), 2)
                sorted_latencies = sorted(latencies)
                index = int(0.95 * (len(sorted_latencies) - 1))
                p95 = round(sorted_latencies[index], 2)
            return MetricsSnapshot(
                requests_total=self._requests_total,
                failures_total=self._failures_total,
                quota_blocked_total=self._quota_blocked_total,
                avg_response_ms=avg,
                p95_response_ms=p95,
            )


bot_metrics = BotMetrics()
