# DURUM RAPORU — H-Nav Stage-0 Kampanyası

> Tarih: 2026-08-14, öğleden önce (denetçi ajan raporu)
> Dal: `claude/evomembench-hnav-analysis-nfwl9z` · Box: `ozonderlab2` (`/mnt/nvmes/nvme1/egekutlu/EvoMemBench`)
> Bu raporun yazıldığı anda boru hattı box'ta **çalışıyor** (t4 aşamasında, nohup altında).

---

## 1. Bugüne kadar yapılanların özeti

### T0 — Ofansif ölçümlerin yeniden üretimi (lokal, stdlib)
- `conflict_analysis.py`: sh_262k'da 11.037 anahtar / 7.197 çakışmalı (%65,2) — doğrulandı.
- `gold_rule.py`: sh_262k sorularının %77'si çakışmalı; 73/77 soruda gold = LATEST — doğrulandı.
- `marginal_diff.py`: yalnız leksik vekil; hiçbir eşik buradan türetilmedi.

### T1 — M1 geometri kalibrasyonu (box, in-process float32 `HFEmbedder`, Qwen/Qwen3-Embedding-4B) — **PASS, S3 ateşlemedi**
| subset | n_facts | çakışma çifti | median whole_blob_sim | kontrol medyanı | AUC (çakışma vs kontrol) |
| --- | --- | --- | --- | --- | --- |
| sh_6k | 455 | 160 | **0.9636** | 0.5977 | 1.0000 |
| sh_32k | 2.310 | 835 | **0.9638** | 0.6051 | 1.0000 |
| sh_64k | 4.580 | 1.687 | **0.9638** | 0.6021 | 1.0000 |
| sh_262k | 18.332 | 7.197 | **0.9641** | 0.6109 | 0.9999 |

S3 eşiği 0.70'ti; medyan ~0.964 → geometri öncülü bu benchmark'ta sağlam. Çakışan çiftler kontrol çiftlerinden neredeyse mükemmel ayrışıyor.

### T2 — M1b gruplama ablasyonu (geometri vs regex-oracle) — **PASS**
| subset | en iyi F1 | precision | recall | eşik (τ) |
| --- | --- | --- | --- | --- |
| sh_6k | **0.892** | 0.860 | 0.925 | 0.91 |
| sh_32k | **0.839** | 0.847 | 0.831 | 0.93 |
| sh_64k | **0.821** | 0.896 | 0.758 | 0.94 |
| sh_262k | **0.757** | 0.829 | 0.696 | 0.95 |

