"""
Enhanced CV matcher using advanced Qdrant filtering for precise job requirement matching.
Leverages nested object filtering for skills, experience, education, and certifications.
"""

from typing import Dict, List, Any, Optional
from agents.job_breakdown.job_analyzer import JobRequirements
from modules.cv_ingestion.enhanced_cv_processor import EnhancedCVProcessor
import logging

logger = logging.getLogger(__name__)

class EnhancedCVMatcher:
    """Enhanced CV matcher with advanced filtering capabilities."""
    
    def __init__(self):
        """Initialize enhanced CV matcher."""
        self.cv_processor = EnhancedCVProcessor()
    
    def match_job_requirements_enhanced(
        self,
        job_requirements: JobRequirements,
        user_id: str,
        cv_id: Optional[str] = None,
        top_k: int = 15
    ) -> Dict[str, Any]:
        """
        Match job requirements against CV content using enhanced filtering.
        
        Args:
            job_requirements: Structured job requirements
            user_id: User identifier
            cv_id: Optional CV identifier (if None, searches across all user's CVs)
            top_k: Number of top matches to retrieve
            
        Returns:
            Enhanced matching results with detailed evidence
        """
        matches = {
            "user_id": user_id,
            "cv_id": cv_id,
            "job_requirements": job_requirements.dict(),
            "enhanced_matches": {},
            "skill_inventory": {},
            "match_summary": {}
        }
        
        try:
            # Get user's comprehensive skill inventory
            skill_inventory = self.cv_processor.get_user_skill_inventory(user_id)
            matches["skill_inventory"] = skill_inventory
            
            # Convert job requirements to enhanced filter format
            enhanced_filters = self._convert_job_requirements_to_filters(job_requirements)
            
            # Perform enhanced matching with multiple strategies
            matches["enhanced_matches"] = {
                "skill_proficiency_matches": self._match_skill_proficiency(
                    job_requirements, user_id, cv_id, top_k
                ),
                "experience_level_matches": self._match_experience_level(
                    job_requirements, user_id, cv_id, top_k
                ),
                "multi_criteria_matches": self._match_multi_criteria(
                    job_requirements, user_id, cv_id, enhanced_filters, top_k
                ),
                "education_matches": self._match_education_requirements(
                    job_requirements, user_id, cv_id, top_k
                ),
                "certification_matches": self._match_certification_requirements(
                    job_requirements, user_id, cv_id, top_k
                )
            }
            
            # Generate comprehensive match summary
            matches["match_summary"] = self._generate_enhanced_match_summary(
                matches["enhanced_matches"], 
                skill_inventory,
                job_requirements
            )
            
            logger.info(f"Successfully performed enhanced matching for user {user_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error in enhanced job matching: {e}")
            return {
                "user_id": user_id,
                "cv_id": cv_id,
                "error": str(e),
                "enhanced_matches": {},
                "match_summary": {}
            }
    
    def _convert_job_requirements_to_filters(self, job_requirements: JobRequirements) -> Dict[str, Any]:
        """Convert job requirements to enhanced filter format."""
        filters = {
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": []
        }
        
        # Convert skills to filter format
        if job_requirements.skills_required:
            for skill in job_requirements.skills_required:
                filters["skills"].append({
                    "name": skill,
                    "proficiency": "intermediate",  # Default minimum
                    "min_years": 1
                })
        
        if job_requirements.skills_preferred:
            for skill in job_requirements.skills_preferred:
                filters["skills"].append({
                    "name": skill,
                    "proficiency": "beginner",  # Lower threshold for preferred
                    "min_years": 0
                })
        
        # Convert experience to filter format
        if job_requirements.experience:
            for exp_req in job_requirements.experience:
                # Parse experience requirement text for structured data
                exp_filter = self._parse_experience_requirement(exp_req)
                if exp_filter:
                    filters["experience"].append(exp_filter)
        
        # Convert qualifications to education filter format
        if job_requirements.qualifications:
            for qual in job_requirements.qualifications:
                edu_filter = self._parse_qualification_requirement(qual)
                if edu_filter:
                    filters["education"].append(edu_filter)
        
        return filters
    
    def _match_skill_proficiency(
        self,
        job_requirements: JobRequirements,
        user_id: str,
        cv_id: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Match skills with proficiency requirements."""
        if not job_requirements.skills_required and not job_requirements.skills_preferred:
            return []
        
        all_skills = (job_requirements.skills_required or []) + (job_requirements.skills_preferred or [])
        skill_matches = []
        
        for skill in all_skills:
            # Determine minimum proficiency based on whether it's required or preferred
            min_proficiency = "intermediate" if skill in (job_requirements.skills_required or []) else "beginner"
            min_years = 2 if skill in (job_requirements.skills_required or []) else 1
            
            # Search for skill-specific matches
            matches = self.cv_processor.search_with_advanced_filters(
                query=f"{skill} programming development experience",
                user_id=user_id,
                skill_requirements=[{
                    "name": skill,
                    "proficiency": min_proficiency,
                    "min_years": min_years
                }],
                limit=top_k // len(all_skills) + 1
            )
            
            for match in matches:
                match["matched_skill"] = skill
                match["required_proficiency"] = min_proficiency
                match["required_years"] = min_years
                match["match_type"] = "skill_proficiency"
            
            skill_matches.extend(matches)
        
        # Sort by relevance score
        skill_matches.sort(key=lambda x: x["score"], reverse=True)
        return skill_matches[:top_k]
    
    def _match_experience_level(
        self,
        job_requirements: JobRequirements,
        user_id: str,
        cv_id: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Match experience level requirements."""
        if not job_requirements.experience:
            return []
        
        experience_matches = []
        
        for exp_req in job_requirements.experience:
            # Parse experience requirement
            parsed_exp = self._parse_experience_requirement(exp_req)
            
            if parsed_exp:
                matches = self.cv_processor.search_with_advanced_filters(
                    query=f"{parsed_exp.get('role', '')} {exp_req}",
                    user_id=user_id,
                    experience_requirements=[parsed_exp],
                    limit=top_k // len(job_requirements.experience) + 1
                )
                
                for match in matches:
                    match["matched_experience"] = exp_req
                    match["parsed_requirements"] = parsed_exp
                    match["match_type"] = "experience_level"
                
                experience_matches.extend(matches)
        
        # Sort by relevance score
        experience_matches.sort(key=lambda x: x["score"], reverse=True)
        return experience_matches[:top_k]
    
    def _match_multi_criteria(
        self,
        job_requirements: JobRequirements,
        user_id: str,
        cv_id: Optional[str],
        enhanced_filters: Dict[str, Any],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Match using multiple criteria simultaneously."""
        # Create a comprehensive query combining all requirements
        query_parts = []
        
        if job_requirements.skills_required:
            query_parts.extend(job_requirements.skills_required)
        
        if job_requirements.experience:
            query_parts.extend(job_requirements.experience)
        
        if job_requirements.qualifications:
            query_parts.extend(job_requirements.qualifications)
        
        query = " ".join(query_parts)
        
        # Perform multi-criteria search
        matches = self.cv_processor.search_with_advanced_filters(
            query=query,
            user_id=user_id,
            skill_requirements=enhanced_filters.get("skills"),
            experience_requirements=enhanced_filters.get("experience"),
            education_requirements=enhanced_filters.get("education"),
            certification_requirements=enhanced_filters.get("certifications"),
            limit=top_k
        )
        
        for match in matches:
            match["match_type"] = "multi_criteria"
            match["criteria_matched"] = self._analyze_criteria_match(match, enhanced_filters)
        
        return matches
    
    def _match_education_requirements(
        self,
        job_requirements: JobRequirements,
        user_id: str,
        cv_id: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Match education requirements."""
        if not job_requirements.qualifications:
            return []
        
        education_matches = []
        
        for qual in job_requirements.qualifications:
            edu_filter = self._parse_qualification_requirement(qual)
            
            if edu_filter:
                matches = self.cv_processor.search_with_advanced_filters(
                    query=f"education {qual} degree university",
                    user_id=user_id,
                    education_requirements=[edu_filter],
                    limit=top_k // len(job_requirements.qualifications) + 1
                )
                
                for match in matches:
                    match["matched_qualification"] = qual
                    match["parsed_education"] = edu_filter
                    match["match_type"] = "education"
                
                education_matches.extend(matches)
        
        # Sort by relevance score
        education_matches.sort(key=lambda x: x["score"], reverse=True)
        return education_matches[:top_k]
    
    def _match_certification_requirements(
        self,
        job_requirements: JobRequirements,
        user_id: str,
        cv_id: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Match certification requirements."""
        # Look for certification keywords in qualifications
        cert_keywords = ["certified", "certification", "certificate", "aws", "azure", "google", "microsoft"]
        
        cert_qualifications = []
        if job_requirements.qualifications:
            for qual in job_requirements.qualifications:
                if any(keyword in qual.lower() for keyword in cert_keywords):
                    cert_qualifications.append(qual)
        
        if not cert_qualifications:
            return []
        
        certification_matches = []
        
        for cert_qual in cert_qualifications:
            cert_filter = self._parse_certification_requirement(cert_qual)
            
            if cert_filter:
                matches = self.cv_processor.search_with_advanced_filters(
                    query=f"certification {cert_qual} certified",
                    user_id=user_id,
                    certification_requirements=[cert_filter],
                    limit=top_k // len(cert_qualifications) + 1
                )
                
                for match in matches:
                    match["matched_certification"] = cert_qual
                    match["parsed_certification"] = cert_filter
                    match["match_type"] = "certification"
                
                certification_matches.extend(matches)
        
        # Sort by relevance score
        certification_matches.sort(key=lambda x: x["score"], reverse=True)
        return certification_matches[:top_k]
    
    def _parse_experience_requirement(self, exp_req: str) -> Optional[Dict[str, Any]]:
        """Parse experience requirement text into structured format."""
        import re
        
        # Extract role
        role_patterns = [
            r"(?i)(software engineer|developer|analyst|manager|consultant|architect|lead|director)",
            r"(?i)(senior|junior|mid-level|entry-level)\s+(engineer|developer|analyst)"
        ]
        
        role = None
        seniority = "mid"  # Default
        
        for pattern in role_patterns:
            match = re.search(pattern, exp_req)
            if match:
                role = match.group(0)
                if "senior" in role.lower():
                    seniority = "senior"
                elif "junior" in role.lower():
                    seniority = "junior"
                break
        
        # Extract years
        years_match = re.search(r"(\d+)\s*(?:years?|yrs?)", exp_req, re.IGNORECASE)
        min_duration = int(years_match.group(1)) if years_match else 2
        
        # Extract technologies
        tech_patterns = [
            r"(?i)(python|java|javascript|typescript|c\+\+|c#|ruby|go|rust|php)",
            r"(?i)(react|angular|vue|node\.js|express|django|flask|spring)",
            r"(?i)(aws|azure|gcp|docker|kubernetes|jenkins|git)"
        ]
        
        technologies = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, exp_req, re.IGNORECASE)
            technologies.extend(matches)
        
        if role or technologies or min_duration > 0:
            return {
                "role": role or "developer",
                "seniority": seniority,
                "min_duration": min_duration,
                "technologies": list(set(technologies))
            }
        
        return None
    
    def _parse_qualification_requirement(self, qual: str) -> Optional[Dict[str, Any]]:
        """Parse qualification requirement into education filter."""
        import re
        
        # Extract degree level
        degree_patterns = [
            r"(?i)(bachelor|master|phd|doctorate|diploma)",
            r"(?i)(bs|ba|ms|ma|mba|phd)"
        ]
        
        degree = None
        level = "bachelor"  # Default
        
        for pattern in degree_patterns:
            match = re.search(pattern, qual)
            if match:
                degree = match.group(0)
                if any(word in degree.lower() for word in ["master", "ms", "ma", "mba"]):
                    level = "master"
                elif any(word in degree.lower() for word in ["phd", "doctorate"]):
                    level = "doctorate"
                break
        
        # Extract field
        field_patterns = [
            r"(?i)(?:in\s+|of\s+)([a-zA-Z\s]+?)(?:\s+from|\s+at|\s*$)",
            r"(?i)(computer science|engineering|mathematics|physics|business)"
        ]
        
        field = None
        for pattern in field_patterns:
            match = re.search(pattern, qual)
            if match:
                field = match.group(1).strip()
                break
        
        if degree or field:
            return {
                "degree": f"{degree} {field}".strip() if degree and field else qual,
                "level": level
            }
        
        return None
    
    def _parse_certification_requirement(self, cert_req: str) -> Optional[Dict[str, Any]]:
        """Parse certification requirement."""
        import re
        
        # Extract certification name and level
        cert_patterns = [
            r"(?i)(aws|azure|google|microsoft|oracle|cisco)\s+(certified|certification)",
            r"(?i)(pmp|scrum|agile)\s+(certified|certification|certificate)"
        ]
        
        name = cert_req
        level = "foundational"  # Default
        
        for pattern in cert_patterns:
            match = re.search(pattern, cert_req)
            if match:
                name = match.group(0)
                if any(word in cert_req.lower() for word in ["professional", "expert", "advanced"]):
                    level = "professional"
                elif any(word in cert_req.lower() for word in ["associate", "practitioner"]):
                    level = "associate"
                break
        
        return {
            "name": name,
            "level": level
        }
    
    def _analyze_criteria_match(self, match: Dict[str, Any], enhanced_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze which criteria were matched in a multi-criteria search."""
        criteria_matched = {
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": []
        }
        
        # Check which skills were matched
        match_skills = match.get("skills", [])
        for skill in match_skills:
            for filter_skill in enhanced_filters.get("skills", []):
                if skill["name"].lower() == filter_skill["name"].lower():
                    criteria_matched["skills"].append({
                        "skill": skill["name"],
                        "proficiency": skill.get("proficiency"),
                        "years": skill.get("years_experience"),
                        "required_proficiency": filter_skill.get("proficiency"),
                        "required_years": filter_skill.get("min_years")
                    })
        
        # Check which experience was matched
        match_experience = match.get("experience", [])
        for exp in match_experience:
            for filter_exp in enhanced_filters.get("experience", []):
                if (exp["role"].lower() in filter_exp.get("role", "").lower() or
                    any(tech in exp.get("technologies", []) for tech in filter_exp.get("technologies", []))):
                    criteria_matched["experience"].append({
                        "role": exp["role"],
                        "duration": exp.get("duration_years"),
                        "seniority": exp.get("seniority"),
                        "technologies": exp.get("technologies", [])
                    })
        
        # Check education and certifications similarly
        criteria_matched["education"] = match.get("education", [])
        criteria_matched["certifications"] = match.get("certifications", [])
        
        return criteria_matched
    
    def _generate_enhanced_match_summary(
        self,
        enhanced_matches: Dict[str, Any],
        skill_inventory: Dict[str, Any],
        job_requirements: JobRequirements
    ) -> Dict[str, Any]:
        """Generate comprehensive match summary with enhanced metrics."""
        summary = {
            "overall_match_score": 0.0,
            "skill_match_rate": 0.0,
            "experience_match_rate": 0.0,
            "education_match_rate": 0.0,
            "certification_match_rate": 0.0,
            "strengths": [],
            "gaps": [],
            "recommendations": [],
            "detailed_analysis": {}
        }
        
        # Analyze skill matches
        skill_analysis = self._analyze_skill_matches(
            enhanced_matches.get("skill_proficiency_matches", []),
            skill_inventory,
            job_requirements.skills_required or [],
            job_requirements.skills_preferred or []
        )
        summary.update(skill_analysis)
        
        # Analyze experience matches
        experience_analysis = self._analyze_experience_matches(
            enhanced_matches.get("experience_level_matches", []),
            job_requirements.experience or []
        )
        summary["experience_match_rate"] = experience_analysis["match_rate"]
        summary["detailed_analysis"]["experience"] = experience_analysis
        
        # Calculate overall match score
        weights = {"skills": 0.4, "experience": 0.3, "education": 0.15, "certifications": 0.15}
        summary["overall_match_score"] = (
            summary["skill_match_rate"] * weights["skills"] +
            summary["experience_match_rate"] * weights["experience"] +
            summary["education_match_rate"] * weights["education"] +
            summary["certification_match_rate"] * weights["certifications"]
        )
        
        # Generate recommendations
        summary["recommendations"] = self._generate_recommendations(summary, job_requirements)
        
        return summary
    
    def _analyze_skill_matches(
        self,
        skill_matches: List[Dict[str, Any]],
        skill_inventory: Dict[str, Any],
        required_skills: List[str],
        preferred_skills: List[str]
    ) -> Dict[str, Any]:
        """Analyze skill matching results."""
        user_skills = skill_inventory.get("skills", {})
        
        # Check required skills coverage
        required_covered = 0
        for skill in required_skills:
            if any(skill.lower() in user_skill.lower() for user_skill in user_skills.keys()):
                required_covered += 1
        
        # Check preferred skills coverage
        preferred_covered = 0
        for skill in preferred_skills:
            if any(skill.lower() in user_skill.lower() for user_skill in user_skills.keys()):
                preferred_covered += 1
        
        skill_match_rate = (
            (required_covered / len(required_skills) if required_skills else 1.0) * 0.7 +
            (preferred_covered / len(preferred_skills) if preferred_skills else 1.0) * 0.3
        )
        
        # Identify strengths and gaps
        strengths = []
        gaps = []
        
        for skill_name, skill_data in user_skills.items():
            if skill_data["max_years"] >= 3 and skill_data["max_proficiency"] in ["expert", "intermediate"]:
                strengths.append(f"Strong {skill_name} experience ({skill_data['max_years']} years)")
        
        for skill in required_skills:
            if not any(skill.lower() in user_skill.lower() for user_skill in user_skills.keys()):
                gaps.append(f"Missing required skill: {skill}")
        
        return {
            "skill_match_rate": skill_match_rate,
            "strengths": strengths,
            "gaps": gaps,
            "detailed_analysis": {
                "skills": {
                    "required_covered": required_covered,
                    "required_total": len(required_skills),
                    "preferred_covered": preferred_covered,
                    "preferred_total": len(preferred_skills),
                    "user_skill_count": len(user_skills)
                }
            }
        }
    
    def _analyze_experience_matches(
        self,
        experience_matches: List[Dict[str, Any]],
        required_experience: List[str]
    ) -> Dict[str, Any]:
        """Analyze experience matching results."""
        if not required_experience:
            return {"match_rate": 1.0, "details": "No specific experience requirements"}
        
        # Simple analysis - can be enhanced based on specific requirements
        match_rate = min(1.0, len(experience_matches) / len(required_experience))
        
        return {
            "match_rate": match_rate,
            "matches_found": len(experience_matches),
            "requirements_total": len(required_experience),
            "details": experience_matches[:3]  # Top 3 matches
        }
    
    def _generate_recommendations(
        self,
        summary: Dict[str, Any],
        job_requirements: JobRequirements
    ) -> List[str]:
        """Generate actionable recommendations based on match analysis."""
        recommendations = []
        
        # Skill-based recommendations
        if summary["skill_match_rate"] < 0.7:
            recommendations.append("Consider highlighting transferable skills and relevant projects")
            recommendations.append("Focus on demonstrating practical application of existing skills")
        
        # Experience-based recommendations
        if summary["experience_match_rate"] < 0.6:
            recommendations.append("Emphasize relevant experience and achievements in similar roles")
            recommendations.append("Include specific examples of projects and technologies used")
        
        # General recommendations
        if summary["overall_match_score"] > 0.8:
            recommendations.append("Strong match - highlight key achievements and quantifiable results")
        elif summary["overall_match_score"] > 0.6:
            recommendations.append("Good match - focus on addressing any skill gaps mentioned")
        else:
            recommendations.append("Consider tailoring experience to better match job requirements")
        
        return recommendations
