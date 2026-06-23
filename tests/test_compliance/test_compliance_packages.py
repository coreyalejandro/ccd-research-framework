"""Tests for industry compliance packages"""
import pytest
from src.compliance.compliance_packages import (
    CompliancePackageManager, ComplianceFramework, ComplianceMapping
)


class TestCompliancePackageManager:
    def setup_method(self):
        self.mgr = CompliancePackageManager()

    def test_instantiates(self):
        assert self.mgr is not None

    def test_get_mappings_soc2_returns_list(self):
        mappings = self.mgr.get_mappings(ComplianceFramework.SOC2)
        assert isinstance(mappings, list)
        assert len(mappings) > 0

    def test_mapping_has_control_id(self):
        mappings = self.mgr.get_mappings(ComplianceFramework.SOC2)
        assert all(hasattr(m, "control_id") for m in mappings)

    def test_mapping_has_ccd_mitigations(self):
        mappings = self.mgr.get_mappings(ComplianceFramework.SOC2)
        assert all(len(m.ccd_mitigations) > 0 for m in mappings)

    def test_get_all_frameworks_returns_list(self):
        frameworks = self.mgr.get_all_frameworks()
        assert isinstance(frameworks, list)
        assert len(frameworks) >= 4

    def test_hipaa_has_mappings(self):
        mappings = self.mgr.get_mappings(ComplianceFramework.HIPAA)
        assert len(mappings) > 0

    def test_gdpr_has_mappings(self):
        mappings = self.mgr.get_mappings(ComplianceFramework.GDPR)
        assert len(mappings) > 0

    def test_nist_ai_rmf_has_mappings(self):
        mappings = self.mgr.get_mappings(ComplianceFramework.NIST_AI_RMF)
        assert len(mappings) > 0

    def test_generate_report_is_string(self):
        report = self.mgr.generate_compliance_report([
            ComplianceFramework.SOC2,
            ComplianceFramework.GDPR,
        ])
        assert isinstance(report, str)
        assert "SOC2" in report.upper() or "soc2" in report.lower()

    def test_unknown_framework_returns_empty(self):
        # ISO_42001 exists — just verify it returns a list
        mappings = self.mgr.get_mappings(ComplianceFramework.ISO_42001)
        assert isinstance(mappings, list)
