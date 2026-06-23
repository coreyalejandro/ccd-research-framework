"""
Cross-model transfer learning protocol for CCD detection.

Calibrates PROACTIVE detector feature weights from one model's
session corpus to another, preserving discriminative power across
model families (Claude, GPT-4, Gemini, etc.).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TransferConfig:
    source_model: str
    target_model: str
    source_weights: Dict[str, float]
    calibration_sessions: int
    calibration_timestamp: float = field(default_factory=time.time)
    performance_delta: Optional[Dict[str, float]] = None


class TransferLearningProtocol:
    """
    Protocol for transferring CCD detection calibration across model families.

    Approach:
    1. Fit feature weights on source model corpus (train)
    2. Evaluate on target model corpus before calibration
    3. Fine-tune weights using labeled target model sessions
    4. Report performance delta (pre vs. post calibration)
    """

    DEFAULT_WEIGHTS = {
        "f1_cross_session_persistence": 0.30,
        "f2_artifact_divergence": 0.35,
        "f3_admission_delta": 0.20,
        "f4_deference_escalation": 0.15,
    }

    def __init__(self) -> None:
        self._configs: Dict[str, TransferConfig] = {}

    def calibrate(
        self,
        source_model: str,
        target_model: str,
        target_sessions: List[Dict[str, Any]],
        source_weights: Optional[Dict[str, float]] = None,
    ) -> TransferConfig:
        """
        Calibrate feature weights for target_model using labeled sessions.
        Sessions must have 'is_ccd', 'f1', 'f2', 'f3', 'f4' float fields.
        """
        weights = dict(source_weights or self.DEFAULT_WEIGHTS)

        # Simple gradient-free calibration: weight each feature by
        # its mean difference between CCD-positive and control groups.
        ccd = [s for s in target_sessions if s.get("is_ccd")]
        ctrl = [s for s in target_sessions if not s.get("is_ccd")]

        if ccd and ctrl:
            for feat in ("f1", "f2", "f3", "f4"):
                feat_key = {
                    "f1": "f1_cross_session_persistence",
                    "f2": "f2_artifact_divergence",
                    "f3": "f3_admission_delta",
                    "f4": "f4_deference_escalation",
                }[feat]
                ccd_mean = sum(s.get(feat, 0.0) for s in ccd) / len(ccd)
                ctrl_mean = sum(s.get(feat, 0.0) for s in ctrl) / len(ctrl)
                diff = ccd_mean - ctrl_mean
                # Increase weight proportionally to discriminative power
                weights[feat_key] = max(0.05, min(0.60, diff + weights[feat_key]))

            # Normalize
            total = sum(weights.values())
            if total > 0:
                weights = {k: round(v / total, 4) for k, v in weights.items()}

        config = TransferConfig(
            source_model=source_model,
            target_model=target_model,
            source_weights=weights,
            calibration_sessions=len(target_sessions),
        )
        key = f"{source_model}->{target_model}"
        self._configs[key] = config
        return config

    def get_config(self, source_model: str, target_model: str) -> Optional[TransferConfig]:
        return self._configs.get(f"{source_model}->{target_model}")

    def export_configs(self) -> str:
        """Export all calibration configs as JSON."""
        return json.dumps(
            {k: {"source": v.source_model, "target": v.target_model,
                 "weights": v.source_weights, "sessions": v.calibration_sessions}
             for k, v in self._configs.items()},
            indent=2
        )
