"""Tests for GDPR/CCPA compliance module"""
import json
import pytest
from src.privacy.gdpr_compliance import (
    GDPRComplianceManager, ConsentStatus, ConsentRecord,
    DataCategory, RetentionPolicy
)


class TestGDPRComplianceManager:
    def setup_method(self):
        self.mgr = GDPRComplianceManager()

    def test_instantiates(self):
        assert self.mgr is not None

    def test_anonymize_session_returns_dict(self):
        session = {
            "session_id": "orig-123",
            "session_type": "ccd_positive",
            "interactions": []
        }
        result = self.mgr.anonymize_session(session)
        assert isinstance(result, dict)

    def test_anonymize_session_hashes_session_id(self):
        session = {"session_id": "orig-123", "interactions": []}
        result = self.mgr.anonymize_session(session)
        assert result["session_id"] != "orig-123"

    def test_anonymize_session_does_not_mutate_original(self):
        session = {"session_id": "orig-123", "interactions": []}
        _ = self.mgr.anonymize_session(session)
        assert session["session_id"] == "orig-123"

    def test_anonymize_corpus_returns_list(self):
        sessions = [{"session_id": f"s{i}", "interactions": []} for i in range(3)]
        result = self.mgr.anonymize_corpus(sessions)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_record_consent_returns_consent_record(self):
        record = self.mgr.record_consent(
            subject_id="user_001",
            status=ConsentStatus.GRANTED,
            purposes=["ccd_detection", "research"],
            data_categories=[DataCategory.SESSION_INTERACTION],
        )
        assert isinstance(record, ConsentRecord)
        assert record.status == ConsentStatus.GRANTED

    def test_check_consent_granted(self):
        self.mgr.record_consent(
            "user_001", ConsentStatus.GRANTED,
            ["ccd_detection"], [DataCategory.SESSION_INTERACTION]
        )
        assert self.mgr.check_consent("user_001", "ccd_detection") is True

    def test_check_consent_unknown_subject(self):
        assert self.mgr.check_consent("unknown", "anything") is False

    def test_withdraw_consent_blocks_access(self):
        self.mgr.record_consent(
            "user_002", ConsentStatus.GRANTED,
            ["research"], [DataCategory.SESSION_INTERACTION]
        )
        self.mgr.withdraw_consent("user_002")
        assert self.mgr.check_consent("user_002", "research") is False

    def test_register_data_returns_record_id(self):
        record_id = self.mgr.register_data(
            "user_001",
            {"component": "auth", "session": "s1"},
            DataCategory.SESSION_INTERACTION,
        )
        assert isinstance(record_id, str)
        assert len(record_id) > 0

    def test_delete_subject_data_returns_count(self):
        self.mgr.register_data("user_del", {"x": 1}, DataCategory.SESSION_INTERACTION)
        count = self.mgr.delete_subject_data("user_del")
        assert isinstance(count, int)
        assert count >= 1

    def test_delete_subject_clears_consent(self):
        self.mgr.record_consent("user_del2", ConsentStatus.GRANTED, ["r"], [DataCategory.SESSION_INTERACTION])
        self.mgr.delete_subject_data("user_del2")
        assert self.mgr.check_consent("user_del2", "r") is False

    def test_export_subject_data_returns_json_string(self):
        self.mgr.register_data("user_export", {"x": 1}, DataCategory.SESSION_INTERACTION)
        result = self.mgr.export_subject_data("user_export")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "records" in parsed

    def test_enforce_retention_returns_list(self):
        result = self.mgr.enforce_retention()
        assert isinstance(result, list)

    def test_interaction_pii_redacted(self):
        session = {
            "session_id": "s1",
            "interactions": [
                {
                    "turn_id": 1,
                    "user_prompt": "email me at john.doe@example.com about auth",
                    "agent_response": "I will contact john.doe@example.com",
                    "artifacts_generated": [],
                    "is_challenge": False,
                    "admission_type": None,
                }
            ]
        }
        result = self.mgr.anonymize_session(session)
        prompt = result["interactions"][0]["user_prompt"]
        assert "john.doe@example.com" not in prompt
        assert "[EMAIL]" in prompt
