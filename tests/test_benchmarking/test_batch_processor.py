"""Tests for batch processing mode"""
import json
import pytest
from src.detector.batch_processor import BatchProcessor, BatchJob


class FakeResult:
    def __init__(self):
        self.is_ccd = True
        self.confidence = 0.85


class TestBatchProcessor:
    def setup_method(self):
        self.processor = BatchProcessor(detector_fn=lambda s: FakeResult())

    def test_instantiates(self):
        assert self.processor is not None

    def test_process_sessions_returns_batch_job(self):
        sessions = [{"session_id": f"s{i}", "interactions": [], "component_name": "auth"} for i in range(5)]
        job = self.processor.process_sessions(sessions)
        assert isinstance(job, BatchJob)

    def test_job_is_complete_after_processing(self):
        sessions = [{"session_id": "s1", "interactions": [], "component_name": "x"}]
        job = self.processor.process_sessions(sessions)
        assert job.is_complete

    def test_processed_count_matches_input(self):
        sessions = [{"session_id": f"s{i}", "interactions": [], "component_name": "x"} for i in range(8)]
        job = self.processor.process_sessions(sessions)
        assert job.processed == 8

    def test_results_populated(self):
        sessions = [{"session_id": "s1", "interactions": [], "component_name": "x"}]
        job = self.processor.process_sessions(sessions)
        assert len(job.results) == 1
        assert "is_ccd" in job.results[0]

    def test_export_results_is_json_string(self):
        sessions = [{"session_id": "s1", "interactions": [], "component_name": "x"}]
        job = self.processor.process_sessions(sessions)
        exported = self.processor.export_results(job)
        parsed = json.loads(exported)
        assert "job_id" in parsed

    def test_no_detector_fn_returns_results(self):
        processor = BatchProcessor()
        sessions = [{"session_id": "s1", "interactions": [], "component_name": "x"}]
        job = processor.process_sessions(sessions)
        assert len(job.results) == 1

    def test_get_job_by_id(self):
        sessions = [{"session_id": "s1", "interactions": [], "component_name": "x"}]
        job = self.processor.process_sessions(sessions, job_id="test_job")
        retrieved = self.processor.get_job("test_job")
        assert retrieved is job

    def test_get_job_unknown_returns_none(self):
        assert self.processor.get_job("nonexistent") is None

    def test_progress_property(self):
        job = BatchJob(job_id="x", total=10, processed=5)
        assert job.progress == 0.5
