"""
CV processor for handling CV upload, parsing, chunking, and indexing.
"""

import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from utils.cv_parser import CVParser
from utils.embeddings import EmbeddingGenerator
from utils.qdrant_client import QdrantCVClient

logger = logging.getLogger(__name__)

class CVProcessor:
    """Process CV documents: parse, chunk, embed, and store in Qdrant."""
    
    def __init__(self, embedding_model: str = "openai"):
        """
        Initialize CV processor.
        
        Args:
            embedding_model: "openai" or "sentence-transformers"
        """
        self.parser = CVParser()
        self.embedding_generator = EmbeddingGenerator(embedding_model)
        self.qdrant_client = QdrantCVClient()
        
        # Ensure Qdrant collection exists
        self.qdrant_client.create_collection()
    
    def process_cv(
        self,
        file_path: str,
        user_id: str,
        cv_id: Optional[str] = None,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> Dict[str, Any]:
        """
        Process a CV file: parse, chunk, embed, and store.
        
        Args:
            file_path: Path to the CV file
            user_id: User identifier
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
            logger.info(f"Parsing CV file: {file_path}")
            parsed_content = self.parser.parse_file(file_path)
            
            # Step 2: Chunk the text
            logger.info("Chunking CV text")
            chunks = self.parser.chunk_text(parsed_content, chunk_size, overlap)
            
            if not chunks:
                raise ValueError("No text chunks extracted from CV")
            
            # Step 3: Generate embeddings
            logger.info("Generating embeddings for chunks")
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedding_generator.generate_embeddings(chunk_texts)
            
            if not embeddings:
                raise ValueError("Failed to generate embeddings")
            
            # Step 4: Store in Qdrant
            logger.info("Storing chunks and embeddings in Qdrant")
            success = self.qdrant_client.upsert_embeddings(
                cv_id=cv_id,
                user_id=user_id,
                chunks=chunks,
                embeddings=embeddings
            )
            
            if not success:
                raise ValueError("Failed to store embeddings in Qdrant")
            
            # Step 5: Extract contact information
            full_text = " ".join([chunk["text"] for chunk in chunks])
            contact_info = self.parser.extract_contact_info(full_text)
            
            # Step 6: Prepare results
            result = {
                "cv_id": cv_id,
                "user_id": user_id,
                "file_path": file_path,
                "file_type": parsed_content["file_type"],
                "total_chunks": len(chunks),
                "total_embeddings": len(embeddings),
                "contact_info": contact_info,
                "sections": self._get_section_summary(chunks),
                "processed_at": datetime.now().isoformat(),
                "status": "success"
            }
            
            logger.info(f"Successfully processed CV {cv_id} with {len(chunks)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error processing CV {file_path}: {e}")
            return {
                "cv_id": cv_id,
                "user_id": user_id,
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
        return self.qdrant_client.get_cv_stats(cv_id)
    
    def delete_cv(self, cv_id: str) -> bool:
        """Delete a CV and all its chunks from Qdrant."""
        return self.qdrant_client.delete_cv_chunks(cv_id)
    
    def search_similar_chunks(
        self,
        query: str,
        cv_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in CV data.
        
        Args:
            query: Search query text
            cv_id: Filter by specific CV
            user_id: Filter by specific user
            limit: Maximum number of results
            
        Returns:
            List of similar chunks with scores
        """
        # Generate embedding for query
        query_embedding = self.embedding_generator.generate_single_embedding(query)
        
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            return []
        
        # Search in Qdrant
        return self.qdrant_client.query_similar_chunks(
            query_embedding=query_embedding,
            cv_id=cv_id,
            user_id=user_id,
            limit=limit
        )
    
    def get_user_cvs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all CVs for a specific user."""
        return self.qdrant_client.get_user_cvs(user_id)
    
    def get_user_cv_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a user's CV collection."""
        return self.qdrant_client.get_user_cv_stats(user_id)
    
    def search_across_all_user_cvs(
        self,
        query: str,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks across ALL CVs for a user.
        
        Args:
            query: Search query text
            user_id: User identifier
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
        return self.qdrant_client.query_across_all_user_cvs(
            query_embedding=query_embedding,
            user_id=user_id,
            limit=limit
        )
