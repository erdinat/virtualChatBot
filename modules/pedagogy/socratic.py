"""
Sokratik Pedagoji Modülü

Öğrenciye doğrudan cevap vermek yerine düşündürücü ipuçları ve
yönlendirici sorularla aktif öğrenmeyi destekler.

Referans: Brown ve diğ. (2024), Kazemitabaar ve diğ. (2023)
"""

from typing import Optional


# ===== Soru Tipleri =====
QUESTION_TYPES = {
    "concept": "Kavramsal soru (ör: 'List ile Tuple farkı nedir?')",
    "bug": "Hata/Debug sorusu (ör: 'Kodum çalışmıyor, yardım edin')",
    "howto": "Nasıl yapılır sorusu (ör: 'Sıralama nasıl yapılır?')",
    "exercise": "Alıştırma çözümü (ör: 'Bu ödevin cevabı ne?')",
}


# ===== İpucu Kademeleri =====
HINT_LEVELS = {
    1: {
        "name": "Genel İpucu",
        "description": "Düşünmeye yönlendiren genel bir soru",
        "prompt_suffix": """
Öğrenciye sadece düşündürücü bir soru sor. Cevabı veya kodu VERME.
Örnek: "Bu problemi çözmek için hangi veri tipini kullanırdın?"
""",
    },
    2: {
        "name": "Spesifik Yönlendirme",
        "description": "Daha spesifik bir ipucu ve yaklaşım önerisi",
        "prompt_suffix": """
Öğrenciye hangi Python yapısını/fonksiyonunu kullanması gerektiğini söyle,
ama tam kodu VERME. Yaklaşımı adım adım açıkla.
Örnek: "Burada bir for döngüsü ve enumerate() işine yarayabilir. İlk adım olarak..."
""",
    },
    3: {
        "name": "Kısmi Çözüm",
        "description": "İskelet kod, boşlukları öğrenci doldursun",
        "prompt_suffix": """
Öğrenciye kısmi bir kod çözümü ver. Kritik kısımları '# BURAYA KOD YAZIN' 
şeklinde boş bırak. Öğrencinin tamamlaması gereken yerleri açıkla.
""",
    },
    4: {
        "name": "Tam Çözüm",
        "description": "Son çare – tam açıklamalı çözüm",
        "prompt_suffix": """
Öğrenci birçok kez denedi. Artık tam çözümü gösterebilirsin, 
ama HER SATIRI açıklayarak öğretici bir şekilde sun.
""",
    },
}


class SocraticManager:
    """
    Sokratik yönlendirme akışını yöneten sınıf.

    Öğrencinin aynı konudaki deneme sayısını takip eder 
    ve ipucu seviyesini kademeli olarak artırır.
    """

    def __init__(self):
        # {conversation_key: attempt_count} – deneme sayıları
        self.attempt_tracker: dict[str, int] = {}

    def get_hint_level(self, conversation_key: str) -> int:
        """Mevcut deneme sayısına göre ipucu seviyesini döndürür."""
        attempts = self.attempt_tracker.get(conversation_key, 0)

        if attempts == 0:
            return 1  # İlk soru – genel ipucu
        elif attempts == 1:
            return 2  # İkinci deneme – spesifik yönlendirme
        elif attempts == 2:
            return 3  # Üçüncü deneme – kısmi çözüm
        else:
            return 4  # 4+ deneme – tam çözüm

    def record_attempt(self, conversation_key: str):
        """Bir deneme kaydeder."""
        self.attempt_tracker[conversation_key] = (
            self.attempt_tracker.get(conversation_key, 0) + 1
        )

    def reset_attempts(self, conversation_key: str):
        """Deneme sayısını sıfırlar (yeni konuya geçildiğinde)."""
        self.attempt_tracker.pop(conversation_key, None)

    def get_socratic_prompt_suffix(
        self, conversation_key: str, topic_level: str = "beginner"
    ) -> str:
        """
        Mevcut ipucu seviyesine göre prompt suffix'ini döndürür.
        topic_level parametresi hint başlangıç seviyesini kalibre eder:
          beginner     → standart sıra (1 → 2 → 3 → 4)
          intermediate → en az seviye 2'den başla
          advanced     → en az seviye 3'ten başla
        """
        raw_level = self.get_hint_level(conversation_key)
        self.record_attempt(conversation_key)

        if topic_level == "intermediate":
            effective_level = max(raw_level, 2)
        elif topic_level == "advanced":
            effective_level = max(raw_level, 3)
        else:
            effective_level = raw_level

        return HINT_LEVELS[effective_level]["prompt_suffix"]

    def get_current_level_info(self, conversation_key: str) -> dict:
        """Mevcut seviye bilgisini döndürür (UI için)."""
        level = self.get_hint_level(conversation_key)
        return {
            "level": level,
            "name": HINT_LEVELS[level]["name"],
            "description": HINT_LEVELS[level]["description"],
            "attempts": self.attempt_tracker.get(conversation_key, 0),
        }


# Modül düzeyinde tekil instance
socratic_manager = SocraticManager()
