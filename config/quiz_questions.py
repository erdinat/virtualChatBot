"""
Sanal Öğretmen — Quiz Soruları

Her konu için 3 çoktan seçmeli soru.
Hem Ara Değerlendirme (mid-topic test) hem Seviye Tespit Sınavı'nda kullanılır.

Her soru: {text, options: [A,B,C,D], answer: "A"|"B"|"C"|"D"}
"""

QUIZ_QUESTIONS: dict[int, list[dict]] = {
    1: [  # Değişkenler ve Veri Tipleri
        {
            "text": "x = 5 ifadesinde x değişkeninin veri tipi nedir?",
            "options": ["str", "int", "float", "bool"],
            "answer": "B",
        },
        {
            "text": "type(\"merhaba\") ifadesi ne döndürür?",
            "options": ["int", "float", "str", "bool"],
            "answer": "C",
        },
        {
            "text": "x = True ifadesinde x'in veri tipi nedir?",
            "options": ["str", "int", "float", "bool"],
            "answer": "D",
        },
    ],
    2: [  # Operatörler ve İfadeler
        {
            "text": "10 % 3 ifadesinin sonucu nedir?",
            "options": ["3", "1", "0", "10"],
            "answer": "B",
        },
        {
            "text": "2 ** 3 ifadesinin sonucu nedir?",
            "options": ["6", "8", "9", "23"],
            "answer": "B",
        },
        {
            "text": "5 // 2 ifadesinin sonucu nedir?",
            "options": ["2.5", "3", "2", "0"],
            "answer": "C",
        },
    ],
    3: [  # Koşul İfadeleri
        {
            "text": "if 5 > 3: print(\"doğru\") — çıktı nedir?",
            "options": ["doğru", "Hata", "Boş çıktı", "False"],
            "answer": "A",
        },
        {
            "text": "if 0: print(\"evet\") else: print(\"hayır\") — çıktı nedir?",
            "options": ["evet", "hayır", "Hata", "None"],
            "answer": "B",
        },
        {
            "text": "elif bloğu hangi durumda çalışır?",
            "options": [
                "Her zaman çalışır",
                "if koşulu yanlışsa ve elif koşulu doğruysa",
                "Sadece else'ten önce",
                "Hiçbir zaman",
            ],
            "answer": "B",
        },
    ],
    4: [  # Döngüler
        {
            "text": "for i in range(3): print(i) — kaç sayı yazdırılır?",
            "options": ["2", "3", "4", "0"],
            "answer": "B",
        },
        {
            "text": "while False: print(\"test\") — döngü kaç kez çalışır?",
            "options": ["1 kez", "Sonsuz kez", "0 kez", "Hata verir"],
            "answer": "C",
        },
        {
            "text": "break komutu ne yapar?",
            "options": [
                "Bir sonraki iterasyona atlar",
                "Döngüden tamamen çıkar",
                "Döngüyü yeniden başlatır",
                "Hata fırlatır",
            ],
            "answer": "B",
        },
    ],
    5: [  # Listeler ve Tuple'lar
        {
            "text": "liste = [1, 2, 3]; print(liste[0]) — çıktı nedir?",
            "options": ["2", "3", "1", "Hata"],
            "answer": "C",
        },
        {
            "text": "liste = [1,2,3]; liste.append(4); print(len(liste)) — çıktı?",
            "options": ["3", "4", "5", "Hata"],
            "answer": "B",
        },
        {
            "text": "Tuple ile listenin temel farkı nedir?",
            "options": [
                "Tuple değiştirilemez (immutable)",
                "Liste değiştirilemez",
                "İkisi tamamen aynıdır",
                "Tuple daha hızlıdır sadece",
            ],
            "answer": "A",
        },
    ],
    6: [  # Sözlükler ve Kümeler
        {
            "text": "d = {\"a\": 1, \"b\": 2}; print(d[\"a\"]) — çıktı nedir?",
            "options": ["2", "\"a\"", "1", "Hata"],
            "answer": "C",
        },
        {
            "text": "s = {1, 2, 2, 3}; print(len(s)) — çıktı nedir?",
            "options": ["4", "3", "2", "1"],
            "answer": "B",
        },
        {
            "text": "d = {\"x\": 10}; d[\"y\"] = 20; print(len(d)) — çıktı?",
            "options": ["1", "2", "3", "Hata"],
            "answer": "B",
        },
    ],
    7: [  # Fonksiyonlar
        {
            "text": "def topla(a, b): return a + b — topla(3, 4) sonucu?",
            "options": ["7", "34", "12", "Hata"],
            "answer": "A",
        },
        {
            "text": "return ifadesi olmayan bir fonksiyon ne döndürür?",
            "options": ["0", "\"\"", "None", "Hata"],
            "answer": "C",
        },
        {
            "text": "lambda x: x * 2 — bu ne tür bir fonksiyondur?",
            "options": ["Özyinelemeli", "Anonim (lambda)", "Yerleşik", "Asenkron"],
            "answer": "B",
        },
    ],
    8: [  # Dosya İşlemleri
        {
            "text": "open(\"dosya.txt\", \"r\") ne yapar?",
            "options": [
                "Dosyaya yazar",
                "Dosyayı okur",
                "Dosyayı siler",
                "Yeni dosya oluşturur",
            ],
            "answer": "B",
        },
        {
            "text": "with open(...) as f: kullanımının temel faydası nedir?",
            "options": [
                "Daha hızlı okur",
                "Dosyayı otomatik kapatır",
                "Dosyayı şifreler",
                "Hiçbir fark yoktur",
            ],
            "answer": "B",
        },
        {
            "text": "\"w\" modu ne anlama gelir?",
            "options": [
                "Read (okuma)",
                "Write — mevcut içeriği silip yazar",
                "Append — sonuna ekler",
                "Binary (ikili)",
            ],
            "answer": "B",
        },
    ],
    9: [  # Hata Yönetimi
        {
            "text": "try: 1/0 \\nexcept ZeroDivisionError: print(\"sıfır\") — çıktı?",
            "options": ["Hata (crash)", "sıfır", "0", "None"],
            "answer": "B",
        },
        {
            "text": "finally bloğu ne zaman çalışır?",
            "options": [
                "Sadece hata oluştuğunda",
                "Sadece hata oluşmadığında",
                "Her zaman (hata olsa da olmasa da)",
                "Hiçbir zaman",
            ],
            "answer": "C",
        },
        {
            "text": "raise ValueError(\"hata\") ne yapar?",
            "options": [
                "Hatayı yakalar",
                "Elle bir hata fırlatır",
                "Hatayı görmezden gelir",
                "Programı sessizce durdurur",
            ],
            "answer": "B",
        },
    ],
    10: [  # OOP
        {
            "text": "class Araba: pass — ardından Araba() ne oluşturur?",
            "options": ["Sınıf tanımı", "Modül", "Nesne (instance)", "Fonksiyon"],
            "answer": "C",
        },
        {
            "text": "Sınıf metotlarındaki self parametresi ne anlama gelir?",
            "options": [
                "Global değişken",
                "Sınıfın kendisi",
                "Nesnenin (instance) kendisi",
                "Boş parametre",
            ],
            "answer": "C",
        },
        {
            "text": "Kalıtım (inheritance) ne sağlar?",
            "options": [
                "İki sınıfı birleştirir",
                "Kod tekrarını zorlar",
                "Alt sınıf üst sınıfın özelliklerini devralır",
                "Performansı artırır",
            ],
            "answer": "C",
        },
    ],
}


def get_questions_for_topic(topic_id: int, count: int = 3) -> list[dict]:
    """Belirtilen konu için soru listesi döndürür."""
    questions = QUIZ_QUESTIONS.get(topic_id, [])
    return questions[:count]


def get_diagnostic_questions() -> list[dict]:
    """
    Seviye tespit sınavı için her konudan 1 soru döndürür (10 soru toplam).
    Her soruya topic_id eklenir.
    """
    result = []
    for topic_id in range(1, 11):
        qs = QUIZ_QUESTIONS.get(topic_id, [])
        if qs:
            q = dict(qs[0])   # ilk soruyu kopyala
            q["topic_id"] = topic_id
            result.append(q)
    return result
