"""Tests for incremental learning"""
import pytest
from src.learning.incremental_learner import IncrementalCCDLearner, LearningUpdate


def make_sessions(n_ccd, n_ctrl):
    return (
        [{"is_ccd": True, "f1": 0.9, "f2": 0.9, "f3": 0.8, "f4": 0.7}] * n_ccd +
        [{"is_ccd": False, "f1": 0.1, "f2": 0.1, "f3": 0.1, "f4": 0.1}] * n_ctrl
    )


class TestIncrementalCCDLearner:
    def setup_method(self):
        self.learner = IncrementalCCDLearner(alpha=0.1)

    def test_instantiates(self):
        assert self.learner is not None

    def test_update_returns_learning_update(self):
        sessions = make_sessions(5, 5)
        update = self.learner.update(sessions)
        assert isinstance(update, LearningUpdate)

    def test_update_has_weights_before_and_after(self):
        sessions = make_sessions(5, 5)
        update = self.learner.update(sessions)
        assert "f1_cross_session_persistence" in update.weights_before
        assert "f1_cross_session_persistence" in update.weights_after

    def test_weights_sum_to_one_after_update(self):
        sessions = make_sessions(10, 10)
        self.learner.update(sessions)
        total = sum(self.learner.weights.values())
        assert abs(total - 1.0) < 0.02

    def test_total_sessions_tracked(self):
        self.learner.update(make_sessions(5, 5))
        self.learner.update(make_sessions(3, 3))
        assert self.learner.total_sessions_seen() == 16

    def test_update_history_grows(self):
        self.learner.update(make_sessions(5, 5))
        self.learner.update(make_sessions(5, 5))
        assert len(self.learner.get_weight_history()) == 2

    def test_drift_detected_field_is_bool(self):
        sessions = make_sessions(10, 10)
        update = self.learner.update(sessions)
        assert isinstance(update.drift_detected, bool)

    def test_empty_sessions_no_crash(self):
        update = self.learner.update([])
        assert isinstance(update, LearningUpdate)
