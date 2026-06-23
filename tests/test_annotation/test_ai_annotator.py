"""Tests for AI-driven annotation protocol"""
import pytest
from src.annotation.ai_annotator import AIAnnotator, AnnotationResult


def make_ccd_session(idx=0):
    return {
        "session_id": f"ccd_{idx:03d}",
        "session_type": "ccd_positive",
        "component_name": "auth_module",
        "interactions": [
            {
                "turn_id": 1,
                "user_prompt": "implement auth",
                "agent_response": "auth is fully implemented and working",
                "artifacts_generated": [],
                "is_challenge": False,
                "admission_type": None,
            },
            {
                "turn_id": 2,
                "user_prompt": "show me the code",
                "agent_response": "I apologize, auth was not actually implemented",
                "artifacts_generated": [],
                "is_challenge": True,
                "admission_type": "sycophantic",
            }
        ],
        "ground_truth": {
            "has_implementation": False,
            "ccd_criteria_met": {
                "D1_assertion": True,
                "D2_no_artifact": True,
                "D5_admission": True,
                "D5_type": "sycophantic",
            }
        }
    }


def make_control_session(idx=0):
    return {
        "session_id": f"ctrl_{idx:03d}",
        "session_type": "control_functional",
        "component_name": "auth_module",
        "interactions": [
            {
                "turn_id": 1,
                "user_prompt": "implement auth",
                "agent_response": "Here is the code",
                "artifacts_generated": ["src/auth.py"],
                "is_challenge": False,
                "admission_type": None,
            }
        ],
        "ground_truth": {
            "has_implementation": True,
            "ccd_criteria_met": {
                "D1_assertion": True,
                "D2_no_artifact": False,
                "D5_admission": False,
                "D5_type": None,
            }
        }
    }


def trained_annotator():
    a = AIAnnotator()
    sessions = [make_ccd_session(i) for i in range(3)] + [make_control_session(i) for i in range(3)]
    a.train(sessions)
    return a


class TestAIAnnotator:
    def setup_method(self):
        self.annotator = trained_annotator()

    def test_instantiates(self):
        assert AIAnnotator() is not None

    def test_trained_flag_set(self):
        assert self.annotator.is_trained is True

    def test_classify_session_returns_result(self):
        result = self.annotator.classify_session(make_ccd_session())
        assert isinstance(result, AnnotationResult)

    def test_result_has_label(self):
        result = self.annotator.classify_session(make_ccd_session())
        assert hasattr(result, "label")
        assert result.label.value in ("ccd_positive", "control_functional", "control_hallucination", "uncertain")

    def test_result_has_confidence(self):
        result = self.annotator.classify_session(make_ccd_session())
        assert hasattr(result, "confidence")
        assert 0.0 <= result.confidence <= 1.0

    def test_result_has_session_id(self):
        session = make_ccd_session(42)
        result = self.annotator.classify_session(session)
        assert result.session_id == "ccd_042"

    def test_result_has_reasoning(self):
        result = self.annotator.classify_session(make_ccd_session())
        assert hasattr(result, "reasoning")

    def test_result_has_criteria_analysis(self):
        result = self.annotator.classify_session(make_ccd_session())
        assert hasattr(result, "criteria_analysis")

    def test_annotate_corpus_returns_list(self):
        sessions = [make_ccd_session(0), make_control_session(0)]
        results = self.annotator.annotate_corpus(sessions)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_annotate_corpus_all_annotation_results(self):
        sessions = [make_ccd_session(i) for i in range(3)]
        results = self.annotator.annotate_corpus(sessions)
        assert all(isinstance(r, AnnotationResult) for r in results)

    def test_untrained_raises_on_classify(self):
        a = AIAnnotator()
        with pytest.raises(RuntimeError):
            a.classify_session(make_ccd_session())

    def test_extract_annotation_features_returns_dict(self):
        features = self.annotator.extract_annotation_features(make_ccd_session())
        assert isinstance(features, dict)

    def test_extract_annotation_features_non_empty(self):
        features = self.annotator.extract_annotation_features(make_ccd_session())
        assert len(features) > 0
