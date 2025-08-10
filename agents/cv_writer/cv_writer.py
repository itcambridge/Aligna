"""
CV writer agent for generating grounded CVs based on job requirements and CV content.
"""

import os
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from agents.job_breakdown.job_analyzer import JobRequirements
from agents.cv_matcher.cv_matcher import CVMatcher
import logging

logger = logging.getLogger(__name__)

class CVSection(BaseModel):
    """A section of the generated CV."""
    
    title: str = Field(description="Section title")
    content: str = Field(description="Section content")
    evidence: List[str] = Field(description="List of evidence sources used")

class GeneratedCV(BaseModel):
    """Complete generated CV with sections."""
    
    contact_info: Dict[str, str] = Field(description="Contact information")
    summary: CVSection = Field(description="Professional summary")
    experience: CVSection = Field(description="Work experience")
    skills: CVSection = Field(description="Skills section")
    education: CVSection = Field(description="Education section")
    additional_sections: List[CVSection] = Field(description="Additional sections like projects, certifications")
    match_evidence: Dict[str, Any] = Field(description="Evidence used for each section")

class CVWriter:
    """Generate grounded CVs based on job requirements and CV content."""
    
    def __init__(self, model_name: str = "gpt-4"):
        """
        Initialize CV writer.
        
        Args:
            model_name: OpenAI model to use for generation
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.parser = PydanticOutputParser(pydantic_object=GeneratedCV)
        self.cv_matcher = CVMatcher()
        
        # Create the CV generation prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert CV writer. Your task is to generate a tailored CV based on job requirements and the candidate's actual experience.

IMPORTANT RULES:
1. ONLY use information that is supported by the provided evidence
2. DO NOT make up or embellish any information
3. If there's no evidence for a requirement, clearly indicate this
4. Use the exact wording and details from the evidence when possible
5. Organize information in a professional, clear format
6. Focus on relevance to the job requirements

Generate a CV with the following sections:
- Contact Information (from original CV)
- Professional Summary (tailored to job requirements)
- Work Experience (relevant experience only)
- Skills (matching job requirements)
- Education (relevant qualifications)
- Additional sections as needed

Use the provided evidence to support each section."""),
            ("user", """Job Requirements:
{job_requirements}

CV Evidence:
{cv_evidence}

Contact Information:
{contact_info}

Generate a tailored CV using ONLY the provided evidence.""")
        ])
    
    def generate_cv(
        self,
        job_requirements: JobRequirements,
        cv_matches: Dict[str, Any],
        contact_info: Dict[str, str],
        cv_id: str,
        user_id: str
    ) -> GeneratedCV:
        """
        Generate a grounded CV based on job requirements and CV evidence.
        
        Args:
            job_requirements: Structured job requirements
            cv_matches: Matching results from CV matcher
            contact_info: Contact information from original CV
            cv_id: CV identifier
            user_id: User identifier
            
        Returns:
            Generated CV with evidence
        """
        try:
            # Prepare evidence for the prompt
            cv_evidence = self._prepare_cv_evidence(cv_matches)
            
            # Get response from LLM
            formatted_prompt = self.prompt.format_messages(
                job_requirements=job_requirements.dict(),
                cv_evidence=cv_evidence,
                contact_info=contact_info
            )
            formatted_prompt.append(("system", f"Format your response as JSON according to this schema:\n{self.parser.get_format_instructions()}"))
            
            response = self.llm.invoke(formatted_prompt)
            
            # Try to parse with Pydantic parser
            try:
                result = self.parser.parse(response.content)
                logger.info(f"Successfully generated CV for user {user_id} with Pydantic parser")
            except Exception as parse_error:
                logger.warning(f"Pydantic parsing failed: {parse_error}, trying manual parsing")
                # Fallback: manual parsing from text response
                result = self._parse_text_cv_response(response.content, contact_info, cv_matches)
                logger.info(f"Successfully generated CV for user {user_id} with manual parsing")
            
            # Add match evidence to the result
            result.match_evidence = cv_matches
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating CV: {e}")
            # Return a minimal CV structure on error
            return self._create_fallback_cv(contact_info, cv_matches)
    
    def _prepare_cv_evidence(self, cv_matches: Dict[str, Any]) -> str:
        """Prepare CV evidence for the prompt."""
        evidence_parts = []
        
        # Handle different cv_matches structures
        if "matches" in cv_matches and isinstance(cv_matches["matches"], list):
            # Knowledge base format: list of matches
            evidence_parts.append("RELEVANT EXPERIENCE FROM CV KNOWLEDGE BASE:")
            evidence_parts.append("-" * 50)
            
            for i, match in enumerate(cv_matches["matches"][:10], 1):  # Top 10 matches
                text = match.get("text", "No text available")
                score = match.get("score", 0.0)
                section = match.get("section", "Unknown section")
                cv_id = match.get("cv_id", "Unknown CV")
                
                evidence_parts.append(f"{i}. [{section}] {text}")
                evidence_parts.append(f"   Source: CV {cv_id[:8]}... | Relevance: {score:.2f}")
                evidence_parts.append("")
                
        elif "matches" in cv_matches and isinstance(cv_matches["matches"], dict):
            # Original format: nested dictionary
            for category, category_matches in cv_matches["matches"].items():
                evidence_parts.append(f"\n{category.upper()}:")
                
                for requirement, matches in category_matches.items():
                    evidence_parts.append(f"\n  {requirement}:")
                    
                    if matches:
                        for i, match in enumerate(matches[:3], 1):  # Top 3 matches
                            evidence_parts.append(f"    {i}. {match['text']} (Score: {match['score']:.2f})")
                    else:
                        evidence_parts.append("    No matching evidence found")
        else:
            # Fallback: try to extract any available matches
            evidence_parts.append("AVAILABLE EVIDENCE:")
            evidence_parts.append("-" * 30)
            
            # Look for any list of matches in the structure
            matches = []
            if isinstance(cv_matches, dict):
                for key, value in cv_matches.items():
                    if isinstance(value, list) and value:
                        matches.extend(value)
            
            if matches:
                for i, match in enumerate(matches[:10], 1):
                    if isinstance(match, dict):
                        text = match.get("text", str(match))
                        score = match.get("score", "N/A")
                        evidence_parts.append(f"{i}. {text} (Score: {score})")
            else:
                evidence_parts.append("No evidence available")
        
        return "\n".join(evidence_parts)
    
    def _parse_text_cv_response(self, text_response: str, contact_info: Dict[str, str], cv_matches: Dict[str, Any]) -> GeneratedCV:
        """
        Manually parse text CV response when JSON parsing fails.
        
        Args:
            text_response: Raw text response from LLM
            contact_info: Contact information
            cv_matches: CV matches for evidence
            
        Returns:
            Parsed GeneratedCV
        """
        try:
            # Initialize sections
            summary_content = ""
            experience_content = ""
            skills_content = ""
            education_content = ""
            
            # Split response into lines and parse sections
            lines = text_response.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identify section headers
                if 'professional summary' in line.lower() or 'summary' in line.lower():
                    if current_section and current_content:
                        self._assign_section_content(current_section, '\n'.join(current_content), locals())
                    current_section = 'summary'
                    current_content = []
                elif 'work experience' in line.lower() or 'experience' in line.lower():
                    if current_section and current_content:
                        self._assign_section_content(current_section, '\n'.join(current_content), locals())
                    current_section = 'experience'
                    current_content = []
                elif 'skills' in line.lower():
                    if current_section and current_content:
                        self._assign_section_content(current_section, '\n'.join(current_content), locals())
                    current_section = 'skills'
                    current_content = []
                elif 'education' in line.lower():
                    if current_section and current_content:
                        self._assign_section_content(current_section, '\n'.join(current_content), locals())
                    current_section = 'education'
                    current_content = []
                elif not line.startswith('*') and not line.startswith('#') and current_section:
                    # This is content for the current section
                    current_content.append(line)
            
            # Handle the last section
            if current_section and current_content:
                self._assign_section_content(current_section, '\n'.join(current_content), locals())
            
            # If no sections were parsed, use the entire response as summary
            if not summary_content and not experience_content and not skills_content and not education_content:
                summary_content = text_response[:500] + "..." if len(text_response) > 500 else text_response
            
            logger.info("Successfully parsed text CV response manually")
            return GeneratedCV(
                contact_info=contact_info,
                summary=CVSection(
                    title="Professional Summary",
                    content=summary_content or "Professional summary could not be extracted.",
                    evidence=[]
                ),
                experience=CVSection(
                    title="Work Experience",
                    content=experience_content or "Work experience could not be extracted.",
                    evidence=[]
                ),
                skills=CVSection(
                    title="Skills",
                    content=skills_content or "Skills could not be extracted.",
                    evidence=[]
                ),
                education=CVSection(
                    title="Education",
                    content=education_content or "Education could not be extracted.",
                    evidence=[]
                ),
                additional_sections=[],
                match_evidence=cv_matches
            )
            
        except Exception as e:
            logger.error(f"Error in manual CV parsing: {e}")
            return self._create_fallback_cv(contact_info, cv_matches)
    
    def _assign_section_content(self, section: str, content: str, local_vars: dict):
        """Helper method to assign content to section variables."""
        if section == 'summary':
            local_vars['summary_content'] = content
        elif section == 'experience':
            local_vars['experience_content'] = content
        elif section == 'skills':
            local_vars['skills_content'] = content
        elif section == 'education':
            local_vars['education_content'] = content
    
    def _create_fallback_cv(self, contact_info: Dict[str, str], cv_matches: Dict[str, Any]) -> GeneratedCV:
        """Create a fallback CV when generation fails."""
        return GeneratedCV(
            contact_info=contact_info,
            summary=CVSection(
                title="Professional Summary",
                content="CV generation failed. Please check the original CV content.",
                evidence=[]
            ),
            experience=CVSection(
                title="Work Experience",
                content="Experience section could not be generated.",
                evidence=[]
            ),
            skills=CVSection(
                title="Skills",
                content="Skills section could not be generated.",
                evidence=[]
            ),
            education=CVSection(
                title="Education",
                content="Education section could not be generated.",
                evidence=[]
            ),
            additional_sections=[],
            match_evidence=cv_matches
        )
    
    def generate_cv_text(self, generated_cv: GeneratedCV) -> str:
        """
        Convert the generated CV to plain text format.
        
        Args:
            generated_cv: Generated CV object
            
        Returns:
            Formatted CV text
        """
        cv_text = []
        
        # Contact Information
        cv_text.append("CONTACT INFORMATION")
        cv_text.append("=" * 50)
        for key, value in generated_cv.contact_info.items():
            cv_text.append(f"{key.title()}: {value}")
        cv_text.append("")
        
        # Summary
        cv_text.append("PROFESSIONAL SUMMARY")
        cv_text.append("=" * 50)
        cv_text.append(generated_cv.summary.content)
        cv_text.append("")
        
        # Experience
        cv_text.append("WORK EXPERIENCE")
        cv_text.append("=" * 50)
        cv_text.append(generated_cv.experience.content)
        cv_text.append("")
        
        # Skills
        cv_text.append("SKILLS")
        cv_text.append("=" * 50)
        cv_text.append(generated_cv.skills.content)
        cv_text.append("")
        
        # Education
        cv_text.append("EDUCATION")
        cv_text.append("=" * 50)
        cv_text.append(generated_cv.education.content)
        cv_text.append("")
        
        # Additional sections
        for section in generated_cv.additional_sections:
            cv_text.append(section.title.upper())
            cv_text.append("=" * 50)
            cv_text.append(section.content)
            cv_text.append("")
        
        return "\n".join(cv_text)
    
    def generate_cv_with_evidence_report(self, generated_cv: GeneratedCV) -> str:
        """
        Generate a report showing the evidence used for each section.
        
        Args:
            generated_cv: Generated CV object
            
        Returns:
            Evidence report text
        """
        report = []
        report.append("CV GENERATION EVIDENCE REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Summary evidence
        report.append("PROFESSIONAL SUMMARY EVIDENCE:")
        report.append("-" * 30)
        for evidence in generated_cv.summary.evidence:
            report.append(f"• {evidence}")
        report.append("")
        
        # Experience evidence
        report.append("WORK EXPERIENCE EVIDENCE:")
        report.append("-" * 30)
        for evidence in generated_cv.experience.evidence:
            report.append(f"• {evidence}")
        report.append("")
        
        # Skills evidence
        report.append("SKILLS EVIDENCE:")
        report.append("-" * 30)
        for evidence in generated_cv.skills.evidence:
            report.append(f"• {evidence}")
        report.append("")
        
        # Education evidence
        report.append("EDUCATION EVIDENCE:")
        report.append("-" * 30)
        for evidence in generated_cv.education.evidence:
            report.append(f"• {evidence}")
        report.append("")
        
        # Additional sections evidence
        for section in generated_cv.additional_sections:
            report.append(f"{section.title.upper()} EVIDENCE:")
            report.append("-" * 30)
            for evidence in section.evidence:
                report.append(f"• {evidence}")
            report.append("")
        
        return "\n".join(report)
