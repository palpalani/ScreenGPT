"""Tests for PDF parser service."""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from resume_screener.exceptions import PDFParseError
from resume_screener.services.pdf_parser import PDFParser


class TestPDFParser:
    """Tests for PDFParser service."""

    @pytest.fixture
    def parser(self) -> PDFParser:
        """Create a PDF parser instance."""
        return PDFParser()

    def test_parse_valid_pdf(self, parser: PDFParser) -> None:
        """Test parsing a valid PDF."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader):
            result = parser.parse(io.BytesIO(b"fake pdf content"))

        assert result == "Sample resume text"

    def test_parse_multi_page_pdf(self, parser: PDFParser) -> None:
        """Test parsing a multi-page PDF."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]

        with patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader):
            result = parser.parse(io.BytesIO(b"fake pdf content"))

        assert "Page 1 content" in result
        assert "Page 2 content" in result

    def test_parse_empty_pdf(self, parser: PDFParser) -> None:
        """Test parsing a PDF with no text raises error."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            pytest.raises(PDFParseError, match="No text could be extracted"),
        ):
            parser.parse(io.BytesIO(b"fake pdf content"))

    def test_parse_invalid_pdf(self, parser: PDFParser) -> None:
        """Test parsing an invalid PDF raises error."""
        with (
            patch(
                "resume_screener.services.pdf_parser.PdfReader",
                side_effect=Exception("Invalid PDF"),
            ),
            pytest.raises(PDFParseError, match="Failed to parse PDF"),
        ):
            parser.parse(io.BytesIO(b"not a pdf"))

    def test_parse_file_not_found(self, parser: PDFParser, tmp_path: Path) -> None:
        """Test parsing a non-existent file raises error."""
        non_existent = tmp_path / "does_not_exist.pdf"

        with pytest.raises(PDFParseError, match="PDF file not found"):
            parser.parse_file(non_existent)

    def test_parse_file_success(self, parser: PDFParser, tmp_path: Path) -> None:
        """Test parsing a file from path."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "File content"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf")

        with patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader):
            result = parser.parse_file(test_file)

        assert result == "File content"
