"""
Enhanced CV processor with structured metadata extraction for advanced Qdrant filtering.
Extracts skills, experience, education, and certifications as nested objects.
"""

import os
import uuid
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from utils.cv_parser import CVParser
from utils.embeddings import EmbeddingGenerator
from utils.enhanced_qdrant_client import EnhancedQdrantCVClient

logger = logging.getLogger(__name__)

class EnhancedCVProcessor:
    """Enhanced CV processor with structured metadata extraction."""
    
    def __init__(self, embedding_model: str = "openai"):
        """
        Initialize enhanced CV processor.
        
        Args:
            embedding_model: "openai" or "sentence-transformers"
        """
        self.parser = CVParser()
        self.embedding_generator = EmbeddingGenerator(embedding_model)
        self.qdrant_client = EnhancedQdrantCVClient()
        
        # Ensure enhanced Qdrant collection exists
        self.qdrant_client.create_collection()
        
        # Skill proficiency mapping
        self.proficiency_keywords = {
            "expert": ["expert", "advanced", "senior", "lead", "architect", "specialist"],
            "intermediate": ["intermediate", "proficient", "experienced", "solid", "good"],
            "beginner": ["beginner", "basic", "junior", "entry", "learning", "familiar"]
        }
        
        # Seniority level mapping
        self.seniority_keywords = {
            "senior": ["senior", "lead", "principal", "staff", "architect", "head", "director"],
            "mid": ["mid", "intermediate", "experienced", "regular"],
            "junior": ["junior", "entry", "associate", "trainee", "graduate"]
        }
    
    def process_cv_enhanced(
        self,
        file_path: str,
        user_id: str,
        cv_id: Optional[str] = None,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> Dict[str, Any]:
        """
        Process a CV file with enhanced structured metadata extraction.
        
        Args:
            file_path: Path to the CV file
            user_id: User identifier
            cv_id: Optional CV identifier (generated if not provided)
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            Processing results with enhanced metadata
        """
        if not cv_id:
            cv_id = str(uuid.uuid4())
        
        try:
            # Step 1: Parse the CV file
            logger.info(f"Parsing CV file: {file_path}")
            parsed_content = self.parser.parse_file(file_path)
            
            # Step 2: Extract full text from parsed content
            full_text = self._extract_full_text_from_parsed_content(parsed_content)
            structured_metadata = self._extract_structured_metadata(full_text)
            
            # Step 3: Chunk the text with section awareness
            logger.info("Chunking CV text with enhanced metadata")
            chunks = self._chunk_text_with_metadata(parsed_content, structured_metadata, chunk_size, overlap)
            
            if not chunks:
                raise ValueError("No text chunks extracted from CV")
            
            # Step 4: Generate embeddings
            logger.info("Generating embeddings for enhanced chunks")
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedding_generator.generate_embeddings(chunk_texts)
            
            if not embeddings:
                raise ValueError("Failed to generate embeddings")
            
            # Step 5: Store in enhanced Qdrant collection
            logger.info("Storing enhanced chunks and embeddings in Qdrant")
            success = self.qdrant_client.upsert_enhanced_embeddings(
                cv_id=cv_id,
                user_id=user_id,
                chunks=chunks,
                embeddings=embeddings
            )
            
            if not success:
                raise ValueError("Failed to store enhanced embeddings in Qdrant")
            
            # Step 6: Prepare results
            result = {
                "cv_id": cv_id,
                "user_id": user_id,
                "file_path": file_path,
                "file_type": parsed_content["file_type"],
                "total_chunks": len(chunks),
                "total_embeddings": len(embeddings),
                "structured_metadata": structured_metadata,
                "sections": self._get_section_summary(chunks),
                "processed_at": datetime.now().isoformat(),
                "status": "success"
            }
            
            logger.info(f"Successfully processed enhanced CV {cv_id} with {len(chunks)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error processing enhanced CV {file_path}: {e}")
            return {
                "cv_id": cv_id,
                "user_id": user_id,
                "file_path": file_path,
                "status": "error",
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    def _extract_full_text_from_parsed_content(self, parsed_content: Dict[str, Any]) -> str:
        """
        Extract full text from parsed content structure.
        
        Args:
            parsed_content: Parsed content from CV parser
            
        Returns:
            Combined full text string
        """
        full_text = ""
        
        # Handle the content list structure from CV parser
        for item in parsed_content.get("content", []):
            full_text += item.get("text", "") + "\n"
        
        return full_text.strip()
    
    def _extract_structured_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract structured metadata from CV text.
        
        Args:
            text: Full CV text
            
        Returns:
            Dictionary containing structured metadata
        """
        metadata = {
            "skills": self._extract_skills(text),
            "experience": self._extract_experience(text),
            "education": self._extract_education(text),
            "certifications": self._extract_certifications(text)
        }
        
        return metadata
    
    def _extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """Extract skills with proficiency and context information."""
        skills = []
        
        # Common skill patterns
        skill_patterns = [
            r"(?i)(python|java|javascript|typescript|c\+\+|c#|ruby|go|rust|php|swift|kotlin)",
            r"(?i)(react|angular|vue|node\.js|express|django|flask|spring|laravel)",
            r"(?i)(aws|azure|gcp|docker|kubernetes|jenkins|git|linux|windows)",
            r"(?i)(mysql|postgresql|mongodb|redis|elasticsearch|sql server)",
            r"(?i)(machine learning|ai|data science|analytics|statistics)",
            r"(?i)(project management|agile|scrum|kanban|leadership|communication)"
        ]
        
        # Extract skills with context
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skill_name = match.group(1)
                
                # Get surrounding context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                # Determine proficiency level from context
                proficiency = self._determine_proficiency(context)
                
                # Extract years of experience if mentioned
                years_match = re.search(r"(\d+)\s*(?:years?|yrs?)", context, re.IGNORECASE)
                years_experience = int(years_match.group(1)) if years_match else 0
                
                skills.append({
                    "name": skill_name,
                    "proficiency": proficiency,
                    "years_experience": years_experience,
                    "context": context
                })
        
        # Remove duplicates and merge similar skills
        unique_skills = {}
        for skill in skills:
            key = skill["name"].lower()
            if key not in unique_skills or skill["years_experience"] > unique_skills[key]["years_experience"]:
                unique_skills[key] = skill
        
        return list(unique_skills.values())
    
    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience with structured information."""
        experience = []
        
        # Pattern to match job entries
        job_patterns = [
            r"(?i)(software engineer|developer|analyst|manager|consultant|architect|lead|director)\s+(?:at\s+)?([a-zA-Z\s&.,]+?)(?:\s+\||\s+\n|\s+\d{4})",
            r"(?i)([a-zA-Z\s&.,]+?)\s+(?:-|–)\s+(software engineer|developer|analyst|manager|consultant|architect|lead|director)"
        ]
        
        for pattern in job_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                if len(match.groups()) >= 2:
                    role = match.group(1).strip()
                    company = match.group(2).strip()
                    
                    # Get surrounding context for more details
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 200)
                    context = text[start:end]
                    
                    # Extract duration
                    duration_years = self._extract_duration(context)
                    
                    # Determine seniority level
                    seniority = self._determine_seniority(role, context)
                    
                    # Extract technologies mentioned in context
                    technologies = self._extract_technologies_from_context(context)
                    
                    experience.append({
                        "role": role,
                        "company": company,
                        "duration_years": duration_years,
                        "seniority": seniority,
                        "technologies": technologies,
                        "context": context
                    })
        
        return experience
    
    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education information."""
        education = []
        
        # Education patterns
        education_patterns = [
            r"(?i)(bachelor|master|phd|doctorate|diploma|certificate)\s+(?:of\s+)?(?:science\s+)?(?:in\s+)?([a-zA-Z\s]+?)(?:\s+from\s+|\s+at\s+|\s+-\s+)([a-zA-Z\s&.,]+?)(?:\s+\d{4}|\s+\n)",
            r"(?i)([a-zA-Z\s&.,]+?)\s+(?:-|–)\s+(bachelor|master|phd|doctorate|diploma|certificate)"
        ]
        
        for pattern in education_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    degree = groups[0].strip() if groups[0] else ""
                    field = groups[1].strip() if len(groups) > 1 and groups[1] else ""
                    institution = groups[2].strip() if len(groups) > 2 and groups[2] else ""
                    
                    # Extract year
                    context = text[match.start():match.end() + 50]
                    year_match = re.search(r"(\d{4})", context)
                    year = int(year_match.group(1)) if year_match else None
                    
                    # Determine education level
                    level = self._determine_education_level(degree)
                    
                    education.append({
                        "degree": f"{degree} {field}".strip(),
                        "level": level,
                        "institution": institution,
                        "year": year
                    })
        
        return education
    
    def _extract_certifications(self, text: str) -> List[Dict[str, Any]]:
        """Extract certification information."""
        certifications = []
        
        # Certification patterns
        cert_patterns = [
            r"(?i)(aws|azure|google|microsoft|oracle|cisco|pmp|scrum|agile)\s+(certified|certification|certificate)\s+([a-zA-Z\s]+?)(?:\s+\d{4}|\s+\n)",
            r"(?i)(certified|certification|certificate)\s+([a-zA-Z\s]+?)(?:\s+\d{4}|\s+\n)"
        ]
        
        for pattern in cert_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    provider = groups[0].strip() if groups[0] else ""
                    cert_type = groups[1].strip() if groups[1] else ""
                    name = groups[2].strip() if len(groups) > 2 and groups[2] else ""
                    
                    # Extract year
                    context = text[match.start():match.end() + 50]
                    year_match = re.search(r"(\d{4})", context)
                    year = int(year_match.group(1)) if year_match else None
                    
                    # Determine certification level
                    level = self._determine_certification_level(f"{provider} {cert_type} {name}")
                    
                    certifications.append({
                        "name": f"{provider} {cert_type} {name}".strip(),
                        "level": level,
                        "year": year
                    })
        
        return certifications
    
    def _chunk_text_with_metadata(
        self,
        parsed_content: Dict[str, Any],
        structured_metadata: Dict[str, Any],
        chunk_size: int,
        overlap: int
    ) -> List[Dict[str, Any]]:
        """Chunk text and associate relevant metadata with each chunk."""
        # Use the parser's chunk_text method with the correct structure
        chunks = self.parser.chunk_text(parsed_content, chunk_size, overlap)
        
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            # Determine which metadata is relevant to this chunk
            chunk_skills = self._get_relevant_skills(chunk["text"], structured_metadata["skills"])
            chunk_experience = self._get_relevant_experience(chunk["text"], structured_metadata["experience"])
            chunk_education = self._get_relevant_education(chunk["text"], structured_metadata["education"])
            chunk_certifications = self._get_relevant_certifications(chunk["text"], structured_metadata["certifications"])
            
            enhanced_chunk = {
                "text": chunk["text"],
                "section": chunk.get("section", "unknown"),
                "created_at": datetime.now().isoformat(),
                "skills": chunk_skills,
                "experience": chunk_experience,
                "education": chunk_education,
                "certifications": chunk_certifications,
                "metadata": chunk.get("metadata", {})
            }
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _get_relevant_skills(self, chunk_text: str, all_skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get skills relevant to this chunk."""
        relevant_skills = []
        chunk_lower = chunk_text.lower()
        
        for skill in all_skills:
            if skill["name"].lower() in chunk_lower:
                relevant_skills.append(skill)
        
        return relevant_skills
    
    def _get_relevant_experience(self, chunk_text: str, all_experience: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get experience relevant to this chunk."""
        relevant_experience = []
        chunk_lower = chunk_text.lower()
        
        for exp in all_experience:
            if (exp["role"].lower() in chunk_lower or 
                exp["company"].lower() in chunk_lower or
                any(tech.lower() in chunk_lower for tech in exp["technologies"])):
                relevant_experience.append(exp)
        
        return relevant_experience
    
    def _get_relevant_education(self, chunk_text: str, all_education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get education relevant to this chunk."""
        relevant_education = []
        chunk_lower = chunk_text.lower()
        
        for edu in all_education:
            if (edu["degree"].lower() in chunk_lower or 
                edu["institution"].lower() in chunk_lower):
                relevant_education.append(edu)
        
        return relevant_education
    
    def _get_relevant_certifications(self, chunk_text: str, all_certifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get certifications relevant to this chunk."""
        relevant_certifications = []
        chunk_lower = chunk_text.lower()
        
        for cert in all_certifications:
            if cert["name"].lower() in chunk_lower:
                relevant_certifications.append(cert)
        
        return relevant_certifications
    
    def _determine_proficiency(self, context: str) -> str:
        """Determine skill proficiency from context."""
        context_lower = context.lower()
        
        for level, keywords in self.proficiency_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                return level
        
        return "intermediate"  # Default
    
    def _determine_seniority(self, role: str, context: str) -> str:
        """Determine seniority level from role and context."""
        combined_text = f"{role} {context}".lower()
        
        for level, keywords in self.seniority_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return level
        
        return "mid"  # Default
    
    def _extract_duration(self, context: str) -> int:
        """Extract duration in years from context."""
        # Look for patterns like "2 years", "3 yrs", "2019-2021"
        year_patterns = [
            r"(\d+)\s*(?:years?|yrs?)",
            r"(\d{4})\s*(?:-|–)\s*(\d{4})",
            r"(\d{4})\s*(?:-|–)\s*present"
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                if len(match.groups()) == 1:
                    return int(match.group(1))
                elif len(match.groups()) == 2:
                    start_year = int(match.group(1))
                    end_year = int(match.group(2)) if match.group(2).isdigit() else datetime.now().year
                    return max(1, end_year - start_year)
        
        return 1  # Default to 1 year
    
    def _extract_technologies_from_context(self, context: str) -> List[str]:
        """Extract technologies mentioned in context."""
        tech_patterns = [
            r"(?i)(python|java|javascript|typescript|c\+\+|c#|ruby|go|rust|php|swift|kotlin)",
            r"(?i)(react|angular|vue|node\.js|express|django|flask|spring|laravel)",
            r"(?i)(aws|azure|gcp|docker|kubernetes|jenkins|git|linux|windows)",
            r"(?i)(mysql|postgresql|mongodb|redis|elasticsearch|sql server)"
        ]
        
        technologies = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, context)
            technologies.extend(matches)
        
        return list(set(technologies))  # Remove duplicates
    
    def _determine_education_level(self, degree: str) -> str:
        """Determine education level from degree."""
        degree_lower = degree.lower()
        
        if any(word in degree_lower for word in ["phd", "doctorate", "doctoral"]):
            return "doctorate"
        elif any(word in degree_lower for word in ["master", "msc", "mba", "ma"]):
            return "master"
        elif any(word in degree_lower for word in ["bachelor", "bsc", "ba", "bs"]):
            return "bachelor"
        else:
            return "other"
    
    def _determine_certification_level(self, cert_name: str) -> str:
        """Determine certification level."""
        cert_lower = cert_name.lower()
        
        if any(word in cert_lower for word in ["professional", "expert", "advanced", "architect"]):
            return "professional"
        elif any(word in cert_lower for word in ["associate", "practitioner", "intermediate"]):
            return "associate"
        else:
            return "foundational"
    
    def _get_section_summary(self, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get summary of sections in the enhanced CV."""
        section_counts = {}
        for chunk in chunks:
            section = chunk.get("section", "other")
            section_counts[section] = section_counts.get(section, 0) + 1
        return section_counts
    
    def search_with_advanced_filters(
        self,
        query: str,
        user_id: str,
        skill_requirements: Optional[List[Dict[str, Any]]] = None,
        experience_requirements: Optional[List[Dict[str, Any]]] = None,
        education_requirements: Optional[List[Dict[str, Any]]] = None,
        certification_requirements: Optional[List[Dict[str, Any]]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search with advanced filtering capabilities.
        
        Args:
            query: Search query text
            user_id: User identifier
            skill_requirements: List of skill requirements
            experience_requirements: List of experience requirements
            education_requirements: List of education requirements
            certification_requirements: List of certification requirements
            limit: Maximum number of results
            
        Returns:
            List of matching chunks with enhanced metadata
        """
        # Generate embedding for query
        query_embedding = self.embedding_generator.generate_single_embedding(query)
        
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            return []
        
        # Use enhanced Qdrant client for advanced search
        return self.qdrant_client.query_with_advanced_filters(
            query_embedding=query_embedding,
            user_id=user_id,
            skill_requirements=skill_requirements,
            experience_requirements=experience_requirements,
            education_requirements=education_requirements,
            certification_requirements=certification_requirements,
            limit=limit
        )
    
    def get_user_skill_inventory(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive skill inventory for a user."""
        return self.qdrant_client.get_user_skill_inventory(user_id)
    
    def search_across_all_user_cvs(
        self,
        user_id: str,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search across all CVs in a user's knowledge base.
        
        Args:
            user_id: User identifier
            query: Search query (job description or requirements)
            limit: Maximum number of results to return
            
        Returns:
            List of relevant CV chunks from all user's CVs
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_generator.generate_single_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate embedding for search query")
                return []
            
            # Use enhanced Qdrant client to search with user filtering
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Search in the enhanced collection with user filtering
            search_results = self.qdrant_client.client.search(
                collection_name=self.qdrant_client.collection_name,
                query_vector=query_embedding,
                query_filter=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                ),
                limit=limit,
                with_payload=True,
                score_threshold=0.3  # Minimum relevance threshold
            )
            
            # Format results for compatibility with existing workflow
            formatted_results = []
            for result in search_results:
                payload = result.payload
                
                formatted_result = {
                    "id": str(result.id),
                    "text": payload.get("text", ""),
                    "section": payload.get("section", "unknown"),
                    "cv_id": payload.get("cv_id", ""),
                    "user_id": payload.get("user_id", ""),
                    "score": float(result.score),
                    "created_at": payload.get("created_at", ""),
                    # Include enhanced metadata
                    "skills": payload.get("skills", []),
                    "experience": payload.get("experience", []),
                    "education": payload.get("education", []),
                    "certifications": payload.get("certifications", []),
                    "metadata": payload.get("metadata", {})
                }
                
                formatted_results.append(formatted_result)
            
            logger.info(f"Found {len(formatted_results)} relevant chunks across user's CV knowledge base")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching across user CVs: {e}")
            return []
    
    def delete_cv(self, cv_id: str) -> bool:
        """Delete a CV and all its chunks from enhanced Qdrant."""
        return self.qdrant_client.delete_cv_chunks(cv_id)
    
    def get_user_cv_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get user CV statistics from enhanced Qdrant collection.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary containing user CV statistics
        """
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Get collection stats
            collection_stats = self.qdrant_client.get_collection_stats()
            
            # Query user's CV chunks from enhanced collection
            scroll_result = self.qdrant_client.client.scroll(
                collection_name=self.qdrant_client.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                ),
                limit=1000,
                with_payload=True
            )
            
            # Process the results to get CV statistics
            cv_chunks = scroll_result[0]
            cv_ids = set()
            sections = set()
            total_chunks = len(cv_chunks)
            
            for chunk in cv_chunks:
                payload = chunk.payload
                cv_ids.add(payload.get("cv_id"))
                sections.add(payload.get("section", "unknown"))
            
            # Get user skill inventory (which includes detailed analysis)
            skill_inventory = self.qdrant_client.get_user_skill_inventory(user_id)
            
            # Create CV list with basic info
            cv_list = []
            for cv_id in cv_ids:
                cv_list.append({
                    "cv_id": cv_id,
                    "name": f"CV {cv_id[:8]}",
                    "display_name": f"CV {cv_id[:8]}",
                    "chunks": len([c for c in cv_chunks if c.payload.get("cv_id") == cv_id])
                })
            
            # Build comprehensive stats
            stats = {
                "user_id": user_id,
                "total_cvs": len(cv_ids),
                "total_chunks": total_chunks,
                "unique_sections": len(sections),
                "cv_list": cv_list,
                "collection_stats": collection_stats,
                "sections": list(sections)
            }
            
            # Add skill inventory data if available
            if "error" not in skill_inventory:
                stats.update({
                    "total_skills": skill_inventory.get("summary", {}).get("total_skills", 0),
                    "total_roles": skill_inventory.get("summary", {}).get("total_roles", 0),
                    "total_education": skill_inventory.get("summary", {}).get("total_education", 0),
                    "total_certifications": skill_inventory.get("summary", {}).get("total_certifications", 0),
                    "skill_inventory": skill_inventory
                })
            
            logger.info(f"Retrieved CV stats for user {user_id}: {len(cv_ids)} CVs, {total_chunks} chunks")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user CV stats: {e}")
            return {
                "user_id": user_id,
                "total_cvs": 0,
                "total_chunks": 0,
                "unique_sections": 0,
                "error": str(e)
            }
