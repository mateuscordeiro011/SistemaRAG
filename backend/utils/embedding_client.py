"""
Cliente de Embeddings para SistemaRAG
Suporta OpenAI, Sentence Transformers (local), e Ollama
"""

import os
import logging
import asyncio
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Configuração via variáveis de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")  # openai, sentence_transformers, ollama
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# Cliente OpenAI (lazy load)
_openai_client = None

def _get_openai_client():
    global _openai_client
    if _openai_client is None and OPENAI_API_KEY:
        try:
            from openai import OpenAI
            _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        except ImportError:
            logger.warning("OpenAI package not installed")
    return _openai_client


class EmbeddingClient:
    """Cliente unificado para geração de embeddings"""
    
    def __init__(self):
        self.provider = EMBEDDING_PROVIDER
        self._st_model = None
    
    def _get_st_model(self):
        """Lazy load Sentence Transformers model"""
        if self._st_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._st_model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
                logger.info(f"Loaded SentenceTransformer model: {SENTENCE_TRANSFORMER_MODEL}")
            except ImportError:
                logger.error("sentence-transformers not installed")
                raise
        return self._st_model
    
    async def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings para uma lista de textos
        
        Args:
            texts: Lista de strings para gerar embeddings
            
        Returns:
            Lista de embeddings (lista de listas de floats)
        """
        if not texts:
            return []
        
        if self.provider == "openai":
            return await self._encode_openai(texts)
        elif self.provider == "sentence_transformers":
            return await self._encode_sentence_transformers(texts)
        elif self.provider == "ollama":
            return await self._encode_ollama(texts)
        else:
            logger.warning(f"Unknown provider {self.provider}, falling back to sentence_transformers")
            return await self._encode_sentence_transformers(texts)
    
    async def encode_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Gera embeddings em lotes para textos grandes
        """
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self.encode(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings
    
    async def _encode_openai(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings via OpenAI API"""
        client = _get_openai_client()
        if not client:
            logger.error("OpenAI client not available, API key not set")
            # Fallback para sentence transformers
            return await self._encode_sentence_transformers(texts)
        
        try:
            # OpenAI aceita até 2048 inputs por chamada
            response = await asyncio.to_thread(
                client.embeddings.create,
                input=texts,
                model=OPENAI_EMBEDDING_MODEL
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            # Fallback
            return await self._encode_sentence_transformers(texts)
    
    async def _encode_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings localmente com Sentence Transformers"""
        try:
            model = self._get_st_model()
            embeddings = await asyncio.to_thread(model.encode, texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Sentence Transformers embedding error: {e}")
            raise
    
    async def _encode_ollama(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings via Ollama"""
        import aiohttp
        
        embeddings = []
        async with aiohttp.ClientSession() as session:
            for text in texts:
                try:
                    async with session.post(
                        f"{OLLAMA_BASE_URL}/api/embeddings",
                        json={
                            "model": OLLAMA_EMBEDDING_MODEL,
                            "prompt": text
                        }
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            embeddings.append(data.get("embedding", []))
                        else:
                            logger.error(f"Ollama error: {response.status}")
                            embeddings.append([0.0] * 768)  # fallback dimension
                except Exception as e:
                    logger.error(f"Ollama embedding error: {e}")
                    embeddings.append([0.0] * 768)
        return embeddings


# Instância global
embedding_client = EmbeddingClient()