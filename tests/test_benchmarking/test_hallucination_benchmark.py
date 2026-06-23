"""Tests for hallucination benchmark suite"""
import pytest
from src.benchmarking.hallucination_benchmark import HallucinationBenchmarkSuite, BenchmarkResult


class FakeResult:
    def __init__(self, is_ccd):
        self.is_ccd = is_ccd
        self.confidence = 0.9 if is_ccd else 0.3


def make_sessions(n_ccd, n_clean):
    return (
        [{"is_ccd": True, "interactions": [], "component": "auth"} for _ in range(n_ccd)] +
        [{"is_ccd": False, "interactions": [], "component": "util"} for _ in range(n_clean)]
    )


class TestHallucinationBenchmarkSuite:
    def setup_method(self):
        self.suite = HallucinationBenchmarkSuite()

    def test_instantiates(self):
        assert self.suite is not None

    def test_run_returns_benchmark_result(self):
        sessions = make_sessions(5, 5)
        result = self.suite.run(
            detector_fn=lambda s: FakeResult(s["is_ccd"]),
            labeled_sessions=sessions,
        )
        assert isinstance(result, BenchmarkResult)

    def test_perfect_detector_f1_one(self):
        sessions = make_sessions(10, 10)
        result = self.suite.run(
            detector_fn=lambda s: FakeResult(s["is_ccd"]),
            labeled_sessions=sessions,
        )
        assert result.f1 == 1.0
        assert result.precision == 1.0
        assert result.recall == 1.0

    def test_always_negative_detector_f1_zero(self):
        sessions = make_sessions(10, 10)
        result = self.suite.run(
            detector_fn=lambda s: FakeResult(False),
            labeled_sessions=sessions,
        )
        assert result.recall == 0.0

    def test_result_stores_session_counts(self):
        sessions = make_sessions(3, 3)
        result = self.suite.run(lambda s: FakeResult(s["is_ccd"]), sessions)
        assert result.total_sessions == 6

    def test_latency_fields_present(self):
        sessions = make_sessions(5, 5)
        result = self.suite.run(lambda s: FakeResult(s["is_ccd"]), sessions)
        assert result.avg_latency_ms >= 0
        assert result.p95_latency_ms >= 0

    def test_accuracy_property(self):
        sessions = make_sessions(5, 5)
        result = self.suite.run(lambda s: FakeResult(s["is_ccd"]), sessions)
        assert 0.0 <= result.accuracy <= 1.0

    def test_compare_returns_delta_dict(self):
        sessions = make_sessions(5, 5)
        r1 = self.suite.run(lambda s: FakeResult(s["is_ccd"]), sessions, suite_name="A")
        r2 = self.suite.run(lambda s: FakeResult(False), sessions, suite_name="B")
        delta = self.suite.compare(r1, r2)
        assert "f1_delta" in delta
        assert "precision_delta" in delta

    def test_summary_report_is_string(self):
        sessions = make_sessions(3, 3)
        self.suite.run(lambda s: FakeResult(s["is_ccd"]), sessions)
        report = self.suite.summary_report()
        assert isinstance(report, str)
        assert len(report) > 0
