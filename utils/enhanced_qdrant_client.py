"""
Enhanced Qdrant client with advanced filtering and nested object support.
Implements improvements based on Qdrant API v1.15.x documentation.
"""

import os
import uuid
from typing import List, Dict, Optional, Any, Union
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    NestedCondition,
    HasIdCondition,
)
from qdrant_client.http import models
import logging

logger = logging.getLogger(__name__)

class EnhancedQdrantCVClient:
    """Enhanced client for managing CV embeddings with advanced filtering in Qdrant."""
    
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize enhanced Qdrant client."""
        self.url = url or os.getenv("QDRANT_URL")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        
        if not self.url:
            raise ValueError("QDRANT_URL environment variable is required")
        
        self.client = QdrantClient(url=self.url, api_key=self.api_key)
        self.collection_name = "cv_chunks_enhanced"
        self.vector_size = 1536  # OpenAI embedding dimension
        
    def create_collection(self) -> bool:
        """Create the enhanced CV chunks collection if it doesn't exist."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created enhanced collection: {self.collection_name}")
                
                # Create field indexes for performance
                self._create_field_indexes()
                return True
            else:
                logger.info(f"Enhanced collection {self.collection_name} already exists")
                return True
        except Exception as e:
            logger.error(f"Error creating enhanced collection: {e}")
            return False
    
    def _create_field_indexes(self) -> None:
        """Create field indexes for enhanced filtering performance."""
        indexes_to_create = [
            # Basic fields
            ("user_id", "keyword"),
            ("cv_id", "keyword"),
            ("section", "keyword"),
            
            # Nested skill fields
            ("skills[].name", "keyword"),
            ("skills[].proficiency", "keyword"),
            ("skills[].years_experience", "integer"),
            ("skills[].context", "keyword"),
            
            # Nested experience fields
            ("experience[].role", "keyword"),
            ("experience[].company", "keyword"),
            ("experience[].duration_years", "integer"),
            ("experience[].seniority", "keyword"),
            ("experience[].technologies[]", "keyword"),
            
            # Nested education fields
            ("education[].degree", "keyword"),
            ("education[].level", "keyword"),
            ("education[].institution", "keyword"),
            ("education[].year", "integer"),
            
            # Nested certification fields
            ("certifications[].name", "keyword"),
            ("certifications[].level", "keyword"),
            ("certifications[].year", "integer"),
        ]
        
        for field_name, field_schema in indexes_to_create:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_schema
                )
                logger.info(f"Created index for field: {field_name}")
            except Exception as e:
                logger.warning(f"Could not create index for {field_name}: {e}")
    
    def upsert_enhanced_embeddings(
        self,
        cv_id: str,
        user_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Upsert CV chunks with enhanced nested metadata structure.
        
        Args:
            cv_id: Unique CV identifier
            user_id: User identifier
            chunks: List of text chunks with enhanced metadata
            embeddings: List of embedding vectors
        """
        try:
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Enhanced payload structure with nested objects
                payload = {
                    "cv_id": cv_id,
                    "user_id": user_id,
                    "chunk_text": chunk["text"],
                    "chunk_index": i,
                    "section": chunk.get("section", "unknown"),
                    "created_at": chunk.get("created_at"),
                    
                    # Nested skills array
                    "skills": chunk.get("skills", []),
                    
                    # Nested experience array
                    "experience": chunk.get("experience", []),
                    
                    # Nested education array
                    "education": chunk.get("education", []),
                    
                    # Nested certifications array
                    "certifications": chunk.get("certifications", []),
                    
                    # Additional metadata
                    "metadata": chunk.get("metadata", {})
                }
                
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} enhanced chunks for CV {cv_id}")
            return True
        except Exception as e:
            logger.error(f"Error upserting enhanced embeddings: {e}")
            return False
    
    def query_with_advanced_filters(
        self,
        query_embedding: List[float],
        user_id: str,
        skill_requirements: Optional[List[Dict[str, Any]]] = None,
        experience_requirements: Optional[List[Dict[str, Any]]] = None,
        education_requirements: Optional[List[Dict[str, Any]]] = None,
        certification_requirements: Optional[List[Dict[str, Any]]] = None,
        section_filter: Optional[str] = None,
        cv_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Advanced query with nested filtering capabilities.
        
        Args:
            query_embedding: Query embedding vector
            user_id: User identifier
            skill_requirements: List of skill requirements with nested conditions
            experience_requirements: List of experience requirements
            education_requirements: List of education requirements
            certification_requirements: List of certification requirements
            section_filter: Filter by specific section
            cv_id: Filter by specific CV
            limit: Maximum number of results
            
        Returns:
            List of matching chunks with scores
        """
        try:
            # Build filter conditions
            filter_conditions = [
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            ]
            
            # Add CV filter if specified
            if cv_id:
                filter_conditions.append(
                    FieldCondition(key="cv_id", match=MatchValue(value=cv_id))
                )
            
            # Add section filter if specified
            if section_filter:
                filter_conditions.append(
                    FieldCondition(key="section", match=MatchValue(value=section_filter))
                )
            
            # Add nested skill filters
            if skill_requirements:
                for skill_req in skill_requirements:
                    skill_conditions = []
                    
                    if "name" in skill_req:
                        skill_conditions.append(
                            FieldCondition(key="name", match=MatchValue(value=skill_req["name"]))
                        )
                    
                    if "proficiency" in skill_req:
                        skill_conditions.append(
                            FieldCondition(key="proficiency", match=MatchValue(value=skill_req["proficiency"]))
                        )
                    
                    if "min_years" in skill_req:
                        skill_conditions.append(
                            FieldCondition(
                                key="years_experience",
                                range=Range(gte=skill_req["min_years"])
                            )
                        )
                    
                    if skill_conditions:
                        filter_conditions.append(
                            NestedCondition(
                                key="skills",
                                filter=Filter(must=skill_conditions)
                            )
                        )
            
            # Add nested experience filters
            if experience_requirements:
                for exp_req in experience_requirements:
                    exp_conditions = []
                    
                    if "role" in exp_req:
                        exp_conditions.append(
                            FieldCondition(key="role", match=MatchValue(value=exp_req["role"]))
                        )
                    
                    if "seniority" in exp_req:
                        exp_conditions.append(
                            FieldCondition(key="seniority", match=MatchValue(value=exp_req["seniority"]))
                        )
                    
                    if "min_duration" in exp_req:
                        exp_conditions.append(
                            FieldCondition(
                                key="duration_years",
                                range=Range(gte=exp_req["min_duration"])
                            )
                        )
                    
                    if "technologies" in exp_req:
                        for tech in exp_req["technologies"]:
                            exp_conditions.append(
                                FieldCondition(key="technologies", match=MatchValue(value=tech))
                            )
                    
                    if exp_conditions:
                        filter_conditions.append(
                            NestedCondition(
                                key="experience",
                                filter=Filter(must=exp_conditions)
                            )
                        )
            
            # Add nested education filters
            if education_requirements:
                for edu_req in education_requirements:
                    edu_conditions = []
                    
                    if "degree" in edu_req:
                        edu_conditions.append(
                            FieldCondition(key="degree", match=MatchValue(value=edu_req["degree"]))
                        )
                    
                    if "level" in edu_req:
                        edu_conditions.append(
                            FieldCondition(key="level", match=MatchValue(value=edu_req["level"]))
                        )
                    
                    if edu_conditions:
                        filter_conditions.append(
                            NestedCondition(
                                key="education",
                                filter=Filter(must=edu_conditions)
                            )
                        )
            
            # Add nested certification filters
            if certification_requirements:
                for cert_req in certification_requirements:
                    cert_conditions = []
                    
                    if "name" in cert_req:
                        cert_conditions.append(
                            FieldCondition(key="name", match=MatchValue(value=cert_req["name"]))
                        )
                    
                    if "level" in cert_req:
                        cert_conditions.append(
                            FieldCondition(key="level", match=MatchValue(value=cert_req["level"]))
                        )
                    
                    if cert_conditions:
                        filter_conditions.append(
                            NestedCondition(
                                key="certifications",
                                filter=Filter(must=cert_conditions)
                            )
                        )
            
            # Create final filter
            query_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Execute search with advanced filtering
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            results = []
            for result in search_result:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                    "text": result.payload.get("chunk_text", ""),
                    "section": result.payload.get("section", "unknown"),
                    "skills": result.payload.get("skills", []),
                    "experience": result.payload.get("experience", []),
                    "education": result.payload.get("education", []),
                    "certifications": result.payload.get("certifications", []),
                    "metadata": result.payload.get("metadata", {})
                })
            
            logger.info(f"Found {len(results)} matches with advanced filtering")
            return results
            
        except Exception as e:
            logger.error(f"Error in advanced query: {e}")
            return []
    
    def query_skill_proficiency_match(
        self,
        query_embedding: List[float],
        user_id: str,
        required_skills: List[str],
        min_proficiency: str = "intermediate",
        min_years: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query for chunks with specific skill proficiency requirements.
        
        Args:
            query_embedding: Query embedding vector
            user_id: User identifier
            required_skills: List of required skill names
            min_proficiency: Minimum proficiency level
            min_years: Minimum years of experience
            limit: Maximum number of results
            
        Returns:
            List of matching chunks with skill evidence
        """
        skill_requirements = []
        for skill in required_skills:
            skill_requirements.append({
                "name": skill,
                "proficiency": min_proficiency,
                "min_years": min_years
            })
        
        return self.query_with_advanced_filters(
            query_embedding=query_embedding,
            user_id=user_id,
            skill_requirements=skill_requirements,
            limit=limit
        )
    
    def query_experience_level_match(
        self,
        query_embedding: List[float],
        user_id: str,
        target_role: str,
        min_years: int = 2,
        seniority_level: str = "mid",
        required_technologies: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query for chunks with specific experience level requirements.
        
        Args:
            query_embedding: Query embedding vector
            user_id: User identifier
            target_role: Target job role
            min_years: Minimum years of experience
            seniority_level: Required seniority level
            required_technologies: List of required technologies
            limit: Maximum number of results
            
        Returns:
            List of matching chunks with experience evidence
        """
        experience_req = {
            "role": target_role,
            "min_duration": min_years,
            "seniority": seniority_level
        }
        
        if required_technologies:
            experience_req["technologies"] = required_technologies
        
        return self.query_with_advanced_filters(
            query_embedding=query_embedding,
            user_id=user_id,
            experience_requirements=[experience_req],
            limit=limit
        )
    
    def query_multi_criteria_match(
        self,
        query_embedding: List[float],
        user_id: str,
        job_requirements: Dict[str, Any],
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Query with multiple criteria for comprehensive job matching.
        
        Args:
            query_embedding: Query embedding vector
            user_id: User identifier
            job_requirements: Dictionary containing all job requirements
            limit: Maximum number of results
            
        Returns:
            List of matching chunks with comprehensive evidence
        """
        return self.query_with_advanced_filters(
            query_embedding=query_embedding,
            user_id=user_id,
            skill_requirements=job_requirements.get("skills", []),
            experience_requirements=job_requirements.get("experience", []),
            education_requirements=job_requirements.get("education", []),
            certification_requirements=job_requirements.get("certifications", []),
            limit=limit
        )
    
    def get_user_skill_inventory(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive skill inventory for a user across all CVs.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary containing skill inventory with proficiency levels
        """
        try:
            # Scroll through all points for this user
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                ),
                limit=1000,
                with_payload=True
            )
            
            # Aggregate skills across all chunks
            skill_inventory = {}
            experience_inventory = {}
            education_inventory = []
            certification_inventory = []
            
            for point in scroll_result[0]:
                payload = point.payload
                
                # Process skills
                for skill in payload.get("skills", []):
                    skill_name = skill.get("name", "").lower()
                    if skill_name:
                        if skill_name not in skill_inventory:
                            skill_inventory[skill_name] = {
                                "name": skill.get("name", ""),
                                "max_proficiency": skill.get("proficiency", ""),
                                "max_years": skill.get("years_experience", 0),
                                "contexts": set()
                            }
                        else:
                            # Update with highest proficiency and years
                            current_years = skill.get("years_experience", 0)
                            if current_years > skill_inventory[skill_name]["max_years"]:
                                skill_inventory[skill_name]["max_years"] = current_years
                                skill_inventory[skill_name]["max_proficiency"] = skill.get("proficiency", "")
                        
                        skill_inventory[skill_name]["contexts"].add(skill.get("context", ""))
                
                # Process experience
                for exp in payload.get("experience", []):
                    role = exp.get("role", "")
                    if role:
                        if role not in experience_inventory:
                            experience_inventory[role] = {
                                "total_years": 0,
                                "companies": set(),
                                "technologies": set(),
                                "seniority_levels": set()
                            }
                        
                        experience_inventory[role]["total_years"] += exp.get("duration_years", 0)
                        experience_inventory[role]["companies"].add(exp.get("company", ""))
                        experience_inventory[role]["technologies"].update(exp.get("technologies", []))
                        experience_inventory[role]["seniority_levels"].add(exp.get("seniority", ""))
                
                # Process education
                for edu in payload.get("education", []):
                    if edu not in education_inventory:
                        education_inventory.append(edu)
                
                # Process certifications
                for cert in payload.get("certifications", []):
                    if cert not in certification_inventory:
                        certification_inventory.append(cert)
            
            # Convert sets to lists for JSON serialization
            for skill in skill_inventory.values():
                skill["contexts"] = list(skill["contexts"])
            
            for exp in experience_inventory.values():
                exp["companies"] = list(exp["companies"])
                exp["technologies"] = list(exp["technologies"])
                exp["seniority_levels"] = list(exp["seniority_levels"])
            
            return {
                "user_id": user_id,
                "skills": skill_inventory,
                "experience": experience_inventory,
                "education": education_inventory,
                "certifications": certification_inventory,
                "summary": {
                    "total_skills": len(skill_inventory),
                    "total_roles": len(experience_inventory),
                    "total_education": len(education_inventory),
                    "total_certifications": len(certification_inventory)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user skill inventory: {e}")
            return {"user_id": user_id, "error": str(e)}
    
    def delete_cv_chunks(self, cv_id: str) -> bool:
        """Delete all chunks for a specific CV."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=Filter(
                        must=[FieldCondition(key="cv_id", match=MatchValue(value=cv_id))]
                    )
                )
            )
            logger.info(f"Deleted all enhanced chunks for CV {cv_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting enhanced CV chunks: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the enhanced collection."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "status": collection_info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
