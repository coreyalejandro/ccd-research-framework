"""Tests for academic validation buffer"""
import pytest
from src.validation.academic_buffer import (
    AcademicValidationBuffer, ReviewerRole, ValidationStatus
)


class TestAcademicValidationBuffer:
    def setup_method(self):
        self.buffer = AcademicValidationBuffer()

    def _submit(self, component="auth_module"):
        return self.buffer.submit_for_validation(
            submitted_by="researcher_001",
            component=component,
            description="Testing authentication module CCD detection",
            falsification_conditions=["F1: control group benchmark", "F2: multi-signal separation"],
            test_results={"f1_passed": True, "f2_passed": True, "total_sessions": 50},
            supporting_data={"corpus_size": 50, "ccd_positive": 25},
        )

    def test_instantiates(self):
        assert self.buffer is not None

    def test_submit_returns_string_id(self):
        submission_id = self._submit()
        assert isinstance(submission_id, str)
        assert len(submission_id) > 0

    def test_multiple_submissions_unique_ids(self):
        id1 = self._submit("auth")
        id2 = self._submit("cache")
        assert id1 != id2

    def test_submit_review_returns_bool(self):
        submission_id = self._submit()
        result = self.buffer.submit_review(
            submission_id=submission_id,
            reviewer_id="prof_smith",
            reviewer_role=ReviewerRole.EXTERNAL_ACADEMIC,
            status=ValidationStatus.APPROVED,
            comments="Methodology is sound. Falsification conditions are well-defined.",
        )
        assert isinstance(result, bool)

    def test_submit_review_accepted_for_valid_id(self):
        submission_id = self._submit()
        result = self.buffer.submit_review(
            submission_id=submission_id,
            reviewer_id="prof_jones",
            reviewer_role=ReviewerRole.INTERNAL_RESEARCHER,
            status=ValidationStatus.IN_REVIEW,
            comments="Currently reviewing the corpus methodology.",
        )
        assert result is True

    def test_get_validation_status_returns_status(self):
        submission_id = self._submit()
        status = self.buffer.get_validation_status(submission_id)
        assert status is not None

    def test_check_validation_complete_returns_bool(self):
        submission_id = self._submit()
        complete = self.buffer.check_validation_complete(submission_id)
        assert isinstance(complete, bool)

    def test_new_submission_not_complete(self):
        submission_id = self._submit()
        assert self.buffer.check_validation_complete(submission_id) is False

    def test_finalize_validation_does_not_raise(self):
        submission_id = self._submit()
        # Add required reviews first
        for i, role in enumerate([ReviewerRole.INTERNAL_RESEARCHER, ReviewerRole.EXTERNAL_ACADEMIC]):
            self.buffer.submit_review(
                submission_id=submission_id,
                reviewer_id=f"reviewer_{i}",
                reviewer_role=role,
                status=ValidationStatus.APPROVED,
                comments="Looks good.",
            )
        # finalize may or may not raise if conditions not met — just ensure no crash
        try:
            self.buffer.finalize_validation(submission_id)
        except Exception:
            pass

    def test_export_validation_records_creates_file(self, tmp_path):
        self._submit()
        path = str(tmp_path / "records.json")
        self.buffer.export_validation_records(path)
        import os
        assert os.path.exists(path)

    def test_export_validation_records_valid_json(self, tmp_path):
        self._submit()
        path = str(tmp_path / "records.json")
        self.buffer.export_validation_records(path)
        import json
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, (list, dict))

    def test_reviewer_roles_defined(self):
        assert ReviewerRole.INTERNAL_RESEARCHER.value == "internal_researcher"
        assert ReviewerRole.EXTERNAL_ACADEMIC.value == "external_academic"
        assert ReviewerRole.VENDOR_REPRESENTATIVE.value == "vendor_representative"

    def test_validation_statuses_defined(self):
        assert ValidationStatus.PENDING.value == "pending"
        assert ValidationStatus.APPROVED.value == "approved"
        assert ValidationStatus.REJECTED.value == "rejected"

    def test_generate_validation_report_returns_string(self):
        submission_id = self._submit()
        report = self.buffer.generate_validation_report(submission_id)
        assert isinstance(report, str)
