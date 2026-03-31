# Micro RAG API

A lightweight, production-ready RAG backend for SMEs to chat with their PDFs.

Micro RAG API lets teams upload PDF documents, index them into a local vector database, and query them through a clean REST API powered by retrieval-augmented generation.

## Why This Project

- Built for real business workflows (law firms, accountants, consultants, SMEs)
- Fast ingestion and semantic retrieval from PDFs
- Clear, modular architecture for easy maintenance and scaling
- Local ChromaDB persistence for simple deployment

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- ChromaDB (persistent local vector store)
- Google Gemini API (`google-genai`) for embeddings and generation
- LangChain text splitters (`RecursiveCharacterTextSplitter`)
- PyPDF2 for PDF extraction
- Pydantic / Pydantic Settings
- Optional frontend: Streamlit

## Project Structure

```text
mini-rag/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── document.py
│   ├── schemas/
│   │   └── document.py
│   └── services/
│       ├── pdf_service.py
│       ├── chunking_service.py
│       ├── vector_store.py
│       └── llm_service.py
├── chroma_db/            # local persistent vectors (ignored by git)
├── ui.py                 # optional Streamlit interface
├── .env.example
├── .gitignore
└── requirements.txt
```

## Local Setup

### 1. Clone repository

```bash
git clone https://github.com/<your-username>/mini-rag.git
cd mini-rag
```

### 2. Create and activate virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Update `.env` with your values:

```env
GOOGLE_API_KEY=your_real_key
CHROMA_DB_DIR=./chroma_db
CHROMA_COLLECTION_NAME=documents
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
LLM_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
```

### 5. Run API server

```bash
uvicorn app.main:app --reload
```

Swagger docs:

- http://127.0.0.1:8000/docs

Health check:

- http://127.0.0.1:8000/health

## API Usage Examples

### 1) Upload a PDF

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/document/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf;type=application/pdf"
```

Example response:

```json
{
  "document_id": "e008bc7413594f17aa9fce3c1df9b269",
  "filename": "document.pdf",
  "chunks_processed": 417,
  "message": "Document uploaded and indexed successfully"
}
```

### 2) Query indexed content

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/document/query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize the key points in 5 bullets"}'
```

Example response:

```json
{
  "answer": "...",
  "sources": [
    "chunk excerpt 1...",
    "chunk excerpt 2...",
    "chunk excerpt 3..."
  ]
}
```

## Optional Streamlit UI

```bash
streamlit run ui.py
```

## Security Notes

- Never commit `.env` to git.
- Keep API keys in environment variables only.
- `chroma_db/` can grow large; it is intentionally excluded from source control.

## Author

**Uziel Fassi**  
Computer Science Student

GitHub: https://github.com/Uziel-Fassi  

LinkedIn: https://www.linkedin.com/in/uziel-fassi-08840a287/
