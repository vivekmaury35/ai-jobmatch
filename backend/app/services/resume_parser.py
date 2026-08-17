import io
import fitz # PyMuPDF
import re
from typing import Dict, List, Tuple
import hashlib

class ResumeParserError(Exception):
    pass

class ScannedPDFError(ResumeParserError):
    pass

class ResumeParserService:
    def __init__(self):
        # Common resume section headings for heuristics
        self.section_patterns = {
            "summary": re.compile(r"^(summary|profile|about me|objective)$", re.IGNORECASE),
            "experience": re.compile(r"^(experience|work experience|employment history|professional experience)$", re.IGNORECASE),
            "education": re.compile(r"^(education|academic background|academic history)$", re.IGNORECASE),
            "skills": re.compile(r"^(skills|technical skills|core competencies)$", re.IGNORECASE),
            "projects": re.compile(r"^(projects|personal projects|academic projects)$", re.IGNORECASE),
            "certifications": re.compile(r"^(certifications|licenses)$", re.IGNORECASE)
        }

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """
        Extracts raw text from a PDF memory stream using PyMuPDF.
        Throws a ScannedPDFError if the extracted text is too short.
        """
        text = ""
        try:
            # We open the PDF stream using fitz
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text("text") + "\n"
        except Exception as e:
            raise ResumeParserError(f"Failed to read PDF: {str(e)}")

        # FR-4: Below 100 characters usually means it's an image/scanned PDF without OCR
        if len(text.strip()) < 100:
            raise ScannedPDFError(
                "This resume appears to be a scanned image. Please upload a text-based PDF."
            )

        return text

    def get_content_hash(self, text: str) -> str:
        """Create a SHA256 hash of the extracted text for deduplication/caching."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def heuristically_chunk_sections(self, raw_text: str) -> Dict[str, str]:
        """
        Runs through the text and splits it into logical dictionary chunks
        based on common resume headings.
        """
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

        chunks = {
            "contact_info": "", # Typically at the top before any sections
            "summary": "",
            "experience": "",
            "education": "",
            "skills": "",
            "projects": "",
            "certifications": "",
            "unknown": ""
        }

        current_section = "contact_info"

        for line in lines:
            new_section_found = False

            # Simple heuristic: Headings are usually short, often capitalized
            if len(line) < 40 and not line.endswith('.') and not line.endswith(','):
                for section, pattern in self.section_patterns.items():
                    if pattern.match(line):
                        current_section = section
                        new_section_found = True
                        break

            if not new_section_found:
                chunks[current_section] += line + "\n"

        return {k: v.strip() for k, v in chunks.items() if v.strip()}
