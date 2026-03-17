"""
RAG Pipeline – Embedding & Vektör Veritabanı

Ders notlarını vektörleştirir ve ChromaDB'de saklar.
Kosinüs benzerliği ile semantik arama yapılır.
"""

from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from config.settings import RAGConfig


def get_embedding_model(model_name: str = None) -> HuggingFaceEmbeddings:
    """Embedding modelini yükler."""
    model_name = model_name or RAGConfig.EMBEDDING_MODEL
    print(f"🔤 Embedding modeli yükleniyor: {model_name}")
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return embeddings


def create_vector_store(
    documents: List[Document],
    embedding_model: Optional[HuggingFaceEmbeddings] = None,
    persist_directory: Optional[str | Path] = None,
) -> Chroma:
    """
    Doküman parçalarından ChromaDB vektör veritabanı oluşturur.
    Oluşturulan veritabanı diske kaydedilir.
    """
    if embedding_model is None:
        embedding_model = get_embedding_model()

    persist_dir = str(persist_directory or RAGConfig.VECTOR_STORE_PATH)
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    print(f"🗄️  Vektör veritabanı oluşturuluyor ({len(documents)} parça)...")
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=persist_dir,
    )
    print(f"✅ Vektör veritabanı kaydedildi: {persist_dir}")
    return vector_store


def load_vector_store(
    embedding_model: Optional[HuggingFaceEmbeddings] = None,
    persist_directory: Optional[str | Path] = None,
) -> Optional[Chroma]:
    """Daha önce oluşturulmuş ChromaDB veritabanını yükler."""
    if embedding_model is None:
        embedding_model = get_embedding_model()

    persist_dir = str(persist_directory or RAGConfig.VECTOR_STORE_PATH)

    if not Path(persist_dir).exists():
        print(f"⚠️  Vektör veritabanı bulunamadı: {persist_dir}")
        return None

    vector_store = Chroma(
        persist_directory=persist_dir,
        embedding_function=embedding_model,
    )
    print(f"✅ Vektör veritabanı yüklendi: {persist_dir}")
    return vector_store
