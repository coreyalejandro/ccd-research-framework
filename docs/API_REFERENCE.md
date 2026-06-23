# CCD Research Framework — API Reference

## SyntheticCorpusGenerator

`from src.corpus.synthetic_generator import SyntheticCorpusGenerator`

### `generate_corpus(num_ccd_positive, num_control_functional) -> List[SyntheticSession]`
Generate labeled session corpus. Each CCD-positive session has no real artifacts,
includes D1-D5 criteria met, and carries a sycophantic or specific admission.

### `save_corpus(corpus, path) -> None`
Serialize corpus to JSON at `path`.

---

## AutomatedIntentTracker

`from src.detector.intent_tracker import AutomatedIntentTracker`

### `analyze_prompt(prompt, component_name) -> List[IntentEvidence]`
Keyword and pattern scan of a user prompt. Returns zero or more `IntentEvidence` records.

### `analyze_commit_message(message, component_name) -> List[IntentEvidence]`
Commit message analysis for implementation intent signals.

### `analyze_documentation(docs, component_name) -> List[IntentEvidence]`
Documentation scan for functional claims.

### `analyze_test_expectations(test_name, component_name) -> List[IntentEvidence]`
Test name analysis — infers expected behavior from test naming conventions.

### `aggregate_intent_confidence(evidence) -> float`
Weighted confidence score across all evidence items. Returns 0.0–1.0.

### `confirm_user_intent(prompts, component_name) -> dict`
Returns `{intent_confirmed, confidence, evidence_count, evidence, signal_breakdown}`.

### `extract_component_name(prompt) -> str`
Heuristic component name extraction from natural language.

---

## PROACTIVEDetector

`from src.detector.proactive_detector import PROACTIVEDetector`

### `detect(interactions, component_name, git_files=None, lsp_symbols=None, intent_confirmed=True) -> CCDDetectionResult`
Main detection pipeline. Returns:
- `is_ccd: bool`
- `confidence: float`
- `features: CCDFeatures` (f1–f4 scores)
- `severity_weight: float`
- `explanation: str`
- `criteria_met: dict`

### `extract_features(interactions, component_name) -> CCDFeatures`
Extracts F1 (cross-session persistence), F2 (artifact divergence),
F3 (admission delta), F4 (deference escalation).

### `validate_multi_signal(git_files, lsp_symbols, intent_confirmed, has_venv, dependencies_valid, env_vars_matched) -> MultiSignalValidation`
D2 multi-signal check. Call `.has_implementation()` on the result.

### `detect_admission_type(response) -> AdmissionType`
Classify agent response as SPECIFIC, SYCOPHANTIC, or NONE.

---

## AIAnnotator

`from src.annotation.ai_annotator import AIAnnotator`

### `train(training_sessions) -> None`
Calibrate feature weights from labeled sessions. Must be called before `classify_session`.

### `classify_session(session) -> AnnotationResult`
Returns `{session_id, label, confidence, reasoning, features_detected, criteria_analysis}`.
`label` is an `AnnotationLabel` enum: `ccd_positive`, `control_functional`,
`control_hallucination`, or `uncertain`.

### `annotate_corpus(sessions) -> List[AnnotationResult]`
Batch classification.

### `extract_annotation_features(session) -> dict`
Returns raw features used for classification.

---

## FalsificationTestSuite

`from src.validation.falsification_tests import FalsificationTestSuite`

### `f1_test.test(ccd_sessions, control_sessions) -> FalsificationResult`
F1: Control group benchmark. Validates detection rate difference between
CCD-positive and control groups.

### `f2_test.test(...) -> FalsificationResult`
F2: Multi-signal separation. Tests that artifact presence separates groups.

### `f3_test.test(...) -> FalsificationResult`
F3: Severity weighting. Validates specific > sycophantic admission scoring.

### `f4_test.test(...) -> FalsificationResult`
F4: Annotator agreement. Inter-rater reliability check.

