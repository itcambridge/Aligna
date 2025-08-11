"""
Main application for the Grounded CV Generator MVP.
Orchestrates the entire workflow from CV upload to grounded CV generation.
"""

import os
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
from modules.cv_ingestion.cv_processor import CVProcessor
from modules.job_search.job_searcher import JobSearcher
from agents.job_breakdown.job_analyzer import JobAnalyzer
from agents.cv_matcher.cv_matcher import CVMatcher
from agents.cv_writer.cv_writer import CVWriter
from agents.evidence_validator.evidence_validator import EvidenceValidator

class GroundedCVGenerator:
    """Main orchestrator for the grounded CV generation system."""
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize the CV generator with all components.
        
        Args:
            user_id: Optional user identifier for user-specific operations
        """
        self.user_id = user_id
        self.cv_processor = CVProcessor()
        self.job_searcher = JobSearcher()
        self.job_analyzer = JobAnalyzer()
        self.cv_matcher = CVMatcher()
        self.cv_writer = CVWriter()
        self.evidence_validator = EvidenceValidator()
    
    def process_cv_upload(
        self,
        file_path: str,
        user_id: str,
        cv_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a CV upload: parse, chunk, embed, and store.
        
        Args:
            file_path: Path to the CV file
            user_id: User identifier
            cv_id: Optional CV identifier
            
        Returns:
            Processing results
        """
        logger.info(f"Processing CV upload: {file_path}")
        
        try:
            result = self.cv_processor.process_cv(
                file_path=file_path,
                user_id=user_id,
                cv_id=cv_id
            )
            
            if result["status"] == "success":
                logger.info(f"Successfully processed CV: {result['cv_id']}")
            else:
                logger.error(f"Failed to process CV: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing CV upload: {e}")
            return {
                "status": "error",
                "error": str(e),
                "cv_id": cv_id or str(uuid.uuid4()),
                "user_id": user_id
            }
    
    def search_and_analyze_job(
        self,
        job_title: str,
        location: str,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for a job and analyze its requirements.
        
        Args:
            job_title: Job title to search for
            location: Location to search in
            job_id: Optional specific job ID
            
        Returns:
            Job analysis results
        """
        logger.info(f"Searching for job: {job_title} in {location}")
        
        try:
            # Search for job
            job_search_result = self.job_searcher.search_jobs(
                job_title=job_title,
                location=location,
                job_id=job_id
            )
            
            if job_search_result["status"] != "success":
                return job_search_result
            
            # Analyze job requirements
            job_description = job_search_result.get("job_description", "")
            job_requirements = self.job_analyzer.analyze_job_description(job_description)
            
            result = {
                "status": "success",
                "job_id": job_id or str(uuid.uuid4()),
                "job_title": job_title,
                "location": location,
                "job_description": job_description,
                "job_requirements": job_requirements.dict(),
                "search_metadata": job_search_result.get("metadata", {})
            }
            
            logger.info(f"Successfully analyzed job requirements for {job_title}")
            return result
            
        except Exception as e:
            logger.error(f"Error searching and analyzing job: {e}")
            return {
                "status": "error",
                "error": str(e),
                "job_id": job_id or str(uuid.uuid4()),
                "job_title": job_title,
                "location": location
            }
    
    def match_cv_to_job(
        self,
        cv_id: str,
        user_id: str,
        job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Match CV content against job requirements using enhanced system.
        
        Args:
            cv_id: CV identifier
            user_id: User identifier
            job_requirements: Structured job requirements
            
        Returns:
            Matching results with evidence
        """
        logger.info(f"Matching CV {cv_id} to job requirements for user {user_id}")
        
        try:
            # Convert dict back to JobRequirements object
            from agents.job_breakdown.job_analyzer import JobRequirements
            requirements_obj = JobRequirements(**job_requirements)
            
            # Use enhanced CV matcher
            matches = self.cv_matcher.match_job_requirements(
                job_requirements=requirements_obj,
                cv_id=cv_id,
                user_id=user_id,
                top_k=15
            )
            
            logger.info(f"Successfully matched CV with enhanced system - overall score: {matches['match_summary']['overall_match_score']:.2f}")
            return matches
            
        except Exception as e:
            logger.error(f"Error matching CV to job: {e}")
            return {
                "status": "error",
                "error": str(e),
                "cv_id": cv_id,
                "user_id": user_id
            }
    
    def validate_evidence_coverage(
        self,
        job_requirements: Dict[str, Any],
        user_id: str,
        cv_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate evidence coverage for job requirements using the evidence validator.
        
        Args:
            job_requirements: Structured job requirements
            user_id: User identifier
            cv_ids: Specific CV IDs to validate (None for all user CVs)
            
        Returns:
            Evidence validation results with coverage matrix
        """
        logger.info(f"Validating evidence coverage for user {user_id}")
        
        try:
            # Convert dict back to JobRequirements object
            from agents.job_breakdown.job_analyzer import JobRequirements
            requirements_obj = JobRequirements(**job_requirements)
            
            # Validate evidence
            validation_result = self.evidence_validator.validate_evidence(
                job_requirements=requirements_obj,
                user_id=user_id,
                cv_ids=cv_ids,
                top_k=5
            )
            
            logger.info(f"Evidence validation complete for user {user_id}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating evidence coverage: {e}")
            return {
                "status": "error",
                "error": str(e),
                "user_id": user_id
            }
    
    def generate_grounded_cv(
        self,
        cv_id: str,
        user_id: str,
        job_requirements: Dict[str, Any],
        cv_matches: Dict[str, Any],
        contact_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generate a grounded CV based on job requirements and CV evidence.
        
        Args:
            cv_id: CV identifier
            user_id: User identifier
            job_requirements: Structured job requirements
            cv_matches: Matching results from CV matcher
            contact_info: Contact information from original CV
            
        Returns:
            Generated CV with evidence
        """
        logger.info(f"Generating grounded CV for user {user_id}")
        
        try:
            # Convert dict back to JobRequirements object
            from agents.job_breakdown.job_analyzer import JobRequirements
            requirements_obj = JobRequirements(**job_requirements)
            
            # Generate the CV
            generated_cv = self.cv_writer.generate_cv(
                job_requirements=requirements_obj,
                cv_matches=cv_matches,
                contact_info=contact_info,
                cv_id=cv_id,
                user_id=user_id
            )
            
            # Generate text versions
            cv_text = self.cv_writer.generate_cv_text(generated_cv)
            evidence_report = self.cv_writer.generate_cv_with_evidence_report(generated_cv)
            
            result = {
                "status": "success",
                "cv_id": cv_id,
                "user_id": user_id,
                "generated_cv": generated_cv.dict(),
                "cv_text": cv_text,
                "evidence_report": evidence_report,
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully generated grounded CV for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating grounded CV: {e}")
            return {
                "status": "error",
                "error": str(e),
                "cv_id": cv_id,
                "user_id": user_id
            }
    
    def get_user_cv_collection(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's complete CV collection with statistics.
        
        Args:
            user_id: User identifier
            
        Returns:
            User's CV collection information
        """
        logger.info(f"Getting CV collection for user {user_id}")
        
        try:
            return self.cv_processor.get_user_cv_stats(user_id)
        except Exception as e:
            logger.error(f"Error getting user CV collection: {e}")
            return {
                "user_id": user_id,
                "total_cvs": 0,
                "total_chunks": 0,
                "unique_sections": 0,
                "error": str(e)
            }
    
    def generate_cv_from_knowledge_base(
        self,
        user_id: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Generate CV from user's knowledge base using evidence validation.
        
        Args:
            user_id: User identifier
            job_description: Job description text
            
        Returns:
            Generated CV with evidence validation
        """
        logger.info(f"Generating CV from knowledge base for user {user_id}")
        
        try:
            # Step 1: Analyze job requirements
            job_requirements = self.job_analyzer.analyze_job_description(job_description)
            
            # Step 2: Validate evidence coverage
            evidence_validation = self.evidence_validator.validate_evidence(
                job_requirements=job_requirements,
                user_id=user_id,
                top_k=5
            )
            
            if evidence_validation["status"] != "success":
                return {
                    "status": "error",
                    "error": "Failed to validate evidence coverage",
                    "user_id": user_id
                }
            
            # Step 3: Get covered requirements only
            scored_requirements = evidence_validation["scored_requirements"]
            covered_requirements = self.evidence_validator.get_covered_requirements(
                [self._dict_to_requirement_score(req) for req in scored_requirements],
                min_confidence=0.4
            )
            
            # Step 4: Generate CV using only covered requirements
            if not covered_requirements:
                return {
                    "status": "error",
                    "error": "No requirements have sufficient evidence coverage",
                    "user_id": user_id,
                    "evidence_validation": evidence_validation
                }
            
            # Create mock CV matches from covered requirements
            cv_matches = self._create_matches_from_covered_requirements(covered_requirements)
            
            # Extract contact info from any available evidence
            contact_info = self._extract_contact_from_matches(cv_matches)
            
            # Generate CV
            generated_cv = self.cv_writer.generate_cv(
                job_requirements=job_requirements,
                cv_matches=cv_matches,
                contact_info=contact_info,
                cv_id="knowledge_base",
                user_id=user_id
            )
            
            # Generate text versions
            cv_text = self.cv_writer.generate_cv_text(generated_cv)
            evidence_report = self.cv_writer.generate_cv_with_evidence_report(generated_cv)
            
            # Create source attribution
            source_attribution = self._create_source_attribution_from_evidence(evidence_validation)
            
            result = {
                "status": "success",
                "user_id": user_id,
                "cv_text": cv_text,
                "evidence_report": evidence_report,
                "evidence_validation": evidence_validation,
                "coverage_matrix": evidence_validation["coverage_matrix"],
                "source_attribution": source_attribution,
                "matches_summary": {
                    "total_matches": len(cv_matches),
                    "cv_sources_used": list(source_attribution.keys()),
                    "match_rate": evidence_validation["coverage_matrix"]["summary"]["overall_coverage_rate"]
                },
                "cv_stats": self.cv_processor.get_user_cv_stats(user_id),
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully generated CV from knowledge base for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating CV from knowledge base: {e}")
            return {
                "status": "error",
                "error": str(e),
                "user_id": user_id
            }
    
    def _dict_to_requirement_score(self, req_dict: Dict[str, Any]):
        """Convert dictionary back to RequirementScore object."""
        from agents.evidence_validator.requirement_scorer import RequirementScore
        return RequirementScore(
            req_id=req_dict["req_id"],
            text=req_dict["text"],
            category=req_dict["category"],
            signals=req_dict["signals"],
            decision=req_dict["decision"],
            evidence=req_dict["evidence"]
        )
    
    def _create_matches_from_covered_requirements(
        self,
        covered_requirements: List
    ) -> Dict[str, Any]:
        """Create CV matches structure from covered requirements."""
        matches = {
            "cv_id": "knowledge_base",
            "user_id": self.user_id,
            "job_requirements": {},
            "matches": {},
            "summary": {
                "overall_match_score": 0.0,
                "total_matches": 0
            }
        }
        
        # Group evidence by requirement category
        for req in covered_requirements:
            category = req.category
            if category not in matches["matches"]:
                matches["matches"][category] = []
            
            # Add evidence as matches
            for evidence in req.evidence:
                match = {
                    "text": evidence.get("snippet", evidence.get("text", "")),
                    "score": evidence.get("score", 0.0),
                    "cv_id": evidence.get("cv_id", "unknown"),
                    "section": evidence.get("section", "unknown"),
                    "chunk_index": evidence.get("chunk_index", 0)
                }
                matches["matches"][category].append(match)
        
        # Calculate summary
        total_matches = sum(len(matches["matches"][cat]) for cat in matches["matches"])
        avg_score = sum(
            match["score"] 
            for cat in matches["matches"].values() 
            for match in cat
        ) / total_matches if total_matches > 0 else 0.0
        
        matches["summary"]["total_matches"] = total_matches
        matches["summary"]["overall_match_score"] = avg_score
        
        return matches
    
    def _extract_contact_from_matches(self, matches: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extract contact information from matches."""
        # This is a simplified version - in practice, you'd want to extract
        # contact info from the original CVs
        return {
            "email": "contact@example.com",
            "phone": "+1-555-0123",
            "name": "Professional Candidate"
        }
    
    def _create_source_attribution_from_evidence(
        self,
        evidence_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create source attribution from evidence validation results."""
        source_attribution = {}
        
        for req in evidence_validation["scored_requirements"]:
            for evidence in req["evidence"]:
                cv_id = evidence.get("cv_id", "unknown")
                if cv_id not in source_attribution:
                    source_attribution[cv_id] = {
                        "cv_name": f"CV {cv_id[:8]}",
                        "matches_contributed": 0,
                        "sections_used": set(),
                        "sample_contributions": [],
                        "avg_relevance_score": 0.0
                    }
                
                source_attribution[cv_id]["matches_contributed"] += 1
                source_attribution[cv_id]["sections_used"].add(evidence.get("section", "unknown"))
                source_attribution[cv_id]["sample_contributions"].append({
                    "text": evidence.get("snippet", evidence.get("text", ""))[:100] + "...",
                    "score": evidence.get("score", 0.0)
                })
        
        # Convert sets to lists and calculate averages
        for cv_id, attribution in source_attribution.items():
            attribution["sections_used"] = list(attribution["sections_used"])
            if attribution["sample_contributions"]:
                avg_score = sum(contrib["score"] for contrib in attribution["sample_contributions"]) / len(attribution["sample_contributions"])
                attribution["avg_relevance_score"] = avg_score
        
        return source_attribution
    
    def run_complete_workflow(
        self,
        cv_file_path: str,
        user_id: str,
        job_title: str,
        location: str
    ) -> Dict[str, Any]:
        """
        Run the complete CV generation workflow with evidence validation.
        
        Args:
            cv_file_path: Path to CV file
            user_id: User identifier
            job_title: Job title to target
            location: Job location
            
        Returns:
            Complete workflow results
        """
        logger.info(f"Running complete workflow for user {user_id}")
        
        try:
            # Step 1: Process CV upload
            cv_result = self.process_cv_upload(cv_file_path, user_id)
            if cv_result["status"] != "success":
                return cv_result
            
            cv_id = cv_result["cv_id"]
            
            # Step 2: Search and analyze job
            job_result = self.search_and_analyze_job(job_title, location)
            if job_result["status"] != "success":
                return job_result
            
            job_requirements = job_result["job_requirements"]
            
            # Step 3: Validate evidence coverage
            evidence_validation = self.validate_evidence_coverage(
                job_requirements=job_requirements,
                user_id=user_id,
                cv_ids=[cv_id]
            )
            
            if evidence_validation["status"] != "success":
                return {
                    "status": "error",
                    "error": "Failed to validate evidence coverage",
                    "cv_result": cv_result,
                    "job_result": job_result
                }
            
            # Step 4: Match CV to job
            match_result = self.match_cv_to_job(cv_id, user_id, job_requirements)
            if match_result["status"] != "success":
                return match_result
            
            # Step 5: Generate grounded CV
            contact_info = cv_result.get("contact_info", {})
            cv_generation_result = self.generate_grounded_cv(
                cv_id=cv_id,
                user_id=user_id,
                job_requirements=job_requirements,
                cv_matches=match_result,
                contact_info=contact_info
            )
            
            if cv_generation_result["status"] != "success":
                return cv_generation_result
            
            # Step 6: Compile final results
            final_result = {
                "status": "success",
                "user_id": user_id,
                "cv_id": cv_id,
                "job_title": job_title,
                "location": location,
                "cv_processing": cv_result,
                "job_analysis": job_result,
                "evidence_validation": evidence_validation,
                "cv_matching": match_result,
                "cv_generation": cv_generation_result,
                "final_result": {
                    "cv_text": cv_generation_result["cv_text"],
                    "evidence_report": cv_generation_result["evidence_report"],
                    "coverage_matrix": evidence_validation["coverage_matrix"],
                    "hallucination_risk": evidence_validation["hallucination_risk"]
                },
                "workflow_completed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Complete workflow finished successfully for user {user_id}")
            return final_result
            
        except Exception as e:
            logger.error(f"Error in complete workflow: {e}")
            return {
                "status": "error",
                "error": str(e),
                "user_id": user_id,
                "cv_file_path": cv_file_path,
                "job_title": job_title,
                "location": location
            }

def main():
    """Main function for testing the CV generator."""
    # Example usage
    generator = GroundedCVGenerator()
    
    # Test with sample data
    result = generator.run_complete_workflow(
        cv_file_path="path/to/sample_cv.pdf",
        user_id="test_user_123",
        job_title="Software Engineer",
        location="San Francisco, CA"
    )
    
    print("Workflow result:", result)

if __name__ == "__main__":
    main()
