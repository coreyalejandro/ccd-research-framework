"""
Customer Success Metrics Dashboard for CCD Research Framework.

Tracks adoption, time-to-value, and satisfaction metrics per tenant.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CustomerSuccessRecord:
    tenant_id: str
    onboarded_at: float
    first_detection_at: Optional[float]
    total_detections: int
    false_positives_reported: int
    csat_score: Optional[float]  # 0.0–1.0
    notes: str = ""

    @property
    def time_to_first_detection_hours(self) -> Optional[float]:
        if self.first_detection_at is None:
            return None
        return (self.first_detection_at - self.onboarded_at) / 3600

    @property
    def fp_rate(self) -> float:
        if self.total_detections == 0:
            return 0.0
        return self.false_positives_reported / self.total_detections


class CustomerSuccessDashboard:
    """
    Tracks per-tenant success metrics: adoption speed, detection volume,
    reported false positives, and satisfaction scores.
    """

    def __init__(self) -> None:
        self._records: Dict[str, CustomerSuccessRecord] = {}

    def onboard(self, tenant_id: str) -> CustomerSuccessRecord:
        record = CustomerSuccessRecord(
            tenant_id=tenant_id,
            onboarded_at=time.time(),
            first_detection_at=None,
            total_detections=0,
            false_positives_reported=0,
            csat_score=None,
        )
        self._records[tenant_id] = record
        return record

    def record_detection(self, tenant_id: str) -> None:
        record = self._records.get(tenant_id)
        if record is None:
            return
        record.total_detections += 1
        if record.first_detection_at is None:
            record.first_detection_at = time.time()

    def report_false_positive(self, tenant_id: str) -> None:
        record = self._records.get(tenant_id)
        if record:
            record.false_positives_reported += 1

    def record_csat(self, tenant_id: str, score: float) -> None:
        record = self._records.get(tenant_id)
        if record:
            record.csat_score = max(0.0, min(1.0, score))

    def get_record(self, tenant_id: str) -> Optional[CustomerSuccessRecord]:
        return self._records.get(tenant_id)

    def get_portfolio_summary(self) -> Dict[str, Any]:
        records = list(self._records.values())
        if not records:
            return {"tenants": 0, "avg_csat": None, "avg_fp_rate": 0.0}
        csat_scores = [r.csat_score for r in records if r.csat_score is not None]
        return {
            "tenants": len(records),
            "avg_csat": round(sum(csat_scores) / len(csat_scores), 3) if csat_scores else None,
            "avg_fp_rate": round(sum(r.fp_rate for r in records) / len(records), 4),
            "total_detections": sum(r.total_detections for r in records),
        }
