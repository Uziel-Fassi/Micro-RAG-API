import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.document import QueryRequest, QueryResponse, UploadResponse
from app.services.chunking_service import split_text_into_chunks
from app.services.llm_service import generate_answer
from app.services.pdf_service import extract_text_from_pdf
from app.services.vector_store import add_chunks, query_chunks

router = APIRouter(prefix="/api/v1/document", tags=["document"])

PDF_MIME = "application/pdf"
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if file.content_type != PDF_MIME:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    filename = file.filename or "uploaded.pdf"

    text = await asyncio.to_thread(extract_text_from_pdf, content, filename)
    chunks = await asyncio.to_thread(split_text_into_chunks, text)

    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks could be generated from this document")

    document_id = await add_chunks(chunks=chunks, filename=filename)

    return UploadResponse(
        document_id=document_id,
        filename=filename,
        chunks_processed=len(chunks),
        message="Document uploaded and indexed successfully",
    )


@router.post("/query", response_model=QueryResponse)
async def query_document(payload: QueryRequest) -> QueryResponse:
    retrieved_chunks = await query_chunks(query=payload.query, top_k=3)

    answer = await generate_answer(question=payload.query, context_chunks=retrieved_chunks)

    sources = [chunk[:220] + ("..." if len(chunk) > 220 else "") for chunk in retrieved_chunks]

    return QueryResponse(answer=answer, sources=sources)
