from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User question")
    document_id: str | None = Field(default=None, description="Optional document scope")


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_processed: int
    message: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
