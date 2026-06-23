"""
Multi-tenancy support for CCD Research Framework.

Isolates detection state, dashboards, and configuration per tenant.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TenantConfig:
    tenant_id: str
    name: str
    detection_threshold: float = 0.7
    max_sessions_per_month: int = 10_000
    enabled_features: List[str] = field(default_factory=lambda: ["detection", "dashboard", "validation"])
    metadata: Dict[str, Any] = field(default_factory=dict)


class TenantRegistry:
    """
    Registry and isolation layer for multi-tenant deployments.

    Each tenant gets isolated detection state and configuration.
    """

    def __init__(self) -> None:
        self._tenants: Dict[str, TenantConfig] = {}
        self._session_counts: Dict[str, int] = {}

    def register_tenant(
        self,
        name: str,
        detection_threshold: float = 0.7,
        max_sessions: int = 10_000,
        tenant_id: Optional[str] = None,
    ) -> TenantConfig:
        """Register a new tenant. Returns TenantConfig."""
        tid = tenant_id or str(uuid.uuid4())[:8]
        config = TenantConfig(
            tenant_id=tid,
            name=name,
            detection_threshold=detection_threshold,
            max_sessions_per_month=max_sessions,
        )
        self._tenants[tid] = config
        self._session_counts[tid] = 0
        return config

    def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        return self._tenants.get(tenant_id)

    def update_tenant(self, tenant_id: str, **kwargs: Any) -> bool:
        """Update mutable config fields. Returns False if tenant not found."""
        config = self._tenants.get(tenant_id)
        if config is None:
            return False
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return True

    def deregister_tenant(self, tenant_id: str) -> bool:
        """Remove a tenant and all associated state."""
        if tenant_id not in self._tenants:
            return False
        del self._tenants[tenant_id]
        self._session_counts.pop(tenant_id, None)
        return True

    def record_session(self, tenant_id: str) -> bool:
        """
        Increment session counter. Returns False if quota exceeded.
        """
        config = self._tenants.get(tenant_id)
        if config is None:
            return False
        count = self._session_counts.get(tenant_id, 0)
        if count >= config.max_sessions_per_month:
            return False
        self._session_counts[tenant_id] = count + 1
        return True

    def get_usage(self, tenant_id: str) -> Dict[str, Any]:
        config = self._tenants.get(tenant_id)
        if config is None:
            return {}
        used = self._session_counts.get(tenant_id, 0)
        return {
            "tenant_id": tenant_id,
            "name": config.name,
            "sessions_used": used,
            "sessions_quota": config.max_sessions_per_month,
            "quota_pct": round(used / config.max_sessions_per_month * 100, 1),
        }

    def list_tenants(self) -> List[TenantConfig]:
        return list(self._tenants.values())
