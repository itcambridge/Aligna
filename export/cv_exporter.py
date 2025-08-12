"""
CV Exporter for generating CVs in different formats with citations.
"""

import os
import json
import re
import io
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import tempfile

# Import libraries for DOCX and PDF generation
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

class CVExporter:
    """Export CVs in different formats with citations."""
    
    def __init__(self, templates_dir: str = "export/templates"):
        """
        Initialize CV exporter.
        
        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load all templates from the templates directory."""
        templates = {}
        
        try:
            # List all JSON files in the templates directory
            template_files = [f for f in os.listdir(self.templates_dir) if f.endswith('.json')]
            
            for file_name in template_files:
                template_path = os.path.join(self.templates_dir, file_name)
                template_id = file_name.replace('.json', '')
                
                with open(template_path, 'r') as f:
                    template_data = json.load(f)
                    templates[template_id] = template_data
            
            logger.info(f"Loaded {len(templates)} CV templates")
            return templates
            
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            return {}
    
    def export_cv(
        self,
        cv_data: Dict[str, Any],
        template_id: str = "classic",
        output_format: str = "text",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export a CV using the specified template and format.
        
        Args:
            cv_data: CV data to export
            template_id: Template ID to use
            output_format: Output format (text, docx, pdf, json)
            output_path: Path to save the output file
            
        Returns:
            Export result with file path and status
        """
        try:
            # Check if template exists
            if template_id not in self.templates:
                raise ValueError(f"Template '{template_id}' not found")
            
            template = self.templates[template_id]
            
            # Generate CV content based on template
            cv_content = self._generate_cv_content(cv_data, template)
            
            # Export in the specified format
            if output_format == "text":
                result = self._export_text(cv_content, output_path)
            elif output_format == "docx":
                result = self._export_docx(cv_content, template, output_path)
            elif output_format == "pdf":
                result = self._export_pdf(cv_content, template, output_path)
            elif output_format == "json":
                result = self._export_json(cv_data, output_path)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            logger.info(f"Successfully exported CV in {output_format} format using {template_id} template to {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error exporting CV: {e}")
            return {
                "status": "error",
                "error": str(e),
                "template_id": template_id,
                "output_format": output_format
            }
    
    def _generate_cv_content(self, cv_data: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, str]:
        """Generate CV content based on template."""
        content = {}
        
        # Process each section in the template
        for section in template["sections"]:
            section_id = section["id"]
            section_format = section["format"]
            content_template = section["content_template"]
            
            # Generate content for this section
            if section_id == "contact":
                content[section_id] = self._format_contact_section(cv_data, content_template)
            elif section_id == "summary":
                content[section_id] = self._format_summary_section(cv_data, content_template, section_format)
            elif section_id == "skills":
                content[section_id] = self._format_skills_section(cv_data, content_template, section_format)
            elif section_id == "experience":
                content[section_id] = self._format_experience_section(cv_data, content_template, section_format)
            elif section_id == "education":
                content[section_id] = self._format_education_section(cv_data, content_template, section_format)
            elif section_id == "certifications":
                content[section_id] = self._format_certifications_section(cv_data, content_template, section_format)
            elif section_id == "footnotes":
                content[section_id] = self._format_footnotes_section(cv_data, content_template, template["citation_format"], template["footnote_format"])
            elif section_id == "impact_highlights":
                content[section_id] = self._format_impact_highlights_section(cv_data, content_template)
        
        return content
    
    def _format_contact_section(self, cv_data: Dict[str, Any], content_template: str) -> str:
        """Format contact information section."""
        contact_info = cv_data.get("contact_info", {})
        
        # Replace placeholders in template
        return content_template.format(
            name=contact_info.get("name", ""),
            email=contact_info.get("email", ""),
            phone=contact_info.get("phone", ""),
            location=contact_info.get("location", ""),
            linkedin=contact_info.get("linkedin", "")
        )
    
    def _format_summary_section(self, cv_data: Dict[str, Any], content_template: str, section_format: str) -> str:
        """Format summary section."""
        summary = cv_data.get("summary", {})
        summary_text = summary.get("content", "")
        
        if section_format == "paragraph_bold_highlights":
            # Highlight key skills and achievements
            summary_text = self._add_bold_highlights(summary_text)
        
        return content_template.format(
            summary_text=summary_text,
            summary_text_with_highlights=self._add_bold_highlights(summary_text)
        )
    
    def _format_skills_section(self, cv_data: Dict[str, Any], content_template: str, section_format: str) -> str:
        """Format skills section."""
        skills = cv_data.get("skills", {})
        skills_content = skills.get("content", "")
        
        # Extract bullet points
        skills_bullets = self._extract_bullets(skills_content)
        
        if section_format == "comma_list":
            # Convert bullets to comma-separated list
            skills_list = ", ".join([b.strip() for b in skills_bullets])
            return content_template.format(skills_list=skills_list)
        elif section_format == "categorized_skills":
            # Group skills by category (simplified implementation)
            skills_by_category = self._categorize_skills(skills_bullets)
            return content_template.format(skills_by_category=skills_by_category)
        else:
            # Default: bullet list
            formatted_bullets = "\n".join([f"• {b}" for b in skills_bullets])
            return content_template.format(skills_bullets=formatted_bullets)
    
    def _format_experience_section(self, cv_data: Dict[str, Any], content_template: str, section_format: str) -> str:
        """Format experience section."""
        experience = cv_data.get("experience", {})
        experience_content = experience.get("content", "")
        
        # Extract bullet points with citations
        experience_bullets = self._extract_bullets_with_citations(experience_content, cv_data)
        
        if section_format == "compact_bullets":
            # Compact format with fewer details
            formatted_bullets = "\n".join([f"- {self._shorten_bullet(b)}" for b in experience_bullets])
            return content_template.format(experience_bullets=formatted_bullets)
        elif section_format == "experience_with_metrics":
            # Highlight metrics in the bullets
            formatted_bullets = "\n".join([f"→ {self._highlight_metrics(b)}" for b in experience_bullets])
            return content_template.format(experience_with_metrics=formatted_bullets)
        else:
            # Default: standard bullets
            formatted_bullets = "\n".join([f"• {b}" for b in experience_bullets])
            return content_template.format(experience_bullets=formatted_bullets)
    
    def _format_education_section(self, cv_data: Dict[str, Any], content_template: str, section_format: str) -> str:
        """Format education section."""
        education = cv_data.get("education", {})
        education_content = education.get("content", "")
        
        # Extract bullet points
        education_bullets = self._extract_bullets(education_content)
        
        if section_format == "compact_list":
            # Compact list format
            education_compact = "; ".join([b.strip() for b in education_bullets])
            return content_template.format(education_compact=education_compact)
        elif section_format == "education_with_highlights":
            # Add highlights to education entries
            education_with_highlights = "\n".join([f"• {self._add_bold_highlights(b)}" for b in education_bullets])
            return content_template.format(education_with_highlights=education_with_highlights)
        else:
            # Default: standard bullets
            formatted_bullets = "\n".join([f"• {b}" for b in education_bullets])
            return content_template.format(education_bullets=formatted_bullets)
    
    def _format_certifications_section(self, cv_data: Dict[str, Any], content_template: str, section_format: str) -> str:
        """Format certifications section."""
        # This is a simplified implementation
        return content_template.format(certification_bullets="")
    
    def _format_footnotes_section(
        self,
        cv_data: Dict[str, Any],
        content_template: str,
        citation_format: str,
        footnote_format: str
    ) -> str:
        """Format footnotes section with citations."""
        # Get all citations from the CV data
        citations = self._extract_all_citations(cv_data)
        
        if not citations:
            return ""
        
        # Format footnotes based on template
        if citation_format == "superscript_number":
            footnotes = []
            for i, citation in enumerate(citations, 1):
                source = citation.get("cv_id", "Unknown Source")
                snippet = citation.get("snippet", "")
                date = citation.get("date", "")
                
                footnote = footnote_format.format(
                    index=i,
                    source=source,
                    snippet=snippet,
                    date=date
                )
                footnotes.append(footnote)
            
            return content_template.format(footnotes="\n".join(footnotes))
        
        elif citation_format == "superscript_letter":
            footnotes = []
            for i, citation in enumerate(citations):
                letter = chr(97 + i % 26)  # a, b, c, ...
                source = citation.get("cv_id", "Unknown Source")
                
                footnote = footnote_format.format(
                    letter=letter,
                    source=source
                )
                footnotes.append(footnote)
            
            return content_template.format(footnotes_minimal=", ".join(footnotes))
        
        elif citation_format == "inline_bracket":
            footnotes = []
            for i, citation in enumerate(citations, 1):
                source = citation.get("cv_id", "Unknown Source")
                snippet = citation.get("snippet", "")
                date = citation.get("date", datetime.now().strftime("%Y-%m-%d"))
                
                footnote = footnote_format.format(
                    index=i,
                    source=source,
                    snippet=snippet,
                    date=date
                )
                footnotes.append(footnote)
            
            return content_template.format(footnotes_detailed="\n\n".join(footnotes))
        
        else:
            return ""
    
    def _format_impact_highlights_section(self, cv_data: Dict[str, Any], content_template: str) -> str:
        """Format impact highlights section."""
        # Extract high-impact bullets from experience section
        experience = cv_data.get("experience", {})
        experience_content = experience.get("content", "")
        
        # Extract bullet points
        all_bullets = self._extract_bullets(experience_content)
        
        # Filter for impact bullets (containing metrics or achievements)
        impact_bullets = [b for b in all_bullets if self._is_impact_bullet(b)]
        
        # Format as impact statements
        formatted_bullets = "\n".join([f"→ {self._highlight_metrics(b)}" for b in impact_bullets[:3]])
        
        return content_template.format(impact_bullets=formatted_bullets)
    
    def _extract_bullets(self, content: str) -> List[str]:
        """Extract bullet points from content."""
        if not content:
            return []
        
        # Split by common bullet markers
        bullet_pattern = r'(?:^|\n)(?:\s*[-•*]\s*|\s*\d+\.\s*)(.*?)(?=(?:\n\s*[-•*]|\n\s*\d+\.|\n\n|$))'
        bullets = re.findall(bullet_pattern, content, re.DOTALL)
        
        # Clean up bullets
        return [b.strip() for b in bullets if b.strip()]
    
    def _extract_bullets_with_citations(self, content: str, cv_data: Dict[str, Any]) -> List[str]:
        """Extract bullet points and add citations."""
        bullets = self._extract_bullets(content)
        
        # In a real implementation, we would match bullets to their evidence
        # For now, we'll just return the bullets
        return bullets
    
    def _extract_all_citations(self, cv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all citations from CV data."""
        citations = []
        
        # In a real implementation, we would extract citations from the CV data
        # For now, we'll create some placeholder citations
        match_evidence = cv_data.get("match_evidence", {})
        matches = match_evidence.get("matches", [])
        
        if isinstance(matches, list):
            for match in matches:
                citation = {
                    "cv_id": match.get("cv_id", "Unknown"),
                    "section": match.get("section", "Unknown"),
                    "snippet": match.get("text", ""),
                    "score": match.get("score", 0.0),
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
                citations.append(citation)
        
        return citations
    
    def _add_bold_highlights(self, text: str) -> str:
        """Add bold formatting to key terms in text."""
        # In a real implementation, we would identify key terms to highlight
        # For now, we'll just return the original text
        return text
    
    def _highlight_metrics(self, text: str) -> str:
        """Highlight metrics in text."""
        # Highlight numbers, percentages, etc.
        return re.sub(r'(\d+%|\d+ percent|\d+x|\bincreased\b|\bimproved\b|\breduced\b|\bby \d+\b)', r'**\1**', text)
    
    def _shorten_bullet(self, text: str) -> str:
        """Shorten a bullet point for compact format."""
        # Simplify and shorten the bullet
        if len(text) > 80:
            return text[:77] + "..."
        return text
    
    def _is_impact_bullet(self, text: str) -> bool:
        """Check if a bullet point is impact-focused."""
        # Look for metrics, results, or achievements
        impact_patterns = [
            r'\d+%', r'\d+ percent', r'\d+x',
            r'\bincreased\b', r'\bimproved\b', r'\breduced\b',
            r'\bby \d+\b', r'\bachieved\b', r'\bdelivered\b',
            r'\bsuccess\b', r'\brecognized\b', r'\baward\b'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in impact_patterns)
    
    def _categorize_skills(self, skills: List[str]) -> str:
        """Categorize skills into groups."""
        # Simplified implementation - in reality, would use NLP to categorize
        categories = {
            "Programming": [],
            "Tools & Frameworks": [],
            "Soft Skills": [],
            "Domain Knowledge": []
        }
        
        # Simple keyword-based categorization
        for skill in skills:
            if any(lang in skill.lower() for lang in ["python", "java", "javascript", "c++", "ruby", "go"]):
                categories["Programming"].append(skill)
            elif any(tool in skill.lower() for tool in ["docker", "kubernetes", "aws", "azure", "git", "jenkins"]):
                categories["Tools & Frameworks"].append(skill)
            elif any(soft in skill.lower() for soft in ["communication", "leadership", "teamwork", "agile", "scrum"]):
                categories["Soft Skills"].append(skill)
            else:
                categories["Domain Knowledge"].append(skill)
        
        # Format as categorized list
        result = []
        for category, category_skills in categories.items():
            if category_skills:
                result.append(f"{category}: {', '.join(category_skills)}")
        
        return "\n".join(result)
    
    def _export_text(self, cv_content: Dict[str, str], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export CV as plain text."""
        # Combine all sections
        text_content = []
        
        for section_id, content in cv_content.items():
            if content:
                if section_id == "contact":
                    # Contact info at the top
                    text_content.insert(0, content)
                elif section_id == "footnotes":
                    # Footnotes at the bottom
                    text_content.append("\n" + "=" * 40 + "\n" + content)
                else:
                    # Add section title and content
                    section_title = section_id.replace("_", " ").upper()
                    text_content.append(f"\n{section_title}\n{'-' * len(section_title)}\n{content}")
        
        text_output = "\n".join(text_content)
        
        # Save to file if output path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(text_output)
        
        return {
            "status": "success",
            "format": "text",
            "content": text_output,
            "file_path": output_path
        }
    
    def _export_docx(self, cv_content: Dict[str, str], template: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export CV as DOCX."""
        try:
            # Create a new document
            doc = docx.Document()
            
            # Set document properties
            doc.core_properties.author = cv_content.get("contact", "").split("\n")[0] if "contact" in cv_content else "CV Owner"
            doc.core_properties.title = f"CV - {doc.core_properties.author}"
            
            # Debug log
            logger.info(f"Creating DOCX with content keys: {list(cv_content.keys())}")
            
            # Set document styles
            style = doc.styles['Normal']
            style.font.name = 'Calibri'
            style.font.size = Pt(11)
            
            # Add contact information
            if "contact" in cv_content:
                contact_lines = cv_content["contact"].split("\n")
                # Name in larger font
                if contact_lines:
                    name_paragraph = doc.add_paragraph()
                    name_run = name_paragraph.add_run(contact_lines[0])
                    name_run.font.size = Pt(16)
                    name_run.font.bold = True
                
                # Contact details
                if len(contact_lines) > 1:
                    contact_paragraph = doc.add_paragraph()
                    contact_run = contact_paragraph.add_run(" | ".join(contact_lines[1:]))
                    contact_run.font.size = Pt(10)
            
            # Add summary
            if "summary" in cv_content and cv_content["summary"]:
                doc.add_heading('PROFESSIONAL SUMMARY', level=1)
                doc.add_paragraph(cv_content["summary"])
            
            # Add experience
            if "experience" in cv_content and cv_content["experience"]:
                doc.add_heading('WORK EXPERIENCE', level=1)
                
                # Split experience into bullet points
                experience_bullets = cv_content["experience"].split("\n")
                for bullet in experience_bullets:
                    if bullet.strip():
                        p = doc.add_paragraph()
                        p.add_run(bullet.strip())
                        p.style = 'List Bullet'
            
            # Add skills
            if "skills" in cv_content and cv_content["skills"]:
                doc.add_heading('SKILLS', level=1)
                
                # Check if skills are in bullet format or comma-separated
                if "•" in cv_content["skills"] or "-" in cv_content["skills"]:
                    # Bullet format
                    skills_bullets = cv_content["skills"].split("\n")
                    for bullet in skills_bullets:
                        if bullet.strip():
                            p = doc.add_paragraph()
                            p.add_run(bullet.strip())
                            p.style = 'List Bullet'
                else:
                    # Comma-separated format
                    doc.add_paragraph(cv_content["skills"])
            
            # Add education
            if "education" in cv_content and cv_content["education"]:
                doc.add_heading('EDUCATION', level=1)
                
                # Split education into bullet points
                education_bullets = cv_content["education"].split("\n")
                for bullet in education_bullets:
                    if bullet.strip():
                        p = doc.add_paragraph()
                        p.add_run(bullet.strip())
                        p.style = 'List Bullet'
            
            # Add footnotes if available
            if "footnotes" in cv_content and cv_content["footnotes"]:
                doc.add_page_break()
                doc.add_heading('EVIDENCE & CITATIONS', level=1)
                doc.add_paragraph(cv_content["footnotes"])
            
            # Add a simple paragraph to ensure the document is not empty
            doc.add_paragraph("CV Content:")
            
            # Save the document
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                doc.save(output_path)
            else:
                # If no output path, save to the exports directory
                exports_dir = os.path.join(os.getcwd(), "exports")
                os.makedirs(exports_dir, exist_ok=True)
                template_name = template.get("id", "default")
                output_path = os.path.join(exports_dir, f"cv_{template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")
                doc.save(output_path)
            
            # Read the file content for return
            with open(output_path, 'rb') as f:
                docx_content = f.read()
            
            # Log success
            logger.info(f"Successfully created DOCX file at {output_path}")
            
            return {
                "status": "success",
                "format": "docx",
                "content": docx_content,
                "file_path": output_path
            }
        
        except Exception as e:
            logger.error(f"Error creating DOCX: {e}")
            return {
                "status": "error",
                "format": "docx",
                "error": str(e),
                "file_path": None
            }
    
    def _export_pdf(self, cv_content: Dict[str, str], template: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export CV as PDF."""
        try:
            # Create a buffer if no output path
            if not output_path:
                buffer = io.BytesIO()
                pdf_output = buffer
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                pdf_output = output_path
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                pdf_output,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Create styles
            styles = getSampleStyleSheet()
            
            # Define custom styles, checking if they already exist
            custom_styles = {
                'CustomHeading1': ParagraphStyle(
                    name='CustomHeading1',
                    parent=styles['Heading1'],
                    fontSize=14,
                    spaceAfter=12
                ),
                'CustomNormal': ParagraphStyle(
                    name='CustomNormal',
                    parent=styles['Normal'],
                    fontSize=11,
                    spaceAfter=6
                ),
                'CustomBullet': ParagraphStyle(
                    name='CustomBullet',
                    parent=styles['Normal'],
                    fontSize=11,
                    leftIndent=20,
                    firstLineIndent=-15,
                    spaceAfter=6
                )
            }
            
            # Add custom styles to the stylesheet
            for style_name, style in custom_styles.items():
                if style_name not in styles:
                    styles.add(style)
            
            # Build the document content
            content = []
            
            # Add contact information
            if "contact" in cv_content:
                contact_lines = cv_content["contact"].split("\n")
                # Name in larger font
                if contact_lines:
                    name_style = ParagraphStyle(
                        name='Name',
                        parent=styles['Normal'],
                        fontSize=16,
                        alignment=1,  # Center
                        spaceAfter=6
                    )
                    content.append(Paragraph(contact_lines[0], name_style))
                
                # Contact details
                if len(contact_lines) > 1:
                    contact_style = ParagraphStyle(
                        name='Contact',
                        parent=styles['Normal'],
                        fontSize=10,
                        alignment=1,  # Center
                        spaceAfter=12
                    )
                    content.append(Paragraph(" | ".join(contact_lines[1:]), contact_style))
            
            # Add summary
            if "summary" in cv_content and cv_content["summary"]:
                content.append(Paragraph("PROFESSIONAL SUMMARY", styles["CustomHeading1"]))
                content.append(Paragraph(cv_content["summary"], styles["CustomNormal"]))
                content.append(Spacer(1, 12))
            
            # Add experience
            if "experience" in cv_content and cv_content["experience"]:
                content.append(Paragraph("WORK EXPERIENCE", styles["CustomHeading1"]))
                
                # Split experience into bullet points
                experience_bullets = cv_content["experience"].split("\n")
                for bullet in experience_bullets:
                    if bullet.strip():
                        # Clean up bullet markers
                        clean_bullet = bullet.strip()
                        if clean_bullet.startswith("•") or clean_bullet.startswith("-"):
                            clean_bullet = clean_bullet[1:].strip()
                        content.append(Paragraph(f"• {clean_bullet}", styles["CustomBullet"]))
                
                content.append(Spacer(1, 12))
            
            # Add skills
            if "skills" in cv_content and cv_content["skills"]:
                content.append(Paragraph("SKILLS", styles["CustomHeading1"]))
                
                # Check if skills are in bullet format or comma-separated
                if "•" in cv_content["skills"] or "-" in cv_content["skills"]:
                    # Bullet format
                    skills_bullets = cv_content["skills"].split("\n")
                    for bullet in skills_bullets:
                        if bullet.strip():
                            # Clean up bullet markers
                            clean_bullet = bullet.strip()
                            if clean_bullet.startswith("•") or clean_bullet.startswith("-"):
                                clean_bullet = clean_bullet[1:].strip()
                            content.append(Paragraph(f"• {clean_bullet}", styles["CustomBullet"]))
                else:
                    # Comma-separated format
                    content.append(Paragraph(cv_content["skills"], styles["CustomNormal"]))
                
                content.append(Spacer(1, 12))
            
            # Add education
            if "education" in cv_content and cv_content["education"]:
                content.append(Paragraph("EDUCATION", styles["CustomHeading1"]))
                
                # Split education into bullet points
                education_bullets = cv_content["education"].split("\n")
                for bullet in education_bullets:
                    if bullet.strip():
                        # Clean up bullet markers
                        clean_bullet = bullet.strip()
                        if clean_bullet.startswith("•") or clean_bullet.startswith("-"):
                            clean_bullet = clean_bullet[1:].strip()
                        content.append(Paragraph(f"• {clean_bullet}", styles["CustomBullet"]))
                
                content.append(Spacer(1, 12))
            
            # Add footnotes if available
            if "footnotes" in cv_content and cv_content["footnotes"]:
                content.append(Paragraph("EVIDENCE & CITATIONS", styles["CustomHeading1"]))
                
                # Split footnotes into individual entries
                footnote_entries = cv_content["footnotes"].split("\n")
                for entry in footnote_entries:
                    if entry.strip():
                        content.append(Paragraph(entry.strip(), styles["CustomNormal"]))
            
            # Build the PDF
            doc.build(content)
            
            # Get the PDF content if using buffer
            if not output_path:
                pdf_content = buffer.getvalue()
                buffer.close()
                
                # Save to the exports directory
                exports_dir = os.path.join(os.getcwd(), "exports")
                os.makedirs(exports_dir, exist_ok=True)
                template_name = template.get("id", "default")
                output_path = os.path.join(exports_dir, f"cv_{template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
                with open(output_path, 'wb') as f:
                    f.write(pdf_content)
            else:
                # Read the file content for return
                with open(output_path, 'rb') as f:
                    pdf_content = f.read()
            
            return {
                "status": "success",
                "format": "pdf",
                "content": pdf_content,
                "file_path": output_path
            }
        
        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
            return {
                "status": "error",
                "format": "pdf",
                "error": str(e),
                "file_path": None
            }
    
    def _export_json(self, cv_data: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export CV as JSON."""
        # Save to file if output path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(cv_data, f, indent=2)
        
        return {
            "status": "success",
            "format": "json",
            "content": cv_data,
            "file_path": output_path
        }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates."""
        templates_info = []
        
        for template_id, template_data in self.templates.items():
            templates_info.append({
                "id": template_id,
                "name": template_data.get("name", template_id),
                "description": template_data.get("description", "")
            })
        
        return templates_info
