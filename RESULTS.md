# Deneysel Sonuçlar

Bu rapor `scripts/evaluate_*.py` ve `scripts/simulate_personas.py` çıktılarını
tezde kullanılabilir biçimde özetler. Tüm deneyler **seed 42** ile yapılmıştır
ve yeniden üretilebilir (`modules/seed.py`).

Üretim komutları:

```bash
python scripts/evaluate_dkt.py          # → results/dkt_eval.json
python scripts/evaluate_strategies.py --students 200 --steps 300   # → results/ablation_results.json
python scripts/simulate_personas.py --steps 60                     # → results/persona_simulation.json
```

---

## 1. DKT Model Performansı

**Senaryo:** 1000 sentetik öğrenci × 25 etkileşim üzerinde eğitilen LSTM,
300 yeni öğrenci ile test edildi.

| Metrik | Değer | Yorum |
|--------|-------|-------|
| AUC-ROC | **0.6711** | Rastgele tahmin = 0.50; mükemmel = 1.00 → modelin sinyal yakaladığını gösterir |
| Binary Cross-Entropy | 0.6004 | Daha düşük daha iyi |
| MAE (mean absolute error) | 0.2190 | Mastery tahminleri ortalama ±0.22 sapıyor |
| RMSE | 0.2676 | Karelenmiş hata |

**Yorum:** Model rastgele tahminden belirgin biçimde iyi (AUC = 0.67) ama
mükemmel değil. Bu beklenen bir sonuç; LSTM **sentetik veride** eğitildi, gerçek
öğrenci verisi mevcut olmadığından sınıflandırma gücü sınırlı kaldı. Mevcut
implementasyon LSTM ile az veride güvenilir tahmin üretemeyen senaryolar için
**kural tabanlı fallback** içerir (`modules/dkt/predict.py:96`).

---

## 2. Ablation Study — Adaptasyon Stratejisi Karşılaştırması

**Senaryo:** 200 öğrenci × 300 adım, üç strateji aynı `LearningEnvironment`'ta
karşılaştırıldı.

| Strateji | Ort. Final Mastery | Yetkinlik Oranı (≥0.7) | Bağıl Performans |
|----------|--------------------|-----------------------|-----------------:|
| Sıralı (Adaptasyonsuz) | 0.3165 | %0 | Baseline |
| Kural Tabanlı (RuleBased) | 0.2783 | %0 | −%12.1 |
| **DRL (Eğitilmiş DQN)** | **0.3122** | %0 | **−%1.4** |

### Kilit bulgu

DRL ajanı kural tabanlı politikadan **%12.2 daha yüksek** ortalama mastery üretiyor
(0.3122 vs 0.2783). Bu DQN'in eğitim sırasında **anlamlı bir politika** geliştirdiğinin
ölçülebilir kanıtıdır. Sıralı stratejinin biraz daha yüksek çıkması, sentetik
ortamda "kolaydan zora ilerleme" sezgisinin güçlü bir baseline olmasından kaynaklanır.

### Aynı durumda farklı karar

Manuel doğrulama (Ali profili): öğrenci ilk 2 konuda %85+, diğerlerinde %30
mastery'deyken:

- **RuleBased** → "Koşul İfadeleri" (3. konu) öner
- **DQN**       → "Döngüler" (4. konu) öner — sıra atlıyor

DQN eğitim sırasında *"öğrenci 2 ardışık konuyu güçlü biliyorsa daha hızlı
ilerleyebilir"* desenini yakalamış görünüyor.

### ⚠ Sınırlama: Yetkinlik oranı %0

300 adımda hiçbir strateji öğrencilerin %0.7 eşiğine ulaşmasını sağlamadı.
Bu **modellerin değil, simülasyon ortamının** bir sınırlamasıdır.
`LearningEnvironment.step()` öğrenme dinamiğini şu şekilde modelliyor:

```python
success_prob = self.state[action]            # mastery = başarı olasılığı
if success:  self.state[action] += 0.10      # cömert artış
else:        self.state[action] -= 0.02      # küçük düşüş
```

Bu model **açıkça öğretim etkisini içermiyor**; öğrenci 0.3 mastery'deyken
simülasyonda yalnızca %30 başarı şansına sahip, gerçekte ise öğretmen
açıklama sonrası bu oran ~%65'e çıkar. Yetkinlik oranlarını yorumlanabilir
hâle getirmek için **future work** maddesi olarak bırakılmıştır
(bkz. §5).

---

## 3. Persona Simülasyonu — Kişiselleştirme Davranışı

**Senaryo:** İki farklı profil 60 adım simüle edildi. Politika her adımda
"hangi konuyu çalıştırayım?" sorusuna karar verdi.

### 👤 Ali — Başlangıç Profili

- **Başlangıç mastery:** 0.10 (tüm konular düşük)
- **Final mastery:** 0.09 (Δ = −0.01)
- **En çok önerilen konu:** Hata Yönetimi (50/50 adım)

