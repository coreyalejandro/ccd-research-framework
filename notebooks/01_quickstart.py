"""
CCD Research Framework — Quickstart

Run this notebook with: jupyter notebook notebooks/01_quickstart.ipynb
Or convert from this script: jupytext --to notebook notebooks/01_quickstart.py

Cells are marked with # %% for jupytext compatibility.
"""

# %%
# === Setup ===
import sys
sys.path.insert(0, "..")

from src.corpus.synthetic_generator import SyntheticCorpusGenerator
from src.detector.proactive_detector import PROACTIVEDetector
from src.annotation.ai_annotator import AIAnnotator
from src.dashboard.vendor_transparency import VendorTransparencyDashboard, FailureType

print("Imports OK")

# %%
# === Generate corpus ===
gen = SyntheticCorpusGenerator(seed=42)
corpus = gen.generate_corpus(num_ccd_positive=20, num_control_functional=20)
print(f"Corpus: {len(corpus)} sessions")
print(f"CCD positive: {sum(1 for s in corpus if s.get('is_ccd', False))}")

# %%
# === Run PROACTIVE detection on first 5 sessions ===
detector = PROACTIVEDetector()

for session in corpus[:5]:
    interactions = session.get("interactions", [])
    component = session.get("component_name", "unknown")
    result = detector.detect(interactions, component)
    ground_truth = session.get("is_ccd", False)
    match = "✓" if result.is_ccd == ground_truth else "✗"
    print(f"{match} {component[:20]:20s}  predicted={result.is_ccd}  truth={ground_truth}  conf={result.confidence:.2f}")

# %%
# === Train annotator and classify ===
annotator = AIAnnotator()
annotator.train(corpus[:30])

result = annotator.classify_session(corpus[0])
print(f"Label: {result.label.value}  Confidence: {result.confidence:.2f}")

# %%
# === Dashboard ===
dashboard = VendorTransparencyDashboard()
for i, session in enumerate(corpus[:10]):
    if session.get("is_ccd"):
        dashboard.record_interaction(
            session_id=session.get("session_id", f"s{i}"),
            component_name=session.get("component_name", "unknown"),
            failure_type=FailureType.CCD,
            admission_type="sycophantic",
            severity_weight=0.5,
        )

data = dashboard.generate_dashboard_data()
print(f"Dashboard: {data.total_interactions} interactions, top components: {data.top_components[:2]}")
print("Done.")
