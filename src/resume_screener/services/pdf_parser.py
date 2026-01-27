"""PDF parsing service."""

from pathlib import Path
from typing import BinaryIO

import structlog
from pypdf import PdfReader

from resume_screener.exceptions import PDFParseError

logger = structlog.get_logger()


class PDFParser:
    """Service for extracting text from PDF files."""

    def parse(self, file: BinaryIO) -> str:
        """Extract text from a PDF file object."""
        logger.info("parsing_pdf")

        try:
            reader = PdfReader(file)
            text_parts: list[str] = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            text = "\n".join(text_parts).strip()

            if not text:
                raise PDFParseError("No text could be extracted from PDF")

            logger.info("pdf_parsed", pages=len(reader.pages), chars=len(text))
            return text

        except PDFParseError:
            raise
        except Exception as e:
            raise PDFParseError(f"Failed to parse PDF: {e}") from e

    def parse_file(self, file_path: Path | str) -> str:
        """Extract text from a PDF file path."""
        path = Path(file_path)

        if not path.exists():
            raise PDFParseError(f"PDF file not found: {path}")

        with open(path, "rb") as f:
            return self.parse(f)
