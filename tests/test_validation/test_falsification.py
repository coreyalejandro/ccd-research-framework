"""Tests for falsification condition testing framework"""
import pytest
from src.validation.falsification_tests import FalsificationTestSuite, FalsificationResult


def make_dr(is_ccd, confidence=0.8):
    return {
        "session_id": "s001",
        "is_ccd": is_ccd,
        "confidence": confidence,
        "severity_weight": 0.8 if is_ccd else 0.0,
        "features": {"f1": 2, "f2": 0.9, "f3": 0.7, "f4": 0.6},
        "criteria_met": {"D1": True, "D2": is_ccd, "D5": is_ccd},
        "explanation": "test"
    }


class TestFalsificationTestSuite:
    def setup_method(self):
        self.suite = FalsificationTestSuite()

    def test_instantiates(self):
        assert self.suite is not None

    def test_has_sub_tests(self):
        assert hasattr(self.suite, "f1_test")
        assert hasattr(self.suite, "f2_test")
        assert hasattr(self.suite, "f3_test")
        assert hasattr(self.suite, "f4_test")

    def test_f1_test_has_test_method(self):
        assert callable(self.suite.f1_test.test)

    def test_f2_test_has_test_method(self):
        assert callable(self.suite.f2_test.test)

    def test_f3_test_has_test_method(self):
        assert callable(self.suite.f3_test.test)

    def test_generate_report_returns_string(self):
        report = self.suite.generate_report({})
        assert isinstance(report, str)

    def test_f1_test_returns_falsification_result(self):
        ccd = [make_dr(True) for _ in range(5)]
        ctrl = [make_dr(False, 0.2) for _ in range(5)]
        result = self.suite.f1_test.test(ccd, ctrl)
        assert isinstance(result, FalsificationResult)

    def test_f1_result_has_is_falsified(self):
        ccd = [make_dr(True) for _ in range(5)]
        ctrl = [make_dr(False, 0.1) for _ in range(5)]
        result = self.suite.f1_test.test(ccd, ctrl)
        assert hasattr(result, "is_falsified")
        assert isinstance(result.is_falsified, bool)

    def test_f1_result_has_condition(self):
        ccd = [make_dr(True) for _ in range(5)]
        ctrl = [make_dr(False, 0.1) for _ in range(5)]
        result = self.suite.f1_test.test(ccd, ctrl)
        assert hasattr(result, "condition")

    def test_f1_result_has_metric_value(self):
        ccd = [make_dr(True) for _ in range(5)]
        ctrl = [make_dr(False, 0.1) for _ in range(5)]
        result = self.suite.f1_test.test(ccd, ctrl)
        assert hasattr(result, "metric_value")
        assert isinstance(result.metric_value, (int, float))

    def test_f1_result_has_threshold(self):
        ccd = [make_dr(True) for _ in range(5)]
        ctrl = [make_dr(False, 0.1) for _ in range(5)]
        result = self.suite.f1_test.test(ccd, ctrl)
        assert hasattr(result, "threshold")

    def test_f1_result_has_explanation(self):
        ccd = [make_dr(True) for _ in range(5)]
        ctrl = [make_dr(False, 0.1) for _ in range(5)]
        result = self.suite.f1_test.test(ccd, ctrl)
        assert hasattr(result, "explanation")
        assert isinstance(result.explanation, str)

    def test_generate_report_with_results(self):
        ccd = [make_dr(True) for _ in range(5)]
        ctrl = [make_dr(False, 0.1) for _ in range(5)]
        f1_result = self.suite.f1_test.test(ccd, ctrl)
        report = self.suite.generate_report({"F1": f1_result})
        assert isinstance(report, str)
        assert len(report) > 0
