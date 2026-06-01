from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException

from backend.auth import get_current_user, require_teacher
from backend.schemas import UploadResponse
from backend.routers.chat import _rag_chain_cache, invalidate_chains

router = APIRouter()

RAW_PDFS_PATH = Path("data/raw_pdfs")
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB

# PDF magic bytes: %PDF (her geçerli PDF böyle başlar — RFC 8118 §4)
# Sadece uzantı kontrolü polyglot dosyaları yakalayamaz; içerik imzası gerekir.
_PDF_MAGIC = b"%PDF-"


def _is_pdf_content(content: bytes) -> bool:
    """İlk 5 bayt PDF magic imzasıyla eşleşiyor mu?"""
    return len(content) >= len(_PDF_MAGIC) and content[: len(_PDF_MAGIC)] == _PDF_MAGIC


@router.post("/upload", response_model=UploadResponse)
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    topic_ids: str = Form(""),   # "1" veya "1,3" veya "" (opsiyonel)
    teacher: dict = Depends(require_teacher),
):
    """PDF ders notlarını yükler ve vektör veritabanına ekler."""
    if not any(f.filename.endswith(".pdf") for f in files):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları kabul edilir")

    # Konu etiketi parse — primary topic (ilk seçilen)
    parsed_ids = [int(x) for x in topic_ids.split(",") if x.strip().isdigit()]
    primary_topic: int | None = parsed_ids[0] if parsed_ids else None

    RAW_PDFS_PATH.mkdir(parents=True, exist_ok=True)

    saved = []
    for upload in files:
        if not upload.filename.endswith(".pdf"):
            continue
        # Path traversal koruması — sadece dosya adını al, path bileşenlerini at
        safe_name = Path(upload.filename).name
        dest = RAW_PDFS_PATH / safe_name
        content = await upload.read()
        if len(content) > MAX_PDF_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"{safe_name} dosyası 10 MB limitini aşıyor ({len(content)//1024//1024} MB)"
            )
        # Magic byte kontrolü — uzantı manipülasyonuna karşı içerik doğrulaması
        if not _is_pdf_content(content):
            raise HTTPException(
                status_code=400,
                detail=f"{safe_name} geçerli bir PDF dosyası değil (imza eşleşmiyor)"
            )
        dest.write_bytes(content)
        saved.append(dest)

    try:
        from modules.rag import (
            load_single_pdf, split_documents,
            get_embedding_model, create_vector_store, load_vector_store,
        )
        from modules.rag.pdf_loader import tag_documents_with_topic

        embedding_model = get_embedding_model()

        # Her yeni dosyayı ayrı yükle ve konu etiketle
        new_docs = []
        for path in saved:
            docs = load_single_pdf(path)
            docs = tag_documents_with_topic(docs, primary_topic)
            new_docs.extend(docs)

        chunks = split_documents(new_docs)

        # Mevcut store'a ekle (rebuild yerine append)
        vs = load_vector_store(embedding_model)
        if vs is None:
            vs = create_vector_store(chunks, embedding_model)
        else:
            vs.add_documents(chunks)

        _rag_chain_cache["vector_store"] = vs
        invalidate_chains()  # Eski zincirler stale — yeniden oluşturulsun

        return UploadResponse(
            message="PDF'ler başarıyla işlendi",
            files_processed=len(saved),
            chunks_created=len(chunks),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF işleme hatası: {e}")


@router.get("/status")
def pdf_status(_user: dict = Depends(get_current_user)):
    """RAG zincirinin yüklenip yüklenmediğini döner.
    Auth zorunlu — bilgi sızıntısını minimize eder, desen tutarlılığı sağlar.
    """
    return {"loaded": _rag_chain_cache.get("vector_store") is not None}
