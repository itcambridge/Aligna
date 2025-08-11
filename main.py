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

# Check orchestrator configuration
ORCHESTRATOR = os.getenv("ORCHESTRATOR", "langchain").lower()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules - Enhanced versions for better performance
from modules.cv_ingestion.enhanced_cv_processor import EnhancedCVProcessor
from modules.cv_ingestion.user_cv_processor import UserCVProcessor
from modules.job_search.job_searcher import JobSearcher
from agents.job_breakdown.job_analyzer import JobAnalyzer
from agents.cv_matcher.enhanced_cv_matcher import EnhancedCVMatcher
from agents.cv_writer.cv_writer import CVWriter
from utils.enhanced_qdrant_client import EnhancedQdrantCVClient

class GroundedCVGenerator:
    """Main orchestrator for the grounded CV generation system."""
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize the CV generator with all components.
        
        Args:
            user_id: User identifier for multi-tenant support
        """
        self.user_id = user_id
        
        # Initialize components with enhanced versions
        self.cv_processor = EnhancedCVProcessor()
        self.enhanced_qdrant_client = EnhancedQdrantCVClient()
        
        self.job_searcher = JobSearcher()
        self.job_analyzer = JobAnalyzer()
        self.cv_matcher = EnhancedCVMatcher()
        self.cv_writer = CVWriter()
    
    def process_cv_upload(
        self,
        file_path: str,
        user_id: str,
        cv_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a CV upload: parse, chunk, embed, and store with enhanced metadata.
        
        Args:
            file_path: Path to the CV file
            user_id: User identifier
            cv_id: Optional CV identifier
            
        Returns:
            Processing results with enhanced metadata
        """
        logger.info(f"Processing CV upload with enhanced system: {file_path}")
        
        try:
            result = self.cv_processor.process_cv_enhanced(
                file_path=file_path,
                user_id=user_id,
                cv_id=cv_id
            )
            
            if result["status"] == "success":
                logger.info(f"Successfully processed enhanced CV: {result['cv_id']}")
                logger.info(f"Extracted structured metadata: {len(result['structured_metadata']['skills'])} skills, {len(result['structured_metadata']['experience'])} experience entries")
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
            # Search for jobs
            jobs = self.job_searcher.search_jobs(
                job_title=job_title,
                location=location,
                limit=5
            )
            
            if not jobs:
                return {
                    "status": "error",
                    "error": "No jobs found"
                }
            
            # Use the first job or specified job
            selected_job = jobs[0] if not job_id else next(
                (job for job in jobs if job["id"] == job_id), jobs[0]
            )
            
            # Get detailed job description
            job_description = self.job_searcher.get_job_description(selected_job["id"])
            
            if not job_description:
                return {
                    "status": "error",
                    "error": "Could not retrieve job description"
                }
            
            # Analyze job requirements
            job_requirements = self.job_analyzer.analyze_job_description(job_description)
            
            result = {
                "status": "success",
                "job": selected_job,
                "job_description": job_description,
                "job_requirements": job_requirements.dict(),
                "job_summary": self.job_analyzer.generate_job_summary(job_requirements)
            }
            
            logger.info(f"Successfully analyzed job: {selected_job['title']}")
            return result
            
        except Exception as e:
            logger.error(f"Error searching and analyzing job: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def match_cv_to_job(
        self,
        cv_id: str,
        user_id: str,
        job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Match CV content against job requirements using RAG.
        
        Args:
            cv_id: CV identifier
            user_id: User identifier
            job_requirements: Structured job requirements
            
        Returns:
            Matching results with evidence
        """
        logger.info(f"Matching CV {cv_id} against job requirements")
        
        try:
            # Convert dict back to JobRequirements object
            from agents.job_breakdown.job_analyzer import JobRequirements
            requirements_obj = JobRequirements(**job_requirements)
            
            # Match CV against job requirements using enhanced matcher
            matches = self.cv_matcher.match_job_requirements_enhanced(
                job_requirements=requirements_obj,
                user_id=user_id,
                cv_id=cv_id,
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
        Generate CV using ALL CVs in user's knowledge base.
        
        Args:
            user_id: User identifier
            job_description: Job description text
            
        Returns:
            Generated CV with comprehensive evidence from all CVs
        """
        logger.info(f"Generating CV from knowledge base for user {user_id}")
        
        try:
            # Step 1: Get user's CV collection stats
            cv_stats = self.get_user_cv_collection(user_id)
            
            if cv_stats["total_cvs"] == 0:
                return {
                    "status": "error",
                    "error": "No CVs found in user's knowledge base",
                    "user_id": user_id
                }
            
            # Step 2: Analyze job requirements
            job_requirements = self.job_analyzer.analyze_job_description(job_description)
            
            # Step 3: Search across ALL user's CVs for relevant experience
            matches = self.cv_processor.search_across_all_user_cvs(
                user_id=user_id,
                query=job_description,
                limit=20  # Get more matches since we have more data
            )
            
            if not matches:
                return {
                    "status": "error",
                    "error": "No relevant experience found in CV knowledge base",
                    "user_id": user_id,
                    "cv_stats": cv_stats
                }
            
            # Step 4: Group matches by CV source for transparency
            matches_by_cv = {}
            for match in matches:
                cv_id = match["cv_id"]
                if cv_id not in matches_by_cv:
                    matches_by_cv[cv_id] = []
                matches_by_cv[cv_id].append(match)
            
            # Step 5: Create comprehensive match result
            comprehensive_matches = {
                "matches": matches,
                "matches_by_cv": matches_by_cv,
                "total_matches": len(matches),
                "cv_sources": len(matches_by_cv),
                "summary": {
                    "total_matches": len(matches),  # Add this key to summary
                    "match_rate": min(1.0, len(matches) / 10),  # Normalize to 0-1
                    "total_requirements": len(job_requirements.skills_required + job_requirements.skills_preferred),
                    "matched_requirements": len(matches),
                    "cv_sources_used": list(matches_by_cv.keys())
                }
            }
            
            # Step 6: Extract contact info from most recent CV
            recent_cv = cv_stats["cv_list"][0] if cv_stats["cv_list"] else {}
            contact_info = self._extract_contact_from_matches(matches)
            
            # Step 7: Generate comprehensive CV
            generated_cv = self.cv_writer.generate_cv(
                job_requirements=job_requirements,
                cv_matches=comprehensive_matches,
                contact_info=contact_info,
                cv_id="knowledge_base",  # Special identifier for multi-CV generation
                user_id=user_id
            )
            
            # Step 8: Generate text versions with source attribution
            cv_text = self.cv_writer.generate_cv_text(generated_cv)
            evidence_report = self.cv_writer.generate_cv_with_evidence_report(generated_cv)
            
            # Step 9: Add knowledge base specific information
            result = {
                "status": "success",
                "generation_type": "knowledge_base",
                "user_id": user_id,
                "cv_stats": cv_stats,
                "matches_summary": comprehensive_matches["summary"],
                "generated_cv": generated_cv.dict(),
                "cv_text": cv_text,
                "evidence_report": evidence_report,
                "source_attribution": self._create_source_attribution(matches_by_cv, cv_stats["cv_list"]),
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully generated comprehensive CV using {len(matches_by_cv)} CV sources")
            return result
            
        except Exception as e:
            logger.error(f"Error generating CV from knowledge base: {e}")
            return {
                "status": "error",
                "error": str(e),
                "user_id": user_id
            }
    
    def _extract_contact_from_matches(self, matches: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extract contact information from CV matches."""
        contact_info = {}
        
        # Look for contact information in the matches
        for match in matches:
            text = match.get("text", "").lower()
            
            # Simple email extraction
            if "@" in text and "email" not in contact_info:
                import re
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                if email_match:
                    contact_info["email"] = email_match.group()
            
            # Simple phone extraction
            if any(word in text for word in ["phone", "mobile", "tel"]) and "phone" not in contact_info:
                import re
                phone_match = re.search(r'[\+]?[1-9]?[0-9]{7,15}', text)
                if phone_match:
                    contact_info["phone"] = phone_match.group()
        
        return contact_info
    
    def _create_source_attribution(
        self, 
        matches_by_cv: Dict[str, List[Dict[str, Any]]], 
        cv_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create source attribution report showing which CVs contributed what."""
        
        # Create CV lookup
        cv_lookup = {cv["cv_id"]: cv for cv in cv_list}
        
        attribution = {}
        for cv_id, matches in matches_by_cv.items():
            cv_info = cv_lookup.get(cv_id, {"name": f"CV {cv_id[:8]}", "total_chunks": 0})
            
            attribution[cv_id] = {
                "cv_name": cv_info.get("name", f"CV {cv_id[:8]}"),
                "cv_display_name": cv_info.get("display_name", f"CV {cv_id[:8]}"),
                "matches_contributed": len(matches),
                "sections_used": list(set(match.get("section", "unknown") for match in matches)),
                "avg_relevance_score": sum(match.get("score", 0) for match in matches) / len(matches),
                "sample_contributions": [
                    {
                        "text": match.get("text", "")[:100] + "...",
                        "section": match.get("section", "unknown"),
                        "score": match.get("score", 0)
                    }
                    for match in matches[:3]  # Show top 3 contributions
                ]
            }
        
        return attribution
    
    def run_complete_workflow(
        self,
        cv_file_path: str,
        user_id: str,
        job_title: str,
        location: str
    ) -> Dict[str, Any]:
        """
        Run the complete workflow from CV upload to grounded CV generation.
        
        Args:
            cv_file_path: Path to the CV file
            user_id: User identifier
            job_title: Job title to search for
            location: Location to search in
            
        Returns:
            Complete workflow results
        """
        logger.info("Starting complete grounded CV generation workflow")
        
        workflow_result = {
            "workflow_id": str(uuid.uuid4()),
            "user_id": user_id,
            "started_at": datetime.now().isoformat(),
            "steps": {}
        }
        
        try:
            # Step 1: Process CV upload
            logger.info("Step 1: Processing CV upload")
            cv_result = self.process_cv_upload(cv_file_path, user_id)
            workflow_result["steps"]["cv_upload"] = cv_result
            
            if cv_result["status"] != "success":
                workflow_result["status"] = "error"
                workflow_result["error"] = cv_result.get("error", "CV upload failed")
                return workflow_result
            
            cv_id = cv_result["cv_id"]
            contact_info = cv_result.get("contact_info", {})
            
            # Step 2: Search and analyze job
            logger.info("Step 2: Searching and analyzing job")
            job_result = self.search_and_analyze_job(job_title, location)
            workflow_result["steps"]["job_analysis"] = job_result
            
            if job_result["status"] != "success":
                workflow_result["status"] = "error"
                workflow_result["error"] = job_result.get("error", "Job analysis failed")
                return workflow_result
            
            job_requirements = job_result["job_requirements"]
            
            # Step 3: Match CV to job requirements
            logger.info("Step 3: Matching CV to job requirements")
            match_result = self.match_cv_to_job(cv_id, user_id, job_requirements)
            workflow_result["steps"]["cv_matching"] = match_result
            
            if match_result.get("status") == "error":
                workflow_result["status"] = "error"
                workflow_result["error"] = match_result.get("error", "CV matching failed")
                return workflow_result
            
            # Step 4: Generate grounded CV
            logger.info("Step 4: Generating grounded CV")
            cv_generation_result = self.generate_grounded_cv(
                cv_id, user_id, job_requirements, match_result, contact_info
            )
            workflow_result["steps"]["cv_generation"] = cv_generation_result
            
            if cv_generation_result["status"] != "success":
                workflow_result["status"] = "error"
                workflow_result["error"] = cv_generation_result.get("error", "CV generation failed")
                return workflow_result
            
            # Workflow completed successfully
            workflow_result["status"] = "success"
            workflow_result["completed_at"] = datetime.now().isoformat()
            workflow_result["final_result"] = cv_generation_result
            
            logger.info("Complete workflow finished successfully")
            return workflow_result
            
        except Exception as e:
            logger.error(f"Error in complete workflow: {e}")
            workflow_result["status"] = "error"
            workflow_result["error"] = str(e)
            workflow_result["completed_at"] = datetime.now().isoformat()
            return workflow_result

def main():
    """Main function to demonstrate the system."""
    # Initialize the system
    generator = GroundedCVGenerator()
    
    # Example usage
    print("🚀 Grounded CV Generator MVP")
    print("=" * 50)
    
    # Example workflow (you would replace these with actual values)
    cv_file_path = "path/to/your/cv.pdf"  # Replace with actual CV file
    user_id = "user_123"
    job_title = "Software Engineer"
    location = "San Francisco, CA"
    
    print(f"CV File: {cv_file_path}")
    print(f"User ID: {user_id}")
    print(f"Job Title: {job_title}")
    print(f"Location: {location}")
    print()
    
    # Run the complete workflow
    result = generator.run_complete_workflow(cv_file_path, user_id, job_title, location)
    
    if result["status"] == "success":
        print("✅ Workflow completed successfully!")
        print("\nGenerated CV:")
        print("-" * 30)
        print(result["final_result"]["cv_text"])
    else:
        print(f"❌ Workflow failed: {result.get('error')}")

if __name__ == "__main__":
    main()
