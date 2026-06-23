"""Tests for cross-model rollout infrastructure"""
import pytest
from src.rollout.cross_model_rollout import (
    CrossModelRolloutManager, ModelConfig, ModelProvider,
    RolloutPhase, RolloutHealth, RolloutEvent
)


def make_config(model_id="claude-3-sonnet", provider=ModelProvider.ANTHROPIC):
    return ModelConfig(
        model_id=model_id,
        provider=provider,
        detection_threshold=0.7,
        enabled=True,
        rollout_phase=RolloutPhase.CANARY,
        traffic_percentage=0.05,
    )


class TestCrossModelRolloutManager:
    def setup_method(self):
        self.mgr = CrossModelRolloutManager()

    def test_instantiates(self):
        assert self.mgr is not None

    def test_register_model_does_not_raise(self):
        self.mgr.register_model(make_config())

    def test_list_models_empty_initially(self):
        assert self.mgr.list_models() == []

    def test_list_models_after_register(self):
        self.mgr.register_model(make_config("gpt-4", ModelProvider.OPENAI))
        assert "gpt-4" in self.mgr.list_models()

    def test_get_config_returns_config(self):
        cfg = make_config()
        self.mgr.register_model(cfg)
        result = self.mgr.get_config("claude-3-sonnet")
        assert isinstance(result, ModelConfig)
        assert result.model_id == "claude-3-sonnet"

    def test_get_config_missing_returns_none(self):
        assert self.mgr.get_config("nonexistent") is None

    def test_check_health_returns_rollout_health(self):
        self.mgr.register_model(make_config())
        health = self.mgr.check_health("claude-3-sonnet")
        assert isinstance(health, RolloutHealth)

    def test_new_model_is_healthy(self):
        self.mgr.register_model(make_config())
        health = self.mgr.check_health("claude-3-sonnet")
        assert health.healthy is True

    def test_advance_phase_from_canary_to_pilot(self):
        self.mgr.register_model(make_config())
        new_phase = self.mgr.advance_phase("claude-3-sonnet")
        assert new_phase == RolloutPhase.PILOT

    def test_advance_updates_traffic_percentage(self):
        self.mgr.register_model(make_config())
        self.mgr.advance_phase("claude-3-sonnet")
        cfg = self.mgr.get_config("claude-3-sonnet")
        assert cfg.traffic_percentage == CrossModelRolloutManager.PHASE_TRAFFIC[RolloutPhase.PILOT]

    def test_rollback_sets_phase_to_rollback(self):
        self.mgr.register_model(make_config())
        self.mgr.rollback("claude-3-sonnet", reason="high fp rate")
        cfg = self.mgr.get_config("claude-3-sonnet")
        assert cfg.rollout_phase == RolloutPhase.ROLLBACK
        assert cfg.traffic_percentage == 0.0

    def test_rollback_logs_event(self):
        self.mgr.register_model(make_config())
        self.mgr.rollback("claude-3-sonnet", reason="test")
        trail = self.mgr.get_audit_trail("claude-3-sonnet")
        actions = [e.action for e in trail]
        assert "rollback" in actions

    def test_should_detect_returns_bool(self):
        self.mgr.register_model(make_config())
        result = self.mgr.should_detect("claude-3-sonnet")
        assert isinstance(result, bool)

    def test_rolled_back_model_never_detects(self):
        self.mgr.register_model(make_config())
        self.mgr.rollback("claude-3-sonnet", reason="test")
        results = [self.mgr.should_detect("claude-3-sonnet") for _ in range(20)]
        assert all(r is False for r in results)

    def test_full_phase_always_detects(self):
        cfg = make_config()
        cfg.rollout_phase = RolloutPhase.FULL
        cfg.traffic_percentage = 1.0
        self.mgr.register_model(cfg)
        results = [self.mgr.should_detect("claude-3-sonnet") for _ in range(20)]
        assert all(r is True for r in results)

    def test_record_result_updates_stats(self):
        self.mgr.register_model(make_config())
        self.mgr.record_result("claude-3-sonnet", is_ccd=True)
        health = self.mgr.check_health("claude-3-sonnet")
        assert health.sessions_processed == 1
        assert health.ccd_detections == 1

    def test_high_fp_rate_triggers_auto_rollback(self):
        self.mgr.register_model(make_config())
        # Record 100 sessions with 20% fp rate (exceeds 10% threshold)
        for _ in range(80):
            self.mgr.record_result("claude-3-sonnet", is_ccd=False)
        for _ in range(20):
            self.mgr.record_result("claude-3-sonnet", is_ccd=False, is_false_positive=True)
        cfg = self.mgr.get_config("claude-3-sonnet")
        assert cfg.rollout_phase == RolloutPhase.ROLLBACK

    def test_get_all_health_returns_list(self):
        self.mgr.register_model(make_config("m1"))
        self.mgr.register_model(make_config("m2", ModelProvider.OPENAI))
        all_health = self.mgr.get_all_health()
        assert isinstance(all_health, list)
        assert len(all_health) == 2

    def test_export_config_returns_json_string(self):
        import json
        self.mgr.register_model(make_config())
        exported = self.mgr.export_config()
        assert isinstance(exported, str)
        parsed = json.loads(exported)
        assert "claude-3-sonnet" in parsed

    def test_audit_trail_returns_list(self):
        self.mgr.register_model(make_config())
        trail = self.mgr.get_audit_trail()
        assert isinstance(trail, list)

    def test_audit_trail_filtered_by_model(self):
        self.mgr.register_model(make_config("m1"))
        self.mgr.register_model(make_config("m2", ModelProvider.OPENAI))
        trail = self.mgr.get_audit_trail("m1")
        assert all(e.model_id == "m1" for e in trail)

    def test_advance_unregistered_raises(self):
        with pytest.raises(KeyError):
            self.mgr.advance_phase("nonexistent")