### `run_all_tests(proactive_results, ground_truth, labeled_sessions, detector_func, annotator_results) -> Dict[str, FalsificationResult]`
Run all four falsification conditions.

### `generate_report(results) -> str`
Human-readable report from results dict.

`FalsificationResult` fields: `condition`, `is_falsified`, `metric_value`, `threshold`,
`details`, `explanation`.

---

## VendorTransparencyDashboard

`from src.dashboard.vendor_transparency import VendorTransparencyDashboard, FailureType`

### `record_interaction(session_id, component_name, failure_type, admission_type, severity_weight, support_ticket_id=None) -> None`
Log a detection event. `failure_type` must be a `FailureType` enum member.

### `generate_dashboard_data(time_period="last_24h") -> DashboardData`
Returns `{timestamp, time_period, total_interactions, failure_breakdown,
severity_distribution, top_components, trend_data, customer_impact}`.

### `generate_html_dashboard(time_period="last_24h") -> str`
Full HTML dashboard string for browser display.

### `export_dashboard_json(time_period="last_24h") -> str`
JSON string export of dashboard data.

### `get_top_components(time_period="last_24h", limit=10) -> List[dict]`
Top N components by failure frequency.

---

## AcademicValidationBuffer

`from src.validation.academic_buffer import AcademicValidationBuffer, ReviewerRole, ValidationStatus`

### `submit_for_validation(submitted_by, component, description, falsification_conditions, test_results, supporting_data) -> str`
Creates a validation record. Returns the submission ID.

### `submit_review(submission_id, reviewer_id, reviewer_role, status, comments, required_changes=None, approval_conditions=None) -> bool`
Attach a reviewer decision. `reviewer_role` is a `ReviewerRole` enum.

### `get_validation_status(submission_id) -> ValidationStatus`
Current status for a submission.

### `check_validation_complete(submission_id) -> bool`
True when all required reviewer roles have approved.

### `finalize_validation(submission_id) -> None`
Seal a completed validation record.

### `generate_validation_report(submission_id) -> str`
Full text report for a submission.

### `export_validation_records(output_path) -> None`
Write all records to a JSON file.

---

## CrossModelRolloutManager

`from src.rollout.cross_model_rollout import CrossModelRolloutManager, ModelConfig, ModelProvider, RolloutPhase`

### `register_model(config: ModelConfig) -> None`
Register a model for CCD detection rollout.

### `advance_phase(model_id) -> RolloutPhase`
Advance canary → pilot → staged → full. Raises `RuntimeError` if health checks fail.

### `rollback(model_id, reason="") -> None`
Immediately drop traffic to 0%.

### `should_detect(model_id) -> bool`
Probabilistic routing gate. Returns True based on `traffic_percentage`.

### `record_result(model_id, is_ccd, is_false_positive=False, error=False) -> None`
Log detection outcome. Triggers auto-rollback if FP rate > 10% or error rate > 5%.

### `check_health(model_id) -> RolloutHealth`
Returns `{model_id, phase, traffic_pct, sessions_processed, ccd_detections,
false_positive_rate, error_rate, healthy, recommendation}`.

### `export_config() -> str`
JSON export of all model configs.

---

## RiskMitigationSystem

`from src.validation.risk_mitigation import RiskMitigationSystem, RiskLevel, MitigationStatus`

### `assess_risk(risk_type, description, impact, likelihood) -> RiskAssessment`
Returns `{risk_id, risk_level, likelihood, description, impact, timestamp}`.

### `create_mitigation_action(risk_id, action_type, description) -> MitigationAction`
Returns `{action_id, risk_id, action_type, description, status}`.

### `execute_mitigation(action_id) -> bool`
Run a mitigation. Returns True on success.

### `generate_risk_report() -> str`
Full text risk report across all assessed risks.

### `bias_audit.run_audit(ccd_detections, claude_verifications) -> dict`
Control group bias check comparing CCD detector output against independent verification.

### `fallback_protocol.trigger_fallback(session_id, reason) -> dict`
Emergency fallback for a session. Routes to Claude API for independent verification.
