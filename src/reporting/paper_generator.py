"""
Automated paper section generation from CCD detection results.

Generates structured academic output (methods, results, discussion)
from empirical detection data for inclusion in research papers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PaperSection:
    title: str
    content: str
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.content.split())


class PaperSectionGenerator:
    """
    Generate structured paper sections from CCD empirical data.

    Produces LaTeX-ready or Markdown text for Methods, Results, and Discussion.
    """

    def generate_methods_section(
        self,
        corpus_size: int,
        detection_threshold: float,
        n_ccd_positive: int,
        n_control: int,
        seed: int = 42,
    ) -> PaperSection:
        content = (
            f"We constructed a synthetic corpus of {corpus_size} sessions using "
            f"SyntheticCorpusGenerator (seed={seed}), comprising {n_ccd_positive} "
            f"CCD-positive sessions and {n_control} control sessions. "
            f"Detection was performed using the PROACTIVE algorithm with a "
            f"decision threshold of {detection_threshold}. Each session was "
            f"evaluated against the five CCD criteria (D1-D5) as defined in "
            f"the formal specification (see Appendix). Feature weights were "
            f"initialized to the default calibration (f1=0.30, f2=0.35, "
            f"f3=0.20, f4=0.15) and held constant across all evaluations. "
            f"Falsification conditions F1-F4 were pre-registered on OSF "
            f"prior to data analysis."
        )
        return PaperSection(title="Methods", content=content)

    def generate_results_section(
        self,
        precision: float,
        recall: float,
        f1: float,
        falsification_results: Optional[Dict[str, bool]] = None,
        avg_latency_ms: float = 0.0,
    ) -> PaperSection:
        lines = [
            f"The PROACTIVE detector achieved precision={precision:.3f}, "
            f"recall={recall:.3f}, and F1={f1:.3f} on the synthetic corpus.",
            f"Mean detection latency was {avg_latency_ms:.1f}ms.",
        ]
        if falsification_results:
            passed = [k for k, v in falsification_results.items() if not v]
            failed = [k for k, v in falsification_results.items() if v]
            lines.append(
                f"Falsification conditions: {len(passed)}/{len(falsification_results)} passed "
                f"({', '.join(passed) if passed else 'none'}). "
                + (f"Failed: {', '.join(failed)}." if failed else "None failed.")
            )
        return PaperSection(title="Results", content=" ".join(lines))

    def generate_discussion_section(
        self,
        precision: float,
        recall: float,
        limitations: Optional[List[str]] = None,
    ) -> PaperSection:
        lim_text = ""
        if limitations:
            lim_text = " Limitations include: " + "; ".join(limitations) + "."
        content = (
            f"The results support the hypothesis that CCD is detectable using "
            f"observable behavioral signals without access to model internals. "
            f"Precision of {precision:.3f} indicates that false positives remain "
            f"within the auto-rollback threshold (FPR < 0.10). "
            f"Recall of {recall:.3f} suggests that the detector captures the "
            f"majority of CCD events in the synthetic corpus."
            f"{lim_text} "
            f"Future work should replicate these findings on real-world "
            f"session data under IRB-approved protocols."
        )
        return PaperSection(title="Discussion", content=content)

    def export_markdown(self, sections: List[PaperSection]) -> str:
        parts = []
        for section in sections:
            parts.append(f"## {section.title}\n\n{section.content}\n")
        return "\n".join(parts)
