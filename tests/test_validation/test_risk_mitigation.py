"""Tests for risk mitigation protocols"""
import pytest
from src.validation.risk_mitigation import (
    RiskMitigationSystem, RiskAssessment, RiskLevel,
    MitigationStatus, MitigationAction, ControlGroupBiasAudit, FallbackProtocol
)


class TestRiskMitigationSystem:
    def setup_method(self):
        self.system = RiskMitigationSystem()

    def test_instantiates(self):
        assert self.system is not None

    def test_assess_risk_returns_risk_assessment(self):
        result = self.system.assess_risk(
            risk_type="false_positive",
            description="Detector flags functional code as CCD",
            impact="Developer trust erosion",
            likelihood=0.3,
        )
        assert isinstance(result, RiskAssessment)

    def test_risk_assessment_has_risk_id(self):
        ra = self.system.assess_risk(
            "false_positive", "false positive risk", "low impact", 0.2
        )
        assert hasattr(ra, "risk_id")
        assert isinstance(ra.risk_id, str)

    def test_risk_assessment_has_level(self):
        ra = self.system.assess_risk(
            "false_positive", "desc", "impact", 0.8
        )
        assert hasattr(ra, "risk_level")
        assert isinstance(ra.risk_level, RiskLevel)

    def test_risk_assessment_has_likelihood(self):
        ra = self.system.assess_risk(
            "false_positive", "desc", "impact", 0.5
        )
        assert hasattr(ra, "likelihood")
        assert ra.likelihood == 0.5

    def test_multiple_risk_assessments_stored(self):
        self.system.assess_risk("fp", "desc1", "impact1", 0.3)
        self.system.assess_risk("fn", "desc2", "impact2", 0.4)
        assert len(self.system.risk_assessments) == 2

    def test_create_mitigation_action_returns_action(self):
        ra = self.system.assess_risk("fp", "desc", "impact", 0.3)
        action = self.system.create_mitigation_action(
            risk_id=ra.risk_id,
            action_type="threshold_adjustment",
            description="Adjust detection threshold to reduce FP rate",
        )
        assert isinstance(action, MitigationAction)

    def test_mitigation_action_has_action_id(self):
        ra = self.system.assess_risk("fp", "desc", "impact", 0.3)
        action = self.system.create_mitigation_action(ra.risk_id, "adjust", "desc")
        assert hasattr(action, "action_id")
        assert isinstance(action.action_id, str)

    def test_mitigation_action_has_status(self):
        ra = self.system.assess_risk("fp", "desc", "impact", 0.3)
        action = self.system.create_mitigation_action(ra.risk_id, "adjust", "desc")
        assert hasattr(action, "status")
        assert isinstance(action.status, MitigationStatus)

    def test_execute_mitigation_returns_bool(self):
        ra = self.system.assess_risk("fp", "desc", "impact", 0.3)
        action = self.system.create_mitigation_action(ra.risk_id, "adjust", "desc")
        result = self.system.execute_mitigation(action.action_id)
        assert isinstance(result, bool)

    def test_generate_risk_report_returns_string(self):
        self.system.assess_risk("fp", "desc", "impact", 0.3)
        report = self.system.generate_risk_report()
        assert isinstance(report, str)
        assert len(report) > 0

    def test_risk_level_values(self):
        assert RiskLevel.LOW.value in ("low", "LOW")
        assert RiskLevel.HIGH.value in ("high", "HIGH")

    def test_mitigation_status_values(self):
        assert MitigationStatus.PENDING.value in ("pending", "PENDING")

    def test_bias_audit_has_run_audit(self):
        assert hasattr(self.system.bias_audit, "run_audit")
        assert callable(self.system.bias_audit.run_audit)

    def test_bias_audit_run_audit_returns_dict(self):
        ccd_detections = [
            {"session_id": f"s{i}", "is_ccd": True, "confidence": 0.85}
            for i in range(10)
        ]
        claude_verifications = [
            {"session_id": f"s{i}", "claude_says_ccd": True}
            for i in range(10)
        ]
        result = self.system.bias_audit.run_audit(ccd_detections, claude_verifications)
        assert isinstance(result, dict)

    def test_fallback_protocol_exists(self):
        assert hasattr(self.system, "fallback_protocol")
        assert isinstance(self.system.fallback_protocol, FallbackProtocol)

    def test_fallback_protocol_has_trigger_fallback(self):
        assert hasattr(self.system.fallback_protocol, "trigger_fallback")
        assert callable(self.system.fallback_protocol.trigger_fallback)
