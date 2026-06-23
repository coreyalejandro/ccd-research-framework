"""Tests for sensitivity analysis module"""
import pytest
from src.analysis.sensitivity_analysis import SensitivityAnalyzer, ThresholdResult


class FakeResult:
    def __init__(self, is_ccd):
        self.is_ccd = is_ccd


def make_sessions(n_ccd, n_clean):
    return (
        [{"is_ccd": True} for _ in range(n_ccd)] +
        [{"is_ccd": False} for _ in range(n_clean)]
    )


class TestSensitivityAnalyzer:
    def setup_method(self):
        self.analyzer = SensitivityAnalyzer()

    def test_instantiates(self):
        assert self.analyzer is not None

    def test_sweep_returns_list_of_threshold_results(self):
        sessions = make_sessions(10, 10)
        results = self.analyzer.sweep_threshold(
            detector_fn=lambda s, t: FakeResult(s["is_ccd"] and t <= 0.7),
            labeled_sessions=sessions,
            thresholds=[0.5, 0.7, 0.9],
        )
        assert len(results) == 3
        assert all(isinstance(r, ThresholdResult) for r in results)

    def test_sweep_uses_default_thresholds_if_none(self):
        sessions = make_sessions(5, 5)
        results = self.analyzer.sweep_threshold(
            detector_fn=lambda s, t: FakeResult(s["is_ccd"]),
            labeled_sessions=sessions,
        )
        assert len(results) > 0

    def test_find_optimal_returns_best_f1(self):
        results = [
            ThresholdResult(0.5, 0.8, 0.9, 0.85, 10, 20),
            ThresholdResult(0.7, 0.95, 0.75, 0.84, 8, 20),
            ThresholdResult(0.9, 1.0, 0.5, 0.67, 5, 20),
        ]
        optimal = self.analyzer.find_optimal_threshold(results, metric="f1")
        assert optimal.threshold == 0.5

    def test_find_optimal_empty_raises(self):
        with pytest.raises(ValueError):
            self.analyzer.find_optimal_threshold([])

    def test_generate_report_is_string(self):
        sessions = make_sessions(5, 5)
        results = self.analyzer.sweep_threshold(
            lambda s, t: FakeResult(s["is_ccd"]),
            sessions,
            thresholds=[0.6, 0.7],
        )
        report = self.analyzer.generate_report(results)
        assert isinstance(report, str)

    def test_false_positive_rate_property(self):
        r = ThresholdResult(0.7, 0.8, 0.9, 0.85, 10, 20)
        assert r.false_positive_rate == pytest.approx(0.2, abs=0.001)
