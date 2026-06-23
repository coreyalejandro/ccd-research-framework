"""Tests for usage analytics dashboard"""
import json
import pytest
from src.analytics.usage_analytics import UsageAnalyticsDashboard, AnalyticsEvent


def make_event(tenant_id="t1", is_ccd=True):
    return AnalyticsEvent(
        event_type="detection",
        tenant_id=tenant_id,
        component_name="auth",
        value=1.0 if is_ccd else 0.0,
    )


class TestUsageAnalyticsDashboard:
    def setup_method(self):
        self.dash = UsageAnalyticsDashboard()

    def test_instantiates(self):
        assert self.dash is not None

    def test_record_event_increments_count(self):
        self.dash.record_event(make_event())
        assert self.dash.all_events_count() == 1

    def test_get_tenant_summary_returns_dict(self):
        self.dash.record_event(make_event("t1", is_ccd=True))
        self.dash.record_event(make_event("t1", is_ccd=False))
        summary = self.dash.get_tenant_summary("t1")
        assert isinstance(summary, dict)
        assert summary["total_sessions"] == 2

    def test_ccd_rate_calculation(self):
        for i in range(10):
            self.dash.record_event(make_event("t2", is_ccd=(i < 4)))
        summary = self.dash.get_tenant_summary("t2")
        assert summary["ccd_rate"] == pytest.approx(0.4, abs=0.01)

    def test_unknown_tenant_returns_zero_summary(self):
        summary = self.dash.get_tenant_summary("nobody")
        assert summary["total_sessions"] == 0

    def test_get_top_components_returns_list(self):
        self.dash.record_event(make_event("t3", is_ccd=True))
        top = self.dash.get_top_components("t3")
        assert isinstance(top, list)

    def test_get_trend_returns_list(self):
        self.dash.record_event(make_event("t4"))
        trend = self.dash.get_trend("t4")
        assert isinstance(trend, list)

    def test_export_json_per_tenant(self):
        self.dash.record_event(make_event("t5"))
        result = self.dash.export_json("t5")
        parsed = json.loads(result)
        assert "summary" in parsed

    def test_export_json_all_tenants(self):
        self.dash.record_event(make_event("tA"))
        self.dash.record_event(make_event("tB"))
        result = self.dash.export_json()
        parsed = json.loads(result)
        assert len(parsed) >= 2
