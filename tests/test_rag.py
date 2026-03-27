"""
Test modülü – app.py yardımcı fonksiyon testleri.

Bu testler Streamlit gerektirmeyen saf Python fonksiyonlarını kapsar:
  - detect_topic()         : kullanıcı sorusundan konu ID'si çıkarma
  - is_curriculum_query()  : müfredat navigasyon sorusu mu?
  - _rule_based_mastery()  : etkileşim geçmişinden mastery hesabı
"""

import sys
import types
import pytest

# ---------------------------------------------------------------------------
# app.py'yi import etmeden önce streamlit'i mockla.
# Streamlit browser bağlantısı açmaya çalıştığından test ortamında patlıyor.
# ---------------------------------------------------------------------------
_st_mock = types.ModuleType("streamlit")

class _SessionState(dict):
    """st.session_state mock: attribute ve dict erişimini destekler."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)
    def __setattr__(self, name, value):
        self[name] = value

_st_mock.session_state = _SessionState()

# Sık kullanılan st fonksiyonları — testlerde çağrılmayacak ama import sırasında gerekiyor
for _fn in (
    "set_page_config", "title", "caption", "header", "subheader",
    "markdown", "progress", "info", "success", "warning", "error",
    "divider", "sidebar", "columns", "chat_message", "chat_input",
    "button", "file_uploader", "spinner", "rerun", "write",
):
    setattr(_st_mock, _fn, lambda *a, **kw: None)

# st.sidebar da mock olmalı (with st.sidebar: bloğu için __enter__/__exit__ gerek)
class _SidebarMock:
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def __getattr__(self, name): return lambda *a, **kw: None

_st_mock.sidebar = _SidebarMock()

# st.columns mock — (col1, col2, col3) şeklinde unpack ediliyor
_st_mock.columns = lambda *a, **kw: [_SidebarMock(), _SidebarMock(), _SidebarMock()]

sys.modules["streamlit"] = _st_mock

# Şimdi app.py güvenle import edilebilir
from app import (
    detect_topic,
    is_curriculum_query,
    get_level_context,
)
from modules.dkt.predict import _rule_based_mastery
from config.settings import CURRICULUM


# ===========================================================================
# detect_topic() testleri
# ===========================================================================

class TestDetectTopic:
    def test_loop_keywords(self):
        """'for döngüsü' → konu 4 (Döngüler)"""
        assert detect_topic("for döngüsü nasıl çalışır?") == 4

    def test_while_keyword(self):
        assert detect_topic("while döngüsü ne zaman kullanılır?") == 4

    def test_function_keyword(self):
        """'def ' → konu 7 (Fonksiyonlar)"""
        assert detect_topic("def ile nasıl fonksiyon yazarım?") == 7

    def test_variable_keyword(self):
        """'değişken' → konu 1"""
        assert detect_topic("değişken nasıl tanımlanır?") == 1

    def test_class_keyword(self):
        """'class ' → konu 10 (OOP)"""
        assert detect_topic("class nedir, nasıl kullanılır?") == 10

    def test_condition_keyword(self):
        """'if' → konu 3 (Koşul İfadeleri)"""
        assert detect_topic("if elif else nasıl çalışır?") == 3

    def test_list_keyword(self):
        """'liste' → konu 5"""
        assert detect_topic("listeye eleman nasıl eklenir?") == 5

    def test_dict_keyword(self):
        """'sözlük' → konu 6"""
        assert detect_topic("sözlükten nasıl değer okunur?") == 6

    def test_file_keyword(self):
        """'dosya' → konu 8"""
        assert detect_topic("dosya nasıl açılır?") == 8

    def test_exception_keyword(self):
        """'try:' → konu 9"""
        assert detect_topic("try: except ne işe yarar?") == 9

    def test_unknown_returns_none(self):
        """Tanımsız konu → None"""
        assert detect_topic("merhaba nasılsın?") is None

    def test_case_insensitive(self):
        """Büyük/küçük harf fark etmez."""
        assert detect_topic("FOR DÖNGÜSÜ") == 4


# ===========================================================================
# is_curriculum_query() testleri
# ===========================================================================

class TestIsCurriculumQuery:
    def test_diger_konu(self):
        assert is_curriculum_query("diğer konu nedir?") is True

    def test_siradaki_konu(self):
        assert is_curriculum_query("sıradaki konuya geçelim") is True

    def test_konu_listesi(self):
        assert is_curriculum_query("konu listesini göster") is True

    def test_mufredat(self):
        assert is_curriculum_query("müfredat nedir?") is True

    def test_normal_question_is_false(self):
        assert is_curriculum_query("for döngüsü nasıl çalışır?") is False

    def test_hello_world_is_false(self):
        assert is_curriculum_query("Merhaba dünya nasıl yazılır?") is False

    def test_ne_ogrenecegim(self):
        assert is_curriculum_query("neleri öğreneceğim?") is True

    def test_case_insensitive(self):
        assert is_curriculum_query("MÜFREDAT NEDİR") is True


# ===========================================================================
# _rule_based_mastery() testleri
# ===========================================================================

class TestRuleBasedMastery:
    def test_empty_history_returns_zero(self):
        """Boş geçmiş → tüm konular 0.0 başlangıç değerinde."""
        result = _rule_based_mastery([])
        assert all(v == 0.0 for v in result.values())

    def test_correct_answer_increases_mastery(self):
        """Doğru cevap → mastery artar (0.0'dan yukarı)."""
        history = [{"skill_id": 1, "correct": True}]
        result = _rule_based_mastery(history)
        assert result["Değişkenler ve Veri Tipleri"] > 0.0

    def test_wrong_answer_decreases_mastery(self):
        """Yanlış cevap → mastery 0.0'da kalır (alt sınır)."""
        history = [{"skill_id": 1, "correct": False}]
        result = _rule_based_mastery(history)
        assert result["Değişkenler ve Veri Tipleri"] == 0.0

    def test_correct_delta_is_005(self):
        """Doğru cevap +0.05 ekler (başlangıç 0.0)."""
        history = [{"skill_id": 1, "correct": True}]
        result = _rule_based_mastery(history)
        assert abs(result["Değişkenler ve Veri Tipleri"] - 0.05) < 1e-6

    def test_wrong_delta_is_004(self):
        """Yanlış cevap -0.04 çıkarır, ama 0.0 alt sınır."""
        history = [{"skill_id": 1, "correct": False}]
        result = _rule_based_mastery(history)
        assert abs(result["Değişkenler ve Veri Tipleri"] - 0.0) < 1e-6

    def test_mastery_capped_at_1(self):
        """Üst sınır 1.0'ı geçemez."""
        history = [{"skill_id": 1, "correct": True}] * 20
        result = _rule_based_mastery(history)
        assert result["Değişkenler ve Veri Tipleri"] <= 1.0

    def test_mastery_floored_at_0(self):
        """Alt sınır 0.0'ın altına inemez."""
        history = [{"skill_id": 1, "correct": False}] * 20
        result = _rule_based_mastery(history)
        assert result["Değişkenler ve Veri Tipleri"] >= 0.0

    def test_other_topics_unaffected(self):
        """Sadece etkilenen konu değişir, diğerleri 0.0 kalır."""
        history = [{"skill_id": 1, "correct": True}]
        result = _rule_based_mastery(history)
        for topic in CURRICULUM:
            if topic["id"] != 1:
                assert result[topic["name"]] == 0.0

    def test_returns_all_topics(self):
        """Her zaman tüm 10 konu için değer döner."""
        result = _rule_based_mastery([])
        assert len(result) == len(CURRICULUM)
        for topic in CURRICULUM:
            assert topic["name"] in result

    def test_unknown_skill_id_ignored(self):
        """Geçersiz skill_id sessizce yoksayılır."""
        history = [{"skill_id": 999, "correct": True}]
        result = _rule_based_mastery(history)
        assert all(v == 0.0 for v in result.values())


# ===========================================================================
# get_level_context() testleri
# ===========================================================================

class TestGetLevelContext:
    def test_no_history_is_beginner(self):
        result = get_level_context([], {})
        assert "Yeni başlayan" in result

    def test_low_mastery_is_beginner_acemi(self):
        mastery = {t["name"]: 0.3 for t in CURRICULUM}
        history = [{"skill_id": 1, "correct": False}]
        result = get_level_context(history, mastery)
        assert "başlangıç" in result

    def test_high_mastery_is_advanced(self):
        mastery = {t["name"]: 0.9 for t in CURRICULUM}
        history = [{"skill_id": 1, "correct": True}]
        result = get_level_context(history, mastery)
        assert "ileri" in result

    def test_oop_exclusion_in_beginner(self):
        """Acemi seviyesinde OOP kullanma uyarısı olmalı."""
        mastery = {t["name"]: 0.2 for t in CURRICULUM}
        history = [{"skill_id": 1, "correct": False}]
        result = get_level_context(history, mastery)
        assert "OOP" in result or "class" in result
