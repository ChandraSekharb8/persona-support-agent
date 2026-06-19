from pathlib import Path
from typing import List, Dict

import chromadb
from google import genai
from google.genai import types
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from src.config import (
    DATA_DIR,
    CHROMA_DB_DIR,
    GEMINI_API_KEY,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K
)


class LocalRAGPipeline:
    """
    Loads support documents, chunks them, embeds them,
    stores them in ChromaDB, and retrieves relevant chunks.
    """

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")

        self.client = genai.Client(api_key=GEMINI_API_KEY)

        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

        self.collection = self.chroma_client.get_or_create_collection(
            name="support_kb",
            metadata={"hnsw:space": "cosine"}
        )

    def get_embedding(self, text: str, task_type: str) -> List[float]:
        """
        Generates Gemini embedding for text.
        task_type should be RETRIEVAL_DOCUMENT or RETRIEVAL_QUERY.
        """
        response = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type
            )
        )
        return response.embeddings[0].values
    

    def _read_txt_or_md(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8", errors="ignore")

    def _read_pdf(self, file_path: Path) -> str:
        reader = PdfReader(str(file_path))
        pdf_text = ""

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            pdf_text += f"\n\n[Page {page_number}]\n{page_text}"

        return pdf_text

    def load_documents(self) -> List[Dict]:
        """
        Loads .txt, .md, and .pdf files from data folder.
        """
        documents = []

        supported_extensions = [".txt", ".md", ".pdf"]

        for file_path in DATA_DIR.iterdir():
            if file_path.suffix.lower() not in supported_extensions:
                continue

            if file_path.suffix.lower() == ".pdf":
                content = self._read_pdf(file_path)
            else:
                content = self._read_txt_or_md(file_path)

            if content.strip():
                documents.append({
                    "source": file_path.name,
                    "content": content
                })

        return documents

    def build_vector_database(self, force_rebuild: bool = False) -> int:
        """
        Builds ChromaDB vector index from knowledge base documents.
        If already built, it will not rebuild unless force_rebuild=True.
        """

        existing_count = self.collection.count()

        if existing_count > 0 and not force_rebuild:
            return existing_count

        if force_rebuild:
            try:
                self.chroma_client.delete_collection("support_kb")
            except Exception:
                pass

            self.collection = self.chroma_client.get_or_create_collection(
                name="support_kb",
                metadata={"hnsw:space": "cosine"}
            )

        documents = self.load_documents()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        total_chunks = 0

        for document in documents:
            source = document["source"]
            content = document["content"]

            chunks = splitter.split_text(content)

            for index, chunk in enumerate(chunks):
                chunk_id = f"{source}_chunk_{index}"

                embedding = self.get_embedding(chunk, task_type="RETRIEVAL_DOCUMENT")

                self.collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "source": source,
                        "chunk_index": index
                    }]
                )

                total_chunks += 1

        return total_chunks

    def retrieve_context(self, query: str, top_k: int = TOP_K) -> List[Dict]:
        """
        Retrieves top-k relevant chunks from ChromaDB.
        """

        query_embedding = self.get_embedding(query, task_type="RETRIEVAL_QUERY")

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        retrieved_items = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_text in enumerate(documents):
            distance = distances[i] if i < len(distances) else 1.0
            score = max(0.0, min(1.0, 1.0 - distance))

            metadata = metadatas[i] if i < len(metadatas) else {}

            retrieved_items.append({
                "text": doc_text,
                "source": metadata.get("source", "Unknown"),
                "chunk_index": metadata.get("chunk_index", i),
                "score": score
            })

        return retrieved_items


if __name__ == "__main__":
    rag = LocalRAGPipeline()
    count = rag.build_vector_database(force_rebuild=True)
    print("Vector database built. Total chunks:", count)

    query = "My API token is giving 401 unauthorized error."
    results = rag.retrieve_context(query)

    for item in results:
        print(item["source"], item["score"])
        print(item["text"][:200])
        print("-" * 50)