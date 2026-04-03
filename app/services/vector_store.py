from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

import chromadb
from chromadb import Collection
from fastapi import HTTPException
from google import genai

from app.config import settings

logger = logging.getLogger(__name__)

_client: chromadb.PersistentClient | None = None
_genai_client: genai.Client | None = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        try:
            _client = chromadb.PersistentClient(path=settings.chroma_db_dir)
        except Exception as exc:
            logger.exception("Could not initialize ChromaDB client")
            raise HTTPException(status_code=500, detail="Vector DB initialization failed") from exc
    return _client


def _get_collection() -> Collection:
    client = _get_client()
    try:
        return client.get_or_create_collection(name=settings.chroma_collection_name)
    except Exception as exc:
        logger.exception("Could not access Chroma collection")
        raise HTTPException(status_code=500, detail="Vector DB collection access failed") from exc


def _get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        try:
            _genai_client = genai.Client(api_key=settings.google_api_key)
        except Exception as exc:
            logger.exception("Could not initialize Google GenAI client")
            raise HTTPException(status_code=500, detail="LLM client initialization failed") from exc
    return _genai_client


async def _embed_documents(texts: list[str]) -> list[list[float]]:
    try:
        client = _get_genai_client()
        vectors: list[list[float]] = []
        for text in texts:
            response = await client.aio.models.embed_content(model=settings.embedding_model, contents=text)
            vectors.append(list(response.embeddings[0].values))
        return vectors
    except Exception as exc:
        logger.exception("Embedding API request failed")
        raise HTTPException(status_code=502, detail="Embedding API call failed. Check GOOGLE_API_KEY") from exc


async def _embed_query(text: str) -> list[float]:
    try:
        client = _get_genai_client()
        response = await client.aio.models.embed_content(model=settings.embedding_model, contents=text)
        return list(response.embeddings[0].values)
    except Exception as exc:
        logger.exception("Embedding query API request failed")
        raise HTTPException(status_code=502, detail="Embedding API call failed. Check GOOGLE_API_KEY") from exc


async def add_chunks(chunks: list[str], filename: str) -> str:
    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks generated from document")

    document_id = uuid.uuid4().hex
    ids = [f"{document_id}:{i}" for i in range(len(chunks))]
    metadatas: list[dict[str, Any]] = [
        {"document_id": document_id, "filename": filename, "chunk_index": i} for i in range(len(chunks))
    ]

    vectors = await _embed_documents(chunks)

    collection = _get_collection()
    try:
        await asyncio.to_thread(collection.add, ids=ids, embeddings=vectors, documents=chunks, metadatas=metadatas)
    except Exception as exc:
        logger.exception("Could not write chunks to ChromaDB")
        raise HTTPException(status_code=500, detail="Failed to store chunks in vector DB") from exc

    return document_id


async def query_chunks(query: str, top_k: int = 3, document_id: str | None = None) -> list[str]:
    vector = await _embed_query(query)
    collection = _get_collection()

    try:
        query_kwargs: dict[str, Any] = {
            "query_embeddings": [vector],
            "n_results": top_k,
        }
        if document_id:
            query_kwargs["where"] = {"document_id": document_id}

        result = await asyncio.to_thread(collection.query, **query_kwargs)
    except Exception as exc:
        logger.exception("Chroma query failed")
        raise HTTPException(status_code=500, detail="Vector DB query failed") from exc

    docs = result.get("documents", [])
    if not docs or not docs[0]:
        raise HTTPException(status_code=404, detail="No relevant chunks found")

    return [str(chunk) for chunk in docs[0]]
