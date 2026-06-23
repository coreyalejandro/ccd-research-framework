"""Tests for PROACTIVE detector"""
import pytest
from src.detector.proactive_detector import (
    PROACTIVEDetector, CCDDetectionResult, CCDFeatures, AdmissionType
)


def make_interaction(user, agent, artifacts=None, is_challenge=False, admission_type=None):
    return {
        "turn_id": 1,
        "timestamp": "2026-06-23T00:00:00",
        "user_prompt": user,
        "agent_response": agent,
        "artifacts_generated": artifacts or [],
        "component_claims": [],
        "is_challenge": is_challenge,
        "admission_type": admission_type,
    }


class TestPROACTIVEDetector:
    def setup_method(self):
        self.detector = PROACTIVEDetector()

    def test_instantiates(self):
        assert self.detector is not None

    def test_detect_returns_result_object(self):
        interactions = [
            make_interaction(
                "Can you implement the auth middleware?",
                "Yes, I have implemented the authentication middleware."
            )
        ]
        result = self.detector.detect(interactions, "auth middleware")
        assert isinstance(result, CCDDetectionResult)

    def test_result_has_required_fields(self):
        interactions = [
            make_interaction("Does it work?", "Yes it is fully implemented.")
        ]
        result = self.detector.detect(interactions, "component")
        assert hasattr(result, "is_ccd")
        assert hasattr(result, "confidence")
        assert hasattr(result, "features")
        assert hasattr(result, "severity_weight")
        assert hasattr(result, "explanation")

    def test_confidence_in_range(self):
        interactions = [make_interaction("Build X", "X is built and working.")]
        result = self.detector.detect(interactions, "X")
        assert 0.0 <= result.confidence <= 1.0

    def test_severity_weight_positive(self):
        interactions = [make_interaction("Build X", "X is built.")]
        result = self.detector.detect(interactions, "X")
        assert result.severity_weight >= 0.0

    def test_extract_features_returns_features(self):
        interactions = [
            make_interaction(
                "implement caching", "Caching layer is implemented."
            ),
            make_interaction(
                "is it real?", "Actually I was wrong.",
                is_challenge=True, admission_type="specific"
            )
        ]
        features = self.detector.extract_features(interactions, "caching")
        assert isinstance(features, CCDFeatures)

    def test_features_f1_is_float(self):
        interactions = [make_interaction("build X", "X built.")]
        features = self.detector.extract_features(interactions, "X")
        assert isinstance(features.f1_cross_session_persistence, (int, float))

    def test_features_f2_is_float(self):
        interactions = [make_interaction("build auth", "auth module is ready")]
        features = self.detector.extract_features(interactions, "auth")
        assert isinstance(features.f2_artifact_divergence, float)

    def test_validate_multi_signal_returns_validation(self):
        validation = self.detector.validate_multi_signal(
            git_files=["src/auth.py"],
            lsp_symbols=["AuthClass"],
            intent_confirmed=True,
        )
        assert hasattr(validation, "has_implementation")

    def test_no_implementation_triggers_d2(self):
        validation = self.detector.validate_multi_signal(
            git_files=[],
            lsp_symbols=[],
            intent_confirmed=True,
            has_venv=False,
            dependencies_valid=False,
        )
        assert validation.has_implementation() is False

    def test_with_implementation_passes_d2(self):
        validation = self.detector.validate_multi_signal(
            git_files=["src/auth.py"],
            lsp_symbols=["AuthMiddleware"],
            intent_confirmed=True,
            has_venv=True,
            dependencies_valid=True,
            env_vars_matched=True,
        )
        assert validation.has_implementation() is True

    def test_detect_admission_type_sycophantic(self):
        response = "You are absolutely right, I apologize for the confusion."
        admission = self.detector.detect_admission_type(response)
        assert isinstance(admission, AdmissionType)

    def test_criteria_dict_in_result(self):
        interactions = [make_interaction("implement auth", "auth is implemented")]
        result = self.detector.detect(interactions, "auth")
        assert isinstance(result.criteria_met, dict)

    def test_detect_with_git_files(self):
        interactions = [make_interaction("build X", "X is done")]
        result = self.detector.detect(
            interactions, "X",
            git_files=["src/x.py"],
            lsp_symbols=["XClass"]
        )
        assert isinstance(result, CCDDetectionResult)
