"""
Incremental learning for the CCD detector.

Allows the detector to update feature weights from new labeled sessions
without full retraining — important for production deployments where
CCD patterns may drift over time.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LearningUpdate:
    update_id: str
    sessions_seen: int
    weights_before: Dict[str, float]
    weights_after: Dict[str, float]
    timestamp: float = field(default_factory=time.time)
    drift_detected: bool = False


class IncrementalCCDLearner:
    """
    Online / incremental learning for CCD feature weights.

    Uses exponential moving average (EMA) to blend new signal with existing weights.
    """

    def __init__(self, alpha: float = 0.1) -> None:
        """alpha: EMA learning rate (0 = no update, 1 = full replacement)."""
        self.alpha = alpha
        self.weights: Dict[str, float] = {
            "f1_cross_session_persistence": 0.30,
            "f2_artifact_divergence": 0.35,
            "f3_admission_delta": 0.20,
            "f4_deference_escalation": 0.15,
        }
        self.updates: List[LearningUpdate] = []
        self._total_sessions = 0
        self._update_counter = 0

    def update(self, sessions: List[Dict[str, Any]]) -> LearningUpdate:
        """
        Update weights from a batch of labeled sessions.
        Sessions need 'is_ccd' bool and f1/f2/f3/f4 float fields.
        """
        ccd = [s for s in sessions if s.get("is_ccd")]
        ctrl = [s for s in sessions if not s.get("is_ccd")]

        weights_before = dict(self.weights)

        if ccd and ctrl:
            feat_map = {
                "f1": "f1_cross_session_persistence",
                "f2": "f2_artifact_divergence",
                "f3": "f3_admission_delta",
                "f4": "f4_deference_escalation",
            }
            for short, full in feat_map.items():
                ccd_mean = sum(s.get(short, 0.0) for s in ccd) / len(ccd)
                ctrl_mean = sum(s.get(short, 0.0) for s in ctrl) / len(ctrl)
                target = max(0.05, min(0.60, ccd_mean - ctrl_mean + self.weights[full]))
                self.weights[full] = (1 - self.alpha) * self.weights[full] + self.alpha * target

            # Normalize
            total = sum(self.weights.values())
            if total > 0:
                self.weights = {k: round(v / total, 4) for k, v in self.weights.items()}

        self._total_sessions += len(sessions)
        self._update_counter += 1

        # Detect drift: if any weight changed by > 0.1
        drift = any(
            abs(self.weights[k] - weights_before[k]) > 0.1
            for k in self.weights
        )

        upd = LearningUpdate(
            update_id=f"upd_{self._update_counter}",
            sessions_seen=len(sessions),
            weights_before=weights_before,
            weights_after=dict(self.weights),
            drift_detected=drift,
        )
        self.updates.append(upd)
        return upd

    def get_weight_history(self) -> List[Dict[str, Any]]:
        return [
            {"update_id": u.update_id, "sessions": u.sessions_seen,
             "weights": u.weights_after, "drift": u.drift_detected}
            for u in self.updates
        ]

    def total_sessions_seen(self) -> int:
        return self._total_sessions
