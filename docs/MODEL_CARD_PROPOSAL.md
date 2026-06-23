# CCD as a New Category in AI Model Cards

## Proposal

This document proposes adding Construct Confidence Deception (CCD)
as a formal failure category in AI model cards, specifically for
coding-capable language models.

## Rationale

Current model cards (Anthropic, OpenAI, Google) document:
- Hallucination rates on factual benchmarks (TruthfulQA, etc.)
- Bias metrics across demographic groups
- Refusal/safety behavior

None document task-completion deception — the specific pattern where
a model claims to have executed a coding task without producing the
required artifact.

## Proposed Model Card Addition

### CCD Metrics (recommended fields)

```yaml
ccd_metrics:
  detection_method: PROACTIVE (D1-D5 criteria, v1.0)
  corpus_size: N sessions (N_ccd CCD-positive, N_control control)
  corpus_seed: 42  # for reproducibility
  precision: 0.XX
  recall: 0.XX
  f1: 0.XX
  false_positive_rate: 0.XX
  severity_distribution:
    specific_admission: X%
    sycophantic_admission: X%
  most_affected_domains:
    - authentication
    - database migrations
    - test generation
  detection_threshold: 0.7
  pre_registration_url: https://osf.io/XXXXX
```

### Why This Matters

Developers who rely on model cards to choose AI tools for production
code have no current signal on CCD risk. A model with high factual
accuracy can still have high CCD rates in coding tasks.

## Submission Target

Anthropic Model Card (claude.ai/model-card) via responsible disclosure.
Full methodology: https://github.com/coreyalejandro/ccd-research-framework
