"""
User-specific Qdrant client for multi-tenant CV storage.
Each user gets their own collection for complete data isolation.
"""

import os
import uuid
from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from qdrant_client.http import models
import logging

logger = logging.getLogger(__name__)

class UserQdrantClient:
    """User-specific Qdrant client with isolated collections."""
    
    def __init__(self, user_id: str, url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize user-specific Qdrant client.
        
        Args:
            user_id: Unique user identifier
            url: Qdrant server URL
            api_key: Qdrant API key
        """
        self.user_id = user_id
        self.url = url or os.getenv("QDRANT_URL")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        
        if not self.url:
            raise ValueError("QDRANT_URL environment variable is required")
        
        self.client = QdrantClient(url=self.url, api_key=self.api_key)
        
        # User-specific collection name
        self.collection_name = f"cv_chunks_user_{user_id.replace('-', '_')}"
        self.vector_size = 1536  # OpenAI embedding dimension
        
        logger.info(f"Initialized UserQdrantClient for user {user_id} with collection {self.collection_name}")
    
    def ensure_user_collection(self) -> bool:
        """
        Ensure the user's collection exists, create if it doesn't.
        
        Returns:
            True if collection exists or was created successfully
        """
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
                logger.info(f"Created collection: {self.collection_name}")
                return True
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                return True
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            return False
    
    def upsert_embeddings(
        self,
        cv_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Upsert CV chunks with their embeddings to user's collection.
        
        Args:
            cv_id: Unique CV identifier
            chunks: List of text chunks with metadata
            embeddings: List of embedding vectors
            
        Returns:
            True if successful
        """
        try:
            # Ensure collection exists
            if not self.ensure_user_collection():
                return False
            
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "user_id": self.user_id,
                        "cv_id": cv_id,
                        "chunk_text": chunk["text"],
                        "chunk_index": i,
                        "metadata": chunk.get("metadata", {}),
                        "section": chunk.get("section", "unknown"),
                        "created_at": chunk.get("created_at")
                    }
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} chunks for CV {cv_id} in user collection {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error upserting embeddings: {e}")
            return False
    
    def query_similar_chunks(
        self,
        query_embedding: List[float],
        cv_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query for similar CV chunks in user's collection.
        
        Args:
            query_embedding: Query embedding vector
            cv_id: Filter by specific CV (optional)
            limit: Maximum number of results
            
        Returns:
            List of similar chunks with scores
        """
        try:
            # Ensure collection exists
            if not self.ensure_user_collection():
                return []
            
            # Build filter
            filter_conditions = []
            if cv_id:
                filter_conditions.append(
                    FieldCondition(key="cv_id", match=MatchValue(value=cv_id))
                )
            
            filter_query = Filter(must=filter_conditions) if filter_conditions else None
            
            # Search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=filter_query,
                limit=limit,
                with_payload=True
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
                    "metadata": result.payload.get("metadata", {}),
                    "cv_id": result.payload.get("cv_id"),
                    "chunk_index": result.payload.get("chunk_index", 0)
                })
            
            logger.info(f"Found {len(results)} similar chunks for user {self.user_id}")
            return results
        except Exception as e:
            logger.error(f"Error querying similar chunks: {e}")
            return []
    
    def get_user_cvs(self) -> List[Dict[str, Any]]:
        """
        Get all CVs for this user with metadata.
        
        Returns:
            List of CV information with stats
        """
        try:
            # Ensure collection exists
            if not self.ensure_user_collection():
                return []
            
            # Scroll through all points for this user
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,  # Get up to 1000 chunks
                with_payload=True
            )
            
            # Group by CV ID and collect metadata
            cv_data = {}
            for point in scroll_result[0]:  # scroll_result is (points, next_page_offset)
                payload = point.payload
                cv_id = payload.get("cv_id")
                
                if cv_id not in cv_data:
                    cv_data[cv_id] = {
                        "cv_id": cv_id,
                        "user_id": self.user_id,
                        "chunks": [],
                        "sections": set(),
                        "created_at": payload.get("created_at"),
                        "total_chunks": 0
                    }
                
                cv_data[cv_id]["chunks"].append({
                    "text": payload.get("chunk_text", ""),
                    "section": payload.get("section", "unknown"),
                    "chunk_index": payload.get("chunk_index", 0)
                })
                cv_data[cv_id]["sections"].add(payload.get("section", "unknown"))
                cv_data[cv_id]["total_chunks"] += 1
            
            # Convert to list and add derived fields
            cv_list = []
            for cv_id, data in cv_data.items():
                # Get first chunk for preview
                first_chunk = min(data["chunks"], key=lambda x: x["chunk_index"]) if data["chunks"] else None
                preview_text = first_chunk["text"][:200] + "..." if first_chunk else "No content"
                
                # Extract potential name from first chunk
                cv_name = self._extract_cv_name(first_chunk["text"] if first_chunk else "")
                
                cv_info = {
                    "cv_id": cv_id,
                    "user_id": self.user_id,
                    "name": cv_name or f"CV {cv_id[:8]}",
                    "total_chunks": data["total_chunks"],
                    "sections": list(data["sections"]),
                    "preview_text": preview_text,
                    "created_at": data["created_at"],
                    "display_name": f"{cv_name or 'CV'} ({data['total_chunks']} sections)"
                }
                cv_list.append(cv_info)
            
            # Sort by creation date (newest first)
            cv_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            logger.info(f"Found {len(cv_list)} CVs for user {self.user_id}")
            return cv_list
            
        except Exception as e:
            logger.error(f"Error getting user CVs: {e}")
            return []
    
    def get_user_cv_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics for user's CV collection.
        
        Returns:
            Statistics about user's CV collection
        """
        try:
            cvs = self.get_user_cvs()
            
            if not cvs:
                return {
                    "user_id": self.user_id,
                    "total_cvs": 0,
                    "total_chunks": 0,
                    "unique_sections": 0,
                    "cv_list": []
                }
            
            # Calculate aggregate stats
            total_chunks = sum(cv["total_chunks"] for cv in cvs)
            all_sections = set()
            for cv in cvs:
                all_sections.update(cv["sections"])
            
            return {
                "user_id": self.user_id,
                "total_cvs": len(cvs),
                "total_chunks": total_chunks,
                "unique_sections": len(all_sections),
                "sections_list": list(all_sections),
                "cv_list": cvs
            }
            
        except Exception as e:
            logger.error(f"Error getting user CV stats: {e}")
            return {
                "user_id": self.user_id,
                "total_cvs": 0,
                "total_chunks": 0,
                "unique_sections": 0,
                "error": str(e)
            }
    
    def query_across_all_user_cvs(
        self,
        query_embedding: List[float],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Query for similar chunks across ALL CVs for this user.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            
        Returns:
            List of similar chunks from all user's CVs with scores
        """
        try:
            # Ensure collection exists
            if not self.ensure_user_collection():
                return []
            
            # Search across all user's CVs (no CV filter)
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )
            
            # Format results with CV source information
            results = []
            for result in search_result:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "cv_id": result.payload.get("cv_id"),
                    "user_id": result.payload.get("user_id"),
                    "text": result.payload.get("chunk_text", ""),
                    "section": result.payload.get("section", "unknown"),
                    "chunk_index": result.payload.get("chunk_index", 0),
                    "metadata": result.payload.get("metadata", {}),
                    "created_at": result.payload.get("created_at")
                })
            
            logger.info(f"Found {len(results)} matches across all CVs for user {self.user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error querying across user CVs: {e}")
            return []
    
    def delete_cv_chunks(self, cv_id: str) -> bool:
        """
        Delete all chunks for a specific CV.
        
        Args:
            cv_id: CV identifier to delete
            
        Returns:
            True if successful
        """
        try:
            # Ensure collection exists
            if not self.ensure_user_collection():
                return False
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=Filter(
                        must=[FieldCondition(key="cv_id", match=MatchValue(value=cv_id))]
                    )
                )
            )
            logger.info(f"Deleted all chunks for CV {cv_id} in user collection {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting CV chunks: {e}")
            return False
    
    def delete_user_collection(self) -> bool:
        """
        Delete the entire user collection (use with caution).
        
        Returns:
            True if successful
        """
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted user collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user collection: {e}")
            return False
    
    def _extract_cv_name(self, text: str) -> Optional[str]:
        """Extract a potential name from CV text (first few lines)."""
        if not text:
            return None
        
        lines = text.split('\n')[:3]  # Look at first 3 lines
        for line in lines:
            line = line.strip()
            # Look for name patterns (simple heuristic)
            if len(line) > 2 and len(line) < 50 and not any(char.isdigit() for char in line):
                # Skip common CV headers
                skip_words = ['cv', 'resume', 'curriculum', 'vitae', 'profile', 'summary']
                if not any(word in line.lower() for word in skip_words):
                    return line
        
        return None
