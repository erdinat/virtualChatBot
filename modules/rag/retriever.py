"""
RAG Pipeline – Retriever (Alıcı)

Vektör veritabanından en alakalı doküman parçalarını getirir.
Top-K + Kosinüs Benzerliği tabanlı semantik arama.
"""

from typing import List, Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

from config.settings import RAGConfig


def get_retriever(vector_store: Chroma, top_k: int = None, topic_id: int | None = None):
    """
    ChromaDB üzerinden LangChain retriever nesnesi döndürür.
    Cosine similarity ile en alakalı K dokümanı getirir.
    topic_id verilirse yalnızca o konuya ait chunk'lar aranır.
    """
    k = top_k or 6  # Daha derin arama için varsayılan 4'ten 6'ya çıkarıldı

    search_kwargs: dict = {"k": k}
    if topic_id is not None:
        search_kwargs["filter"] = {"topic_id": {"$eq": topic_id}}

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )
    return retriever


def retrieve_context(
    retriever,
    query: str,
) -> List[Document]:
    """
    Verilen sorgu için en alakalı doküman parçalarını getirir.
    Hata ayıklama için kaynak bilgisini de döndürür.
    """
    results = retriever.invoke(query)
    return results


def format_context(documents: List[Document]) -> str:
    """
    Getirilen doküman parçalarını tek bir bağlam metnine dönüştürür.
    LLM'e gönderilecek formatta hazırlar.
    """
    if not documents:
        return "İlgili ders notu bulunamadı."

    context_parts = []
    for i, doc in enumerate(documents, 1):
        source = doc.metadata.get("source", "Bilinmeyen Kaynak")
        page = doc.metadata.get("page", "?")
        context_parts.append(
            f"--- Kaynak {i} (Dosya: {source}, Sayfa: {page}) ---\n{doc.page_content}"
        )

    return "\n\n".join(context_parts)
