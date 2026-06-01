"""
Sanal Öğretmen — Quiz Soruları

Her konu için 10 çoktan seçmeli soru, kademeli zorluk:
  - 4 beginner  (temel tanım/sentaks)
  - 3 intermediate (çıktı tahmini, edge-case)
  - 3 advanced   (ince ayrımlar, Pythonic kalıplar, performans)

Her soru: {text, options: [A,B,C,D], answer: "A"|"B"|"C"|"D", difficulty}

Kullanım yerleri:
  - get_pretest_questions(topic_id)     → ön test (10 soru, kademeli)
  - get_questions_for_topic(topic_id, count=3) → concept-check (3 beginner)
  - get_diagnostic_questions()          → 10 konunun ilk sorusu (seviye tespiti)
"""

DIFFICULTY_BEGINNER = "beginner"
DIFFICULTY_INTERMEDIATE = "intermediate"
DIFFICULTY_ADVANCED = "advanced"


QUIZ_QUESTIONS: dict[int, list[dict]] = {
    # ═══════════════════════════════════════════════════════════════════════
    # 1. Değişkenler ve Veri Tipleri
    # ═══════════════════════════════════════════════════════════════════════
    1: [
        # — Beginner —
        {
            "text": "x = 5 ifadesinde x değişkeninin veri tipi nedir?",
            "options": ["str", "int", "float", "bool"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "type(\"merhaba\") ifadesi ne döndürür?",
            "options": ["int", "float", "str", "bool"],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "x = True ifadesinde x'in veri tipi nedir?",
            "options": ["str", "int", "float", "bool"],
            "answer": "D", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "Aşağıdakilerden hangisi geçerli bir Python değişken adıdır?",
            "options": ["2sayi", "sayi_2", "for", "sayı-2"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        # — Intermediate —
        {
            "text": "x = \"5\" + str(3) — print(x) çıktısı nedir?",
            "options": ["8", "53", "Hata", "5 3"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "x = 7 / 2 ifadesinden sonra type(x) ne döner?",
            "options": ["int", "float", "str", "bool"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "a = 5; b = a; a = 10 — print(b) çıktısı nedir?",
            "options": ["10", "5", "None", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        # — Advanced —
        {
            "text": "a = [1, 2]; b = a; b.append(3) — print(a) çıktısı nedir?",
            "options": ["[1, 2]", "[1, 2, 3]", "[3]", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "a = 256; b = 256; print(a is b) çıktısı CPython'da nedir?",
            "options": ["True", "False", "None", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "x = 0.1 + 0.2 == 0.3 — print(x) çıktısı nedir?",
            "options": ["True", "False", "Hata", "None"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # 2. Operatörler ve İfadeler
    # ═══════════════════════════════════════════════════════════════════════
    2: [
        # — Beginner —
        {
            "text": "10 % 3 ifadesinin sonucu nedir?",
            "options": ["3", "1", "0", "10"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "2 ** 3 ifadesinin sonucu nedir?",
            "options": ["6", "8", "9", "23"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "5 // 2 ifadesinin sonucu nedir?",
            "options": ["2.5", "3", "2", "0"],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "True and False ifadesinin sonucu nedir?",
            "options": ["True", "False", "None", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        # — Intermediate —
        {
            "text": "x = 3 + 4 * 2 — print(x) çıktısı nedir?",
            "options": ["11", "14", "10", "24"],
            "answer": "A", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "not (5 > 2) ifadesinin sonucu nedir?",
            "options": ["True", "False", "5", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "10 == \"10\" ifadesinin sonucu nedir?",
            "options": ["True", "False", "Hata", "None"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        # — Advanced —
        {
            "text": "x = 5; y = 5; print(x is y, x == y) çıktısı nedir?",
            "options": ["True True", "False True", "True False", "False False"],
            "answer": "A", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "0 or \"hello\" or None ifadesinin sonucu nedir?",
            "options": ["0", "True", "\"hello\"", "None"],
            "answer": "C", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "x = 3 < 5 < 7 — print(x) çıktısı nedir?",
            "options": ["True", "False", "Hata", "1"],
            "answer": "A", "difficulty": DIFFICULTY_ADVANCED,
        },
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # 3. Koşul İfadeleri
    # ═══════════════════════════════════════════════════════════════════════
    3: [
        # — Beginner —
        {
            "text": "if 5 > 3: print(\"doğru\") — çıktı nedir?",
            "options": ["doğru", "Hata", "Boş çıktı", "False"],
            "answer": "A", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "if 0: print(\"evet\") else: print(\"hayır\") — çıktı nedir?",
            "options": ["evet", "hayır", "Hata", "None"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "elif bloğu hangi durumda çalışır?",
            "options": [
                "Her zaman çalışır",
                "if koşulu yanlışsa ve elif koşulu doğruysa",
                "Sadece else'ten önce",
                "Hiçbir zaman",
            ],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "Python'da koşul blokları nasıl ayrılır?",
            "options": ["Süslü parantez { }", "Girinti (indentation)", "Noktalı virgül ;", "Anahtar end"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        # — Intermediate —
        {
            "text": "x = 10\nif x > 5:\n    if x > 8:\n        print(\"A\")\n    else:\n        print(\"B\")\n— çıktı nedir?",
            "options": ["A", "B", "A B", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "if \"\": print(\"X\") else: print(\"Y\") — çıktı nedir?",
            "options": ["X", "Y", "Hata", "\"\""],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "x = 5; y = \"büyük\" if x > 3 else \"küçük\"; print(y) — çıktı?",
            "options": ["büyük", "küçük", "True", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        # — Advanced —
        {
            "text": "if None or 0 or []: print(\"A\") else: print(\"B\") — çıktı?",
            "options": ["A", "B", "Hata", "None"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "x = 5\nmatch x:\n    case 1 | 5: print(\"A\")\n    case _: print(\"B\")\n— çıktı? (Python 3.10+)",
            "options": ["A", "B", "A B", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "x = []; print(\"dolu\" if x else \"boş\") — çıktı nedir?",
            "options": ["dolu", "boş", "[]", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # 4. Döngüler
    # ═══════════════════════════════════════════════════════════════════════
    4: [
        # — Beginner —
        {
            "text": "for i in range(3): print(i) — kaç sayı yazdırılır?",
            "options": ["2", "3", "4", "0"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "while False: print(\"test\") — döngü kaç kez çalışır?",
            "options": ["1 kez", "Sonsuz kez", "0 kez", "Hata verir"],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "break komutu ne yapar?",
            "options": [
                "Bir sonraki iterasyona atlar",
                "Döngüden tamamen çıkar",
                "Döngüyü yeniden başlatır",
                "Hata fırlatır",
            ],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "range(1, 5) hangi sayıları üretir?",
            "options": ["1, 2, 3, 4", "1, 2, 3, 4, 5", "0, 1, 2, 3, 4", "2, 3, 4, 5"],
            "answer": "A", "difficulty": DIFFICULTY_BEGINNER,
        },
        # — Intermediate —
        {
            "text": "toplam = 0\nfor i in range(1, 4):\n    toplam += i\nprint(toplam) — çıktı?",
            "options": ["3", "6", "10", "4"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "for i in range(5):\n    if i == 3: continue\n    print(i, end=\" \")\n— çıktı?",
            "options": ["0 1 2 3 4", "0 1 2 4", "0 1 2", "3 4"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "range(10, 0, -2) kaç sayı üretir?",
            "options": ["4", "5", "6", "10"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        # — Advanced —
        {
            "text": "for i in range(3):\n    pass\nelse:\n    print(\"bitti\")\n— çıktı?",
            "options": ["bitti", "Boş", "Hata", "0 1 2"],
            "answer": "A", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "for i in range(3):\n    if i == 1: break\nelse:\n    print(\"tamam\")\n— çıktı?",
            "options": ["tamam", "Boş", "0", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "kareler = [x*x for x in range(4)] — print(kareler) çıktısı?",
            "options": ["[0, 1, 4, 9]", "[1, 4, 9, 16]", "[0, 2, 4, 6]", "[1, 2, 3, 4]"],
            "answer": "A", "difficulty": DIFFICULTY_ADVANCED,
        },
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # 5. Listeler ve Tuple'lar
    # ═══════════════════════════════════════════════════════════════════════
    5: [
        # — Beginner —
        {
            "text": "liste = [1, 2, 3]; print(liste[0]) — çıktı nedir?",
            "options": ["2", "3", "1", "Hata"],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "liste = [1,2,3]; liste.append(4); print(len(liste)) — çıktı?",
            "options": ["3", "4", "5", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "Tuple ile listenin temel farkı nedir?",
            "options": [
                "Tuple değiştirilemez (immutable)",
                "Liste değiştirilemez",
                "İkisi tamamen aynıdır",
                "Tuple daha hızlıdır sadece",
            ],
            "answer": "A", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "liste = [10, 20, 30]; print(liste[-1]) — çıktı nedir?",
            "options": ["10", "20", "30", "Hata"],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        # — Intermediate —
        {
            "text": "liste = [1, 2, 3, 4, 5]; print(liste[1:4]) — çıktı nedir?",
            "options": ["[1, 2, 3]", "[2, 3, 4]", "[1, 2, 3, 4]", "[2, 3, 4, 5]"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "a = [1, 2]; b = [3, 4]; print(a + b) — çıktı nedir?",
            "options": ["[1, 2, 3, 4]", "[4, 6]", "Hata", "[[1,2],[3,4]]"],
            "answer": "A", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "liste = [3, 1, 4, 1, 5]; liste.sort(); print(liste) — çıktı?",
            "options": ["[1, 1, 3, 4, 5]", "[5, 4, 3, 1, 1]", "[3, 1, 4, 1, 5]", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        # — Advanced —
        {
            "text": "matris = [[0]*3]*2; matris[0][0] = 1; print(matris) — çıktı?",
            "options": [
                "[[1, 0, 0], [0, 0, 0]]",
                "[[1, 0, 0], [1, 0, 0]]",
                "[[0, 0, 0], [0, 0, 0]]",
                "Hata",
            ],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "a = (1, 2, 3); a[0] = 5 — sonuç?",
            "options": ["a değişir", "TypeError", "SyntaxError", "Sessizce göz ardı edilir"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "liste = [1, 2, 3]; print(liste[::-1]) — çıktı nedir?",
            "options": ["[1, 2, 3]", "[3, 2, 1]", "[1, 3]", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # 6. Sözlükler ve Kümeler
    # ═══════════════════════════════════════════════════════════════════════
    6: [
        # — Beginner —
        {
            "text": "d = {\"a\": 1, \"b\": 2}; print(d[\"a\"]) — çıktı nedir?",
            "options": ["2", "\"a\"", "1", "Hata"],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "s = {1, 2, 2, 3}; print(len(s)) — çıktı nedir?",
            "options": ["4", "3", "2", "1"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "d = {\"x\": 10}; d[\"y\"] = 20; print(len(d)) — çıktı?",
            "options": ["1", "2", "3", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "Boş bir sözlük nasıl oluşturulur?",
            "options": ["[]", "()", "{}", "set()"],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        # — Intermediate —
        {
            "text": "d = {\"a\": 1}; d.get(\"b\", 99) — sonuç?",
            "options": ["1", "99", "None", "KeyError"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "a = {1, 2, 3}; b = {2, 3, 4}; print(a & b) — çıktı?",
            "options": ["{1, 2, 3, 4}", "{1, 4}", "{2, 3}", "set()"],
            "answer": "C", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "d = {\"a\": 1, \"b\": 2}; print(list(d.keys())) — çıktı?",
            "options": ["[1, 2]", "[\"a\", \"b\"]", "(\"a\", \"b\")", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        # — Advanced —
        {
            "text": "d = {}; d.setdefault(\"x\", []).append(1); d.setdefault(\"x\", []).append(2); print(d) — çıktı?",
            "options": [
                "{\"x\": [1]}",
                "{\"x\": [1, 2]}",
                "{\"x\": [2]}",
                "Hata",
            ],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "d = {\"a\": 1, \"b\": 2}; print({v: k for k, v in d.items()}) — çıktı?",
            "options": [
                "{\"a\": 1, \"b\": 2}",
                "{1: \"a\", 2: \"b\"}",
                "{\"a\": \"b\"}",
                "Hata",
            ],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "s = frozenset({1, 2}); s.add(3) — sonuç?",
            "options": ["{1, 2, 3}", "AttributeError", "{1, 2}", "TypeError"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # 7. Fonksiyonlar
    # ═══════════════════════════════════════════════════════════════════════
    7: [
        # — Beginner —
        {
            "text": "def topla(a, b): return a + b — topla(3, 4) sonucu?",
            "options": ["7", "34", "12", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "return ifadesi olmayan bir fonksiyon ne döndürür?",
            "options": ["0", "\"\"", "None", "Hata"],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "lambda x: x * 2 — bu ne tür bir fonksiyondur?",
            "options": ["Özyinelemeli", "Anonim (lambda)", "Yerleşik", "Asenkron"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "Bir fonksiyon Python'da hangi anahtar kelimeyle tanımlanır?",
            "options": ["function", "def", "fun", "fn"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        # — Intermediate —
        {
            "text": "def f(x, y=10): return x + y\nf(5) — çıktı?",
            "options": ["5", "10", "15", "Hata"],
            "answer": "C", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "def f(*args): return sum(args)\nf(1, 2, 3) — çıktı?",
            "options": ["6", "[1,2,3]", "(1,2,3)", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "kare = lambda x: x ** 2\nkare(5) — çıktı?",
            "options": ["10", "25", "5", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        # — Advanced —
        {
            "text": "def f(x, liste=[]):\n    liste.append(x); return liste\nprint(f(1), f(2)) — çıktı?",
            "options": [
                "[1] [2]",
                "[1] [1, 2]",
                "[1, 2] [1, 2]",
                "Hata",
            ],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "def dış():\n    x = 10\n    def iç(): return x\n    return iç\nprint(dış()()) — çıktı?",
            "options": ["10", "None", "0", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "def f(): yield 1; yield 2\nprint(list(f())) — çıktı?",
            "options": ["[1, 2]", "[1]", "1 2", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_ADVANCED,
        },
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # 8. Dosya İşlemleri
    # ═══════════════════════════════════════════════════════════════════════
    8: [
        # — Beginner —
        {
            "text": "open(\"dosya.txt\", \"r\") ne yapar?",
            "options": [
                "Dosyaya yazar",
                "Dosyayı okur",
                "Dosyayı siler",
                "Yeni dosya oluşturur",
            ],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "with open(...) as f: kullanımının temel faydası nedir?",
            "options": [
                "Daha hızlı okur",
                "Dosyayı otomatik kapatır",
                "Dosyayı şifreler",
                "Hiçbir fark yoktur",
            ],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "\"w\" modu ne anlama gelir?",
            "options": [
                "Read (okuma)",
                "Write — mevcut içeriği silip yazar",
                "Append — sonuna ekler",
                "Binary (ikili)",
            ],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "\"a\" modu ne işe yarar?",
            "options": [
                "Dosyayı baştan okur",
                "Dosyanın sonuna ekleme yapar",
                "Dosyayı arşivler",
                "Dosyayı şifreler",
            ],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        # — Intermediate —
        {
            "text": "with open(\"x.txt\") as f: lines = f.readlines() — lines'ın tipi?",
            "options": ["str", "list", "tuple", "dict"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "Olmayan bir dosyayı \"r\" modunda açmak ne yapar?",
            "options": [
                "Boş dosya oluşturur",
                "FileNotFoundError fırlatır",
                "None döner",
                "Sessizce devam eder",
            ],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "f.read() metodu birden fazla çağrılırsa ikinci çağrıda ne döner?",
            "options": [
                "Yine tüm içerik",
                "Boş string \"\"",
                "Hata",
                "İlk satır",
            ],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        # — Advanced —
        {
            "text": "\"x\" modu (Python 3) ne yapar?",
            "options": [
                "Dosyayı XOR'lar",
                "Yeni dosya oluşturur — varsa FileExistsError",
                "Dosyayı şifreler",
                "Geçici dosya açar",
            ],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "with open(\"x\", \"rb\") as f: data = f.read() — data'nın tipi?",
            "options": ["str", "bytes", "list", "int"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "open(\"x.txt\", encoding=\"utf-8\") — encoding belirtilmezse ne olur?",
            "options": [
                "Her zaman utf-8 kullanılır",
                "Sistem varsayılan encoding'i kullanılır (platforma göre değişir)",
                "Hata verir",
                "ASCII kullanılır",
            ],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # 9. Hata Yönetimi
    # ═══════════════════════════════════════════════════════════════════════
    9: [
        # — Beginner —
        {
            "text": "try: 1/0\nexcept ZeroDivisionError: print(\"sıfır\") — çıktı?",
            "options": ["Hata (crash)", "sıfır", "0", "None"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "finally bloğu ne zaman çalışır?",
            "options": [
                "Sadece hata oluştuğunda",
                "Sadece hata oluşmadığında",
                "Her zaman (hata olsa da olmasa da)",
                "Hiçbir zaman",
            ],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "raise ValueError(\"hata\") ne yapar?",
            "options": [
                "Hatayı yakalar",
                "Elle bir hata fırlatır",
                "Hatayı görmezden gelir",
                "Programı sessizce durdurur",
            ],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "Aşağıdaki ifadelerden hangisi tipik bir hata yakalama bloğu başlatır?",
            "options": ["catch", "try", "throw", "rescue"],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        # — Intermediate —
        {
            "text": "try: int(\"abc\")\nexcept ValueError as e: print(type(e).__name__) — çıktı?",
            "options": ["ValueError", "TypeError", "abc", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "try-except'te else bloğu ne zaman çalışır?",
            "options": [
                "Her zaman",
                "Hata oluşmazsa",
                "Hata oluşursa",
                "Hiçbir zaman",
            ],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "try: x = 1/0\nexcept (ZeroDivisionError, TypeError): print(\"yakalandı\")\n— çıktı?",
            "options": ["yakalandı", "Hata", "0", "None"],
            "answer": "A", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        # — Advanced —
        {
            "text": "try: raise ValueError(\"v\")\nexcept Exception as e: raise RuntimeError(\"r\") from e\n— bu desen neye yarar?",
            "options": [
                "Orijinal hatayı gizler",
                "Exception chaining (sebep zincirleme)",
                "Hatayı log dosyasına yazar",
                "Hatayı sessizce yutar",
            ],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "bare except: kullanımının sakıncası nedir?",
            "options": [
                "Yavaş çalışır",
                "SystemExit ve KeyboardInterrupt dahil her şeyi yakalar — debug zorlaşır",
                "SyntaxError verir",
                "Sadece eski Python'da çalışır",
            ],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "def f():\n    try: return 1\n    finally: return 2\nprint(f()) — çıktı?",
            "options": ["1", "2", "None", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # 10. Sınıflar ve Nesneler (OOP)
    # ═══════════════════════════════════════════════════════════════════════
    10: [
        # — Beginner —
        {
            "text": "class Araba: pass — ardından Araba() ne oluşturur?",
            "options": ["Sınıf tanımı", "Modül", "Nesne (instance)", "Fonksiyon"],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "Sınıf metotlarındaki self parametresi ne anlama gelir?",
            "options": [
                "Global değişken",
                "Sınıfın kendisi",
                "Nesnenin (instance) kendisi",
                "Boş parametre",
            ],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "Kalıtım (inheritance) ne sağlar?",
            "options": [
                "İki sınıfı birleştirir",
                "Kod tekrarını zorlar",
                "Alt sınıf üst sınıfın özelliklerini devralır",
                "Performansı artırır",
            ],
            "answer": "C", "difficulty": DIFFICULTY_BEGINNER,
        },
        {
            "text": "__init__ metodu ne zaman çağrılır?",
            "options": [
                "Sınıf tanımlandığında",
                "Nesne (instance) oluşturulduğunda",
                "Program bittiğinde",
                "Hiçbir zaman otomatik çağrılmaz",
            ],
            "answer": "B", "difficulty": DIFFICULTY_BEGINNER,
        },
        # — Intermediate —
        {
            "text": "class K:\n    def __init__(self, x): self.x = x\nk = K(5); print(k.x) — çıktı?",
            "options": ["K", "5", "self", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "class A:\n    sayac = 0\na1 = A(); A.sayac = 5; print(a1.sayac) — çıktı?",
            "options": ["0", "5", "None", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        {
            "text": "class B(A): pass — B sınıfı ne ifade eder?",
            "options": [
                "A ile aynı sınıf",
                "A'dan kalıtım alan boş alt sınıf",
                "A'yı silen sınıf",
                "Hata verir",
            ],
            "answer": "B", "difficulty": DIFFICULTY_INTERMEDIATE,
        },
        # — Advanced —
        {
            "text": "class K:\n    def __str__(self): return \"K!\"\nprint(K()) — çıktı?",
            "options": ["K!", "<K object>", "K", "Hata"],
            "answer": "A", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "class A:\n    def __init__(self): self._x = 1\n    @property\n    def x(self): return self._x\na = A(); a.x = 5 — sonuç?",
            "options": [
                "a.x = 5 olur",
                "AttributeError (setter yok)",
                "TypeError",
                "Sessizce göz ardı edilir",
            ],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
        {
            "text": "class A:\n    @staticmethod\n    def f(): return \"s\"\nprint(A.f()) — çıktı?",
            "options": ["A.f", "s", "<staticmethod>", "Hata"],
            "answer": "B", "difficulty": DIFFICULTY_ADVANCED,
        },
    ],
}


def get_questions_for_topic(topic_id: int, count: int = 3) -> list[dict]:
    """
    Concept-check ve genel kullanım için belirtilen konudan ilk N soruyu döndürür.
    Varsayılan 3 soru — ilk 3 her zaman beginner seviyesidir.
    """
    questions = QUIZ_QUESTIONS.get(topic_id, [])
    return questions[:count]


def get_pretest_questions(topic_id: int) -> list[dict]:
    """
    Ön test için 10 soruyu kademeli zorluk sırasıyla döner:
      [4 beginner, 3 intermediate, 3 advanced]

    Bu sıralama PreTestModal'ın "kolaydan zora" UX'i için kritik.
    """
    questions = QUIZ_QUESTIONS.get(topic_id, [])

    order = {
        DIFFICULTY_BEGINNER: 0,
        DIFFICULTY_INTERMEDIATE: 1,
        DIFFICULTY_ADVANCED: 2,
    }
    # Stable sort — aynı seviyedeki sorular orijinal sırasını korur
    return sorted(questions, key=lambda q: order.get(q.get("difficulty", DIFFICULTY_BEGINNER), 0))


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
