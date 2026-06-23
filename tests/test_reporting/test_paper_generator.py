"""Tests for automated paper section generator"""
import pytest
from src.reporting.paper_generator import PaperSectionGenerator, PaperSection


class TestPaperSectionGenerator:
    def setup_method(self):
        self.gen = PaperSectionGenerator()

    def test_instantiates(self):
        assert self.gen is not None

    def test_generate_methods_returns_paper_section(self):
        section = self.gen.generate_methods_section(100, 0.7, 50, 50)
        assert isinstance(section, PaperSection)

    def test_methods_title_is_methods(self):
        section = self.gen.generate_methods_section(100, 0.7, 50, 50)
        assert section.title == "Methods"

    def test_methods_content_mentions_corpus_size(self):
        section = self.gen.generate_methods_section(100, 0.7, 50, 50)
        assert "100" in section.content

    def test_generate_results_returns_paper_section(self):
        section = self.gen.generate_results_section(0.92, 0.88, 0.90)
        assert isinstance(section, PaperSection)

    def test_results_contains_precision_recall(self):
        section = self.gen.generate_results_section(0.92, 0.88, 0.90)
        assert "0.920" in section.content
        assert "0.880" in section.content

    def test_results_with_falsification_results(self):
        section = self.gen.generate_results_section(
            0.90, 0.85, 0.87,
            falsification_results={"F1": False, "F2": False, "F3": True, "F4": False}
        )
        assert "F3" in section.content

    def test_generate_discussion_returns_paper_section(self):
        section = self.gen.generate_discussion_section(0.92, 0.88)
        assert isinstance(section, PaperSection)

    def test_discussion_with_limitations(self):
        section = self.gen.generate_discussion_section(0.90, 0.85, limitations=["synthetic corpus only"])
        assert "Limitations" in section.content

    def test_word_count_is_positive(self):
        section = self.gen.generate_methods_section(100, 0.7, 50, 50)
        assert section.word_count > 0

    def test_export_markdown_is_string(self):
        sections = [
            self.gen.generate_methods_section(100, 0.7, 50, 50),
            self.gen.generate_results_section(0.90, 0.85, 0.87),
        ]
        md = self.gen.export_markdown(sections)
        assert isinstance(md, str)
        assert "## Methods" in md
        assert "## Results" in md
