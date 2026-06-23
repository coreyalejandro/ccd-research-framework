"""
Benchmark CCD detector against hallucination detection baselines.

Provides BenchmarkSuite that runs detection on labeled datasets and
reports precision, recall, F1, and latency against configurable baselines.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class BenchmarkResult:
    suite_name: str
    detector_name: str
    total_sessions: int
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    f1: float
    avg_latency_ms: float
    p95_latency_ms: float
    notes: str = ""

    @property
    def accuracy(self) -> float:
        total = self.tp + self.fp + self.tn + self.fn
        return (self.tp + self.tn) / total if total > 0 else 0.0


class HallucinationBenchmarkSuite:
    """
    Benchmark CCD detector against labeled CCD/non-CCD session datasets.

    Usage:
        suite = HallucinationBenchmarkSuite()
        result = suite.run(
            detector_fn=lambda session: detector.detect(session["interactions"], session["component"]),
            labeled_sessions=[{"is_ccd": True, "interactions": [...], "component": "auth"}, ...],
            suite_name="internal_v1",
        )
    """

    def __init__(self, detection_threshold: float = 0.7) -> None:
        self.detection_threshold = detection_threshold
        self.results: List[BenchmarkResult] = []

    def run(
        self,
        detector_fn: Callable[[Dict[str, Any]], Any],
        labeled_sessions: List[Dict[str, Any]],
        suite_name: str = "default",
        detector_name: str = "PROACTIVE",
    ) -> BenchmarkResult:
        """
        Run benchmark. detector_fn must return an object with `.is_ccd` and `.confidence`.
        labeled_sessions must have `is_ccd: bool`.
        """
        tp = fp = tn = fn = 0
        latencies: List[float] = []

        for session in labeled_sessions:
            ground_truth: bool = bool(session.get("is_ccd", False))
            t0 = time.perf_counter()
            try:
                result = detector_fn(session)
                predicted = result.is_ccd
            except Exception:
                predicted = False
            latency_ms = (time.perf_counter() - t0) * 1000
            latencies.append(latency_ms)

            if predicted and ground_truth:
                tp += 1
            elif predicted and not ground_truth:
                fp += 1
            elif not predicted and not ground_truth:
                tn += 1
            else:
                fn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        sorted_lat = sorted(latencies)
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        p95_idx = max(0, int(len(sorted_lat) * 0.95) - 1)
        p95_lat = sorted_lat[p95_idx] if sorted_lat else 0.0

        result_obj = BenchmarkResult(
            suite_name=suite_name,
            detector_name=detector_name,
            total_sessions=len(labeled_sessions),
            tp=tp, fp=fp, tn=tn, fn=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            avg_latency_ms=round(avg_lat, 2),
            p95_latency_ms=round(p95_lat, 2),
        )
        self.results.append(result_obj)
        return result_obj

    def compare(self, result_a: BenchmarkResult, result_b: BenchmarkResult) -> Dict[str, float]:
        """Return delta metrics (A minus B)."""
        return {
            "precision_delta": result_a.precision - result_b.precision,
            "recall_delta": result_a.recall - result_b.recall,
            "f1_delta": result_a.f1 - result_b.f1,
            "latency_delta_ms": result_a.avg_latency_ms - result_b.avg_latency_ms,
        }

    def summary_report(self) -> str:
        lines = ["CCD Benchmark Summary", "=" * 40]
        for r in self.results:
            lines += [
                f"Suite: {r.suite_name} | Detector: {r.detector_name}",
                f"  Sessions: {r.total_sessions} | TP={r.tp} FP={r.fp} TN={r.tn} FN={r.fn}",
                f"  Precision={r.precision:.3f} Recall={r.recall:.3f} F1={r.f1:.3f}",
                f"  Avg latency={r.avg_latency_ms:.1f}ms P95={r.p95_latency_ms:.1f}ms",
                "",
            ]
        return "\n".join(lines)
