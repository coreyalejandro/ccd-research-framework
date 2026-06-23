"""
Sensitivity analysis for PROACTIVE detector threshold parameters.

Sweeps the detection_threshold parameter and reports how precision,
recall, and F1 change across the sweep range.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ThresholdResult:
    threshold: float
    precision: float
    recall: float
    f1: float
    ccd_detections: int
    total_sessions: int

    @property
    def false_positive_rate(self) -> float:
        """Approximated from precision: FPR = 1 - precision (simplified)."""
        return round(1.0 - self.precision, 4)


class SensitivityAnalyzer:
    """
    Sweep detection thresholds to characterize detector sensitivity.

    Usage:
        analyzer = SensitivityAnalyzer()
        results = analyzer.sweep_threshold(
            detector_fn=lambda session, threshold: detect(session, threshold),
            labeled_sessions=sessions,
            thresholds=[0.5, 0.6, 0.7, 0.8, 0.9],
        )
        optimal = analyzer.find_optimal_threshold(results)
    """

    def sweep_threshold(
        self,
        detector_fn: Callable[[Dict[str, Any], float], Any],
        labeled_sessions: List[Dict[str, Any]],
        thresholds: Optional[List[float]] = None,
    ) -> List[ThresholdResult]:
        """
        Run detection at each threshold level. detector_fn receives
        (session, threshold) and must return an object with `.is_ccd`.
        """
        if thresholds is None:
            thresholds = [round(t * 0.1, 1) for t in range(3, 10)]  # 0.3..0.9

        results = []
        for threshold in thresholds:
            tp = fp = tn = fn = 0
            for session in labeled_sessions:
                ground_truth = bool(session.get("is_ccd", False))
                try:
                    result = detector_fn(session, threshold)
                    predicted = result.is_ccd
                except Exception:
                    predicted = False

                if predicted and ground_truth:
                    tp += 1
                elif predicted and not ground_truth:
                    fp += 1
                elif not predicted and not ground_truth:
                    tn += 1
                else:
                    fn += 1

            precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

            results.append(ThresholdResult(
                threshold=threshold,
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1=round(f1, 4),
                ccd_detections=tp + fp,
                total_sessions=len(labeled_sessions),
            ))

        return results

    def find_optimal_threshold(
        self,
        results: List[ThresholdResult],
        metric: str = "f1",
    ) -> ThresholdResult:
        """Return the threshold with the highest value for the given metric."""
        if not results:
            raise ValueError("results list is empty")
        return max(results, key=lambda r: getattr(r, metric))

    def generate_report(self, results: List[ThresholdResult]) -> str:
        lines = ["Threshold Sensitivity Analysis", "=" * 40,
                 f"{'Threshold':>10} {'Precision':>10} {'Recall':>8} {'F1':>8} {'CCD Det':>8}"]
        for r in results:
            lines.append(
                f"{r.threshold:>10.2f} {r.precision:>10.4f} {r.recall:>8.4f} {r.f1:>8.4f} {r.ccd_detections:>8}"
            )
        return "\n".join(lines)
