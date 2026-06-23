"""Tests for customer success metrics dashboard"""
import pytest
from src.analytics.customer_success import CustomerSuccessDashboard, CustomerSuccessRecord


class TestCustomerSuccessDashboard:
    def setup_method(self):
        self.dash = CustomerSuccessDashboard()

    def test_instantiates(self):
        assert self.dash is not None

    def test_onboard_returns_record(self):
        record = self.dash.onboard("tenant_001")
        assert isinstance(record, CustomerSuccessRecord)

    def test_record_has_tenant_id(self):
        record = self.dash.onboard("tenant_001")
        assert record.tenant_id == "tenant_001"

    def test_record_detection_increments_count(self):
        self.dash.onboard("t1")
        self.dash.record_detection("t1")
        self.dash.record_detection("t1")
        record = self.dash.get_record("t1")
        assert record.total_detections == 2

    def test_first_detection_sets_timestamp(self):
        self.dash.onboard("t2")
        self.dash.record_detection("t2")
        record = self.dash.get_record("t2")
        assert record.first_detection_at is not None

    def test_time_to_first_detection_is_positive(self):
        self.dash.onboard("t3")
        self.dash.record_detection("t3")
        record = self.dash.get_record("t3")
        assert record.time_to_first_detection_hours is not None
        assert record.time_to_first_detection_hours >= 0

    def test_report_false_positive(self):
        self.dash.onboard("t4")
        self.dash.record_detection("t4")
        self.dash.record_detection("t4")
        self.dash.report_false_positive("t4")
        record = self.dash.get_record("t4")
        assert record.false_positives_reported == 1
        assert record.fp_rate == 0.5

    def test_record_csat(self):
        self.dash.onboard("t5")
        self.dash.record_csat("t5", 0.95)
        record = self.dash.get_record("t5")
        assert record.csat_score == pytest.approx(0.95)

    def test_csat_clamped_to_one(self):
        self.dash.onboard("t6")
        self.dash.record_csat("t6", 1.5)
        assert self.dash.get_record("t6").csat_score == 1.0

    def test_portfolio_summary_returns_dict(self):
        self.dash.onboard("tA")
        summary = self.dash.get_portfolio_summary()
        assert "tenants" in summary

    def test_get_unknown_tenant_returns_none(self):
        assert self.dash.get_record("ghost") is None
