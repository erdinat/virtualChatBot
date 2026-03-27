"""
Test modülü – DRL / RuleBasedPolicy testleri.

RuleBasedPolicy: öğrenci mastery skorlarına bakarak
"review" veya "advance" önerisi üreten deterministik politika.
"""

import pytest
from config.settings import CURRICULUM
from modules.drl.policy import RuleBasedPolicy


# Tüm konular için sabit mastery sözlüğü oluşturan yardımcı
def _mastery(score: float) -> dict:
    return {topic["name"]: score for topic in CURRICULUM}


class TestSelectNextTopic:
    def test_low_mastery_returns_review(self):
        """Tüm konular düşükse en kolay konuyu tekrar et."""
        policy = RuleBasedPolicy()
        result = policy.select_next_topic(_mastery(0.3))
        assert result["action"] == "review"

    def test_review_starts_from_easiest_topic(self):
        """Birden fazla zayıf konu varsa en düşük zorluklu konu seçilir."""
        policy = RuleBasedPolicy()
        result = policy.select_next_topic(_mastery(0.3))
        assert result["topic"]["difficulty"] == 1  # CURRICULUM'daki ilk konu

    def test_high_mastery_returns_advance(self):
        """Tüm konular yeterliyse ileri geç."""
        policy = RuleBasedPolicy()
        result = policy.select_next_topic(_mastery(0.9))
        assert result["action"] == "advance"

    def test_boundary_07_is_sufficient(self):
        """0.7 eşik değeri yeterli sayılır → advance."""
        policy = RuleBasedPolicy()
        result = policy.select_next_topic(_mastery(0.7))
        assert result["action"] == "advance"

    def test_boundary_069_triggers_review(self):
        """0.69 eşik değerinin altındadır → review."""
        policy = RuleBasedPolicy()
        result = policy.select_next_topic(_mastery(0.69))
        assert result["action"] == "review"

    def test_mixed_mastery_targets_weakest(self):
        """Karışık mastery: en zayıf konu önerilir."""
        policy = RuleBasedPolicy()
        mastery = {topic["name"]: 0.9 for topic in CURRICULUM}
        # Sadece "Döngüler (for/while)" zayıf (id=4, difficulty=2)
        mastery["Döngüler (for/while)"] = 0.2
        result = policy.select_next_topic(mastery)
        assert result["action"] == "review"
        assert result["topic"]["name"] == "Döngüler (for/while)"

    def test_result_has_required_keys(self):
        """Dönen dict her zaman action, topic, reason anahtarlarını içerir."""
        policy = RuleBasedPolicy()
        result = policy.select_next_topic(_mastery(0.5))
        assert "action" in result
        assert "topic" in result
        assert "reason" in result

    def test_reason_is_nonempty_string(self):
        """reason alanı boş string değil."""
        policy = RuleBasedPolicy()
        result = policy.select_next_topic(_mastery(0.5))
        assert isinstance(result["reason"], str)
        assert len(result["reason"]) > 0

    def test_custom_threshold(self):
        """Özelleştirilmiş eşik değeri çalışır."""
        policy = RuleBasedPolicy(mastery_threshold=0.5)
        result = policy.select_next_topic(_mastery(0.5))
        assert result["action"] == "advance"  # 0.5 >= 0.5 → yeterli

        result2 = policy.select_next_topic(_mastery(0.49))
        assert result2["action"] == "review"


class TestShouldTest:
    def test_mid_range_triggers_test(self):
        """0.4–0.7 arası mastery → ara sınav yap."""
        policy = RuleBasedPolicy()
        mastery = _mastery(0.55)
        assert policy.should_test(mastery, CURRICULUM[0]["name"]) is True

    def test_low_mastery_no_test(self):
        """Çok düşük mastery → önce anlat, test etme."""
        policy = RuleBasedPolicy()
        mastery = _mastery(0.2)
        assert policy.should_test(mastery, CURRICULUM[0]["name"]) is False

    def test_high_mastery_no_test(self):
        """Yüksek mastery → test gerekmiyor."""
        policy = RuleBasedPolicy()
        mastery = _mastery(0.9)
        assert policy.should_test(mastery, CURRICULUM[0]["name"]) is False


class TestGetDifficultyLevel:
    def test_low_avg_is_beginner(self):
        policy = RuleBasedPolicy()
        assert policy.get_difficulty_level(_mastery(0.2)) == "başlangıç"

    def test_mid_avg_is_intermediate(self):
        policy = RuleBasedPolicy()
        assert policy.get_difficulty_level(_mastery(0.45)) == "orta"

    def test_high_avg_is_advanced(self):
        policy = RuleBasedPolicy()
        assert policy.get_difficulty_level(_mastery(0.8)) == "ileri"
