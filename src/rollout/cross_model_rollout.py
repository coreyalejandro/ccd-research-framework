"""
Cross-Model Rollout Infrastructure for CCD Detection

Manages staged rollout of CCD detection across multiple AI vendors/models,
with canary testing, per-model configuration, and rollback support.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class RolloutPhase(Enum):
    """Deployment phases for cross-model rollout"""
    CANARY = "canary"          # 1-5% traffic
    PILOT = "pilot"            # 10-25% traffic
    STAGED = "staged"          # 50% traffic
    FULL = "full"              # 100% traffic
    ROLLBACK = "rollback"      # emergency revert


class ModelProvider(Enum):
    """Supported AI model vendors"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    COHERE = "cohere"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    """Per-model detection configuration"""
    model_id: str
    provider: ModelProvider
    detection_threshold: float = 0.7
    enabled: bool = True
    rollout_phase: RolloutPhase = RolloutPhase.CANARY
    traffic_percentage: float = 0.05  # 5% canary by default
    custom_thresholds: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RolloutEvent:
    """Audit trail entry for rollout actions"""
    event_id: str
    timestamp: float
    model_id: str
    action: str  # "phase_advance", "rollback", "config_update", "alert"
    details: Dict[str, Any]
    triggered_by: str = "system"


@dataclass
class RolloutHealth:
    """Health snapshot for a model's rollout"""
    model_id: str
    phase: RolloutPhase
    traffic_pct: float
    sessions_processed: int
    ccd_detections: int
    false_positive_rate: float
    error_rate: float
    healthy: bool
    recommendation: str


