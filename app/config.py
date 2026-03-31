from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")

    chroma_db_dir: str = Field(default="./chroma_db", alias="CHROMA_DB_DIR")
    chroma_collection_name: str = Field(default="documents", alias="CHROMA_COLLECTION_NAME")

    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")

    llm_model: str = Field(default="gemini-2.0-flash", alias="LLM_MODEL")
    embedding_model: str = Field(default="gemini-embedding-001", alias="EMBEDDING_MODEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
