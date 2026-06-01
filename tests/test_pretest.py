"""
Ön test (pre-test) sistem testleri.

Kapsam:
  - Quiz dosyası yapısı (10 soru/konu, 4+3+3 zorluk dağılımı)
  - get_pretest_questions sıralaması (kolay → zor)
  - GET /api/diagnostic/pretest/{topic_id} endpoint
  - POST /api/diagnostic/topic-level tier-based skorlama
"""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production-use")

from backend.auth import create_access_token
from backend.main import app
from config.quiz_questions import (
    QUIZ_QUESTIONS,
    get_pretest_questions,
    get_questions_for_topic,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def student_token():
    return create_access_token({"sub": "ali", "name": "Ali", "role": "student"})


# ── Quiz dosyası yapısı ────────────────────────────────────────────────────

class TestQuizStructure:
    @pytest.mark.parametrize("topic_id", list(range(1, 11)))
    def test_each_topic_has_10_questions(self, topic_id):
        assert len(QUIZ_QUESTIONS[topic_id]) == 10

    @pytest.mark.parametrize("topic_id", list(range(1, 11)))
    def test_each_topic_difficulty_distribution(self, topic_id):
        """4 beginner + 3 intermediate + 3 advanced bekleniyor."""
        diffs = [q["difficulty"] for q in QUIZ_QUESTIONS[topic_id]]
        assert diffs.count("beginner") == 4
        assert diffs.count("intermediate") == 3
        assert diffs.count("advanced") == 3

    @pytest.mark.parametrize("topic_id", list(range(1, 11)))
    def test_all_questions_have_required_fields(self, topic_id):
        for q in QUIZ_QUESTIONS[topic_id]:
            assert "text" in q and q["text"]
            assert "options" in q and len(q["options"]) == 4
            assert q["answer"] in ("A", "B", "C", "D")
            assert q["difficulty"] in ("beginner", "intermediate", "advanced")


# ── get_pretest_questions sıralaması ───────────────────────────────────────

class TestPretestOrder:
    @pytest.mark.parametrize("topic_id", list(range(1, 11)))
    def test_pretest_returns_10_questions(self, topic_id):
        assert len(get_pretest_questions(topic_id)) == 10

    @pytest.mark.parametrize("topic_id", list(range(1, 11)))
    def test_pretest_sorted_easy_to_hard(self, topic_id):
        diffs = [q["difficulty"] for q in get_pretest_questions(topic_id)]
        # İlk 4 beginner, sonraki 3 intermediate, son 3 advanced olmalı
        assert diffs == ["beginner"] * 4 + ["intermediate"] * 3 + ["advanced"] * 3

    def test_concept_check_still_returns_3(self):
        """get_questions_for_topic(count=3) geriye uyumlu kalmalı."""
        assert len(get_questions_for_topic(1, count=3)) == 3


# ── /api/diagnostic/pretest/{topic_id} ─────────────────────────────────────

class TestPretestEndpoint:
    def test_requires_auth(self, client):
        r = client.get("/api/diagnostic/pretest/1")
        assert r.status_code == 401

    def test_returns_10_sorted_questions(self, client, student_token):
        r = client.get(
            "/api/diagnostic/pretest/1",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert r.status_code == 200
        questions = r.json()["questions"]
        assert len(questions) == 10
        diffs = [q["difficulty"] for q in questions]
        assert diffs == ["beginner"] * 4 + ["intermediate"] * 3 + ["advanced"] * 3

    def test_answer_field_not_leaked(self, client, student_token):
        """İstemciye cevap (answer) alanı gönderilmemeli."""
        r = client.get(
            "/api/diagnostic/pretest/1",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        for q in r.json()["questions"]:
            assert "answer" not in q


# ── /api/diagnostic/topic-level tier-based scoring ─────────────────────────

class TestTierBasedScoring:
    """
    Konu 1 (Değişkenler) için cevap sırası — get_pretest_questions(1) çıktısı:
      0-3 beginner:     B, C, D, B  → indeksler 1, 2, 3, 1
      4-6 intermediate: B, B, B     → indeksler 1, 1, 1
      7-9 advanced:     B, A, B     → indeksler 1, 0, 1
    """

    def _post(self, client, token, answers):
        return client.post(
            "/api/diagnostic/topic-level",
            json={"topic_id": 1, "answers": answers},
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_no_answers_returns_beginner(self, client, student_token):
        r = self._post(client, student_token, {})
        body = r.json()
        assert body["level"] == "beginner"
        assert body["score"] == 0
        assert body["total"] == 10

    def test_only_beginner_correct_stays_beginner(self, client, student_token):
        """4/4 beginner doğru ama intermediate sıfır → beginner kalır."""
        answers = {"0": 1, "1": 2, "2": 3, "3": 1}
        r = self._post(client, student_token, answers)
        body = r.json()
        assert body["level"] == "beginner"
        assert body["tier_breakdown"]["beginner"] == {"correct": 4, "total": 4}
        assert body["tier_breakdown"]["intermediate"] == {"correct": 0, "total": 3}

    def test_beginner_plus_intermediate_yields_intermediate(self, client, student_token):
        answers = {"0": 1, "1": 2, "2": 3, "3": 1,    # beginner 4/4
                   "4": 1, "5": 1, "6": 1}             # intermediate 3/3
        r = self._post(client, student_token, answers)
        body = r.json()
        assert body["level"] == "intermediate"
        assert body["tier_breakdown"]["advanced"]["correct"] == 0

    def test_all_correct_yields_advanced(self, client, student_token):
        answers = {"0": 1, "1": 2, "2": 3, "3": 1,
                   "4": 1, "5": 1, "6": 1,
                   "7": 1, "8": 0, "9": 1}
        r = self._post(client, student_token, answers)
        body = r.json()
        assert body["level"] == "advanced"
        assert body["score"] == 10

    def test_partial_intermediate_blocks_promotion(self, client, student_token):
        """Intermediate'ta 1/3 doğru = %33 → eşik altı → beginner kalır."""
        answers = {"0": 1, "1": 2, "2": 3, "3": 1,    # beginner 4/4
                   "4": 1}                              # intermediate sadece 1/3
        r = self._post(client, student_token, answers)
        assert r.json()["level"] == "beginner"

    def test_intermediate_at_threshold_promotes(self, client, student_token):
        """Intermediate'ta 2/3 doğru = %66 → eşik üstü → intermediate."""
        answers = {"0": 1, "1": 2, "2": 3, "3": 1,
                   "4": 1, "5": 1}                    # intermediate 2/3
        r = self._post(client, student_token, answers)
        assert r.json()["level"] == "intermediate"

    def test_skip_beginner_cannot_be_advanced(self, client, student_token):
        """Sadece advanced soruları doğru bilmek advanced yapmaz."""
        answers = {"7": 1, "8": 0, "9": 1}
        r = self._post(client, student_token, answers)
        # Beginner eşiği geçilmediğinden zincir kırılır
        assert r.json()["level"] == "beginner"

    def test_out_of_range_indices_ignored(self, client, student_token):
        """Aralık dışı sayısal seçimler (99, -1) sessizce yanlış sayılır."""
        answers = {"0": 99, "1": -1, "2": 5}
        r = self._post(client, student_token, answers)
        body = r.json()
        assert body["level"] == "beginner"
        assert body["tier_breakdown"]["beginner"]["correct"] == 0

    def test_non_numeric_answer_rejected_by_schema(self, client, student_token):
        """Pydantic schema — sayısal olmayan cevap (str) 422 ile reddedilir."""
        r = self._post(client, student_token, {"0": "abc"})
        assert r.status_code == 422
