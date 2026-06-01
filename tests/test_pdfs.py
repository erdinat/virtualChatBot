"""
PDF upload güvenlik testleri.

Kapsam:
  - Magic byte kontrolü (_is_pdf_content)
  - Geçerli/geçersiz dosya başlıkları
  - /api/pdfs/status auth zorunluluğu
"""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production-use")

from backend.auth import create_access_token
from backend.main import app
from backend.routers.pdfs import _is_pdf_content


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def teacher_token():
    return create_access_token({"sub": "ogretmen", "name": "Öğr", "role": "teacher"})


@pytest.fixture
def student_token():
    return create_access_token({"sub": "ali", "name": "Ali", "role": "student"})


# ── Magic byte kontrolü ────────────────────────────────────────────────────

class TestPdfMagicBytes:
    def test_valid_pdf_header(self):
        assert _is_pdf_content(b"%PDF-1.4\n...") is True

    def test_minimum_valid_header(self):
        assert _is_pdf_content(b"%PDF-") is True

    def test_empty_content_rejected(self):
        assert _is_pdf_content(b"") is False

    def test_too_short_content_rejected(self):
        assert _is_pdf_content(b"%PDF") is False  # 4 bayt — 5 lazım

    def test_zip_disguised_as_pdf_rejected(self):
        # PK = ZIP magic; polyglot saldırı senaryosu
        assert _is_pdf_content(b"PK\x03\x04...") is False

    def test_html_disguised_as_pdf_rejected(self):
        assert _is_pdf_content(b"<html><body>fake</body></html>") is False

    def test_exe_disguised_as_pdf_rejected(self):
        # MZ = DOS/PE executable magic
        assert _is_pdf_content(b"MZ\x90\x00\x03") is False

    def test_pdf_with_bom_rejected(self):
        # UTF-8 BOM önekli "%PDF" geçerli PDF değil
        assert _is_pdf_content(b"\xef\xbb\xbf%PDF-1.4") is False


# ── /api/pdfs/status auth ──────────────────────────────────────────────────

class TestPdfStatusAuth:
    def test_status_requires_auth(self, client):
        r = client.get("/api/pdfs/status")
        assert r.status_code == 401

    def test_status_accepts_student_token(self, client, student_token):
        r = client.get("/api/pdfs/status", headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 200
        assert "loaded" in r.json()

    def test_status_accepts_teacher_token(self, client, teacher_token):
        r = client.get("/api/pdfs/status", headers={"Authorization": f"Bearer {teacher_token}"})
        assert r.status_code == 200


# ── /api/pdfs/upload — magic byte enforcement ──────────────────────────────

class TestPdfUploadValidation:
    def test_upload_requires_teacher(self, client, student_token):
        files = {"files": ("test.pdf", b"%PDF-1.4\nfake", "application/pdf")}
        r = client.post(
            "/api/pdfs/upload",
            files=files,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert r.status_code == 403

    def test_upload_rejects_non_pdf_extension(self, client, teacher_token):
        files = {"files": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")}
        r = client.post(
            "/api/pdfs/upload",
            files=files,
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert r.status_code == 400

    def test_upload_rejects_fake_pdf_extension(self, client, teacher_token):
        # Uzantı .pdf ama içerik PDF değil
        files = {"files": ("malware.pdf", b"PK\x03\x04evil", "application/pdf")}
        r = client.post(
            "/api/pdfs/upload",
            files=files,
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert r.status_code == 400
        assert "imza" in r.json()["detail"].lower() or "pdf" in r.json()["detail"].lower()
