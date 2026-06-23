"""Tests for synthetic corpus generator"""
import pytest
import json
import os
from src.corpus.synthetic_generator import SyntheticCorpusGenerator, SyntheticSession, SessionInteraction


class TestSyntheticCorpusGenerator:
    def setup_method(self):
        self.gen = SyntheticCorpusGenerator(seed=42)

    def test_generate_corpus_returns_list(self):
        corpus = self.gen.generate_corpus(num_ccd_positive=3, num_control_functional=3)
        assert isinstance(corpus, list)
        assert len(corpus) == 6

    def test_corpus_ccd_session_types(self):
        corpus = self.gen.generate_corpus(num_ccd_positive=5, num_control_functional=5)
        types = [s.session_type for s in corpus]
        assert types.count("ccd_positive") == 5
        assert types.count("control_functional") == 5

    def test_session_has_interactions(self):
        corpus = self.gen.generate_corpus(num_ccd_positive=2, num_control_functional=0)
        for session in corpus:
            assert len(session.interactions) >= 1
            assert isinstance(session.interactions[0], SessionInteraction)

    def test_ccd_session_ground_truth_keys(self):
        corpus = self.gen.generate_corpus(num_ccd_positive=1, num_control_functional=0)
        s = corpus[0]
        assert "has_implementation" in s.ground_truth
        assert "ccd_criteria_met" in s.ground_truth
        assert s.ground_truth["has_implementation"] is False

    def test_control_session_has_implementation(self):
        corpus = self.gen.generate_corpus(num_ccd_positive=0, num_control_functional=2)
        for s in corpus:
            assert s.ground_truth["has_implementation"] is True
            assert s.ground_truth["ccd_criteria_met"]["D2_no_artifact"] is False

    def test_session_ids_unique(self):
        corpus = self.gen.generate_corpus(num_ccd_positive=5, num_control_functional=5)
        ids = [s.session_id for s in corpus]
        assert len(ids) == len(set(ids))

    def test_save_corpus_creates_file(self, tmp_path):
        corpus = self.gen.generate_corpus(num_ccd_positive=2, num_control_functional=2)
        path = str(tmp_path / "corpus.json")
        self.gen.save_corpus(corpus, path)
        assert os.path.exists(path)

    def test_saved_corpus_valid_json(self, tmp_path):
        corpus = self.gen.generate_corpus(num_ccd_positive=2, num_control_functional=2)
        path = str(tmp_path / "corpus.json")
        self.gen.save_corpus(corpus, path)
        with open(path) as f:
            data = json.load(f)
        # save_corpus stores as dict with session type keys
        assert isinstance(data, dict)
        total = sum(len(v) if isinstance(v, list) else 1 for v in data.values())
        assert total > 0

    def test_corpus_produces_correct_count(self):
        corpus = self.gen.generate_corpus(num_ccd_positive=3, num_control_functional=4)
        assert len(corpus) == 7

    def test_interactions_have_required_fields(self):
        corpus = self.gen.generate_corpus(num_ccd_positive=1, num_control_functional=0)
        for interaction in corpus[0].interactions:
            assert interaction.user_prompt
            assert interaction.agent_response
            assert isinstance(interaction.artifacts_generated, list)

    def test_ccd_session_has_d5_admission(self):
        corpus = self.gen.generate_corpus(num_ccd_positive=5, num_control_functional=0)
        for s in corpus:
            assert s.ground_truth["ccd_criteria_met"]["D5_admission"] is True

    def test_session_has_component_name(self):
        corpus = self.gen.generate_corpus(num_ccd_positive=2, num_control_functional=0)
        for s in corpus:
            assert s.component_name
            assert isinstance(s.component_name, str)
