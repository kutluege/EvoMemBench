# TEZ BULGULARI — Kanıt Defteri

> Amaç: bugün **savunulabilir** olan her bulgunun tek yerde, kanıt dosyasıyla,
> sınırlılığıyla ve durumuyla listesi. Dış denetime (danışman / hakem / harici
> model) verilecek hâli budur: her sayının ham kaynağı gösterilir.
> Son güncelleme: 2026-08-15. Kod durumu: 315 test yeşil.
>
> **Durum etiketleri:** `KESİN` = ölçüldü, bağımsız doğrulandı, düzeltme
> beklemiyor · `SAĞLAM` = ölçüldü ve denetlendi · `GEÇİCİ` = 512-token kesme
> düzeltmesi sonrası **yeniden türetilecek** (chunk düzeyi gömme türevleri) ·
> `AÇIK` = ölçüm sırada.

---

## A. Ana bulgu — arenanın doğruluğu çakışmasız sorulardan geliyor

**İddia.** MemoryAgentBench `Conflict_Resolution` arenasında manşet doğruluk,
çakışma **içermeyen** sorulardan geliyor; çakışan sorularda model, istem açıkça
"büyük seri numarası daha yeni" dese de **bayat (superseded) değeri** üretiyor.

| ölçüm | sh_6k | sh_32k | sh_64k | sh_262k |
|---|---|---|---|---|
| çakışmayan soru (n) | 26 | 35 | 34 | 21 |
| çakışan soru (n) | 74 | 65 | 66 | 77 (+2 eşleşmeyen) |
| **çakışmayan doğruluk** | **26/26 — 8 koşunun 8'inde** | — | — | — |
| **çakışan doğruluk** | **0–5 / 74** | — | — | — |
| manşet doğruluk (m3) | 0.330 | 0.470 | 0.440 | 0.200 |
| **ima edilen çakışan-only** | **0.095** | 0.185 | 0.152 | ~0 (varsayım ihlali işaretli) |

**Hata taksonomisi (8 koşu, 575 çakışan-soru hatası):** 572 `stale_value`,
3 `off_list`, **0 boş**. Model bağlamı okuyor; kuralı uygulamıyor.

- **Kanıt:** `stage0_results/question_strata.json`, `hnav/labeling/question_strata.py`,
  `stage0_results/t4_s2_evidence/sh_6k_{off,offA,offB,shadow,detA..detD}_results.json`.
  Yeniden hesaplanan notlar koşuların kendi `substring_exact_match` alanıyla **800/800** uyuşuyor.
- **Doğrulama:** iki kez bağımsız (orkestratör betiği → üretim modülü); modülde
  negatif kontroller (yanlış etiketli fixture, "aynı değer iki kez ≠ çakışma",
  "başka anahtarın değeri ≠ stale") ve `gold_rule.py` sırasıyla çapraz oracle.
- **Sınırlılık:** doğrudan ölçüm yalnız sh_6k'da (diğer üç subset için
  çakışmayan-soru-hep-doğru varsayımıyla ima edilir; sh_262k'da varsayım **ihlal
  ediliyor** ve dosyada işaretli). Tek model (Qwen3-4B-Instruct-2507), tek arena.
- **Durum: KESİN.**

**Neden önemli:** (1) bu arenayı kullanan her çalışmanın manşet sayısı büyük
ölçüde çakışmasız soruları ölçüyor; (2) açık talimatla verilen supersession
kuralı ~%95 işlemiyor — bellek yönetişimi için doğrudan motivasyon; (3) tavan
gerçek ve büyük (sh_6k'da 100 sorunun 71'i yanlış, **tek** hata kipi).

**Açık ayrım (probe ölçecek):** bayat değeri vermesinin nedeni *konum/varlık*
mı (bağlamdaki bayat kayda tutunma) yoksa *parametrik öncelik* mi (dünya
bilgisinin bağlamı ezmesi — bayat değerler çoğunlukla dünya-doğrusu). Bu ayrım,
herhangi bir okuma-yolu müdahalesinin işe yarayıp yaramayacağını belirler.
`hnav/stage1/stale_suppression_probe.py` (yazıldı, 938 çağrı, kutu bekliyor).

