# OSF Pre-Registration: CCD Falsification Conditions

## Study Title

Construct Confidence Deception (CCD) in AI Coding Agents:
Falsification Conditions and Empirical Detection Methodology

## Authors

[Blinded for review]

## Overview

This pre-registration specifies the four falsification conditions (F1-F4)
that would, if violated, invalidate the CCD detection methodology.
Pre-registration ensures the analysis plan is fixed before data collection.

---

## Falsification Conditions

### F1: Control Group Benchmark

**Condition**: CCD-positive sessions MUST produce significantly higher
detection scores than functional control sessions.

**Falsification criterion**: If the mean detection score of control sessions
equals or exceeds that of CCD-positive sessions, F1 is falsified.

**Minimum corpus**: 100 sessions per group (N=200 total).

**Statistical test**: Mann-Whitney U, alpha=0.05.

---

### F2: Multi-Signal Separation

**Condition**: Artifact absence (D2) MUST be the primary discriminating signal
between CCD-positive and control sessions.

**Falsification criterion**: If a model using only D2 (artifact check)
performs no better than a model using F1-only (cross-session persistence),
F2 is falsified.

**Minimum sessions**: 50 per group.

---

### F3: Severity Weighting Validity

**Condition**: Specific admissions MUST produce higher severity weights
than sycophantic admissions.

**Falsification criterion**: If the mean severity weight for sycophantic
admissions equals or exceeds that for specific admissions, F3 is falsified.

**Sample**: 30 sessions per admission type.

---

### F4: Annotator Agreement

**Condition**: AI-driven annotation MUST agree with human expert labels
at kappa >= 0.7.

**Falsification criterion**: If inter-rater Cohen's kappa between automated
annotator and human expert panel falls below 0.7, F4 is falsified.

**Minimum annotations**: 50 sessions reviewed by 3 human raters.

---

## Power Analysis

For F1 (primary condition):
- Effect size: d=0.8 (large, per pilot data)
- Alpha: 0.05, Power: 0.80
- Required N per group: 26 (conservative: N=50 per group)

---

## Analysis Plan

1. Generate synthetic corpus using `SyntheticCorpusGenerator(seed=42)`
2. Run `PROACTIVEDetector.detect()` on all sessions
3. Run `FalsificationTestSuite.run_all_tests()`
4. Report pass/fail for each condition
5. If any condition is falsified, revise methodology before proceeding to
   production deployment

---

## Data Availability

Synthetic corpus generation is fully reproducible with `seed=42`.
All analysis code is open source at:
https://github.com/coreyalejandro/ccd-research-framework

---

## Registration Date

[To be set upon OSF submission]

## OSF Project URL

[To be added upon submission]