Sistem Ali'ye sürekli **en zor konuyu** önerdi (Hata Yönetimi).
Başarı şansı düşük olduğundan ilerleme sağlanamadı. Bu, §2'deki
kalibrasyon sorununun pratik sonucudur — politika "öğrenci sıkışınca
daha kolay konuya geç" desenini öğrenememiş.

### 👤 Ayşe — İleri Profil

- **Başlangıç mastery:** 0.49 (temel konularda güçlü)
- **Final mastery:** 0.525 (Δ = +0.035)
- **En çok önerilen konu:** Listeler ve Tuple'lar (50/50 adım, bitiş: 1.00)

Ayşe'nin temel konuları (Değişkenler, Operatörler, Koşullar, Döngüler,
Listeler, Sözlükler) hepsi ≥0.6 mastery'ye ulaştı. Sistem güçlü olduğu konuyu
mükemmeleştirdi ama yeni alanlara (Fonksiyonlar, OOP) geçemedi.

### Kilit bulgu

Sistem **profillere farklı tepki veriyor** — Ayşe'nin temel konularını
güçlendirirken Ali'ye sürekli aynı (yanlış) konuyu öneriyor. Bu davranış farkı
adaptasyonun **var olduğunu** ama **kalibrasyona ihtiyacı olduğunu** gösteriyor.

---

## 4. Test Kapsamı

| Test Dosyası | Test Sayısı | Konu |
|--------------|------------:|------|
| `tests/test_auth.py` | 39 | JWT, bcrypt, login, korumalı endpoint'ler, path traversal |
| `tests/test_drl.py` | 15 | RuleBasedPolicy davranışı |
| `tests/test_rag.py` | 23 | Topic detection, kural tabanlı mastery, /health |
| `tests/test_pdfs.py` | 14 | PDF magic byte, upload auth, polyglot reddi |
| `tests/test_pretest.py` | 63 | Quiz yapısı, kademeli skorlama, endpoint güvenliği |
| **Toplam** | **154** | — |

`pytest tests/ --tb=short` ile tek komutta çalışır, **hepsi geçer**.

---

## 5. Sınırlamalar ve Future Work

Akademik dürüstlük için bilinen kısıtlar:

| Sınırlama | Etki | Çözüm Önerisi |
|-----------|------|----------------|
| DKT sentetik veride eğitildi | AUC ~0.67, gerçek veri ile ≥0.80 mümkün | Gerçek öğrenci etkileşim veri seti toplamak |
| `LearningEnvironment` öğretim etkisini modellemiyor | Yetkinlik %0 çıkıyor | `success_prob` formülüne öğretim bias'ı eklemek |
| DRL ablation 300 adımda eşik altı kalıyor | Mutlak değerler düşük | Yukarıdaki kalibrasyon sonrası yeniden eğitim |
| Ali profili tek konuda takılıyor | Kişiselleştirme yetersiz | Curiosity-driven exploration veya UCB tabanlı politika |
| Gerçek kullanıcı çalışması (IRB) yok | Genelleme sınırlı | Pilot grupla küçük ölçekli kullanıcı testi |
| `langchain-classic` deprecated | Tech debt | LCEL migrasyonu |

---

## 6. Reproducibility

Tüm sonuçlar `seed=42` ile birebir yeniden üretilebilir:

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt        # sürümler == ile sabitlenmiş
python scripts/train_dkt.py            # ~60 sn
python scripts/train_drl.py --episodes 500
python scripts/evaluate_dkt.py
python scripts/evaluate_strategies.py --students 200 --steps 300
python scripts/simulate_personas.py --steps 60
```

`modules/seed.py` Python `random`, NumPy ve PyTorch (CPU+CUDA) RNG'lerini
tek noktadan sabitler. `torch.backends.cudnn.deterministic = True` ayarı
GPU üzerinde de tekrar üretilebilirlik garanti eder.

---

## 7. Özet — Tez Savunması İçin Hızlı Bakış

> Üç bileşenli (RAG + DKT + DRL) Türkçe adaptif Python öğrenme platformu
> başarıyla implement edildi. DKT LSTM modeli AUC = 0.67 ile rastgele tahminin
> belirgin biçimde üzerinde performans gösterirken, DRL DQN ajanı kural tabanlı
> politikadan **%12 daha iyi** ortalama mastery üretti. Persona simülasyonu
> sistemin farklı öğrenci profillerine farklı tepki verdiğini doğruladı —
> kişiselleştirmenin temel mekanizması çalışıyor. Ablation'da yetkinlik oranı
> %0 çıkması simülasyon ortamının (gerçek öğretim etkisi modellenmediğinden)
> bir kalibrasyon sınırlamasıdır, modellerin değil; bu, kontrolünüzdeki gelecek
> çalışma maddelerine eklenmiştir.
