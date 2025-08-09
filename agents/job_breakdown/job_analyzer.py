"""
Job analyzer agent using LangChain to extract structured requirements from job descriptions.
"""

import os
import json
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class JobRequirements(BaseModel):
    """Structured job requirements extracted from job description."""
    
    skills_required: List[str] = Field(description="List of required skills and technologies")
    skills_preferred: List[str] = Field(description="List of preferred or nice-to-have skills")
    experience: List[str] = Field(description="List of experience requirements")
    qualifications: List[str] = Field(description="List of educational or certification requirements")
    responsibilities: List[str] = Field(description="List of key responsibilities and duties")
    industry: Optional[str] = Field(description="Industry or domain of the job")
    level: Optional[str] = Field(description="Job level (entry, mid, senior, lead, etc.)")

class JobAnalyzer:
    """Analyze job descriptions and extract structured requirements using LangChain."""
    
    def __init__(self, model_name: str = "gpt-4"):
        """
        Initialize job analyzer.
        
        Args:
            model_name: OpenAI model to use for analysis
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.parser = PydanticOutputParser(pydantic_object=JobRequirements)
        
        # Create the analysis prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert job analyst. Your task is to extract structured information from job descriptions.
            
            Extract the following information:
            - Required skills and technologies
            - Preferred or nice-to-have skills
            - Experience requirements
            - Educational or certification requirements
            - Key responsibilities and duties
            - Industry or domain
            - Job level (entry, mid, senior, lead, etc.)
            
            Be specific and detailed. If information is not explicitly mentioned, leave the field empty or use "Not specified".
            """),
            ("user", "Analyze the following job description and extract structured requirements:\n\n{job_description}")
        ])
    
    def analyze_job_description(self, job_description: str) -> JobRequirements:
        """
        Analyze a job description and extract structured requirements.
        
        Args:
            job_description: Raw job description text
            
        Returns:
            Structured job requirements
        """
        try:
            # Create the chain
            chain = self.prompt | self.llm | self.parser
            
            # Run the analysis
            result = chain.invoke({"job_description": job_description})
            
            logger.info("Successfully analyzed job description")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing job description: {e}")
            # Return empty requirements on error
            return JobRequirements(
                skills_required=[],
                skills_preferred=[],
                experience=[],
                qualifications=[],
                responsibilities=[],
                industry=None,
                level=None
            )
    
    def analyze_multiple_jobs(self, job_descriptions: List[str]) -> List[JobRequirements]:
        """
        Analyze multiple job descriptions.
        
        Args:
            job_descriptions: List of job description texts
            
        Returns:
            List of structured job requirements
        """
        results = []
        for i, description in enumerate(job_descriptions):
            logger.info(f"Analyzing job {i+1}/{len(job_descriptions)}")
            result = self.analyze_job_description(description)
            results.append(result)
        
        return results
    
    def compare_job_requirements(self, requirements1: JobRequirements, requirements2: JobRequirements) -> Dict[str, Any]:
        """
        Compare two job requirements and find similarities and differences.
        
        Args:
            requirements1: First job requirements
            requirements2: Second job requirements
            
        Returns:
            Comparison results
        """
        comparison = {
            "common_required_skills": list(set(requirements1.skills_required) & set(requirements2.skills_required)),
            "common_preferred_skills": list(set(requirements1.skills_preferred) & set(requirements2.skills_preferred)),
            "unique_required_skills_1": list(set(requirements1.skills_required) - set(requirements2.skills_required)),
            "unique_required_skills_2": list(set(requirements2.skills_required) - set(requirements1.skills_required)),
            "similarity_score": self._calculate_similarity_score(requirements1, requirements2)
        }
        
        return comparison
    
    def _calculate_similarity_score(self, req1: JobRequirements, req2: JobRequirements) -> float:
        """Calculate similarity score between two job requirements."""
        # Simple Jaccard similarity for required skills
        set1 = set(req1.skills_required)
        set2 = set(req2.skills_required)
        
        if not set1 and not set2:
            return 1.0
        elif not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def generate_job_summary(self, requirements: JobRequirements) -> str:
        """
        Generate a human-readable summary of job requirements.
        
        Args:
            requirements: Job requirements to summarize
            
        Returns:
            Summary text
        """
        summary_parts = []
        
        if requirements.level:
            summary_parts.append(f"Level: {requirements.level}")
        
        if requirements.industry:
            summary_parts.append(f"Industry: {requirements.industry}")
        
        if requirements.skills_required:
            summary_parts.append(f"Required Skills: {', '.join(requirements.skills_required)}")
        
        if requirements.skills_preferred:
            summary_parts.append(f"Preferred Skills: {', '.join(requirements.skills_preferred)}")
        
        if requirements.experience:
            summary_parts.append(f"Experience: {'; '.join(requirements.experience)}")
        
        if requirements.qualifications:
            summary_parts.append(f"Qualifications: {'; '.join(requirements.qualifications)}")
        
        return "\n".join(summary_parts)
