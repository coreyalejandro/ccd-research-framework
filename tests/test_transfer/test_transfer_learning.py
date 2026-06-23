"""Tests for cross-model transfer learning protocol"""
import pytest
from src.transfer.transfer_learning import TransferLearningProtocol, TransferConfig


def make_sessions(n_ccd, n_ctrl):
    sessions = []
    for i in range(n_ccd):
        sessions.append({"is_ccd": True, "f1": 0.8, "f2": 0.9, "f3": 0.7, "f4": 0.6})
    for i in range(n_ctrl):
        sessions.append({"is_ccd": False, "f1": 0.2, "f2": 0.1, "f3": 0.1, "f4": 0.2})
    return sessions


class TestTransferLearningProtocol:
    def setup_method(self):
        self.proto = TransferLearningProtocol()

    def test_instantiates(self):
        assert self.proto is not None

    def test_calibrate_returns_transfer_config(self):
        sessions = make_sessions(5, 5)
        config = self.proto.calibrate("claude-3", "gpt-4", sessions)
        assert isinstance(config, TransferConfig)

    def test_config_has_source_and_target(self):
        sessions = make_sessions(5, 5)
        config = self.proto.calibrate("claude-3", "gpt-4", sessions)
        assert config.source_model == "claude-3"
        assert config.target_model == "gpt-4"

    def test_weights_sum_to_one(self):
        sessions = make_sessions(10, 10)
        config = self.proto.calibrate("A", "B", sessions)
        total = sum(config.source_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_all_weights_positive(self):
        sessions = make_sessions(10, 10)
        config = self.proto.calibrate("A", "B", sessions)
        assert all(v > 0 for v in config.source_weights.values())

    def test_get_config_after_calibrate(self):
        sessions = make_sessions(5, 5)
        self.proto.calibrate("M1", "M2", sessions)
        config = self.proto.get_config("M1", "M2")
        assert config is not None
        assert config.source_model == "M1"

    def test_get_unknown_config_returns_none(self):
        assert self.proto.get_config("X", "Y") is None

    def test_export_configs_is_json(self):
        import json
        sessions = make_sessions(5, 5)
        self.proto.calibrate("A", "B", sessions)
        result = self.proto.export_configs()
        parsed = json.loads(result)
        assert len(parsed) >= 1

    def test_calibration_sessions_count(self):
        sessions = make_sessions(3, 3)
        config = self.proto.calibrate("A", "B", sessions)
        assert config.calibration_sessions == 6
