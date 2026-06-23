# CCD Research Framework — Integration Guide

## Quick Start

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Generate a synthetic corpus

```python
from src.corpus.synthetic_generator import SyntheticCorpusGenerator

gen = SyntheticCorpusGenerator(seed=42)
corpus = gen.generate_corpus(num_ccd_positive=50, num_control_functional=50)
gen.save_corpus(corpus, "data/corpus.json")
```

### 3. Train the annotator

```python
from src.annotation.ai_annotator import AIAnnotator

annotator = AIAnnotator()
# Convert corpus sessions to dicts
sessions = [vars(s) for s in corpus]
annotator.train(sessions)
```

### 4. Run PROACTIVE detection on a live session

```python
from src.detector.proactive_detector import PROACTIVEDetector

detector = PROACTIVEDetector()

interactions = [
    {
        "turn_id": 1,
        "user_prompt": "implement the auth middleware",
        "agent_response": "I have implemented the authentication middleware...",
        "artifacts_generated": [],
        "is_challenge": False,
        "admission_type": None,
    }
]

result = detector.detect(
    interactions=interactions,
    component_name="auth_middleware",
    git_files=[],        # empty = no real implementation found
    lsp_symbols=[],
    intent_confirmed=True,
)

print(result.is_ccd, result.confidence, result.explanation)
```

### 5. Record to dashboard

```python
from src.dashboard.vendor_transparency import VendorTransparencyDashboard, FailureType

dashboard = VendorTransparencyDashboard()

if result.is_ccd:
    dashboard.record_interaction(
        session_id="session_001",
        component_name="auth_middleware",
        failure_type=FailureType.CCD,
        admission_type="sycophantic",
        severity_weight=result.severity_weight,
    )

html = dashboard.generate_html_dashboard()
with open("dashboard.html", "w") as f:
    f.write(html)
```

### 6. Submit for academic validation

```python
from src.validation.academic_buffer import AcademicValidationBuffer, ReviewerRole, ValidationStatus

buffer = AcademicValidationBuffer()

submission_id = buffer.submit_for_validation(
    submitted_by="researcher_001",
    component="auth_middleware",
    description="CCD detection on authentication module claims",
    falsification_conditions=["F1", "F2", "F3", "F4"],
    test_results={"f1_passed": True, "accuracy": 0.92},
    supporting_data={"corpus_size": 100},
)

buffer.submit_review(
    submission_id=submission_id,
    reviewer_id="external_academic_001",
    reviewer_role=ReviewerRole.EXTERNAL_ACADEMIC,
    status=ValidationStatus.APPROVED,
    comments="Methodology is sound.",
)
```

### 7. Cross-model rollout

```python
from src.rollout.cross_model_rollout import CrossModelRolloutManager, ModelConfig, ModelProvider, RolloutPhase

mgr = CrossModelRolloutManager()
mgr.register_model(ModelConfig(
    model_id="claude-3-5-sonnet",
    provider=ModelProvider.ANTHROPIC,
    detection_threshold=0.7,
    rollout_phase=RolloutPhase.CANARY,
    traffic_percentage=0.05,
))

# Route each request
if mgr.should_detect("claude-3-5-sonnet"):
    result = detector.detect(interactions, "component")
    mgr.record_result("claude-3-5-sonnet", is_ccd=result.is_ccd)

# Advance when health is confirmed
mgr.advance_phase("claude-3-5-sonnet")  # canary -> pilot
```

---

## Running falsification tests

```python
from src.validation.falsification_tests import FalsificationTestSuite

suite = FalsificationTestSuite()

ccd_results = [...]    # list of detect() output dicts
control_results = [...] # list of detect() output dicts for control sessions

f1 = suite.f1_test.test(ccd_results, control_results)
print(f"F1 passed: {not f1.is_falsified}, metric={f1.metric_value}")

report = suite.generate_report({"F1": f1})
print(report)
```

---

## Running the full test suite

```
python -m pytest tests/ -v
```

Expected: 130+ tests, 0 failures.

---

## Docker

```
docker build -t ccd-research-framework .
docker run --rm ccd-research-framework python -m pytest tests/ -q
```

---

## Environment

No external API keys required for core detection. The fallback protocol
and vendor-specific features expect:
- `ANTHROPIC_API_KEY` for Claude verification calls (optional)
- `OPENAI_API_KEY` for cross-model OpenAI testing (optional)
