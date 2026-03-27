from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from backend.auth import require_teacher
from backend.schemas import UploadResponse
from backend.routers.chat import _rag_chain_cache

router = APIRouter()

RAW_PDFS_PATH = Path("data/raw_pdfs")


@router.post("/upload", response_model=UploadResponse)
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    teacher: dict = Depends(require_teacher),
):
    """PDF ders notlarını yükler ve vektör veritabanını oluşturur."""
    if not any(f.filename.endswith(".pdf") for f in files):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları kabul edilir")

    RAW_PDFS_PATH.mkdir(parents=True, exist_ok=True)

    for upload in files:
        if not upload.filename.endswith(".pdf"):
            continue
        content = await upload.read()
        with open(RAW_PDFS_PATH / upload.filename, "wb") as f:
            f.write(content)

    try:
        from modules.rag import (
            load_all_pdfs, split_documents,
            get_embedding_model, create_vector_store, build_rag_chain,
        )
        documents = load_all_pdfs(RAW_PDFS_PATH)
        chunks = split_documents(documents)
        embedding_model = get_embedding_model()
        vs = create_vector_store(chunks, embedding_model)
        _rag_chain_cache["chain"] = build_rag_chain(vector_store=vs)

        return UploadResponse(
            message="PDF'ler başarıyla işlendi",
            files_processed=len(files),
            chunks_created=len(chunks),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF işleme hatası: {e}")


@router.get("/status")
def pdf_status():
    """RAG zincirinin yüklenip yüklenmediğini döner."""
    return {"loaded": _rag_chain_cache["chain"] is not None}
