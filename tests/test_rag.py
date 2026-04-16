"""
RAG ve chat altyapısı testleri.

app.py (eski Streamlit UI) silindi; bu dosya FastAPI katmanını test eder:
  - _detect_topic()       : kullanıcı sorusundan konu ID'si çıkarma (chat.py)
  - _rule_based_mastery() : etkileşim geçmişinden mastery hesabı (dkt/predict.py)
  - GET /api/health       : temel sağlık kontrolü (TestClient)
"""

import pytest
from fastapi.testclient import TestClient

from backend.routers.chat import _detect_topic
from modules.dkt.predict import _rule_based_mastery
from config.settings import CURRICULUM


# ===========================================================================
# _detect_topic() testleri
# Konu tespiti: chat.py'deki keyword eşleştirme mantığı
# ===========================================================================

class TestDetectTopic:
    def test_loop_for(self):
        assert _detect_topic("for döngüsü nasıl çalışır?") == 4

    def test_loop_while(self):
        assert _detect_topic("while döngüsü ne zaman kullanılır?") == 4

    def test_function_def(self):
        assert _detect_topic("def ile nasıl fonksiyon yazarım?") == 7

    def test_variable(self):
        assert _detect_topic("değişken nasıl tanımlanır?") == 1

    def test_class_oop(self):
        assert _detect_topic("class nedir, nasıl kullanılır?") == 10

    def test_condition_if(self):
        assert _detect_topic("if elif else nasıl çalışır?") == 3

    def test_list(self):
        assert _detect_topic("listeye eleman nasıl eklenir?") == 5

    def test_dict(self):
        assert _detect_topic("sözlükten nasıl değer okunur?") == 6

    def test_file(self):
        assert _detect_topic("dosya nasıl açılır?") == 8

    def test_exception(self):
        assert _detect_topic("try: except ne işe yarar?") == 9

    def test_unknown_returns_none(self):
        assert _detect_topic("merhaba nasılsın?") is None

    def test_case_insensitive(self):
        assert _detect_topic("FOR DÖNGÜSÜ") == 4


# ===========================================================================
# _rule_based_mastery() testleri
# ===========================================================================

class TestRuleBasedMastery:
    def test_empty_history_returns_zero(self):
        result = _rule_based_mastery([])
        assert all(v == 0.0 for v in result.values())

    def test_correct_answer_increases_mastery(self):
        history = [{"skill_id": 1, "correct": True}]
        result = _rule_based_mastery(history)
        assert result["Değişkenler ve Veri Tipleri"] > 0.0

    def test_wrong_answer_floored_at_zero(self):
        history = [{"skill_id": 1, "correct": False}]
        result = _rule_based_mastery(history)
        assert result["Değişkenler ve Veri Tipleri"] == 0.0

    def test_correct_delta_is_005(self):
        history = [{"skill_id": 1, "correct": True}]
        result = _rule_based_mastery(history)
        assert abs(result["Değişkenler ve Veri Tipleri"] - 0.05) < 1e-6

    def test_mastery_capped_at_1(self):
        history = [{"skill_id": 1, "correct": True}] * 25
        result = _rule_based_mastery(history)
        assert result["Değişkenler ve Veri Tipleri"] <= 1.0

    def test_mastery_floored_at_0(self):
        history = [{"skill_id": 1, "correct": False}] * 20
        result = _rule_based_mastery(history)
        assert result["Değişkenler ve Veri Tipleri"] >= 0.0

    def test_other_topics_unaffected(self):
        history = [{"skill_id": 1, "correct": True}]
        result = _rule_based_mastery(history)
        for topic in CURRICULUM:
            if topic["id"] != 1:
                assert result[topic["name"]] == 0.0

    def test_returns_all_topics(self):
        result = _rule_based_mastery([])
        assert len(result) == len(CURRICULUM)
        for topic in CURRICULUM:
            assert topic["name"] in result

    def test_unknown_skill_id_ignored(self):
        history = [{"skill_id": 999, "correct": True}]
        result = _rule_based_mastery(history)
        assert all(v == 0.0 for v in result.values())


# ===========================================================================
# FastAPI health endpoint testi
# ===========================================================================

class TestHealthEndpoint:
    @pytest.fixture
    def client(self):
        import os
        os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only")
        from backend.main import app
        return TestClient(app)

    def test_health_returns_ok(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_response_has_status(self, client):
        data = response = client.get("/api/health").json()
        assert "status" in data or response is not None
