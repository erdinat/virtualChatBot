# Sanal Öğretmen Asistanı

RAG + DKT + DRL tabanlı Türkçe adaptif Python öğrenme platformu.

## Mimari

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| LLM | DeepSeek API | Sokratik yanıt üretimi |
| RAG | ChromaDB + LangChain | PDF ders notu retrieval |
| DKT | LSTM (PyTorch) | Bilgi seviyesi tahmini |
| DRL | DQN (PyTorch) | Adaptif konu sıralama |
| Backend | FastAPI + JWT | REST + SSE API |
| Frontend | React + Vite + Tailwind | SPA arayüz |

## Kurulum

### 1. Gereksinimler

- Python 3.11+
- Node.js 20+

### 2. Ortam Değişkenleri

```bash
cp .env.example .env
# .env dosyasını aç ve DEEPSEEK_API_KEY değerini gir
```

### 3. Python Bağımlılıkları

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Frontend Bağımlılıkları

```bash
cd frontend
npm install
cd ..
```

## Çalıştırma

### Geliştirme Ortamı (Önerilen)

İki ayrı terminal açın:

**Terminal 1 — Backend:**
```bash
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Uygulama: http://localhost:5173
API Docs: http://localhost:8000/docs

### Docker ile Çalıştırma

```bash
cp .env.example .env
# .env dosyasına DEEPSEEK_API_KEY ekle
docker compose up --build
```

## Demo Hesaplar

| Kullanıcı | Şifre | Rol |
|-----------|-------|-----|
| `ali` | `1234` | Öğrenci (Başlangıç) |
| `ayse` | `1234` | Öğrenci (İleri) |
| `ogretmen` | `1234` | Öğretmen |

## ML Model Eğitimi

### DKT Modeli (LSTM)

```bash
python scripts/generate_synthetic_data.py   # Sentetik veri üret
python scripts/train_dkt.py                 # Modeli eğit → models/dkt_model.pt
```

### DRL Ajanı (DQN)

```bash
python scripts/train_drl.py --episodes 500 --verbose
# → models/drl_agent.pt
```

## Değerlendirme ve Analiz

### DKT Model Performansı (AUC-ROC)

```bash
python scripts/evaluate_dkt.py
# → results/dkt_eval.json
```

### Ablation Study — Strateji Karşılaştırması

```bash
python scripts/evaluate_strategies.py --students 200 --steps 60
# → results/ablation_results.json
# Sıralı vs Kural Tabanlı vs DRL karşılaştırma tablosu
```

### Persona Simülasyonu

```bash
python scripts/simulate_personas.py --steps 30
# → results/persona_simulation.json
# Ali (başlangıç) vs Ayşe (ileri) adaptasyon karşılaştırması
```

## Proje Yapısı

```
├── backend/              FastAPI uygulaması
│   ├── routers/          auth, chat, mastery, diagnostic, teacher, pdfs
│   ├── auth.py           JWT kimlik doğrulama
│   └── schemas.py        Pydantic modelleri
├── config/
│   ├── settings.py       Tüm yapılandırma parametreleri
│   ├── users.yaml        Kullanıcı tanımları
│   └── quiz_questions.py Konu bazlı test soruları (30 soru)
├── frontend/             React + Vite + Tailwind
│   └── src/
│       ├── pages/        LoginPage, DiagnosticPage, StudentPage, TeacherPage
│       └── api/client.ts Tüm API çağrıları
├── modules/
│   ├── dkt/              LSTM bilgi takip modeli
│   ├── drl/              DQN adaptif konu sıralama ajanı
│   ├── rag/              PDF yükleme, ChromaDB, LangChain chain
│   ├── pedagogy/         Sokratik yöntem yöneticisi
│   └── storage.py        JSON/JSONL kalıcı veri katmanı
├── models/               Eğitilmiş modeller (.pt dosyaları)
├── data/
│   ├── raw_pdfs/         Yüklenen PDF ders notları
│   ├── vector_store/     ChromaDB vektör veritabanı
│   └── student_logs/     Öğrenci etkileşim geçmişleri
├── scripts/              Eğitim ve analiz scriptleri
└── results/              Değerlendirme sonuçları (JSON)
```
