# Sanal Öğretmen Asistanı

**Türkçe konuşan, Python öğreten, kişiselleşen bir öğrenme ortamı.**

Lisans tezi kapsamında geliştirilmiş, üç farklı yapay zekâ tekniğini bir araya
getiren adaptif öğretim platformu. Öğrenci ile sokratik diyalog kurar, bilgi
seviyesini izler ve sırada hangi konuyu öğrenmesi gerektiğine karar verir.

| Katman | Teknoloji | Görev |
|--------|-----------|-------|
| LLM | DeepSeek API + LangChain | Sokratik yanıt üretimi |
| RAG | ChromaDB + sentence-transformers | PDF ders notu retrieval |
| DKT | LSTM (PyTorch) | Bilgi seviyesi (mastery) tahmini |
| DRL | DQN (PyTorch) — rule-based fallback | Adaptif konu sıralama |
| Backend | FastAPI + JWT + SSE | REST + streaming API |
| Frontend | React 19 + Vite + Tailwind | SPA arayüz |

---

## İçindekiler

- [Motivasyon](#motivasyon)
- [Mimari](#mimari)
- [Kurulum](#kurulum)
- [Çalıştırma](#çalıştırma)
- [Demo Hesaplar](#demo-hesaplar)
- [ML Model Eğitimi](#ml-model-eğitimi)
- [Test ve Değerlendirme](#test-ve-değerlendirme)
- [Reproducibility](#reproducibility)
- [Güvenlik Notları](#güvenlik-notları)
- [Sınırlamalar](#sınırlamalar)
- [Proje Yapısı](#proje-yapısı)
- [Lisans](#lisans)

---

## Motivasyon

Geleneksel "tek beden herkese uyar" yaklaşımı, programlama öğreniminde sınıfın
çoğunluğunu ya sıkmakta ya da geride bırakmaktadır. Bu çalışmada öğrencinin
mevcut bilgi seviyesini sürekli takip eden, doğrudan cevap vermek yerine
sokratik sorular yönelten ve hangi konunun tam zamanı olduğunu öğrenen bir
yapay öğretmen tasarlanmıştır.

Üç bileşen sırasıyla şu soruları yanıtlar:

- **RAG** → "Öğrencinin sorusuyla *gerçekten ilgili* ders içeriği nedir?"
- **DKT** → "Öğrenci şu an her konuyu *ne kadar* biliyor?"
- **DRL** → "Bu öğrenciye *sırada hangi konuyu* önermeliyim?"

---

## Mimari

### Üst seviye veri akışı

```
                 ┌──────────────┐
                 │   Öğrenci    │
                 │   (React)    │
                 └──────┬───────┘
                        │  HTTPS + SSE
                        ▼
┌────────────────────────────────────────────┐
│            FastAPI (backend/)              │
│  /auth  /chat  /mastery  /diagnostic ...   │
└──────┬─────────┬─────────┬─────────┬───────┘
       │         │         │         │
       ▼         ▼         ▼         ▼
   ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
   │ RAG  │  │ DKT  │  │ DRL  │  │ Stor │
   │ Chain│  │ LSTM │  │ Pol. │  │ JSON │
   └───┬──┘  └──────┘  └──────┘  └──────┘
       │
       ▼
   ┌──────────────┐
   │  ChromaDB    │ ← PDF ders notları (modules/rag/pdf_loader.py)
   └──────────────┘
       │
       ▼
   ┌──────────────┐
   │ DeepSeek LLM │
   └──────────────┘
```

### Bir sorunun yaşam döngüsü

```
1. Öğrenci soruyu yazar     ──► frontend `askQuestion()` (SSE)
2. Backend topic'i tespit eder ──► chat.py::_detect_topic
3. SocraticManager hint seviyesini belirler
4. RAG ChromaDB'den 6 chunk çeker (topic_id filtreli)
5. DeepSeek LLM cevabı stream'ler ──► token-by-token SSE
6. mastery/feedback DKT vektörünü günceller
7. Sonraki turda DRL policy "şimdi ne öğret?" sorusunu yanıtlar
```

---

## Kurulum

### Gereksinimler

- Python 3.11+
- Node.js 20+
- (Opsiyonel) Docker 25+ ile `docker compose`

### 1. Ortam değişkenleri

```bash
cp .env.example .env
# .env'i aç, en az şunları doldur:
#   JWT_SECRET_KEY=<openssl rand -hex 32>
#   DEEPSEEK_API_KEY=<deepseek panelinden al>
```

> **Önemli:** `JWT_SECRET_KEY` boşsa backend açılışta `RuntimeError` ile durur.
> Bu kasıtlı bir koruma; gerçek secret olmadan çalışmaması gerekir.

```bash
cp frontend/.env.example frontend/.env
# Varsayılan: VITE_API_URL=http://localhost:8000
```

### 2. Python bağımlılıkları

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Tüm sürümler `==` ile sabitlenmiştir; aynı kurulum 5 yıl sonra da aynı
sürümleri getirir (reproducibility).

### 3. Frontend bağımlılıkları

```bash
cd frontend
npm install
cd ..
```

---

## Çalıştırma

### Geliştirme ortamı

İki ayrı terminal:

```bash
# Terminal 1 — Backend
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

- Uygulama: <http://localhost:5173>
- API Docs: <http://localhost:8000/docs>

### Docker

```bash
docker compose up --build
```

---

## Demo Hesaplar

`config/users.yaml` dosyasında tanımlıdırlar. Şifreler bcrypt ile saklanır;
test için düz metinler:

| Kullanıcı | Şifre | Rol |
|-----------|--------|-----|
| `ali` | `ali123` | Öğrenci (başlangıç profili) |
| `ayse` | `ayse123` | Öğrenci (ileri profil) |
| `ogretmen` | `ogr123` | Öğretmen (analytics + PDF yükleme) |

> Üretimde bu hesaplar **silinmelidir.** Yeni bcrypt hash üretmek için:
> `python -c "import bcrypt; print(bcrypt.hashpw(b'parola', bcrypt.gensalt()).decode())"`

---

## ML Model Eğitimi

### DKT (Deep Knowledge Tracing) LSTM

```bash
python scripts/train_dkt.py            # ~60 saniye, models/dkt_model.pt
```

Sentetik öğrenci üretir (1000 öğrenci × 25 etkileşim), LSTM eğitir, val loss
ile takip eder. Seed `42` ile sabittir — her çalıştırmada birebir aynı model.

### DRL (DQN) Ajanı

```bash
python scripts/train_drl.py --episodes 500 --verbose
# özelleştirilmiş seed:
python scripts/train_drl.py --episodes 1000 --seed 7
```

DQN ajanı `LearningEnvironment` üzerinde eğitilir. Eğitilmiş model yoksa
`RuleBasedPolicy` otomatik fallback olarak devreye girer (çalışma için DQN
**şart değildir**).

---

## Test ve Değerlendirme

### Birim + Entegrasyon Testleri

```bash
source venv/bin/activate
JWT_SECRET_KEY=test-secret python -m pytest tests/ -v
```

Mevcut kapsam:

| Dosya | Test sayısı | Konu |
|-------|-------------|------|
| `tests/test_auth.py` | 39 | JWT, bcrypt, login endpoint, korumalı endpoint'ler, username path traversal |
| `tests/test_drl.py` | 15 | RuleBasedPolicy davranışı |
| `tests/test_rag.py` | 23 | Topic detection, kural tabanlı mastery, /health |
| `tests/test_pdfs.py` | 14 | PDF magic byte kontrolü, upload auth, polyglot reddi |
| **Toplam** | **91** | — |

### Frontend tip kontrolü

```bash
cd frontend
./node_modules/.bin/tsc --noEmit
```

### DKT Model Performansı

```bash
python scripts/evaluate_dkt.py
# → results/dkt_eval.json (AUC-ROC, BCE, MAE, RMSE)
```

### Ablation — Strateji Karşılaştırması

```bash
python scripts/evaluate_strategies.py --students 200 --steps 60
# Sequential vs RuleBased vs DRL: ortalama mastery, mastery rate, adım sayısı
# → results/ablation_results.json
```

### Persona Simülasyonu

```bash
python scripts/simulate_personas.py --steps 30
# Ali (başlangıç) vs Ayşe (ileri) adaptasyon karşılaştırması
# → results/persona_simulation.json
```

---

## Reproducibility

Tezdeki sonuçların tekrar üretilebilmesi için:

1. `requirements.txt` `==` sürümlerle sabitlenmiştir.
2. ML eğitim scriptleri [`modules/seed.py`](modules/seed.py) üzerinden Python
   `random`, NumPy, PyTorch (CPU + CUDA) RNG'lerini seed `42` ile başlatır.
3. `torch.backends.cudnn.deterministic = True` ayarlanmıştır.
4. DataLoader shuffle aynı seed ile aynı sıralamayı üretir.

`scripts/train_dkt.py` veya `scripts/train_drl.py` aynı seed ile iki kez
çalıştırıldığında **aynı modeli üretir**.

---

## Güvenlik Notları

| Önlem | Konum |
|-------|-------|
| JWT secret env zorunlu (boşsa açılış engellenir) | `backend/auth.py` |
| JWT algoritma whitelist (`HS256`) + expiry (24 saat) | `backend/auth.py` |
| Bcrypt şifre hashing | `backend/auth.py::verify_password` |
| Username regex doğrulaması (path traversal koruması) | `modules/storage.py::_validate_username` |
| PDF magic byte kontrolü (polyglot reddi) | `backend/routers/pdfs.py::_is_pdf_content` |
| PDF upload 10 MB sınırı + Path traversal koruması | `backend/routers/pdfs.py` |
| CORS metot/origin kısıtlaması | `backend/main.py` |
| XSS koruması — DOMPurify ile tüm `dangerouslySetInnerHTML` sanitize | `frontend/src/components/student/` |
| LRU cache (memory leak koruması) — socratic 200, chain 100 max | `backend/routers/chat.py` |
| localStorage güvenli sarmalayıcısı (private mode crash önlenmiş) | `frontend/src/utils/safeStorage.ts` |

---

## Sınırlamalar

Akademik dürüstlük gereği, bilinmesi gereken kısıtlar:

- **DKT eğitimi sentetik verilere dayanır.** Gerçek öğrenci verisi
  toplanmadığı için modelin gerçek hayatta nasıl davranacağı `scripts/simulate_personas.py`
  ile *yaklaşık* gösterilebilir. Az veride **kural tabanlı fallback** daha
  güvenilirdir (`modules/dkt/predict.py:96`).
- **DRL DQN ajanı eğitilebilirdir ama eğitilmiş ağırlık dosyası
  (`models/drl_agent.pt`) repo'da yoktur.** Çalışma süresinde
  `RuleBasedPolicy` aktif olur.
- **`langchain-classic` paketi deprecated.** LCEL migrasyonu açık tech debt.
- **Sohbet logları (`data/system_logs/chat_log.jsonl`) sınırsız büyür** —
  rotation/archival mekanizması yoktur.
- **Tek-process uvicorn varsayımı.** Çoklu worker için `storage.py` kilitleri
  Redis/DB'ye taşınmalıdır.
- **Brute-force koruması (auth rate limit) yoktur.**
- **Gerçek kullanıcı çalışması (IRB onayı) yapılmamıştır** — bu mühendislik
  prototipidir.

---

## Proje Yapısı

```
.
├── backend/                  FastAPI uygulaması
│   ├── routers/              auth, chat, mastery, diagnostic, teacher, pdfs
│   ├── auth.py               JWT + bcrypt
│   └── schemas.py            Pydantic v2 modelleri
├── config/
│   ├── settings.py           LLMConfig, RAGConfig, DKTConfig, DRLConfig, CURRICULUM
│   ├── users.yaml            bcrypt hashli kullanıcı tanımları (not in git)
│   └── quiz_questions.py     Statik fallback soruları
├── frontend/                 React 19 + Vite + Tailwind
│   └── src/
│       ├── App.tsx           Routes, ProtectedRoute, RootRedirect
│       ├── api/client.ts     Axios + SSE
│       ├── store/            Zustand auth store
│       ├── pages/            LoginPage, DiagnosticPage, StudentPage, TeacherPage
│       ├── components/       student/* (CurriculumGrid, ChatView, QuizModal …)
│       ├── hooks/            useStudentPage, useParticleCanvas
│       └── utils/            safeStorage (localStorage wrapper)
├── modules/
│   ├── rag/                  pdf_loader, embeddings, retriever, chain
│   ├── dkt/                  LSTM model, predict, train
│   ├── drl/                  DQN agent, environment, RuleBasedPolicy
│   ├── pedagogy/             SocraticManager
│   ├── storage.py            JSON + JSONL persistence (thread-safe)
│   └── seed.py               RNG seed helper (reproducibility)
├── scripts/                  Eğitim ve değerlendirme scriptleri
├── tests/                    pytest test paketi (91 test)
├── data/                     PDF, vektör store, öğrenci logları (not in git)
├── models/                   Eğitilmiş .pt dosyaları (not in git)
├── docker-compose.yml        Backend + frontend servisleri
├── requirements.txt          == ile sabitlenmiş Python bağımlılıkları
├── LICENSE                   MIT
├── README.md                 Bu dosya
└── CLAUDE.md                 Geliştirme rehberi (Claude Code için)
```

---

## Deneysel Sonuçlar

Tüm değerlendirme metrikleri, ablation karşılaştırması ve persona simülasyonları
[RESULTS.md](RESULTS.md) dosyasında detaylı olarak raporlanmıştır.

Özet:
- **DKT LSTM:** AUC-ROC = 0.67 (rastgeleden belirgin biçimde iyi)
- **DRL DQN:** Kural tabanlı politikadan **%12 daha yüksek** ortalama mastery
- **Persona testi:** Sistem Ali ve Ayşe profillerine farklı tepkiler üretiyor (kişiselleştirme doğrulandı)

## Lisans

[MIT](LICENSE) — © 2026 Yerdinat Alikhan
