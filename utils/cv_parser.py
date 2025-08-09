"""
CV parser utility for extracting text from PDF and DOCX files.
"""

import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import pdfplumber
from docx import Document
import logging

logger = logging.getLogger(__name__)

class CVParser:
    """Parse CV documents (PDF/DOCX) and extract structured text."""
    
    def __init__(self):
        """Initialize CV parser."""
        self.supported_extensions = {'.pdf', '.docx', '.doc'}
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a CV file and extract text with metadata.
        
        Args:
            file_path: Path to the CV file
            
        Returns:
            Dictionary with parsed text and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        try:
            if file_extension == '.pdf':
                return self._parse_pdf(file_path)
            elif file_extension in {'.docx', '.doc'}:
                return self._parse_docx(file_path)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            raise
    
    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF file and extract text."""
        text_content = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_content.append({
                        "page": page_num + 1,
                        "text": page_text.strip()
                    })
        
        return {
            "file_path": file_path,
            "file_type": "pdf",
            "total_pages": len(text_content),
            "content": text_content,
            "parsed_at": datetime.now().isoformat()
        }
    
    def _parse_docx(self, file_path: str) -> Dict[str, Any]:
        """Parse DOCX file and extract text."""
        doc = Document(file_path)
        text_content = []
        
        for para_num, paragraph in enumerate(doc.paragraphs):
            if paragraph.text.strip():
                text_content.append({
                    "paragraph": para_num + 1,
                    "text": paragraph.text.strip()
                })
        
        return {
            "file_path": file_path,
            "file_type": "docx",
            "total_paragraphs": len(text_content),
            "content": text_content,
            "parsed_at": datetime.now().isoformat()
        }
    
    def chunk_text(self, parsed_content: Dict[str, Any], chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Chunk the parsed text into smaller segments for embedding.
        
        Args:
            parsed_content: Parsed content from parse_file
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks with metadata
        """
        chunks = []
        all_text = ""
        
        # Combine all text content
        for item in parsed_content["content"]:
            all_text += item["text"] + "\n"
        
        # Split into chunks
        start = 0
        chunk_id = 0
        
        while start < len(all_text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(all_text):
                # Look for sentence endings
                sentence_endings = ['.', '!', '?', '\n']
                for ending in sentence_endings:
                    last_ending = all_text.rfind(ending, start, end)
                    if last_ending > start + chunk_size // 2:  # Only break if we're past halfway
                        end = last_ending + 1
                        break
            
            chunk_text = all_text[start:end].strip()
            
            if chunk_text:
                # Identify section based on common CV headers
                section = self._identify_section(chunk_text)
                
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "section": section,
                    "start_char": start,
                    "end_char": end,
                    "metadata": {
                        "file_type": parsed_content["file_type"],
                        "file_path": parsed_content["file_path"],
                        "parsed_at": parsed_content["parsed_at"]
                    }
                })
                chunk_id += 1
            
            start = end - overlap
            if start >= len(all_text):
                break
        
        return chunks
    
    def _identify_section(self, text: str) -> str:
        """
        Identify the CV section based on common headers.
        
        Args:
            text: Text chunk to analyze
            
        Returns:
            Section name
        """
        text_lower = text.lower()
        
        # Common CV section headers
        section_patterns = {
            "experience": r"\b(experience|work history|employment|professional experience)\b",
            "education": r"\b(education|academic|degree|university|college)\b",
            "skills": r"\b(skills|technical skills|competencies|expertise)\b",
            "summary": r"\b(summary|profile|objective|about)\b",
            "projects": r"\b(projects|portfolio|achievements)\b",
            "certifications": r"\b(certifications|certificates|licenses)\b",
            "languages": r"\b(languages|language skills)\b",
            "interests": r"\b(interests|hobbies|activities)\b"
        }
        
        for section, pattern in section_patterns.items():
            if re.search(pattern, text_lower):
                return section
        
        return "other"
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """
        Extract contact information from CV text.
        
        Args:
            text: Full CV text
            
        Returns:
            Dictionary with contact information
        """
        contact_info = {}
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info["email"] = email_match.group()
        
        # Phone pattern
        phone_pattern = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact_info["phone"] = phone_match.group()
        
        # LinkedIn pattern
        linkedin_pattern = r'linkedin\.com/in/[A-Za-z0-9-]+'
        linkedin_match = re.search(linkedin_pattern, text)
        if linkedin_match:
            contact_info["linkedin"] = linkedin_match.group()
        
        return contact_info
