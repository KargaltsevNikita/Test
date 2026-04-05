"""Knowledge base ingestion script.

Run this file to index text/markdown/docx/pdf documents from a folder into the
local Qdrant vector store.
"""

from __future__ import annotations

from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from app.config import get_settings


LOADER_MAP = {
    ".txt": TextLoader,
    ".md": TextLoader,
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
}


def load_documents(data_dir: Path):
    """Load all supported files from the knowledge base directory."""
    all_docs = []
    for suffix, loader_cls in LOADER_MAP.items():
        pattern = f"**/*{suffix}"
        loader = DirectoryLoader(
            str(data_dir),
            glob=pattern,
            loader_cls=loader_cls,
            show_progress=True,
            use_multithreading=True,
        )
        docs = loader.load()
        for doc in docs:
            doc.metadata["title"] = Path(doc.metadata.get("source", "KB document")).name
        all_docs.extend(docs)
    return all_docs


def main() -> None:
    """Chunk documents, embed them, and write vectors into local Qdrant."""
    settings = get_settings()
    data_dir = Path("./knowledge_base")
    settings.qdrant_dir.mkdir(parents=True, exist_ok=True)

    docs = load_documents(data_dir)
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(
        api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
    )
    client = QdrantClient(path=str(settings.qdrant_dir))

    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        path=str(settings.qdrant_dir),
        collection_name=settings.qdrant_collection,
        force_recreate=True,
    )
    print(f"Indexed {len(chunks)} chunks into collection '{settings.qdrant_collection}'.")


if __name__ == "__main__":
    main()