---

## B. Metodolojik katkı — NLI tek başına bellek çakışmasını doğrulayamaz

**İddia.** Çift yönlü NLI çelişki skoru, bellek çakışması doğrulaması için
**tek başına yetersiz**: aynı şablon/farklı özne çiftlerini çelişki sayıyor.
Ayrıştırılmış **özne-kimliği elemesi** eklendiğinde yanlış-doğrulama sıfırlanıyor.

| yapılandırma | yanlış-doğrulanan çift oranı |
|---|---|
| yalnız çift yönlü NLI (cos 0.90, dondurulmuş r) | **0.933** (12.896 farklı-anahtar / 923 gerçek supersession) |
| yalnız çift yönlü NLI (cos 0.94) | 0.33–0.39 |
| **+ `same_key_pair` özne elemesi** | **0.000 — 162 hücrenin hepsinde, precision 1.00** |

Örnek (gerçek model, box'ta ölçüldü): *"Thomas Kyd was born in the city of
London."* vs *"Marlowe was born in the city of London."* → çelişki **0.99949 /
0.99983**, iki yönde de. Mantıken çelişmeyen iki olgu.

- **Kanıt:** T11 kalibrasyon çıktısı + `hnav/adapters/mab_adapter.py`
  (`same_key_pair`), `hnav/core/read_gate.py` (çift yönlü kapı), supervisor
  denetim kaydı (bağımsız box probe'u).
- **Sınırlılık:** eleme, ayrıştırılabilir özne gerektirir (bu arenada
  `conflict_analysis.parse`, %99.4+ kapsam); serbest metin bellekte karşılığı
  ayrıca tasarlanmalı.
- **Durum: SAĞLAM.** Diğer tüm sonuçlardan bağımsız; RAG bellek sistemlerine
  doğrudan aktarılabilir.

---

## C. Doğrulanmış tespit katmanı (Stage-0)

| bileşen | sonuç | durum |
|---|---|---|
| Geometri öncülü (M1) | çakışan çift medyan benzerlik **0.964** vs kontrol **0.60**; **AUC ≥ 0.9999** 4/4 subset | SAĞLAM (fact düzeyi — kesmeden etkilenmez) |
| Geometrik gruplama (M1b) | best-F1 **0.892** (sh_6k, τ=0.91) → **0.757** (sh_262k, τ=0.95); precision 0.83–0.90 | SAĞLAM (fact düzeyi) |
| Replika sadakati (M0) | **top-1 = top-k = Kendall τ = 1.0000**, maks skor hatası ≤ 4.5e-5, 400/400 çift | KESİN (benchmark'ın kendi vektörleriyle) |
| Sinyal dejenerasyonu (M2) | **NOT_DEGENERATE 4/4** — önceki BFCL dejenerasyon bulgusunu çürütür | GEÇİCİ (chunk düzeyi) |
| Gölge nötrlüğü (T4/S2) | off↔shadow %2.42 < off↔off %3.04; TOST ±2.0 eşdeğerlik (p=0.0008/0.017) | SAĞLAM |
| Ayrıştırıcı kapsamı | %99.44–99.65 | KESİN |

---

## D. Substrat bulguları (metodoloji katkısı)

**D1 — bf16 gömme hassasiyeti retrieval sadakatini sessizce yok ediyor.**
Aynı embedder bf16 servis edildiğinde top-k sıra özdeşliği **0.24**'e düştü;
float32'de **1.0000**. Mekanizma: birim-norm sapması ±2e-3, dot-product
sıralamasının L2 ile özdeşliğini beraberlik ölçeğinde bozuyor.
Kanıt: `stage0_results/final/m0_replica_fidelity.GATE_20260814_bf16.json` (öncesi)
+ `m0_replica_fidelity.json` (sonrası). **Durum: KESİN.**

**D2 — vLLM temperature=0'da koşudan koşuya deterministik değil.**
Çıktı uyuşmazlığı ortalama **%3.0** (maks %9); özdeş iki baseline koşusu arasında
exact-match **26.0 vs 30.0** (4 puan). Ön-kayıtlı TOST protokolüyle ölçüldü
(10 off + 5 shadow koşu). **Yeni incelik:** gürültü **tamamen çakışan soru
katmanında** — 28 koşu-çiftinde çakışmayan soruda **sıfır** çevirme.
Kanıt: `stage0_results/t4_s2_trials_summary.json`, `t4_s2_protocol.md`,
`question_strata.json`. **Durum: KESİN.**
*Sonuç:* bu literatürdeki tek-koşu benchmark iddiaları bu bandın içinde.

**D3 — 512-token kesme tuzağı (kendi kusurumuz, düzeltildi).**
`build_embedder` dört konumsal argüman geçtiği için `max_length=512` hiç
ezilmiyordu; chunk'lar ~4096 token (ölçülen en büyük kalibrasyon chunk'ı
**4.333** tiktoken). Yani chunk düzeyi sinyaller metnin ilk ~%12'sinden
hesaplanmış. M0'ın 1.0000 sadakati bunu **kapsamıyordu** (benchmark'ın kendi
vektörlerini yeniden kullanıyor). Düzeltme `5240774`: `DEFAULT_MAX_LENGTH=8192`,
tüm argümanlar anahtar kelimeyle, **cache namespace'e `L{max_length}` eklendi**
(aksi hâlde 24k kesilmiş vektör geri okunur ve düzeltme "değişiklik yok" ölçerdi).
**Durum: KESİN (kusur ve düzeltme); türevleri GEÇİCİ.**
*Raporlanabilir ders:* gömme boru hattında sessiz kesme + içerik-adresli cache,
düzeltmeyi de görünmez kılar; cache anahtarı her parametreyi taşımalı.

---

## E. CrossEp-Know yazma tarafı yapısal olarak farklı

Byte-özdeş yinelenen yazma oranı (küme-ortalaması, **cluster-first**):
**0.117 kalibrasyon / 0.072 held-out**, 120 bağlamın 89'unda mevcut, en kötü
küme **0.706**; lexical Jaccard ≥0.9 oranı 0.164/0.112. Karşılaştırma:
MemoryAgentBench'te `duplicate_rate` **0.000** her yerde.
Mekanizma tanımlı: her örneğin yörüngesi bağlamın ortak System Context bloğunu
yeniden chunk'lıyor.

- **Kanıt:** `stage0_results/crossep/m5_crossep_write_headroom_qwen3_embedding_SMOKE.json`,
  `CROSSEP_HEADROOM_RAPORU.md`. MD5 ve Jaccard **embedder-bağımsız** → smoke
  koşusuna rağmen gerçek; kesme düzeltmesinden etkilenmez.
- **Doğrulama:** supervisor bağımsız yeniden saydı (en kötü küme 89/126 = 0.7063,
  ham JSONL'den gerçek chunker ile).
- **Sınırlılık:** anlamsal yakın-yineleme ve çelişki eksenleri henüz ölçülmedi
  (gerçek-embedder M5 koşusu sırada); split 48/72 **küme** (ICC 0.346, etkin
  N ≈ 276/884) — güç küme-öncelikli hesaplanmalı.
- **Durum: SAĞLAM (exact-dup ekseni), AÇIK (anlamsal eksen).**

---

## F. Dürüst olumsuz sonuçlar (tezde yer alacak)

1. **Yazma-yolu müdahale tavanı ≈ 0 (MAB).** Veto sonrası müdahale oranı
   %0–1.6; doğrulama subset'inde (sh_64k) could-change-correctness **0.00**.
   → `write_policy` KALICI NO_GO. `KAPI_KARARI.md` §2.
2. **H2 marginal-diff testi ön-kayıtlı konjonksiyonu geçemedi** — düşen koşul
   LRT **p = 0.341** (yön pozitif: in-sample Δauc +0.0674, CV +0.1185).
   `stage0_results/final/m4_marginal_diff_test.json`.
3. **Chunk düzeyi YUKARI rerank net fayda vermedi** — 162 kapı işletim
   noktasında, hücre başına 68–115 sıra-değişen soruda. **Dar okuma zorunlu:**
   kalibrasyon split'inde retrieval zaten eksiksiz (n_chunks 2/9 ≤ top_k 10),
   dolayısıyla bu, "H-Nav çalışmıyor" değil "tek yönlü chunk permütasyonu bu
   koşulda kaldıraçsız" demektir. Güç analizi de zayıf (aşağıda).
4. **Kalibrasyon hedefinin gücü yetersizdi.** Ölçülen %3.3/soru gürültü
   tabanında, hedef saf gürültü altında ~%35 yanlış-pozitif veriyor ve mükemmel
   bir müdahaleye karşı bile ~%81'de doyuyor; 162 hücre ~1–3 bağımsız teste
   denk. → sh_64k ön-kaydı **geri çekildi** (`stage0_results/stage1_preregistration.md`,
   WITHDRAWN, gerekçeli).
5. **Kendi eşiğimizin kusuru: `H_Z_CAL` bir mağaza-boyutu dedektörü.**
   n_chunks=2'de entropi tavanı `ln 2 = 0.693`; dondurulmuş eşik **1.9569** →
   sh_6k'da **hiçbir zaman** ateşleyemez (m2 sh_6k `min=max=p50=0.36533`).
   Ayrıca pooled percentile ile fit edilmiş, deponun kendi "stratify, never
   pool" kuralına aykırı. Yeniden türetme sırada, **subset başına**.

---

## G. Bugün iddia EDİLEMEYENLER

- ❌ **"H-Nav doğruluğu artırır."** Depoda hiçbir pozitif müdahale sonucu yok.
- ❌ "H-Nav'ın okuma-yolu müdahalesi işe yaramaz." Test edilen tek mekanizma
  (tek yönlü chunk rerank) kaldıracın olmadığı bir split'te, güçsüz bir hedefle
  denendi. Bunu H-Nav hakkında olumsuz sonuç diye yazmak yanlış-olumsuz olur.
- ❌ m3'ün sh_64k `+6/−1` enjeksiyon sonucu bir "sonuç" değil: tek tekrarsız
  koşu, benchmark'ın kendi istemi değil, ±3 çevirme gürültüsü, ve 7 chunker
  artefaktı enjeksiyonuyla kirli.
- ❌ Kalibrasyondan sh_64k/sh_262k'ya çıkarım. Dondurulmuş `H_z` eşiği bile
  subset'ler arası %0 / ~%50 / >%90 / %100 ateşliyor.

---

## H. Tavsiye edilen tez omurgası (bugünkü kanıtla)

**Ölçüm ve yönetişim katkısı** (A + B + C + D), **artı** açık bir müdahale
sorusu (probe sonucuna göre E veya A'nın devamı):

> H-Nav, bellek çakışması geometrisi için araçlandırılmış ve doğrulanmış bir
> tespit katmanıdır. Kanonik çakışma-çözümü arenasına uygulandığında, katmanın
> kendi ölçümleri arenanın manşet doğruluğunun çakışmasız sorulardan geldiğini
> ve modelin açık supersession talimatını ~%95 uygulamadığını gösterir. Bu,
> bellek yönetişiminin *nerede* gerekli olduğunu tanımlar. Yol boyunca: NLI'nin
> tek başına çakışma doğrulayıcısı olarak %33–93 yanlış-doğruladığı ve özne
> elemesiyle 0.000'a indiği; bf16 servisin retrieval sadakatini sessizce yok
> ettiği; ve değerlendirme substratının ±2–4 puan gürültü taşıdığı ölçülmüştür.

Bunu bir **iyileştirme** iddiasına çevirmek için tek gereken: probe'un
"bastırma/yerleşim tavanı" ölçümü pozitif çıkarsa, o mekanizmanın yeni bir
ön-kayıtla doğrulanması.
