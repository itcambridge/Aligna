"""
User-specific CV processor for multi-tenant CV storage.
Handles CV processing with user isolation using UserQdrantClient.
"""

import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from utils.cv_parser import CVParser
from utils.embeddings import EmbeddingGenerator
from utils.user_qdrant_client import UserQdrantClient

logger = logging.getLogger(__name__)

class UserCVProcessor:
    """Process CV documents for a specific user with isolated storage."""
    
    def __init__(self, user_id: str, embedding_model: str = "openai"):
        """
        Initialize user-specific CV processor.
        
        Args:
            user_id: User identifier for data isolation
            embedding_model: "openai" or "sentence-transformers"
        """
        self.user_id = user_id
        self.parser = CVParser()
        self.embedding_generator = EmbeddingGenerator(embedding_model)
        self.user_qdrant_client = UserQdrantClient(user_id)
        
        # Ensure user's collection exists
        self.user_qdrant_client.ensure_user_collection()
        
        logger.info(f"Initialized UserCVProcessor for user {user_id}")
    
    def process_cv(
        self,
        file_path: str,
        cv_id: Optional[str] = None,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> Dict[str, Any]:
        """
        Process a CV file: parse, chunk, embed, and store in user's collection.
        
        Args:
            file_path: Path to the CV file
            cv_id: Optional CV identifier (generated if not provided)
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            Processing results with metadata
        """
        if not cv_id:
            cv_id = str(uuid.uuid4())
        
        try:
            # Step 1: Parse the CV file
            logger.info(f"Parsing CV file for user {self.user_id}: {file_path}")
            parsed_content = self.parser.parse_file(file_path)
            
            # Step 2: Chunk the text
            logger.info(f"Chunking CV text for user {self.user_id}")
            chunks = self.parser.chunk_text(parsed_content, chunk_size, overlap)
            
            if not chunks:
                raise ValueError("No text chunks extracted from CV")
            
            # Add user_id and timestamp to chunks
            for chunk in chunks:
                chunk["user_id"] = self.user_id
                chunk["created_at"] = datetime.now().isoformat()
            
            # Step 3: Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedding_generator.generate_embeddings(chunk_texts)
            
            if not embeddings:
                raise ValueError("Failed to generate embeddings")
            
            # Step 4: Store in user's Qdrant collection
            logger.info(f"Storing chunks and embeddings in user collection")
            success = self.user_qdrant_client.upsert_embeddings(
                cv_id=cv_id,
                chunks=chunks,
                embeddings=embeddings
            )
            
            if not success:
                raise ValueError("Failed to store embeddings in user's collection")
            
            # Step 5: Extract contact information
            full_text = " ".join([chunk["text"] for chunk in chunks])
            contact_info = self.parser.extract_contact_info(full_text)
            
            # Step 6: Prepare results
            result = {
                "cv_id": cv_id,
                "user_id": self.user_id,
                "file_path": file_path,
                "file_type": parsed_content["file_type"],
                "total_chunks": len(chunks),
                "total_embeddings": len(embeddings),
                "contact_info": contact_info,
                "sections": self._get_section_summary(chunks),
                "processed_at": datetime.now().isoformat(),
                "status": "success"
            }
            
            logger.info(f"Successfully processed CV {cv_id} for user {self.user_id} with {len(chunks)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error processing CV {file_path} for user {self.user_id}: {e}")
            return {
                "cv_id": cv_id,
                "user_id": self.user_id,
                "file_path": file_path,
                "status": "error",
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    def _get_section_summary(self, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get summary of sections in the CV."""
        section_counts = {}
        for chunk in chunks:
            section = chunk.get("section", "other")
            section_counts[section] = section_counts.get(section, 0) + 1
        return section_counts
    
    def get_cv_info(self, cv_id: str) -> Dict[str, Any]:
        """Get information about a processed CV."""
        try:
            cvs = self.user_qdrant_client.get_user_cvs()
            for cv in cvs:
                if cv["cv_id"] == cv_id:
                    return cv
            return {"error": f"CV {cv_id} not found for user {self.user_id}"}
        except Exception as e:
            logger.error(f"Error getting CV info: {e}")
            return {"error": str(e)}
    
    def delete_cv(self, cv_id: str) -> bool:
        """Delete a CV and all its chunks from user's collection."""
        try:
            return self.user_qdrant_client.delete_cv_chunks(cv_id)
        except Exception as e:
            logger.error(f"Error deleting CV: {e}")
            return False
    
    def search_similar_chunks(
        self,
        query: str,
        cv_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in user's CV data.
        
        Args:
            query: Search query text
            cv_id: Filter by specific CV (optional)
            limit: Maximum number of results
            
        Returns:
            List of similar chunks with scores
        """
        # Generate embedding for query
        query_embedding = self.embedding_generator.generate_single_embedding(query)
        
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            return []
        
        # Search in user's collection
        return self.user_qdrant_client.query_similar_chunks(
            query_embedding=query_embedding,
            cv_id=cv_id,
            limit=limit
        )
    
    def get_user_cvs(self) -> List[Dict[str, Any]]:
        """Get all CVs for this user."""
        return self.user_qdrant_client.get_user_cvs()
    
    def get_user_cv_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for user's CV collection."""
        return self.user_qdrant_client.get_user_cv_stats()
    
    def search_across_all_user_cvs(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks across ALL CVs for this user.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            List of similar chunks from all user's CVs with scores
        """
        # Generate embedding for query
        query_embedding = self.embedding_generator.generate_single_embedding(query)
        
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            return []
        
        # Search across all user's CVs
        return self.user_qdrant_client.query_across_all_user_cvs(
            query_embedding=query_embedding,
            limit=limit
        )
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the user's collection."""
        try:
            collections = self.user_qdrant_client.client.get_collections()
            user_collection = None
            
            for collection in collections.collections:
                if collection.name == self.user_qdrant_client.collection_name:
                    user_collection = collection
                    break
            
            if user_collection:
                return {
                    "collection_name": user_collection.name,
                    "status": user_collection.status,
                    "vectors_count": user_collection.vectors_count,
                    "indexed_vectors_count": user_collection.indexed_vectors_count,
                    "points_count": user_collection.points_count
                }
            else:
                return {"error": f"Collection {self.user_qdrant_client.collection_name} not found"}
                
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}
