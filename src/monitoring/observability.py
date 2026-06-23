"""
Observability and monitoring hooks for CCD detection pipeline.

Provides a lightweight event bus for detection events, latency tracking,
and integration points for external monitoring systems (Prometheus, Datadog, etc.).
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional


@dataclass
class DetectionEvent:
    session_id: str
    component_name: str
    is_ccd: bool
    confidence: float
    latency_ms: float
    timestamp: float = field(default_factory=time.time)
    model_id: Optional[str] = None
    error: Optional[str] = None


class CCDMonitor:
    """
    Lightweight monitoring bus for CCD detection events.

    Wire in your detector and call .record() after each detection.
    Subscribe to events via .on_event().
    """

    def __init__(self, window_size: int = 1000) -> None:
        self._window: Deque[DetectionEvent] = deque(maxlen=window_size)
        self._handlers: List[Callable[[DetectionEvent], None]] = []
        self._error_count = 0
        self._total_count = 0

    def record(self, event: DetectionEvent) -> None:
        """Record a detection event and fire all registered handlers."""
        self._window.append(event)
        self._total_count += 1
        if event.error:
            self._error_count += 1
        for handler in self._handlers:
            try:
                handler(event)
            except Exception:
                pass  # never let a handler crash the detection pipeline

    def on_event(self, handler: Callable[[DetectionEvent], None]) -> None:
        """Register an event handler (e.g. send to Prometheus, log to file)."""
        self._handlers.append(handler)

    def get_metrics(self) -> Dict[str, Any]:
        """Return a snapshot of current metrics."""
        events = list(self._window)
        if not events:
            return {
                "total_events": self._total_count,
                "window_events": 0,
                "ccd_rate": 0.0,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "error_rate": 0.0,
            }

        ccd_count = sum(1 for e in events if e.is_ccd)
        latencies = sorted(e.latency_ms for e in events)
        avg_lat = sum(latencies) / len(latencies)
        p95_idx = max(0, int(len(latencies) * 0.95) - 1)

        return {
            "total_events": self._total_count,
            "window_events": len(events),
            "ccd_rate": ccd_count / len(events),
            "avg_latency_ms": round(avg_lat, 2),
            "p95_latency_ms": round(latencies[p95_idx], 2),
            "error_rate": self._error_count / self._total_count if self._total_count > 0 else 0.0,
        }

    def health_check(self) -> Dict[str, Any]:
        """Return a health summary suitable for a /health endpoint."""
        metrics = self.get_metrics()
        healthy = (
            metrics["error_rate"] < 0.05
            and metrics["p95_latency_ms"] < 2000
        )
        return {"healthy": healthy, **metrics}

    def reset(self) -> None:
        """Clear the event window (does not reset total counters)."""
        self._window.clear()


# Module-level singleton — import and use directly
monitor = CCDMonitor()
