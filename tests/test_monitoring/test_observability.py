"""Tests for monitoring/observability module"""
import pytest
from src.monitoring.observability import CCDMonitor, DetectionEvent, monitor


class TestCCDMonitor:
    def setup_method(self):
        self.mon = CCDMonitor()

    def test_instantiates(self):
        assert self.mon is not None

    def test_record_event_increments_total(self):
        event = DetectionEvent(session_id="s1", component_name="auth", is_ccd=True, confidence=0.9, latency_ms=5.0)
        self.mon.record(event)
        metrics = self.mon.get_metrics()
        assert metrics["total_events"] == 1

    def test_ccd_rate_calculation(self):
        for i in range(5):
            e = DetectionEvent(session_id=f"s{i}", component_name="x", is_ccd=(i < 2), confidence=0.8, latency_ms=3.0)
            self.mon.record(e)
        metrics = self.mon.get_metrics()
        assert metrics["ccd_rate"] == pytest.approx(0.4, abs=0.01)

    def test_avg_latency(self):
        for ms in [10.0, 20.0, 30.0]:
            e = DetectionEvent(session_id="s", component_name="x", is_ccd=False, confidence=0.3, latency_ms=ms)
            self.mon.record(e)
        metrics = self.mon.get_metrics()
        assert metrics["avg_latency_ms"] == pytest.approx(20.0, abs=0.1)

    def test_empty_metrics_returns_zeros(self):
        metrics = self.mon.get_metrics()
        assert metrics["window_events"] == 0
        assert metrics["ccd_rate"] == 0.0

    def test_on_event_fires_handler(self):
        fired = []
        self.mon.on_event(lambda e: fired.append(e.session_id))
        e = DetectionEvent(session_id="test_session", component_name="x", is_ccd=False, confidence=0.3, latency_ms=1.0)
        self.mon.record(e)
        assert "test_session" in fired

    def test_health_check_returns_healthy_flag(self):
        health = self.mon.health_check()
        assert "healthy" in health
        assert isinstance(health["healthy"], bool)

    def test_reset_clears_window(self):
        e = DetectionEvent(session_id="s1", component_name="x", is_ccd=False, confidence=0.3, latency_ms=1.0)
        self.mon.record(e)
        self.mon.reset()
        assert self.mon.get_metrics()["window_events"] == 0

    def test_module_singleton_exists(self):
        assert isinstance(monitor, CCDMonitor)
