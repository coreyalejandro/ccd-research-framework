"""
Usage analytics dashboard for CCD Research Framework customers.

Tracks detection events, trends, and customer-facing metrics.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AnalyticsEvent:
    event_type: str       # "detection", "rollout_advance", "risk_flagged"
    tenant_id: str
    component_name: str
    value: float          # is_ccd, latency, or other metric
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class UsageAnalyticsDashboard:
    """
    Customer-facing analytics dashboard.

    Records detection events per tenant and generates summary reports.
    """

    def __init__(self) -> None:
        self._events: List[AnalyticsEvent] = []
        self._tenant_totals: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "ccd": 0})

    def record_event(self, event: AnalyticsEvent) -> None:
        self._events.append(event)
        if event.event_type == "detection":
            self._tenant_totals[event.tenant_id]["total"] += 1
            if event.value > 0:
                self._tenant_totals[event.tenant_id]["ccd"] += 1

    def get_tenant_summary(self, tenant_id: str) -> Dict[str, Any]:
        totals = self._tenant_totals.get(tenant_id, {"total": 0, "ccd": 0})
        total = totals["total"]
        ccd = totals["ccd"]
        return {
            "tenant_id": tenant_id,
            "total_sessions": total,
            "ccd_detections": ccd,
            "ccd_rate": round(ccd / total, 4) if total > 0 else 0.0,
            "clean_sessions": total - ccd,
        }

    def get_top_components(self, tenant_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        component_counts: Dict[str, int] = defaultdict(int)
        for event in self._events:
            if event.tenant_id == tenant_id and event.event_type == "detection" and event.value > 0:
                component_counts[event.component_name] += 1
        sorted_components = sorted(component_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"component": c, "ccd_count": n} for c, n in sorted_components[:limit]]

    def get_trend(self, tenant_id: str, bucket_hours: int = 24) -> List[Dict[str, Any]]:
        """Aggregate CCD detections into time buckets."""
        bucket_sec = bucket_hours * 3600
        buckets: Dict[int, Dict[str, int]] = defaultdict(lambda: {"total": 0, "ccd": 0})
        for event in self._events:
            if event.tenant_id == tenant_id and event.event_type == "detection":
                bucket = int(event.timestamp // bucket_sec)
                buckets[bucket]["total"] += 1
                if event.value > 0:
                    buckets[bucket]["ccd"] += 1
        return [
            {"bucket_start": b * bucket_sec, "total": v["total"], "ccd": v["ccd"]}
            for b, v in sorted(buckets.items())
        ]

    def export_json(self, tenant_id: Optional[str] = None) -> str:
        if tenant_id:
            data = {
                "summary": self.get_tenant_summary(tenant_id),
                "top_components": self.get_top_components(tenant_id),
                "trend": self.get_trend(tenant_id),
            }
        else:
            data = {
                tid: {
                    "summary": self.get_tenant_summary(tid),
                    "top_components": self.get_top_components(tid),
                }
                for tid in self._tenant_totals
            }
        return json.dumps(data, indent=2)

    def all_events_count(self) -> int:
        return len(self._events)
