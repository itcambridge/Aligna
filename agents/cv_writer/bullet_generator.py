"""
Bullet Generator that implements the bullet_generator.schema.json contract.
Ensures every generated bullet has citations and risk flags.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class BulletInput(BaseModel):
    """Input for bullet generation following the contract."""
    requirement: str = Field(description="The job requirement being addressed")
    evidence_snippets: List[str] = Field(description="Evidence snippets to support the bullet")
    allowed_claims_only: bool = Field(default=True, description="Whether to only make claims supported by evidence")
    style_preference: str = Field(default="action", description="Preferred bullet point style")

class Citation(BaseModel):
    """Citation for a bullet point."""
    cv_id: str = Field(description="CV identifier")
    chunk_index: int = Field(description="Chunk index in the CV")
    section: str = Field(description="Section in the CV")
    snippet: str = Field(description="Text snippet from the CV")
    score: float = Field(description="Relevance score")

class BulletOutput(BaseModel):
    """Output from bullet generation following the contract."""
    bullet: str = Field(description="The generated bullet point text")
    citations: List[Citation] = Field(description="Citations supporting this bullet")
    risk_flags: List[str] = Field(description="Risk flags indicating potential issues")
    confidence: float = Field(description="Confidence score for this bullet")
    evidence_coverage: float = Field(description="Percentage of bullet content supported by evidence")

class BulletGenerator:
    """Generates evidence-based bullet points with citations and risk flags."""
    
    def __init__(self, model_name: str = "gpt-4"):
        """
        Initialize bullet generator.
        
        Args:
            model_name: OpenAI model to use for generation
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.2,  # Lower temperature for more deterministic output
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create the bullet generation prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert CV bullet point generator. Your task is to generate a single, impactful bullet point based on a job requirement and evidence snippets from the candidate's CV.

IMPORTANT RULES:
1. ONLY make claims that are directly supported by the provided evidence snippets
2. DO NOT fabricate or embellish accomplishments, metrics, or experiences
3. If the evidence is insufficient, create a conservative bullet that only mentions what's explicitly in the evidence
4. Use the specified style preference for the bullet format
5. Flag any inferences or assumptions you make
6. Aim for specificity and impact while maintaining strict accuracy

Style preferences:
- action: Start with strong action verb, focus on what was done
- impact: Emphasize results and outcomes with metrics when available
- technical: Highlight technical skills and methodologies
- leadership: Focus on team leadership, mentoring, and management aspects

