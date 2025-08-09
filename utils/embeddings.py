"""
Embeddings utility for generating text embeddings using OpenAI or Sentence Transformers.
"""

import os
from typing import List, Optional
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generate embeddings for text using OpenAI or Sentence Transformers."""
    
    def __init__(self, model_name: str = "openai"):
        """
        Initialize embedding generator.
        
        Args:
            model_name: "openai" for OpenAI embeddings, "sentence-transformers" for local model
        """
        self.model_name = model_name
        
        if model_name == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self.client = OpenAI(api_key=api_key)
            self.model = "text-embedding-3-small"
        elif model_name == "sentence-transformers":
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            raise ValueError(f"Unsupported model: {model_name}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if self.model_name == "openai":
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                return [embedding.embedding for embedding in response.data]
            else:
                # Sentence Transformers
                embeddings = self.model.encode(texts, convert_to_tensor=False)
                return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    def generate_single_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector or None if error
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else None
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        if self.model_name == "openai":
            return 1536  # OpenAI text-embedding-3-small dimension
        else:
            return 384  # all-MiniLM-L6-v2 dimension
