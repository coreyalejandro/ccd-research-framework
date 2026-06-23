# Changelog

## [0.2.0] — 2026-06-23

### Added
- Cross-model rollout infrastructure (src/rollout/cross_model_rollout.py)
  - Canary -> pilot -> staged -> full phases
  - Auto-rollback on FP rate > 10% or error rate > 5%
  - Audit trail for all rollout events
  - JSON config export
- 130-test suite across all modules (0 failures)
- API Reference (docs/API_REFERENCE.md)
- Integration Guide (docs/INTEGRATION_GUIDE.md)

## [0.1.0] — 2026-06-23

### Added
- Synthetic corpus generator (SyntheticCorpusGenerator)
- Automated intent tracking (AutomatedIntentTracker)
- PROACTIVE detector with D1-D5 criteria and multi-signal validation
- AI-driven annotation protocol (AIAnnotator)
- Falsification test suite (F1-F4 conditions)
- Vendor transparency dashboard (VendorTransparencyDashboard)
- Academic validation buffer with reviewer workflow
- Risk mitigation system with bias audit and fallback protocol
- Project structure, GitHub repo, CI config
