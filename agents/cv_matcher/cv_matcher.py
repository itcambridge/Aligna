"""
CV matcher agent using RAG to match job requirements against CV content.
"""

from typing import Dict, List, Any, Optional
from agents.job_breakdown.job_analyzer import JobRequirements
from modules.cv_ingestion.cv_processor import CVProcessor
import logging

logger = logging.getLogger(__name__)

class CVMatcher:
    """Match job requirements against CV content using RAG."""
    
    def __init__(self):
        """Initialize CV matcher."""
        self.cv_processor = CVProcessor()
    
    def match_job_requirements(
        self,
        job_requirements: JobRequirements,
        cv_id: str,
        user_id: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Match job requirements against CV content using RAG.
        
        Args:
            job_requirements: Structured job requirements
            cv_id: CV identifier
            user_id: User identifier
            top_k: Number of top matches to retrieve per requirement
            
        Returns:
            Matching results with evidence
        """
        matches = {
            "cv_id": cv_id,
            "user_id": user_id,
            "job_requirements": job_requirements.dict(),
            "matches": {},
            "summary": {}
        }
        
        try:
            # Match required skills
            if job_requirements.skills_required:
                matches["matches"]["required_skills"] = self._match_skills(
                    job_requirements.skills_required,
                    cv_id,
                    user_id,
                    top_k
                )
            
            # Match preferred skills
            if job_requirements.skills_preferred:
                matches["matches"]["preferred_skills"] = self._match_skills(
                    job_requirements.skills_preferred,
                    cv_id,
                    user_id,
                    top_k
                )
            
            # Match experience requirements
            if job_requirements.experience:
                matches["matches"]["experience"] = self._match_experience(
                    job_requirements.experience,
                    cv_id,
                    user_id,
                    top_k
                )
            
            # Match qualifications
            if job_requirements.qualifications:
                matches["matches"]["qualifications"] = self._match_qualifications(
                    job_requirements.qualifications,
                    cv_id,
                    user_id,
                    top_k
                )
            
            # Generate summary
            matches["summary"] = self._generate_match_summary(matches["matches"])
            
            logger.info(f"Successfully matched job requirements against CV {cv_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error matching job requirements: {e}")
            return {
                "cv_id": cv_id,
                "user_id": user_id,
                "error": str(e),
                "matches": {},
                "summary": {}
            }
    
    def _match_skills(
        self,
        skills: List[str],
        cv_id: str,
        user_id: str,
        top_k: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Match skills against CV content."""
        skill_matches = {}
        
        for skill in skills:
            # Search for similar chunks
            similar_chunks = self.cv_processor.search_similar_chunks(
                query=skill,
                cv_id=cv_id,
                user_id=user_id,
                limit=top_k
            )
            
            skill_matches[skill] = [
                {
                    "text": chunk["text"],
                    "score": chunk["score"],
                    "section": chunk["section"],
                    "metadata": chunk["metadata"]
                }
                for chunk in similar_chunks
            ]
        
        return skill_matches
    
    def _match_experience(
        self,
        experience_requirements: List[str],
        cv_id: str,
        user_id: str,
        top_k: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Match experience requirements against CV content."""
        experience_matches = {}
        
        for requirement in experience_requirements:
            # Search for similar chunks, focusing on experience sections
            similar_chunks = self.cv_processor.search_similar_chunks(
                query=requirement,
                cv_id=cv_id,
                user_id=user_id,
                limit=top_k
            )
            
            # Filter for experience-related sections
            experience_chunks = [
                chunk for chunk in similar_chunks
                if chunk["section"] in ["experience", "work", "employment"]
            ]
            
            experience_matches[requirement] = [
                {
                    "text": chunk["text"],
                    "score": chunk["score"],
                    "section": chunk["section"],
                    "metadata": chunk["metadata"]
                }
                for chunk in experience_chunks
            ]
        
        return experience_matches
    
    def _match_qualifications(
        self,
        qualifications: List[str],
        cv_id: str,
        user_id: str,
        top_k: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Match qualifications against CV content."""
        qualification_matches = {}
        
        for qualification in qualifications:
            # Search for similar chunks, focusing on education and certification sections
            similar_chunks = self.cv_processor.search_similar_chunks(
                query=qualification,
                cv_id=cv_id,
                user_id=user_id,
                limit=top_k
            )
            
            # Filter for education and certification sections
            qualification_chunks = [
                chunk for chunk in similar_chunks
                if chunk["section"] in ["education", "certifications", "qualifications"]
            ]
            
            qualification_matches[qualification] = [
                {
                    "text": chunk["text"],
                    "score": chunk["score"],
                    "section": chunk["section"],
                    "metadata": chunk["metadata"]
                }
                for chunk in qualification_chunks
            ]
        
        return qualification_matches
    
    def _generate_match_summary(self, matches: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the matching results."""
        summary = {
            "total_requirements": 0,
            "matched_requirements": 0,
            "strong_matches": 0,
            "weak_matches": 0,
            "no_matches": 0,
            "match_rate": 0.0,
            "average_score": 0.0
        }
        
        all_scores = []
        total_requirements = 0
        matched_requirements = 0
        
        for category, category_matches in matches.items():
            for requirement, requirement_matches in category_matches.items():
                total_requirements += 1
                
                if requirement_matches:
                    matched_requirements += 1
                    scores = [match["score"] for match in requirement_matches]
                    all_scores.extend(scores)
                    
                    # Categorize match strength
                    max_score = max(scores) if scores else 0
                    if max_score >= 0.7:
                        summary["strong_matches"] += 1
                    elif max_score >= 0.4:
                        summary["weak_matches"] += 1
                    else:
                        summary["no_matches"] += 1
                else:
                    summary["no_matches"] += 1
        
        summary["total_requirements"] = total_requirements
        summary["matched_requirements"] = matched_requirements
        summary["match_rate"] = matched_requirements / total_requirements if total_requirements > 0 else 0.0
        summary["average_score"] = sum(all_scores) / len(all_scores) if all_scores else 0.0
        
        return summary
    
    def get_match_evidence(
        self,
        requirement: str,
        cv_id: str,
        user_id: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get evidence for a specific requirement match.
        
        Args:
            requirement: Specific requirement to match
            cv_id: CV identifier
            user_id: User identifier
            top_k: Number of top matches to retrieve
            
        Returns:
            List of matching evidence with scores
        """
        similar_chunks = self.cv_processor.search_similar_chunks(
            query=requirement,
            cv_id=cv_id,
            user_id=user_id,
            limit=top_k
        )
        
        evidence = [
            {
                "requirement": requirement,
                "evidence_text": chunk["text"],
                "score": chunk["score"],
                "section": chunk["section"],
                "relevance": self._categorize_relevance(chunk["score"])
            }
            for chunk in similar_chunks
        ]
        
        return evidence
    
    def _categorize_relevance(self, score: float) -> str:
        """Categorize the relevance of a match based on score."""
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "very_low"
