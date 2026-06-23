"""Tests for multi-tenancy module"""
import pytest
from src.tenancy.multi_tenant import TenantRegistry, TenantConfig


class TestTenantRegistry:
    def setup_method(self):
        self.registry = TenantRegistry()

    def test_instantiates(self):
        assert self.registry is not None

    def test_register_tenant_returns_config(self):
        config = self.registry.register_tenant("AcmeCorp")
        assert isinstance(config, TenantConfig)
        assert config.name == "AcmeCorp"

    def test_tenant_gets_unique_id(self):
        a = self.registry.register_tenant("A")
        b = self.registry.register_tenant("B")
        assert a.tenant_id != b.tenant_id

    def test_get_tenant_returns_config(self):
        config = self.registry.register_tenant("ACME")
        retrieved = self.registry.get_tenant(config.tenant_id)
        assert retrieved is config

    def test_get_unknown_tenant_returns_none(self):
        assert self.registry.get_tenant("nonexistent") is None

    def test_update_tenant_threshold(self):
        config = self.registry.register_tenant("X")
        result = self.registry.update_tenant(config.tenant_id, detection_threshold=0.85)
        assert result is True
        assert self.registry.get_tenant(config.tenant_id).detection_threshold == 0.85

    def test_update_unknown_tenant_returns_false(self):
        assert self.registry.update_tenant("ghost", detection_threshold=0.5) is False

    def test_deregister_removes_tenant(self):
        config = self.registry.register_tenant("Del")
        self.registry.deregister_tenant(config.tenant_id)
        assert self.registry.get_tenant(config.tenant_id) is None

    def test_deregister_unknown_returns_false(self):
        assert self.registry.deregister_tenant("ghost") is False

    def test_record_session_increments_usage(self):
        config = self.registry.register_tenant("Y")
        self.registry.record_session(config.tenant_id)
        usage = self.registry.get_usage(config.tenant_id)
        assert usage["sessions_used"] == 1

    def test_quota_exceeded_returns_false(self):
        config = self.registry.register_tenant("Small", max_sessions=2)
        self.registry.record_session(config.tenant_id)
        self.registry.record_session(config.tenant_id)
        result = self.registry.record_session(config.tenant_id)
        assert result is False

    def test_list_tenants_returns_list(self):
        self.registry.register_tenant("A")
        self.registry.register_tenant("B")
        tenants = self.registry.list_tenants()
        assert len(tenants) >= 2