Yorum (brief'teki şablon): geometri, ayrıştırma olmadan regex gruplamasını büyük ölçüde geri kazanıyor; F1 mağaza büyüklüğüyle düşüyor (recall kaybı). CrossEp-Know'a taşınabilirlik iddiası bu tabloya dayanacak; sh_262k'daki 0.757 raporda açıkça beyan edilmeli.

### Dünkü (13-14 Ağustos gecesi) blokerler ve düzeltmeleri
- **m2 FAIL** — nltk `punkt` indirilemedi (downloader izin reddi). Düzeltme: `setup_ozonderlab2.sh` punkt'ı `$NVME/nltk_data`'ya elle indiriyor; `NLTK_DATA` `_activate.sh`'de ihraç ediliyor. Bugün `nltk.sent_tokenize` box'ta doğrulandı.
- **m0 / t4 SKIP** — benchmark bağımlılıkları (langchain, faiss-cpu, …) eksikti. Düzeltme: minimal bağımlılık seti kuruldu; bugün her iki deps-probe da geçiyor.
- Bu düzeltmeler `50cb978` commit'inde; box bu sabah `git pull` ile güncellendi.

### Bugünkü SSH otomasyonu
- `ssh -o BatchMode=yes egekutlu@ozonderlab2...` anahtarla, şifresiz çalışıyor (dün akşam kurulan key + `chmod g-w,o-w ~` düzeltmesi).
- Orkestrasyon lokalden: her adım ssh ile tetikleniyor, uzun işler yalnız nohup altında, izleme status/log dosyalarından. PLAN_YARIN.md mimarisine uygun.

---

## 2. GATE S1 teşhisi (bugün 10:30) — sınıf (a): HARNESS HATASI, düzeltildi

### Ne oldu
Sabah 10:30'da devam ettirilen boru hattı, m0 (canlı-indeks replika sadakati) aşamasında ~16 saniyede **S1 kapısını ateşledi** ve kendini durdurdu:

```
sh_6k:   top1=0.9400 topk=0.9400 tau=0.8800 maxΔ=5.26e-01
sh_32k:  top1=0.9000 topk=0.2400 tau=0.9333 maxΔ=5.57e-01
S1 FIRED — worst top-k agreement 0.2400 < 0.999.
```

### Kanıt zinciri (hepsi dosyalanmış durumda)
1. **`hnav/_out/m0_replica_fidelity.GATE_20260814_bf16.json`** (box'ta arşivlendi): her iki subsette `unit_normalized: false`, banka vektör normları **0.9981–1.0022**. fp32-normalize edilmiş vektörlerde norm 1±1e-7 olurdu; ±2e-3 sapma tam olarak bf16 kuantizasyon ölçeğidir.
2. **`hnav/_out/pipeline/embed_server.log`** satır 11: `dtype=torch.bfloat16` — `run_stage0.sh` vLLM sunucusunu `--dtype` bayrağı OLMADAN başlatıyordu; vLLM checkpoint'in bf16'sına düştü. (`pooler_config: pooling_type='LAST', normalize=True` — pooling ve normalizasyon doğruydu; sorun yalnız dtype.)
3. **Mekanizma:** `FaissFlatReplica` sıralamayı iç çarpımla yapar (`matrix @ qv`); bu, native FAISS'in L2 sıralamasıyla **yalnız birim vektörlerde** özdeştir (`d² = 2 − 2·cos`). Norm ±2e-3 kayınca iki belge arasındaki skor farkı ~4e-3'ün altındaysa sıra dönebilir. sh_32k'da 9 chunk aynı bağlamın 4096-token'lık parçaları — orta sıralardaki cos farkları bu bandın içinde. `topk_agreement` k=n=9 üzerinden **tam sıra özdeşliği** istediği için 0.24'e çöktü; top1 (0.90) ve Kendall τ (0.93) yüksek kaldı. Bu imza, "yanlış sıralama kuralı" değil, "beraberlik ölçeğinde monotonluk ihlali" imzasıdır.
4. **Doğrulayıcı deney:** sunucu `--dtype float32` ile yeniden başlatıldığında prob `max |norm−1| = 1.09e-07` ölçtü (bf16'da ~2e-3 idi) ve **aynı replika kodu, aynı m0 çağrısı** ile:

```
sh_6k:   top1=1.0000 topk=1.0000 tau=1.0000 maxΔ=4.08e-05
sh_32k:  top1=1.0000 topk=1.0000 tau=1.0000 maxΔ=1.96e-05
```

### Sınıflandırma gerekçesi
- Kampanyanın dtype'ı **float32 olarak sabitlenmişti** (`hnav/config.py` varsayılanı, box `.env`'inde `HNAV_EMBED_DTYPE=float32`, T1 kalibrasyonu in-process float32 `HFEmbedder` ile). CLAUDE.md: "Dtype is pinned once chosen; drift changes cosines and moves every threshold."
- :8001 sunucusunun bf16 servis etmesi bu sabitlemeye aykırı bir **harness kayması**dır; replika mantığında değil, ölçüm enstrümanında hata → **sınıf (a)**. (Sınıf (b) olsaydı: fp32 vektörlerle de uyuşmazlık sürerdi — sürmedi, 400/400 çiftte tam özdeşlik.)

### Yapılan işlem (minimal düzeltme, commit `4d6feb6`)
- `hnav/deploy/run_stage0.sh`: sunucu başlatmaya `--dtype "$HNAV_EMBED_DTYPE"` (varsayılan float32) ve `--max-model-len 16384` eklendi (fp32 ağırlıklar 15,0 GiB; native 40960'ta profil OOM riski — vLLM'in kendi uyarısı; hiçbir MAB girdisi 16384 token'a yaklaşmıyor, kesme davranışı değişmez).
- Artık ":8001'de zaten cevap veren sunucuyu yeniden kullan" dalı, kullanmadan önce vektör normlarını probluyor (fp32 hassasiyetinde birim-norm değilse sunucuyu öldürüp temiz başlatıyor) — bırakılmış bir bf16 sunucu S1 hatasını sessizce geri getiremez.
- `hnav/deploy/serve_embeddings.sh` (manuel servis yolu) aynı bayraklarla hizalandı.
- `hnav/core/` ve `hnav/stage0/`'a **dokunulmadı**; replika kodu değişmedi.

### m0 yeniden koşum sonucu — **S1 GEÇTİ**
Tam koşum (4 subset × 100 soru = 400 çift, fp32 sunucu):

| subset | n_docs | top1 | topk | τ | maxΔ | unit_normalized |
| --- | --- | --- | --- | --- | --- | --- |
| sh_6k | 2 | 1.0000 | 1.0000 | 1.0000 | 4.08e-05 | true |
| sh_32k | 9 | 1.0000 | 1.0000 | 1.0000 | 2.44e-05 | true |
| sh_64k | 17 | 1.0000 | 1.0000 | 1.0000 | 3.08e-05 | true |
| sh_262k | 67 | 1.0000 | 1.0000 | 1.0000 | 4.53e-05 | true |

`m0.status: PASS 2026-08-14 10:49:14`. Not: 400 çift, protokolün 1.000 hedefinin altında; ancak birincil arenada toplam 400 soru var — bu, arenanın **eksiksiz** kapsamıdır (aşağıda açık soru).

---

## 3. Boru hattının şu anki durumu ve kalan aşamalar

Yeniden başlatma komutu (10:47:01, pid 78843, nohup):

```
cd /mnt/nvmes/nvme1/egekutlu/EvoMemBench && \
nohup bash hnav/deploy/run_stage0.sh --redo m0,t4 > hnav/_out/pipeline/console6.log 2>&1 &
```

| stage | durum | not |
| --- | --- | --- |
| preflight, t1_smoke, t1, t2 | PASS (atlandı) | gece koşumundan |
| **m0** | **PASS 10:49** | S1 geçti, yukarıdaki tablo |
| **t4** | **KOŞUYOR** (10:49'dan beri) | S2 kapısı: off vs shadow bayt-özdeşliği, sh_6k+sh_32k; embed :8001 fp32 + LLM :8000 |
| m2 | sırada (stale FAIL → yeniden koşacak) | punkt düzeltildi; `fallback_chunker=false` tuzağı yine denetlenecek |
| m3 | sırada | en uzun kalem (~2-3k LLM çağrısı, saatler) |
| m4 | sırada | yalnız kalibrasyon spliti (sh_6k+sh_32k) |
| report | sırada | T8 = İNSAN KAPISI, ajan karar vermez |

- İzleme: `tail hnav/_out/pipeline/console6.log` ve `hnav/_out/pipeline/*.status`.
- GPU0/:8000 (kullanıcının LLM'i, PID 52520) hiç dokunulmadı; embed sunucu GPU1'de, boru hattı m2'den önce kendisi kapatıp VRAM'in boşalmasını bekliyor.
- Kural gereği: **S1 bir daha ateşlerse ikinci düzeltme YOK** — durulur ve raporlanır. (Şu ana kadar ateşlemedi; m0 tam koşumda geçti.)

---

## 4. Stage-1 tasarımcısının ihtiyaç duyacağı girdiler

1. **`STAGE0_REPORT.md` + `hnav/_out/m{0,1,1b,2,3,4}_*.json`** (box'ta; `hnav/_out` gitignore'da → `stage0_results/` altına bilinçli commit gerekir, PLAN_YARIN Safha 2).
2. **M3 headroom tabloları** — could-change-correctness oranları Stage-1'de kazanılabilecek maksimumu tanımlar; tezin başarı ölçütleri tablosuna bağlanır.
3. **M1b F1 tablosu (yukarıda)** — kazanımın geometriye mi metadata'ya mı atfedileceğinin kanıtı; sh_262k'da F1 0.757 → büyük mağazada recall kaybı Stage-1 eşik seçiminde dikkate alınmalı. Eşikler YALNIZ sh_6k+sh_32k'dan (kalibrasyon spliti) türetilebilir.
4. **M0 sonucu**: replika fp32 servis altında bire bir sadık → `rank_self`, `margin`, `dH_self`, `dH_neighbor`, `churn` sinyalleri GEÇERLİ. Ek bulgu: bf16 servis altında `FaissFlatReplica`'nın iç-çarpım sıralaması bozulur (topk 0.24 @ k=9). Stage-1 tasarımı, hedef sistem fp32-normalize embedding servis etmiyorsa sıralamayı tam L2 üzerinden yapmalı ya da dtype'ı sabitlemelidir. Bu, tez için raporlanabilir bir gürbüzlük notudur.
5. **M2 ham-entropi verdikti** (`H_raw` degenerasyonu cosine×100'de) — m2 çıktısında; iki cevap da yayınlanabilir.
6. **Değişmezler devam ediyor**: `HNAV_MODE=off`; `write_policy.py`/`read_policy.py` yok (T8 insan kararına kilitli); sh_64k/sh_262k'da eşik ayarı yasak; `hnav/_cache/emb/` silinmez/kopyalanmaz (model|dtype anahtarlı).
7. Arşiv kanıtı: `hnav/_out/m0_replica_fidelity.GATE_20260814_bf16.json` (bf16 GATE ölçümü) — `stage0_results/`'a kopyalanmalı.

---

## 5. KULLANICIYA AÇIK SORULAR

1. **fp32 servis sapması beyanı.** :8001 embed sunucusu artık `--dtype float32` ile koşuyor (kampanyanın sabit dtype'ı; T1/M2/M3 ile tutarlı). Ancak checkpoint'in native dtype'ı bf16'dır ve upstream benchmark yazarlarının servis dtype'ı bilinmiyor. Tezde "embedding'ler fp32 servis edildi" açık bir sapma/konfigürasyon notu olarak beyan edilecek — **onaylıyor musunuz?** (Alternatif — bf16'ya dönmek — T1'den beri yapılan tüm kalibrasyonu geçersiz kılar; önerilmez.)
2. **bf16 GATE ölçümünün tezdeki yeri.** S1'in bf16 altında ateşlemesi kendi başına bir bulgu: "replika sadakati servis dtype'ına birim-norm varsayımı üzerinden duyarlıdır (bf16'da topk 0.24, fp32'de 1.00)". Bunu tezde bir gürbüzlük/negatif-sonuç kutusu olarak raporlamak ister misiniz, yoksa yalnız yöntem notu mu kalsın?
3. **M0 örneklem büyüklüğü.** Protokol arena başına ≥1.000 çift ister; birincil arenada toplam 400 soru var ve 400/400'ü ölçüldü (örnekleme değil, tam sayım). "400 = arenanın eksiksiz kapsamı" gerekçesiyle bu kabul edilebilir mi, yoksa (ör. tekrar sorgular ya da CrossEp-Know tarafında ek çiftlerle) 1.000'e tamamlanması mı istenir?
4. **T8 kapısı bu akşam sizde.** Boru hattı raporu ürettiğinde GO/NO_GO değerlendirmesi yalnız insan tarafından, `EVOMEMBENCH_HNAV_STAGE0_PROTOCOL.md` §4'e göre yapılacak. Ajanlar karar vermeyecek; `KAPI_KARARI.md` yalnız karar destek dosyası olacak.
5. **`--max-model-len 16384`.** fp32 profil OOM riskine karşı eklendi; hiçbir MAB girdisi bu uzunluğa yaklaşmadığı için davranışsal etkisi yok. Yine de sunucu bayraklarındaki her sapma gibi beyan ediyoruz — itirazınız var mı?