Your output should be a single, concise bullet point that accurately represents the candidate's experience relevant to the job requirement."""),
            ("user", """Job Requirement:
{requirement}

Evidence Snippets:
{evidence_snippets}

Style Preference: {style_preference}
Allowed Claims Only: {allowed_claims_only}

Generate a single bullet point that addresses this requirement based ONLY on the evidence provided.""")
        ])
    
    def generate_bullet(self, input_data: BulletInput) -> BulletOutput:
        """
        Generate a bullet point based on requirement and evidence.
        
        Args:
            input_data: Bullet generation input following the contract
            
        Returns:
            Generated bullet with citations and risk flags
        """
        try:
            # Get response from LLM
            formatted_prompt = self.prompt.format_messages(
                requirement=input_data.requirement,
                evidence_snippets="\n\n".join([f"Evidence {i+1}: {snippet}" for i, snippet in enumerate(input_data.evidence_snippets)]),
                style_preference=input_data.style_preference,
                allowed_claims_only=str(input_data.allowed_claims_only)
            )
            
            response = self.llm.invoke(formatted_prompt)
            bullet_text = response.content.strip()
            
            # Extract any risk flags mentioned in the response
            risk_flags = self._extract_risk_flags(bullet_text, input_data)
            
            # Create citations from evidence snippets
            citations = self._create_citations(input_data.evidence_snippets)
            
            # Calculate confidence and evidence coverage
            confidence, evidence_coverage = self._calculate_metrics(bullet_text, input_data.evidence_snippets)
            
            # Clean up the bullet text (remove any notes or flags)
            clean_bullet = self._clean_bullet_text(bullet_text)
            
            return BulletOutput(
                bullet=clean_bullet,
                citations=citations,
                risk_flags=risk_flags,
                confidence=confidence,
                evidence_coverage=evidence_coverage
            )
            
        except Exception as e:
            logger.error(f"Error generating bullet: {e}")
            # Return a minimal bullet on error
            return BulletOutput(
                bullet=f"Experience related to {input_data.requirement}.",
                citations=[],
                risk_flags=["generation_error"],
                confidence=0.0,
                evidence_coverage=0.0
            )
    
    def _extract_risk_flags(self, bullet_text: str, input_data: BulletInput) -> List[str]:
        """Extract risk flags based on bullet text and evidence."""
        risk_flags = []
        
        # Check for metrics (numbers, percentages)
        if re.search(r'\d+%|\d+ percent|\d+x|\bincreased\b|\bimproved\b|\breduced\b|\bby \d+\b', bullet_text, re.IGNORECASE):
            has_metric_evidence = any(re.search(r'\d+%|\d+ percent|\d+x|\bincreased\b|\bimproved\b|\breduced\b|\bby \d+\b', snippet, re.IGNORECASE) for snippet in input_data.evidence_snippets)
            if not has_metric_evidence:
                risk_flags.append("metric_inferred")
        
        # Check for timeframes
        if re.search(r'\d+ years|\d+ months|\d+ weeks|\d+ days', bullet_text, re.IGNORECASE):
            has_timeframe_evidence = any(re.search(r'\d+ years|\d+ months|\d+ weeks|\d+ days', snippet, re.IGNORECASE) for snippet in input_data.evidence_snippets)
            if not has_timeframe_evidence:
                risk_flags.append("timeframe_inferred")
        
        # Check for scope references
        if re.search(r'team of \d+|enterprise|company-wide|global|multiple teams', bullet_text, re.IGNORECASE):
            has_scope_evidence = any(re.search(r'team of \d+|enterprise|company-wide|global|multiple teams', snippet, re.IGNORECASE) for snippet in input_data.evidence_snippets)
            if not has_scope_evidence:
                risk_flags.append("scope_inferred")
        
        # Check for role inferences
        if re.search(r'lead|manager|director|head|chief|supervisor', bullet_text, re.IGNORECASE):
            has_role_evidence = any(re.search(r'lead|manager|director|head|chief|supervisor', snippet, re.IGNORECASE) for snippet in input_data.evidence_snippets)
            if not has_role_evidence:
                risk_flags.append("role_inferred")
        
        # Check for technology mentions
        tech_pattern = r'python|java|javascript|typescript|react|angular|vue|node|aws|azure|gcp|docker|kubernetes|terraform|jenkins|git|agile|scrum|kanban'
        if re.search(tech_pattern, bullet_text, re.IGNORECASE):
            mentioned_techs = set(re.findall(tech_pattern, bullet_text, re.IGNORECASE))
            evidenced_techs = set()
            for snippet in input_data.evidence_snippets:
                evidenced_techs.update(re.findall(tech_pattern, snippet, re.IGNORECASE))
            
            if not mentioned_techs.issubset(evidenced_techs):
                risk_flags.append("technology_inferred")
        
        # Check for direct evidence
        if not input_data.evidence_snippets:
            risk_flags.append("no_direct_evidence")
        
        # Check confidence based on evidence overlap
        if self._calculate_metrics(bullet_text, input_data.evidence_snippets)[0] < 0.5:
            risk_flags.append("low_confidence_match")
        
        return risk_flags
    
    def _create_citations(self, evidence_snippets: List[str]) -> List[Citation]:
        """Create citation objects from evidence snippets."""
        citations = []
        
        for i, snippet in enumerate(evidence_snippets):
            # In a real implementation, these would come from the actual evidence
            # For now, we create placeholder values
            citation = Citation(
                cv_id="knowledge_base",
                chunk_index=i,
                section="Experience",  # This would be extracted from the actual evidence
                snippet=snippet,
                score=0.8  # This would be the actual relevance score
            )
            citations.append(citation)
        
        return citations
    
    def _calculate_metrics(self, bullet_text: str, evidence_snippets: List[str]) -> Tuple[float, float]:
        """Calculate confidence and evidence coverage metrics."""
        if not evidence_snippets:
            return 0.0, 0.0
        
        # Simple word overlap for confidence
        bullet_words = set(re.findall(r'\b\w+\b', bullet_text.lower()))
        evidence_words = set()
        for snippet in evidence_snippets:
            evidence_words.update(re.findall(r'\b\w+\b', snippet.lower()))
        
        if not bullet_words:
            return 0.0, 0.0
        
        # Calculate overlap
        overlap = len(bullet_words.intersection(evidence_words))
        confidence = min(1.0, overlap / len(bullet_words) if bullet_words else 0.0)
        
        # Calculate coverage (what percentage of bullet is covered by evidence)
        coverage = min(1.0, overlap / len(bullet_words) if bullet_words else 0.0)
        
        return confidence, coverage
    
    def _clean_bullet_text(self, bullet_text: str) -> str:
        """Clean up the bullet text by removing notes or flags."""
        # Remove any notes in brackets, parentheses, or after dashes
        clean_text = re.sub(r'\[.*?\]|\(.*?\)|--.*$|NOTE:.*$', '', bullet_text)
        
        # Remove any "Risk:" or "Flag:" annotations
        clean_text = re.sub(r'Risk:.*$|Flag:.*$', '', clean_text)
        
        # Ensure it starts with a capital letter and ends with a period
        clean_text = clean_text.strip()
        if clean_text and not clean_text[0].isupper():
            clean_text = clean_text[0].upper() + clean_text[1:]
        if clean_text and not clean_text.endswith('.'):
            clean_text += '.'
        
        return clean_text
    
    def generate_bullets_for_requirements(
        self,
        requirements: List[Dict[str, Any]],
        evidence_map: Dict[str, List[Dict[str, Any]]],
        style_preference: str = "action"
    ) -> Dict[str, List[BulletOutput]]:
        """
        Generate bullets for multiple requirements with evidence.
        
        Args:
            requirements: List of requirement objects
            evidence_map: Map of requirement IDs to evidence lists
            style_preference: Preferred bullet style
            
        Returns:
            Dictionary mapping requirement categories to bullet outputs
        """
        result = {}
        
        for req in requirements:
            req_id = req.get("req_id", "")
            category = req.get("category", "unknown")
            text = req.get("text", "")
            
            # Get evidence for this requirement
            evidence = evidence_map.get(req_id, [])
            evidence_snippets = [e.get("snippet", e.get("text", "")) for e in evidence]
            
            # Skip if no evidence and allowed_claims_only is True
            if not evidence_snippets:
                continue
            
            # Generate bullet
            bullet_input = BulletInput(
                requirement=text,
                evidence_snippets=evidence_snippets,
                allowed_claims_only=True,
                style_preference=style_preference
            )
            
            bullet_output = self.generate_bullet(bullet_input)
            
            # Add to result by category
            if category not in result:
                result[category] = []
            
            result[category].append(bullet_output)
        
        return result
