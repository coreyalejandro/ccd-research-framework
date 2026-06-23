"""Tests for automated intent tracking"""
import pytest
from src.detector.intent_tracker import AutomatedIntentTracker, IntentEvidence, IntentSignal


class TestAutomatedIntentTracker:
    def setup_method(self):
        self.tracker = AutomatedIntentTracker()

    def test_tracker_instantiates(self):
        assert self.tracker is not None

    def test_analyze_prompt_returns_list(self):
        evidence = self.tracker.analyze_prompt(
            "Can you implement a caching layer?",
            "caching layer"
        )
        assert isinstance(evidence, list)

    def test_analyze_prompt_detects_implementation_keyword(self):
        evidence = self.tracker.analyze_prompt(
            "implement a caching layer for our API",
            "caching layer"
        )
        assert len(evidence) >= 1
        assert all(isinstance(e, IntentEvidence) for e in evidence)

    def test_analyze_prompt_empty_string(self):
        evidence = self.tracker.analyze_prompt("", "component")
        assert isinstance(evidence, list)

    def test_confirm_user_intent_returns_dict(self):
        result = self.tracker.confirm_user_intent(
            ["implement the auth module"],
            "auth module"
        )
        assert isinstance(result, dict)
        assert "intent_confirmed" in result
        assert "confidence" in result

    def test_confirm_user_intent_structure(self):
        result = self.tracker.confirm_user_intent(
            ["I need you to build the authentication system"],
            "authentication"
        )
        assert "evidence_count" in result
        assert "evidence" in result
        assert isinstance(result["confidence"], float)

    def test_confirm_user_intent_no_match(self):
        result = self.tracker.confirm_user_intent(
            ["what time is it?"],
            "authentication"
        )
        assert result["intent_confirmed"] is False

    def test_analyze_commit_message_returns_list(self):
        result = self.tracker.analyze_commit_message(
            "feat: add authentication middleware",
            "authentication"
        )
        assert isinstance(result, list)

    def test_analyze_documentation_returns_list(self):
        result = self.tracker.analyze_documentation(
            "The caching layer handles Redis and in-memory backends.",
            "caching"
        )
        assert isinstance(result, list)

    def test_aggregate_intent_confidence_returns_float(self):
        evidence = self.tracker.analyze_prompt(
            "implement the caching system please",
            "caching"
        )
        conf = self.tracker.aggregate_intent_confidence(evidence)
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0

    def test_extract_component_name_from_prompt(self):
        name = self.tracker.extract_component_name(
            "Can you build the authentication middleware for us?"
        )
        assert isinstance(name, str)

    def test_intent_evidence_has_confidence(self):
        evidence = self.tracker.analyze_prompt(
            "build a rate limiter that handles 1000 req/s",
            "rate limiter"
        )
        for e in evidence:
            assert 0.0 <= e.confidence <= 1.0

    def test_analyze_test_expectations_returns_list(self):
        result = self.tracker.analyze_test_expectations(
            "test_auth_middleware_handles_invalid_token",
            "auth middleware"
        )
        assert isinstance(result, list)
