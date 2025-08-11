"""
Coverage matrix for tracking job requirement coverage and gaps.
Provides comprehensive analysis of evidence coverage across all requirements.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .requirement_scorer import RequirementScore
import logging

logger = logging.getLogger(__name__)

@dataclass
class CoverageSummary:
    """Summary of coverage across all requirements."""
    total_requirements: int
    covered_requirements: int
    partial_requirements: int
    uncovered_requirements: int
    overall_coverage_rate: float
    average_confidence: float
    critical_gaps: List[str]
    coverage_by_category: Dict[str, Dict[str, Any]]

@dataclass
class GapAnalysis:
    """Analysis of gaps in requirement coverage."""
    gap_id: str
    requirement: str
    category: str
    gap_type: str  # "no_evidence", "low_confidence", "partial_coverage"
    closest_evidence: str
    confidence: float
    recommendations: List[str]

class CoverageMatrix:
    """Generate coverage matrix and gap analysis for job requirements."""
    
    def __init__(self):
        """Initialize coverage matrix."""
        pass
    
    def generate_coverage_matrix(
        self,
        scored_requirements: List[RequirementScore]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive coverage matrix.
        
        Args:
            scored_requirements: List of scored requirements
            
        Returns:
            Coverage matrix with summary and detailed analysis
        """
        try:
            # Generate summary
            summary = self._generate_summary(scored_requirements)
            
            # Analyze gaps
            gaps = self._analyze_gaps(scored_requirements)
            
            # Generate coverage by category
            coverage_by_category = self._analyze_coverage_by_category(scored_requirements)
            
            # Generate detailed matrix
            detailed_matrix = self._generate_detailed_matrix(scored_requirements)
            
            return {
                "summary": summary.__dict__,
                "gaps": [gap.__dict__ for gap in gaps],
                "coverage_by_category": coverage_by_category,
                "detailed_matrix": detailed_matrix,
                "recommendations": self._generate_recommendations(summary, gaps)
            }
            
        except Exception as e:
            logger.error(f"Error generating coverage matrix: {e}")
            return {
                "summary": {},
                "gaps": [],
                "coverage_by_category": {},
                "detailed_matrix": [],
                "recommendations": []
            }
    
    def _generate_summary(self, scored_requirements: List[RequirementScore]) -> CoverageSummary:
        """Generate coverage summary."""
        total = len(scored_requirements)
        covered = sum(1 for req in scored_requirements if req.decision["covered"])
        partial = sum(1 for req in scored_requirements if not req.decision["covered"] and req.decision["confidence"] > 0.3)
        uncovered = total - covered - partial
        
        overall_coverage = covered / total if total > 0 else 0.0
        avg_confidence = sum(req.decision["confidence"] for req in scored_requirements) / total if total > 0 else 0.0
        
        # Identify critical gaps (high-priority requirements with no coverage)
        critical_gaps = [
            req.text for req in scored_requirements 
            if req.category == "required_skill" and not req.decision["covered"]
        ]
        
        # Coverage by category
        coverage_by_category = self._analyze_coverage_by_category(scored_requirements)
        
        return CoverageSummary(
            total_requirements=total,
            covered_requirements=covered,
            partial_requirements=partial,
            uncovered_requirements=uncovered,
            overall_coverage_rate=overall_coverage,
            average_confidence=avg_confidence,
            critical_gaps=critical_gaps,
            coverage_by_category=coverage_by_category
        )
    
    def _analyze_gaps(self, scored_requirements: List[RequirementScore]) -> List[GapAnalysis]:
        """Analyze gaps in requirement coverage."""
        gaps = []
        
        for req in scored_requirements:
            if req.decision["covered"]:
                continue
            
            # Determine gap type
            if req.decision["confidence"] == 0.0:
                gap_type = "no_evidence"
            elif req.decision["confidence"] < 0.3:
                gap_type = "low_confidence"
            else:
                gap_type = "partial_coverage"
            
            # Generate recommendations
            recommendations = self._generate_gap_recommendations(req, gap_type)
            
            gap = GapAnalysis(
                gap_id=req.req_id,
                requirement=req.text,
                category=req.category,
                gap_type=gap_type,
                closest_evidence=req.decision["closest_evidence"],
                confidence=req.decision["confidence"],
                recommendations=recommendations
            )
            gaps.append(gap)
        
        return gaps
    
    def _analyze_coverage_by_category(
        self,
        scored_requirements: List[RequirementScore]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze coverage by requirement category."""
        categories = {}
        
        for req in scored_requirements:
            category = req.category
            if category not in categories:
                categories[category] = {
                    "total": 0,
                    "covered": 0,
                    "partial": 0,
                    "uncovered": 0,
                    "avg_confidence": 0.0,
                    "requirements": []
                }
            
            categories[category]["total"] += 1
            categories[category]["requirements"].append(req.text)
            
            if req.decision["covered"]:
                categories[category]["covered"] += 1
            elif req.decision["confidence"] > 0.3:
                categories[category]["partial"] += 1
            else:
                categories[category]["uncovered"] += 1
        
        # Calculate averages
        for category in categories:
            cat_reqs = [req for req in scored_requirements if req.category == category]
            if cat_reqs:
                avg_conf = sum(req.decision["confidence"] for req in cat_reqs) / len(cat_reqs)
                categories[category]["avg_confidence"] = avg_conf
                categories[category]["coverage_rate"] = categories[category]["covered"] / categories[category]["total"]
        
        return categories
    
    def _generate_detailed_matrix(
        self,
        scored_requirements: List[RequirementScore]
    ) -> List[Dict[str, Any]]:
        """Generate detailed coverage matrix."""
        matrix = []
        
        for req in scored_requirements:
            matrix_entry = {
                "req_id": req.req_id,
                "text": req.text,
                "category": req.category,
                "covered": req.decision["covered"],
                "confidence": req.decision["confidence"],
                "signals": req.signals,
                "evidence_count": len(req.evidence),
                "gaps": req.decision["gaps"],
                "closest_evidence": req.decision["closest_evidence"]
            }
            matrix.append(matrix_entry)
        
        return matrix
    
    def _generate_gap_recommendations(
        self,
        requirement: RequirementScore,
        gap_type: str
    ) -> List[str]:
        """Generate recommendations for addressing gaps."""
        recommendations = []
        
        if gap_type == "no_evidence":
            recommendations.extend([
                f"Add experience with {requirement.text} to your CV",
                "Consider taking relevant courses or certifications",
                "Include projects or volunteer work demonstrating this skill"
            ])
        elif gap_type == "low_confidence":
            recommendations.extend([
                "Provide more specific details about your experience with this requirement",
                "Include metrics, outcomes, or specific technologies used",
                "Add context about the scale and impact of your work"
            ])
        elif gap_type == "partial_coverage":
            recommendations.extend([
                "Expand on your existing experience with this requirement",
                "Include more recent examples or projects",
                "Add specific technical details and outcomes"
            ])
        
        # Category-specific recommendations
        if requirement.category == "required_skill":
            recommendations.append("This is a required skill - consider prioritizing it in your CV updates")
        elif requirement.category == "experience":
            recommendations.append("Focus on quantifying your experience and demonstrating progression")
        
        return recommendations
    
    def _generate_recommendations(
        self,
        summary: CoverageSummary,
        gaps: List[GapAnalysis]
    ) -> List[str]:
        """Generate overall recommendations based on coverage analysis."""
        recommendations = []
        
        # Overall coverage recommendations
        if summary.overall_coverage_rate < 0.5:
            recommendations.append("Overall coverage is low. Consider updating your CV with more relevant experience.")
        elif summary.overall_coverage_rate < 0.8:
            recommendations.append("Good coverage, but there's room for improvement in specific areas.")
        else:
            recommendations.append("Excellent coverage! Your CV aligns well with the job requirements.")
        
        # Critical gaps
        if summary.critical_gaps:
            recommendations.append(f"Critical gaps found in required skills: {', '.join(summary.critical_gaps[:3])}")
        
        # Confidence recommendations
        if summary.average_confidence < 0.6:
            recommendations.append("Consider adding more specific details and metrics to strengthen your evidence.")
        
        # Category-specific recommendations
        for category, stats in summary.coverage_by_category.items():
            if stats["coverage_rate"] < 0.5:
                recommendations.append(f"Low coverage in {category.replace('_', ' ')} - focus on this area.")
        
        return recommendations
