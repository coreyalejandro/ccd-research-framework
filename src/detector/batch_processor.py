"""
Batch processing mode for offline CCD detection.

Supports CSV/JSON corpus files and concurrent processing.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class BatchJob:
    job_id: str
    total: int
    processed: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    @property
    def progress(self) -> float:
        return self.processed / self.total if self.total > 0 else 0.0

    @property
    def is_complete(self) -> bool:
        return self.processed >= self.total


class BatchProcessor:
    """
    Offline batch processor for CCD detection over large corpora.

    Usage:
        processor = BatchProcessor(detector_fn=my_detect)
        job = processor.process_sessions(sessions)
        report = processor.export_results(job)
    """

    def __init__(self, detector_fn: Optional[Callable] = None) -> None:
        self._detector_fn = detector_fn
        self._jobs: Dict[str, BatchJob] = {}
        self._job_counter = 0

    def process_sessions(
        self,
        sessions: List[Dict[str, Any]],
        job_id: Optional[str] = None,
        batch_size: int = 50,
    ) -> BatchJob:
        """
        Process a list of sessions in batches.
        Each session must have 'interactions' and 'component_name' keys.
        """
        if job_id is None:
            self._job_counter += 1
            job_id = f"batch_{self._job_counter}"

        job = BatchJob(job_id=job_id, total=len(sessions))
        self._jobs[job_id] = job

        for i in range(0, len(sessions), batch_size):
            batch = sessions[i : i + batch_size]
            for session in batch:
                try:
                    if self._detector_fn is not None:
                        result = self._detector_fn(session)
                        job.results.append({
                            "session_id": session.get("session_id", f"s{job.processed}"),
                            "is_ccd": result.is_ccd,
                            "confidence": result.confidence,
                        })
                    else:
                        job.results.append({
                            "session_id": session.get("session_id", f"s{job.processed}"),
                            "is_ccd": False,
                            "confidence": 0.0,
                            "note": "no detector configured",
                        })
                except Exception as exc:
                    job.errors.append({
                        "session_id": session.get("session_id"),
                        "error": str(exc),
                    })
                job.processed += 1

        job.completed_at = time.time()
        return job

    def load_corpus_json(self, path: str) -> List[Dict[str, Any]]:
        """Load a JSON corpus file. Accepts list or {"sessions": [...]} shape."""
        with open(path) as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "sessions" in data:
            return data["sessions"]
        raise ValueError(f"Unrecognized corpus shape in {path}")

    def export_results(self, job: BatchJob) -> str:
        """Export job results as a JSON string."""
        return json.dumps({
            "job_id": job.job_id,
            "total": job.total,
            "processed": job.processed,
            "ccd_positive": sum(1 for r in job.results if r.get("is_ccd")),
            "errors": len(job.errors),
            "duration_s": (job.completed_at or time.time()) - job.started_at,
            "results": job.results[:100],  # cap export size
        }, indent=2)

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        return self._jobs.get(job_id)