class CrossModelRolloutManager:
    """
    Manages CCD detection deployment across multiple model providers.

    Supports canary -> pilot -> staged -> full rollout with:
    - Per-model configuration and thresholds
    - Health monitoring and auto-rollback triggers
    - Audit trail for all rollout events
    - Traffic splitting per phase
    """

    # Phase advancement thresholds
    PHASE_TRAFFIC = {
        RolloutPhase.CANARY: 0.05,
        RolloutPhase.PILOT: 0.20,
        RolloutPhase.STAGED: 0.50,
        RolloutPhase.FULL: 1.00,
        RolloutPhase.ROLLBACK: 0.00,
    }

    # Max acceptable false positive rate before auto-rollback
    MAX_FP_RATE = 0.10
    # Max acceptable error rate
    MAX_ERROR_RATE = 0.05

    def __init__(self) -> None:
        self._configs: Dict[str, ModelConfig] = {}
        self._events: List[RolloutEvent] = []
        self._stats: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def register_model(self, config: ModelConfig) -> None:
        """Register a model for CCD detection rollout."""
        self._configs[config.model_id] = config
        self._stats[config.model_id] = {
            "sessions_processed": 0,
            "ccd_detections": 0,
            "false_positives": 0,
            "errors": 0,
        }
        self._log_event(config.model_id, "model_registered", {
            "provider": config.provider.value,
            "phase": config.rollout_phase.value,
        })

    def get_config(self, model_id: str) -> Optional[ModelConfig]:
        """Return config for a registered model."""
        return self._configs.get(model_id)

    def list_models(self) -> List[str]:
        """Return all registered model IDs."""
        return list(self._configs.keys())

    # ------------------------------------------------------------------
    # Phase management
    # ------------------------------------------------------------------

    def advance_phase(self, model_id: str) -> RolloutPhase:
        """
        Advance a model to the next rollout phase if health checks pass.
        Returns the new phase.
        """
        config = self._require_config(model_id)
        health = self.check_health(model_id)

        if not health.healthy:
            raise RuntimeError(
                f"Cannot advance {model_id}: health check failed — {health.recommendation}"
            )

        phase_order = [
            RolloutPhase.CANARY,
            RolloutPhase.PILOT,
            RolloutPhase.STAGED,
            RolloutPhase.FULL,
        ]
        current_idx = phase_order.index(config.rollout_phase)
        if current_idx >= len(phase_order) - 1:
            return config.rollout_phase  # already full

        new_phase = phase_order[current_idx + 1]
        config.rollout_phase = new_phase
        config.traffic_percentage = self.PHASE_TRAFFIC[new_phase]

        self._log_event(model_id, "phase_advance", {
            "from": phase_order[current_idx].value,
            "to": new_phase.value,
            "traffic_pct": config.traffic_percentage,
        })
        return new_phase

    def rollback(self, model_id: str, reason: str = "") -> None:
        """Immediately roll back a model to canary traffic."""
        config = self._require_config(model_id)
        prev_phase = config.rollout_phase.value
        config.rollout_phase = RolloutPhase.ROLLBACK
        config.traffic_percentage = 0.0
        self._log_event(model_id, "rollback", {
            "from_phase": prev_phase,
            "reason": reason,
        })

    # ------------------------------------------------------------------
    # Detection routing
    # ------------------------------------------------------------------

    def should_detect(self, model_id: str) -> bool:
        """
        Probabilistic routing: returns True if this request should
        run CCD detection (based on traffic_percentage).
        """
        config = self._configs.get(model_id)
        if config is None or not config.enabled:
            return False
        if config.rollout_phase == RolloutPhase.ROLLBACK:
            return False
        import random
        return random.random() < config.traffic_percentage

    def record_result(
        self,
        model_id: str,
        is_ccd: bool,
        is_false_positive: bool = False,
        error: bool = False,
    ) -> None:
        """Record a detection result for health tracking."""
        stats = self._stats.get(model_id, {})
        stats["sessions_processed"] = stats.get("sessions_processed", 0) + 1
        if is_ccd:
            stats["ccd_detections"] = stats.get("ccd_detections", 0) + 1
        if is_false_positive:
            stats["false_positives"] = stats.get("false_positives", 0) + 1
        if error:
            stats["errors"] = stats.get("errors", 0) + 1
        self._stats[model_id] = stats

        # Auto-rollback if thresholds breached
        health = self.check_health(model_id)
        if not health.healthy and self._configs[model_id].rollout_phase != RolloutPhase.ROLLBACK:
            self.rollback(model_id, reason=health.recommendation)

    # ------------------------------------------------------------------
    # Health monitoring
    # ------------------------------------------------------------------

    def check_health(self, model_id: str) -> RolloutHealth:
        """Return a health snapshot for a model."""
        config = self._require_config(model_id)
        stats = self._stats.get(model_id, {})

        processed = stats.get("sessions_processed", 0)
        ccd = stats.get("ccd_detections", 0)
        fp = stats.get("false_positives", 0)
        errors = stats.get("errors", 0)

        fp_rate = fp / max(processed, 1)
        error_rate = errors / max(processed, 1)

        healthy = (fp_rate <= self.MAX_FP_RATE) and (error_rate <= self.MAX_ERROR_RATE)
        recommendation = "OK"
        if fp_rate > self.MAX_FP_RATE:
            recommendation = f"FP rate {fp_rate:.1%} exceeds threshold {self.MAX_FP_RATE:.1%} — consider rollback"
        elif error_rate > self.MAX_ERROR_RATE:
            recommendation = f"Error rate {error_rate:.1%} exceeds threshold {self.MAX_ERROR_RATE:.1%} — investigate"

        return RolloutHealth(
            model_id=model_id,
            phase=config.rollout_phase,
            traffic_pct=config.traffic_percentage,
            sessions_processed=processed,
            ccd_detections=ccd,
            false_positive_rate=fp_rate,
            error_rate=error_rate,
            healthy=healthy,
            recommendation=recommendation,
        )

    def get_all_health(self) -> List[RolloutHealth]:
        """Return health snapshots for all registered models."""
        return [self.check_health(mid) for mid in self._configs]

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------

    def get_audit_trail(self, model_id: Optional[str] = None) -> List[RolloutEvent]:
        """Return audit trail, optionally filtered by model."""
        if model_id:
            return [e for e in self._events if e.model_id == model_id]
        return list(self._events)

    def export_config(self) -> str:
        """Export all model configs as JSON string."""
        data = {}
        for mid, cfg in self._configs.items():
            data[mid] = {
                "provider": cfg.provider.value,
                "phase": cfg.rollout_phase.value,
                "traffic_pct": cfg.traffic_percentage,
                "threshold": cfg.detection_threshold,
                "enabled": cfg.enabled,
            }
        return json.dumps(data, indent=2)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require_config(self, model_id: str) -> ModelConfig:
        config = self._configs.get(model_id)
        if config is None:
            raise KeyError(f"Model '{model_id}' not registered")
        return config

    def _log_event(self, model_id: str, action: str, details: Dict[str, Any]) -> None:
        self._events.append(RolloutEvent(
            event_id=str(uuid.uuid4())[:8],
            timestamp=time.time(),
            model_id=model_id,
            action=action,
            details=details,
        ))
