import logging

from fastapi import FastAPI

from app.routes.document import router as document_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Micro RAG API",
    description="Lightweight Retrieval-Augmented Generation API for PDFs",
    version="1.0.0",
)

app.include_router(document_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
