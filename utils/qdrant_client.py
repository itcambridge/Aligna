"""
Qdrant client utility for CV storage and retrieval.
Handles connection, collection management, and embedding operations.
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

class QdrantCVClient:
    """Client for managing CV embeddings in Qdrant."""
    
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize Qdrant client."""
        self.url = url or os.getenv("QDRANT_URL")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        
        if not self.url:
            raise ValueError("QDRANT_URL environment variable is required")
        
        self.client = QdrantClient(url=self.url, api_key=self.api_key)
        self.collection_name = "cv_chunks"
        self.vector_size = 1536  # OpenAI embedding dimension
        
    def create_collection(self) -> bool:
        """Create the CV chunks collection if it doesn't exist."""
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
            logger.error(f"Error creating collection: {e}")
            return False
    
    def upsert_embeddings(
        self,
        cv_id: str,
        user_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Upsert CV chunks with their embeddings.
        
        Args:
            cv_id: Unique CV identifier
            user_id: User identifier
            chunks: List of text chunks with metadata
            embeddings: List of embedding vectors
        """
        try:
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "cv_id": cv_id,
                        "user_id": user_id,
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
            logger.info(f"Upserted {len(points)} chunks for CV {cv_id}")
            return True
        except Exception as e:
            logger.error(f"Error upserting embeddings: {e}")
            return False
    
    def query_similar_chunks(
        self,
        query_embedding: List[float],
        cv_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query for similar CV chunks based on embedding.
        
        Args:
            query_embedding: Query embedding vector
            cv_id: Filter by specific CV
            user_id: Filter by specific user
            limit: Maximum number of results
            
        Returns:
            List of similar chunks with scores
        """
        try:
            # Build filter
            filter_conditions = []
            if cv_id:
                filter_conditions.append(
                    FieldCondition(key="cv_id", match=MatchValue(value=cv_id))
                )
            if user_id:
                filter_conditions.append(
                    FieldCondition(key="user_id", match=MatchValue(value=user_id))
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
                    "metadata": result.payload.get("metadata", {})
                })
            
            return results
        except Exception as e:
            logger.error(f"Error querying similar chunks: {e}")
            return []
    
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
            logger.info(f"Deleted all chunks for CV {cv_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting CV chunks: {e}")
            return False
    
    def get_cv_stats(self, cv_id: str) -> Dict[str, Any]:
        """Get statistics for a specific CV."""
        try:
            # Count chunks for this CV
            count_result = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[FieldCondition(key="cv_id", match=MatchValue(value=cv_id))]
                )
            )
            
            return {
                "cv_id": cv_id,
                "total_chunks": count_result.count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"Error getting CV stats: {e}")
            return {"cv_id": cv_id, "total_chunks": 0, "error": str(e)}
    
    def get_user_cvs(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all CVs for a specific user with metadata.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of CV information with stats
        """
        try:
            # Scroll through all points for this user
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                ),
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
                        "user_id": user_id,
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
                    "user_id": user_id,
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
            
            logger.info(f"Found {len(cv_list)} CVs for user {user_id}")
            return cv_list
            
        except Exception as e:
            logger.error(f"Error getting user CVs: {e}")
            return []
    
    def get_user_cv_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a user's CV collection.
        
        Args:
            user_id: User identifier
            
        Returns:
            Statistics about user's CV collection
        """
        try:
            cvs = self.get_user_cvs(user_id)
            
            if not cvs:
                return {
                    "user_id": user_id,
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
                "user_id": user_id,
                "total_cvs": len(cvs),
                "total_chunks": total_chunks,
                "unique_sections": len(all_sections),
                "sections_list": list(all_sections),
                "cv_list": cvs
            }
            
        except Exception as e:
            logger.error(f"Error getting user CV stats: {e}")
            return {
                "user_id": user_id,
                "total_cvs": 0,
                "total_chunks": 0,
                "unique_sections": 0,
                "error": str(e)
            }
    
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
    
    def query_across_all_user_cvs(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Query for similar chunks across ALL CVs for a user.
        
        Args:
            query_embedding: Query embedding vector
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of similar chunks from all user's CVs with scores
        """
        try:
            # Search across all user's CVs
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                ),
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
            
            logger.info(f"Found {len(results)} matches across all CVs for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error querying across user CVs: {e}")
            return []
