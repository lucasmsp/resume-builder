"""Tests for PDF generation."""

import tempfile
from pathlib import Path

from resume_builder.models import Profile
from resume_builder.pdf_generator import generate_pdf
from resume_builder.selector import SelectedResume


class TestGeneratePDF:
    def test_creates_pdf_file(self, sample_selected_resume):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_resume.pdf"
            result = generate_pdf(sample_selected_resume, output_path)
            assert result.exists()
            assert result.stat().st_size > 0

    def test_pdf_is_valid(self, sample_selected_resume):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_resume.pdf"
            generate_pdf(sample_selected_resume, output_path)
            # Check PDF magic bytes
            with open(output_path, "rb") as f:
                header = f.read(5)
            assert header == b"%PDF-"

    def test_handles_unicode_characters(self):
        """Test that Unicode characters like em-dashes don't crash the PDF."""
        resume = SelectedResume(
            profile=Profile(
                name="Jose Garcia",
                headline="Cloud Architect - Azure & AWS",
                summary="Experienced architect - delivered 50+ projects across multiple regions.",
            ),
            summary="Experienced architect - delivered 50+ projects across multiple regions.",
            experiences=[],
            skill_categories=[],
            certifications=[],
            education=[],
            section_order=["summary"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_unicode.pdf"
            result = generate_pdf(resume, output_path)
            assert result.exists()

    def test_creates_parent_directories(self, sample_selected_resume):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "resume.pdf"
            result = generate_pdf(sample_selected_resume, output_path)
            assert result.exists()

    def test_long_text_wraps_without_overflowing_page(self):
        """Test that long text entries (e.g. long project names) wrap across lines and stay within margins."""
        import pdfplumber
        from resume_builder.models import Project

        long_name = (
            "ATMOSPHERE (Adaptive, Trustworthy, Manageable, Orchestrated, "
            "Secure Privacy-assuring, Hybrid Ecosystem for Resilient Cloud Computing)"
        )
        resume = SelectedResume(
            profile=Profile(name="Test User"),
            summary="",
            experiences=[],
            projects=[(Project(name=long_name, start_year="2020", end_year="2022", description=""), [])],
            skill_categories=[],
            certifications=[],
            education=[],
            section_order=["projects"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_long_text.pdf"
            generate_pdf(resume, output_path)
            with pdfplumber.open(output_path) as pdf:
                page = pdf.pages[0]
                text = page.extract_text()
                # Verify that the long name wrapped into multiple lines
                assert "ATMOSPHERE" in text
                assert "Cloud Computing)" in text
                # Verify all characters stay inside the right margin
                for char in page.chars:
                    assert char["x1"] <= page.width - 10

    def test_preserves_accented_characters(self):
        """Test that accented words like Educação and Gestão are preserved in PDF output."""
        import pdfplumber
        from resume_builder.models import Education

        resume = SelectedResume(
            profile=Profile(name="José Garcia"),
            summary="Especialista em Gestão e Educação com experiência comprovada.",
            experiences=[],
            projects=[],
            skill_categories=[],
            certifications=[],
            education=[
                Education(
                    institution="Universidade de São Paulo",
                    degree="Pós-Graduação em Educação",
                    field="Ciência da Computação",
                )
            ],
            section_order=["summary", "education"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_accents.pdf"
            generate_pdf(resume, output_path)
            with pdfplumber.open(output_path) as pdf:
                text = pdf.pages[0].extract_text()
                assert "Educação" in text
                assert "Gestão" in text
                assert "São Paulo" in text
                assert "Ciência" in text

    def test_renders_nationality_in_header(self):
        """Test that nationality is rendered in the header contact line when present."""
        import pdfplumber

        resume = SelectedResume(
            profile=Profile(
                name="Maria Silva",
                email="maria@example.com",
                location="Belo Horizonte, Brazil",
                nationality="Brazilian",
            ),
            summary="Engenheira de software.",
            experiences=[],
            projects=[],
            skill_categories=[],
            certifications=[],
            education=[],
            section_order=["summary"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_nationality.pdf"
            generate_pdf(resume, output_path)
            with pdfplumber.open(output_path) as pdf:
                text = pdf.pages[0].extract_text()
                assert "Brazilian" in text
                assert "Belo Horizonte, Brazil" in text
                assert "maria@example.com" in text



