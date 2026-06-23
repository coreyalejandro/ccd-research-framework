"""Tests for input validation and error handling"""
import pytest
from src.detector.input_validator import (
    validate_interaction, validate_interactions, validate_component_name,
    validate_confidence, ValidationError
)


class TestValidateInteraction:
    def test_valid_interaction_passes(self):
        result = validate_interaction({
            "user_prompt": "implement auth",
            "agent_response": "auth is done",
        })
        assert result["user_prompt"] == "implement auth"

    def test_missing_user_prompt_raises(self):
        with pytest.raises(ValidationError):
            validate_interaction({"agent_response": "done"})

    def test_missing_agent_response_raises(self):
        with pytest.raises(ValidationError):
            validate_interaction({"user_prompt": "implement"})

    def test_non_dict_raises(self):
        with pytest.raises(ValidationError):
            validate_interaction("not a dict")

    def test_defaults_added(self):
        result = validate_interaction({
            "user_prompt": "build X",
            "agent_response": "X built"
        })
        assert "artifacts_generated" in result
        assert "is_challenge" in result
        assert "admission_type" in result

    def test_artifacts_default_empty_list(self):
        result = validate_interaction({"user_prompt": "x", "agent_response": "y"})
        assert result["artifacts_generated"] == []

    def test_does_not_mutate_original(self):
        original = {"user_prompt": "x", "agent_response": "y"}
        validate_interaction(original)
        assert "artifacts_generated" not in original

    def test_non_string_prompt_coerced(self):
        result = validate_interaction({"user_prompt": 42, "agent_response": "ok"})
        assert result["user_prompt"] == "42"


class TestValidateInteractions:
    def test_empty_list_returns_empty(self):
        assert validate_interactions([]) == []

    def test_valid_list_passes(self):
        items = [
            {"user_prompt": "x", "agent_response": "y"},
            {"user_prompt": "a", "agent_response": "b"},
        ]
        result = validate_interactions(items)
        assert len(result) == 2

    def test_non_list_raises(self):
        with pytest.raises(ValidationError):
            validate_interactions("not a list")

    def test_malformed_item_skipped_not_raised(self):
        items = [
            {"user_prompt": "good", "agent_response": "ok"},
            "bad item",  # should be skipped
        ]
        result = validate_interactions(items)
        assert len(result) == 1  # only the good one


class TestValidateComponentName:
    def test_valid_name(self):
        assert validate_component_name("auth_module") == "auth_module"

    def test_strips_whitespace(self):
        assert validate_component_name("  auth  ") == "auth"

    def test_none_raises(self):
        with pytest.raises(ValidationError):
            validate_component_name(None)

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError):
            validate_component_name("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            validate_component_name("   ")


class TestValidateConfidence:
    def test_valid_float(self):
        assert validate_confidence(0.75) == 0.75

    def test_clamps_above_one(self):
        assert validate_confidence(1.5) == 1.0

    def test_clamps_below_zero(self):
        assert validate_confidence(-0.5) == 0.0

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError):
            validate_confidence("not a number")

    def test_zero_valid(self):
        assert validate_confidence(0) == 0.0

    def test_one_valid(self):
        assert validate_confidence(1) == 1.0
