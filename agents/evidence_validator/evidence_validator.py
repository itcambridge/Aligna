"""
Main evidence validator for ensuring zero hallucinations in CV generation.
Orchestrates requirement scoring and coverage matrix generation.
"""

from typing import Dict, List, Any, Optional
from .requirement_scorer import RequirementScorer, RequirementScore
from .coverage_matrix import CoverageMatrix, CoverageSummary
from agents.job_breakdown.job_analyzer import JobRequirements
import logging
import re

logger = logging.getLogger(__name__)

class EvidenceValidator:
    """Main evidence validation system to ensure zero hallucinations."""
    
    def __init__(self):
        """Initialize evidence validator."""
        self.requirement_scorer = RequirementScorer()
        self.coverage_matrix = CoverageMatrix()
    
    def validate_evidence(
        self,
        job_requirements: JobRequirements,
        user_id: str,
        cv_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Validate evidence coverage for all job requirements.
        
        Args:
            job_requirements: Structured job requirements
            user_id: User identifier
            cv_ids: Specific CV IDs to search (None for all user CVs)
            top_k: Number of top matches to retrieve per requirement
            
        Returns:
            Comprehensive evidence validation results
        """
        logger.info(f"Validating evidence for user {user_id}")
        
        try:
            # Score all requirements
            scored_requirements = self.requirement_scorer.score_requirements(
                job_requirements=job_requirements,
                user_id=user_id,
                cv_ids=cv_ids,
                top_k=top_k
            )
            
            # Generate coverage matrix
            coverage_matrix = self.coverage_matrix.generate_coverage_matrix(scored_requirements)
            
            # Validate evidence integrity
            validation_results = self._validate_evidence_integrity(scored_requirements)
            
            # Generate summary
            summary = self._generate_validation_summary(scored_requirements, coverage_matrix, validation_results)
            
            result = {
                "status": "success",
                "user_id": user_id,
                "scored_requirements": [self._requirement_score_to_dict(req) for req in scored_requirements],
                "coverage_matrix": coverage_matrix,
                "validation_results": validation_results,
                "summary": summary,
                "hallucination_risk": self._assess_hallucination_risk(coverage_matrix, validation_results)
            }
            
            logger.info(f"Evidence validation complete for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating evidence: {e}")
            return {
                "status": "error",
                "error": str(e),
                "user_id": user_id
            }
    
    def get_covered_requirements(
        self,
        scored_requirements: List[RequirementScore],
        min_confidence: float = 0.7
    ) -> List[RequirementScore]:
        """
        Get requirements that are covered with sufficient evidence.
        
        Args:
            scored_requirements: List of scored requirements
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of covered requirements
        """
        return [
            req for req in scored_requirements
            if req.decision["covered"] and req.decision["confidence"] >= min_confidence
        ]
    
    def get_gap_requirements(
        self,
        scored_requirements: List[RequirementScore]
    ) -> List[RequirementScore]:
        """
        Get requirements that have gaps or insufficient evidence.
        
        Args:
            scored_requirements: List of scored requirements
            
        Returns:
            List of requirements with gaps
        """
        return [
            req for req in scored_requirements
            if not req.decision["covered"]
        ]
    
    def validate_bullet_point(
        self,
        bullet_text: str,
        requirement: str,
        evidence_snippets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate a single bullet point against evidence.
        
        Args:
            bullet_text: The bullet point text
            requirement: The requirement it addresses
            evidence_snippets: Supporting evidence
            
        Returns:
            Validation results for the bullet point
        """
        # Check if bullet has citations
        has_citations = len(evidence_snippets) > 0
        
        # Check evidence relevance
        evidence_relevance = self._check_evidence_relevance(bullet_text, evidence_snippets)
        
        # Check for potential hallucinations
        hallucination_indicators = self._detect_hallucination_indicators(bullet_text, evidence_snippets)
        
        # Calculate confidence
        confidence = self._calculate_bullet_confidence(evidence_relevance, hallucination_indicators)
        
        return {
            "bullet_text": bullet_text,
            "requirement": requirement,
            "has_citations": has_citations,
            "evidence_count": len(evidence_snippets),
            "evidence_relevance": evidence_relevance,
            "hallucination_indicators": hallucination_indicators,
            "confidence": confidence,
            "is_valid": has_citations and confidence >= 0.7,
            "risk_flags": self._generate_risk_flags(evidence_relevance, hallucination_indicators)
        }
    
    def _validate_evidence_integrity(
        self,
        scored_requirements: List[RequirementScore]
    ) -> Dict[str, Any]:
        """Validate the integrity of evidence across all requirements."""
        total_requirements = len(scored_requirements)
        requirements_with_evidence = sum(1 for req in scored_requirements if req.evidence)
        requirements_covered = sum(1 for req in scored_requirements if req.decision["covered"])
        
        # Check for evidence consistency
        evidence_consistency = self._check_evidence_consistency(scored_requirements)
        
        # Check for duplicate evidence
        duplicate_evidence = self._check_duplicate_evidence(scored_requirements)
        
        return {
            "total_requirements": total_requirements,
            "requirements_with_evidence": requirements_with_evidence,
            "requirements_covered": requirements_covered,
            "evidence_coverage_rate": requirements_with_evidence / total_requirements if total_requirements > 0 else 0.0,
            "evidence_consistency": evidence_consistency,
            "duplicate_evidence": duplicate_evidence,
            "integrity_score": self._calculate_integrity_score(scored_requirements)
        }
    
    def _check_evidence_consistency(
        self,
        scored_requirements: List[RequirementScore]
    ) -> Dict[str, Any]:
        """Check consistency of evidence across requirements."""
        # Collect all evidence
        all_evidence = []
        for req in scored_requirements:
            all_evidence.extend(req.evidence)
        
        # Check for conflicting information
        conflicts = []
        
        # Check for evidence quality
        quality_issues = []
        for evidence in all_evidence:
            text = evidence.get('text', '')
            if len(text) < 10:
                quality_issues.append("Very short evidence snippet")
            elif len(text) > 500:
                quality_issues.append("Very long evidence snippet")
        
        return {
            "total_evidence_snippets": len(all_evidence),
            "conflicts": conflicts,
            "quality_issues": quality_issues,
            "consistency_score": 1.0 - (len(conflicts) + len(quality_issues)) / max(len(all_evidence), 1)
        }
    
    def _check_duplicate_evidence(
        self,
        scored_requirements: List[RequirementScore]
    ) -> Dict[str, Any]:
        """Check for duplicate evidence across requirements."""
        evidence_texts = []
        duplicates = []
        
        for req in scored_requirements:
            for evidence in req.evidence:
                text = evidence.get('text', '').strip()
                if text in evidence_texts:
                    duplicates.append(text[:100] + "...")
                else:
                    evidence_texts.append(text)
        
        return {
            "total_evidence_snippets": len(evidence_texts),
            "duplicate_count": len(duplicates),
            "duplicate_rate": len(duplicates) / len(evidence_texts) if evidence_texts else 0.0,
            "duplicates": duplicates
        }
    
    def _calculate_integrity_score(
        self,
        scored_requirements: List[RequirementScore]
    ) -> float:
        """Calculate overall evidence integrity score."""
        if not scored_requirements:
            return 0.0
        
        # Factors to consider:
        # 1. Coverage rate
        coverage_rate = sum(1 for req in scored_requirements if req.evidence) / len(scored_requirements)
        
        # 2. Average confidence
        avg_confidence = sum(req.decision["confidence"] for req in scored_requirements) / len(scored_requirements)
        
        # 3. Evidence quality (based on length and relevance)
        quality_scores = []
        for req in scored_requirements:
            if req.evidence:
                # Calculate quality based on evidence length and scores
                evidence_scores = [e.get('score', 0.0) for e in req.evidence]
                avg_evidence_score = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.0
                quality_scores.append(avg_evidence_score)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Weighted average
        integrity_score = (coverage_rate * 0.4 + avg_confidence * 0.4 + avg_quality * 0.2)
        
        return integrity_score
    
    def _check_evidence_relevance(
        self,
        bullet_text: str,
        evidence_snippets: List[Dict[str, Any]]
    ) -> float:
        """Check relevance of evidence to bullet point."""
        if not evidence_snippets:
            return 0.0
        
        # Simple keyword overlap check
        bullet_words = set(bullet_text.lower().split())
        total_relevance = 0.0
        
        for evidence in evidence_snippets:
            evidence_text = evidence.get('text', '').lower()
            evidence_words = set(evidence_text.split())
            
            if bullet_words:
                overlap = len(bullet_words.intersection(evidence_words))
                relevance = overlap / len(bullet_words)
                total_relevance += relevance
        
        return total_relevance / len(evidence_snippets)
    
    def _detect_hallucination_indicators(
        self,
        bullet_text: str,
        evidence_snippets: List[Dict[str, Any]]
    ) -> List[str]:
        """Detect potential hallucination indicators in bullet point."""
        indicators = []
        
        if not evidence_snippets:
            indicators.append("no_evidence")
            return indicators
        
        # Check for specific metrics that might be inferred
        metric_patterns = [
            r'\d+%',  # Percentages
            r'\$\d+',  # Dollar amounts
            r'\d+\s*(million|billion|thousand)',  # Large numbers
            r'\d+\s*(users|customers|clients)',  # User counts
        ]
        
        for pattern in metric_patterns:
            if re.search(pattern, bullet_text):
                # Check if this metric appears in evidence
                metric_in_evidence = False
                for evidence in evidence_snippets:
                    if re.search(pattern, evidence.get('text', '')):
                        metric_in_evidence = True
                        break
                
                if not metric_in_evidence:
                    indicators.append("metric_inferred")
        
        # Check for timeframes
        timeframe_patterns = [
            r'\d+\s*(years?|months?|weeks?)',
            r'(annual|monthly|weekly|daily)',
        ]
        
        for pattern in timeframe_patterns:
            if re.search(pattern, bullet_text):
                timeframe_in_evidence = False
                for evidence in evidence_snippets:
                    if re.search(pattern, evidence.get('text', '')):
                        timeframe_in_evidence = True
                        break
                
                if not timeframe_in_evidence:
                    indicators.append("timeframe_inferred")
        
        return indicators
    
    def _calculate_bullet_confidence(
        self,
        evidence_relevance: float,
        hallucination_indicators: List[str]
    ) -> float:
        """Calculate confidence score for a bullet point."""
        # Base confidence on evidence relevance
        confidence = evidence_relevance
        
        # Penalize for hallucination indicators
        penalty = len(hallucination_indicators) * 0.2
        confidence = max(0.0, confidence - penalty)
        
        return confidence
    
    def _generate_risk_flags(
        self,
        evidence_relevance: float,
        hallucination_indicators: List[str]
    ) -> List[str]:
        """Generate risk flags for bullet point."""
        flags = []
        
        if evidence_relevance < 0.3:
            flags.append("low_evidence_relevance")
        
        if "no_evidence" in hallucination_indicators:
            flags.append("no_direct_evidence")
        
        if "metric_inferred" in hallucination_indicators:
            flags.append("metric_inferred")
        
        if "timeframe_inferred" in hallucination_indicators:
            flags.append("timeframe_inferred")
        
        return flags
    
    def _assess_hallucination_risk(
        self,
        coverage_matrix: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall hallucination risk."""
        summary = coverage_matrix.get("summary", {})
        
        # Risk factors
        low_coverage = summary.get("overall_coverage_rate", 0.0) < 0.5
        low_confidence = summary.get("average_confidence", 0.0) < 0.6
        low_integrity = validation_results.get("integrity_score", 0.0) < 0.7
        
        # Calculate risk level
        risk_factors = sum([low_coverage, low_confidence, low_integrity])
        
        if risk_factors == 0:
            risk_level = "low"
        elif risk_factors == 1:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "risk_level": risk_level,
            "risk_factors": {
                "low_coverage": low_coverage,
                "low_confidence": low_confidence,
                "low_integrity": low_integrity
            },
            "recommendations": self._generate_risk_recommendations(risk_level, risk_factors)
        }
    
    def _generate_risk_recommendations(
        self,
        risk_level: str,
        risk_factors: int
    ) -> List[str]:
        """Generate recommendations based on hallucination risk."""
        recommendations = []
        
        if risk_level == "high":
            recommendations.extend([
                "High hallucination risk detected. Review all generated content carefully.",
                "Consider adding more CV content to improve evidence coverage.",
                "Verify all claims against original CV evidence."
            ])
        elif risk_level == "medium":
            recommendations.extend([
                "Medium hallucination risk. Review generated content for accuracy.",
                "Focus on sections with low evidence coverage."
            ])
        else:
            recommendations.append("Low hallucination risk. Content appears well-grounded.")
        
        return recommendations
    
    def _generate_validation_summary(
        self,
        scored_requirements: List[RequirementScore],
        coverage_matrix: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive validation summary."""
        return {
            "total_requirements": len(scored_requirements),
            "coverage_summary": coverage_matrix.get("summary", {}),
            "validation_results": validation_results,
            "evidence_quality": {
                "avg_evidence_per_requirement": sum(len(req.evidence) for req in scored_requirements) / len(scored_requirements) if scored_requirements else 0,
                "requirements_with_evidence": sum(1 for req in scored_requirements if req.evidence),
                "requirements_fully_covered": sum(1 for req in scored_requirements if req.decision["covered"])
            }
        }
    
    def _requirement_score_to_dict(self, req: RequirementScore) -> Dict[str, Any]:
        """Convert RequirementScore to dictionary."""
        return {
            "req_id": req.req_id,
            "text": req.text,
            "category": req.category,
            "signals": req.signals,
            "decision": req.decision,
            "evidence": req.evidence
        }
