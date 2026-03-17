"""
RAG Pipeline – PDF Yükleyici

Eğitmen tarafından yüklenen PDF ders notlarını okur, temizler
ve metin parçalarına (chunk) böler.
"""

from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from config.settings import RAGConfig


def load_single_pdf(pdf_path: str | Path) -> List[Document]:
    """Tek bir PDF dosyasını yükler ve sayfalarına ayırır."""
    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()
    return pages


def load_all_pdfs(directory: str | Path = None) -> List[Document]:
    """
    Belirtilen dizindeki tüm PDF dosyalarını yükler.
    Varsayılan dizin: data/raw_pdfs/
    """
    if directory is None:
        directory = RAGConfig.RAW_PDFS_PATH

    directory = Path(directory)
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        return []

    all_documents = []
    pdf_files = sorted(directory.glob("*.pdf"))

    if not pdf_files:
        print(f"⚠️  '{directory}' dizininde PDF dosyası bulunamadı.")
        return []

    for pdf_file in pdf_files:
        print(f"📄 Yükleniyor: {pdf_file.name}")
        docs = load_single_pdf(pdf_file)
        all_documents.extend(docs)

    print(f"✅ Toplam {len(all_documents)} sayfa yüklendi ({len(pdf_files)} PDF).")
    return all_documents


def split_documents(
    documents: List[Document],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Document]:
    """
    Dokümanları belirtilen boyutlarda metin parçalarına (chunk) böler.
    RecursiveCharacterTextSplitter kullanır – kod ve metin için optimize.
    """
    chunk_size = chunk_size or RAGConfig.CHUNK_SIZE
    chunk_overlap = chunk_overlap or RAGConfig.CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "```", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)
    print(f"📦 {len(documents)} sayfa → {len(chunks)} parçaya bölündü.")
    return chunks
