"""Tests for vendor transparency dashboard"""
import pytest
from src.dashboard.vendor_transparency import (
    VendorTransparencyDashboard, FailureType, DashboardData
)


class TestVendorTransparencyDashboard:
    def setup_method(self):
        self.dashboard = VendorTransparencyDashboard()

    def test_instantiates(self):
        assert self.dashboard is not None

    def test_record_interaction_does_not_raise(self):
        self.dashboard.record_interaction(
            session_id="sess_001",
            component_name="auth_module",
            failure_type=FailureType.CCD,
            admission_type="sycophantic",
            severity_weight=0.8,
        )

    def test_record_multiple_interactions(self):
        for i in range(5):
            self.dashboard.record_interaction(
                session_id=f"sess_{i:03d}",
                component_name="cache_layer",
                failure_type=FailureType.CCD,
                admission_type="specific",
                severity_weight=0.7,
            )
        data = self.dashboard.generate_dashboard_data()
        assert data.total_interactions >= 5

    def test_generate_dashboard_data_returns_dashboard_data(self):
        self.dashboard.record_interaction(
            session_id="s1",
            component_name="rate_limiter",
            failure_type=FailureType.HALLUCINATION,
            admission_type="sycophantic",
            severity_weight=0.5,
        )
        data = self.dashboard.generate_dashboard_data()
        assert isinstance(data, DashboardData)

    def test_dashboard_data_has_required_fields(self):
        data = self.dashboard.generate_dashboard_data()
        assert hasattr(data, "timestamp")
        assert hasattr(data, "time_period")
        assert hasattr(data, "total_interactions")
        assert hasattr(data, "failure_breakdown")
        assert hasattr(data, "severity_distribution")
        assert hasattr(data, "top_components")
        assert hasattr(data, "trend_data")
        assert hasattr(data, "customer_impact")

    def test_failure_type_values(self):
        assert FailureType.CCD.value == "construct_confidence_deception"
        assert FailureType.HALLUCINATION.value == "hallucination"
        assert FailureType.FUNCTIONAL.value == "functional"

    def test_generate_html_dashboard_returns_string(self):
        html = self.dashboard.generate_html_dashboard()
        assert isinstance(html, str)
        assert len(html) > 0

    def test_generate_html_dashboard_contains_html(self):
        html = self.dashboard.generate_html_dashboard()
        assert "<" in html

    def test_export_dashboard_json_returns_string(self):
        result = self.dashboard.export_dashboard_json()
        assert isinstance(result, str)

    def test_export_dashboard_json_is_valid(self):
        import json
        result = self.dashboard.export_dashboard_json()
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_get_top_components_returns_list(self):
        self.dashboard.record_interaction("s1", "auth", FailureType.CCD, "sycophantic", 0.8)
        self.dashboard.record_interaction("s2", "cache", FailureType.CCD, "specific", 0.7)
        self.dashboard.record_interaction("s3", "auth", FailureType.CCD, "sycophantic", 0.9)
        top = self.dashboard.get_top_components(limit=2)
        assert isinstance(top, list)
        assert len(top) <= 2

    def test_record_with_support_ticket(self):
        self.dashboard.record_interaction(
            session_id="s1",
            component_name="auth",
            failure_type=FailureType.CCD,
            admission_type="sycophantic",
            severity_weight=0.8,
            support_ticket_id="TKT-001",
        )
        data = self.dashboard.generate_dashboard_data()
        assert data.total_interactions >= 1
