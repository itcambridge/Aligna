"""
Requirement scorer for tracking evidence coverage and confidence scores.
Implements the requirement scoring contract to ensure zero hallucinations.
"""

import uuid
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from agents.job_breakdown.job_analyzer import JobRequirements
from modules.cv_ingestion.cv_processor import CVProcessor
import logging

logger = logging.getLogger(__name__)

@dataclass
class RequirementScore:
    """Scored requirement with evidence coverage."""
    req_id: str
    text: str
    category: str
    signals: Dict[str, Any]
    decision: Dict[str, Any]
    evidence: List[Dict[str, Any]]

class RequirementScorer:
    """Score job requirements against CV evidence with detailed coverage analysis."""
    
    def __init__(self):
        """Initialize requirement scorer."""
        self.cv_processor = CVProcessor()
        
    def score_requirements(
        self,
        job_requirements: JobRequirements,
        user_id: str,
        cv_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[RequirementScore]:
        """
        Score all job requirements against CV evidence.
        
        Args:
            job_requirements: Structured job requirements
            user_id: User identifier
            cv_ids: Specific CV IDs to search (None for all user CVs)
            top_k: Number of top matches to retrieve per requirement
            
        Returns:
            List of scored requirements with evidence coverage
        """
        scored_requirements = []
        
        try:
            # Score required skills
            if job_requirements.skills_required:
                for skill in job_requirements.skills_required:
                    score = self._score_requirement(
                        requirement=skill,
                        category="required_skill",
                        user_id=user_id,
                        cv_ids=cv_ids,
                        top_k=top_k
                    )
                    scored_requirements.append(score)
            
            # Score preferred skills
            if job_requirements.skills_preferred:
                for skill in job_requirements.skills_preferred:
                    score = self._score_requirement(
                        requirement=skill,
                        category="preferred_skill",
                        user_id=user_id,
                        cv_ids=cv_ids,
                        top_k=top_k
                    )
                    scored_requirements.append(score)
            
            # Score experience requirements
            if job_requirements.experience:
                for exp in job_requirements.experience:
                    score = self._score_requirement(
                        requirement=exp,
                        category="experience",
                        user_id=user_id,
                        cv_ids=cv_ids,
                        top_k=top_k
                    )
                    scored_requirements.append(score)
            
            # Score qualifications
            if job_requirements.qualifications:
                for qual in job_requirements.qualifications:
                    score = self._score_requirement(
                        requirement=qual,
                        category="qualification",
                        user_id=user_id,
                        cv_ids=cv_ids,
                        top_k=top_k
                    )
                    scored_requirements.append(score)
            
            logger.info(f"Successfully scored {len(scored_requirements)} requirements")
            return scored_requirements
            
        except Exception as e:
            logger.error(f"Error scoring requirements: {e}")
            return []
    
    def _score_requirement(
        self,
        requirement: str,
        category: str,
        user_id: str,
        cv_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> RequirementScore:
        """
        Score a single requirement against CV evidence.
        
        Args:
            requirement: The requirement text
            category: Requirement category
            user_id: User identifier
            cv_ids: Specific CV IDs to search
            top_k: Number of top matches
            
        Returns:
            Scored requirement with evidence
        """
        # Search for evidence
        evidence = self._search_evidence(requirement, user_id, cv_ids, top_k)
        
        # Calculate signals
        signals = self._calculate_signals(requirement, evidence)
        
        # Make decision
        decision = self._make_decision(requirement, evidence, signals)
        
        return RequirementScore(
            req_id=str(uuid.uuid4()),
            text=requirement,
            category=category,
            signals=signals,
            decision=decision,
            evidence=evidence
        )
    
    def _search_evidence(
        self,
        requirement: str,
        user_id: str,
        cv_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for evidence supporting the requirement."""
        try:
            # Search across user's CVs
            if cv_ids:
                # Search specific CVs
                all_evidence = []
                for cv_id in cv_ids:
                    evidence = self.cv_processor.search_similar_chunks(
                        query=requirement,
                        cv_id=cv_id,
                        user_id=user_id,
                        limit=top_k
                    )
                    all_evidence.extend(evidence)
                # Sort by score and take top_k
                all_evidence.sort(key=lambda x: x.get('score', 0), reverse=True)
                return all_evidence[:top_k]
            else:
                # Search across all user CVs
                return self.cv_processor.search_similar_chunks(
                    query=requirement,
                    user_id=user_id,
                    limit=top_k
                )
        except Exception as e:
            logger.error(f"Error searching evidence: {e}")
            return []
    
    def _calculate_signals(
        self,
        requirement: str,
        evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate scoring signals from evidence."""
        if not evidence:
            return {
                "semantic_top1": 0.0,
                "avg_top3": 0.0,
                "keyword_overlap": 0.0,
                "years_evidence": 0.0,
                "recency_years": 0.0,
                "evidence_count": 0
            }
        
        # Semantic scores
        scores = [e.get('score', 0.0) for e in evidence]
        semantic_top1 = scores[0] if scores else 0.0
        avg_top3 = sum(scores[:3]) / min(3, len(scores)) if scores else 0.0
        
        # Keyword overlap
        keyword_overlap = self._calculate_keyword_overlap(requirement, evidence)
        
        # Years evidence (extract from experience sections)
        years_evidence = self._extract_years_evidence(evidence)
        
        # Recency (most recent evidence)
        recency_years = self._calculate_recency(evidence)
        
        return {
            "semantic_top1": semantic_top1,
            "avg_top3": avg_top3,
            "keyword_overlap": keyword_overlap,
            "years_evidence": years_evidence,
            "recency_years": recency_years,
            "evidence_count": len(evidence)
        }
    
    def _calculate_keyword_overlap(
        self,
        requirement: str,
        evidence: List[Dict[str, Any]]
    ) -> float:
        """Calculate keyword overlap between requirement and evidence."""
        if not evidence:
            return 0.0
        
        # Extract keywords from requirement
        req_keywords = set(re.findall(r'\b\w+\b', requirement.lower()))
        
        # Extract keywords from evidence
        evidence_text = " ".join([e.get('text', '') for e in evidence])
        evidence_keywords = set(re.findall(r'\b\w+\b', evidence_text.lower()))
        
        # Calculate overlap
        if not req_keywords:
            return 0.0
        
        overlap = len(req_keywords.intersection(evidence_keywords))
        return overlap / len(req_keywords)
    
    def _extract_years_evidence(self, evidence: List[Dict[str, Any]]) -> float:
        """Extract years of experience from evidence."""
        total_years = 0.0
        
        for e in evidence:
            text = e.get('text', '')
            # Look for year patterns in experience sections
            if e.get('section', '').lower() in ['experience', 'work experience']:
                # Extract years from text (simple pattern matching)
                year_patterns = [
                    r'(\d+)\s*years?',
                    r'(\d+)\s*yr',
                    r'(\d+)\s*months?',
                    r'(\d+)\s*mo'
                ]
                
                for pattern in year_patterns:
                    matches = re.findall(pattern, text.lower())
                    for match in matches:
                        years = float(match)
                        if 'month' in pattern or 'mo' in pattern:
                            years /= 12
                        total_years += years
        
        return total_years
    
    def _calculate_recency(self, evidence: List[Dict[str, Any]]) -> float:
        """Calculate recency of evidence in years."""
        # This would need actual date extraction from CV
        # For now, return a placeholder
        return 1.0  # Assume 1 year ago
    
    def _make_decision(
        self,
        requirement: str,
        evidence: List[Dict[str, Any]],
        signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make coverage decision based on evidence and signals."""
        if not evidence:
            return {
                "covered": False,
                "confidence": 0.0,
                "gaps": [requirement],
                "closest_evidence": "No evidence found"
            }
        
        # Determine coverage based on signals
        semantic_score = signals["semantic_top1"]
        keyword_overlap = signals["keyword_overlap"]
        evidence_count = signals["evidence_count"]
        
        # Coverage decision logic (more realistic thresholds)
        covered = semantic_score >= 0.5 and keyword_overlap >= 0.2 and evidence_count > 0
        confidence = min(1.0, (semantic_score * 0.6 + keyword_overlap * 0.4) * (evidence_count / 3))
        
        # Identify gaps
        gaps = []
        if semantic_score < 0.7:
            gaps.append("Low semantic similarity")
        if keyword_overlap < 0.3:
            gaps.append("Limited keyword overlap")
        if evidence_count == 0:
            gaps.append("No evidence found")
        
        # Closest evidence
        closest_evidence = evidence[0].get('text', '')[:100] + "..." if evidence else "No evidence found"
        
        return {
            "covered": covered,
            "confidence": confidence,
            "gaps": gaps,
            "closest_evidence": closest_evidence
        }
