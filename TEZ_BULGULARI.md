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
| çakışmayan soru (n) | 26 | 35 | 34 | 22 |
| çakışan soru (n) | 74 | 65 | 66 | 76 (+2 eşleşmeyen) |
| **çakışmayan doğruluk** | **26/26 — 8 koşunun 8'inde** | — | — | — |
| **çakışan doğruluk** | **0–5 / 74** | — | — | — |
| manşet doğruluk (m3) | 0.330 | 0.470 | 0.440 | 0.200 |
| **çakışan-only doğruluk** | **0.095** `estimate` | **[0.185, 0.723]** `bound` | **[0.152, 0.667]** `bound` | **[0.000, 0.263]** `bound` |

> **Neden yalnız sh_6k nokta tahmin:** "çakışmayan soru hep doğru" öncülü
> **yalnız sh_6k'da ölçüldü** (26/26, 8 koşu). Diğerlerinde öncül ölçülmedi,
> sh_262k'da ise **çürütüldü** (`assumption_refuted: true`; öncül doğru olsaydı
> ima edilen değer negatif çıkardı — yani öncülün yanlışlığının kanıtı).
> Varsayımsız savunulabilir ifade **aralıktır**; sh_262k için çakışmayan
> doğruluk üst sınırı 20/22 = 0.909. Negatif bir olasılık yayımlamak tüm
> ekstrapolasyonu haklı olarak şüpheye açardı — bu yüzden `question_strata.json`
> `kind: estimate|bound` alanını **yapısal** olarak taşır, negatif değer
> üretilemez. Ayrıca ima/sınır satırları m3 harness istemiyle ölçülmüştür
> (benchmark'ın şablonlu sorgusu değil); doğrudan ölçüm yalnız sh_6k'dadır.

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

## A2. TAVAN ÖLÇÜLDÜ — bayat kaydı bastırmak çakışan soru doğruluğunu 5–10× artırıyor

**İddia.** A'daki hata kipi **düzeltilebilirdir**: bağlamdan bayat kayıt
çıkarıldığında model doğru cevabı veriyor. Yani başarısızlık "modelin dünya
bilgisini bağlama tercih etmesi" (parametrik öncelik) DEĞİL, **bağlamdaki bayat
kaydın varlığına/konumuna tutunmadır**.

Oracle probe, gerçek model + benchmark'ın kendi istemi + dondurulmuş `:8003`
substratı, yalnız kalibrasyon split'i (938 çağrı):

| kol | sh_6k genel | sh_6k çakışan | sh_32k genel | sh_32k çakışan | McNemar |
|---|---|---|---|---|---|
| native | 0.290 | 4/74 (%5.4) | 0.420 | 7/65 (%10.8) | — |
| A/A tabanı (native_repeat) | 0.290 | 4/74 | 0.420 | 7/65 | **0/0 uyuşmazlık, iki subset'te de** |
| **oracle_suppress** (bayatı sil) | **0.910** | **66/74 (%89.2)** | **0.880** | **53/65 (%81.5)** | +62 (p=4e-19) · +46 (p=3e-14) |
| **oracle_recency** (LATEST'i sona al) | 0.460 | 20/74 (%27.0) | 0.680 | 33/65 (%50.8) | +17 (p=8e-05) · +26 (p=9e-07) |
| anti (LATEST'i başa al) | 0.260 | 1/74 (%1.4) | 0.380 | 4/65 (%6.2) | −3 · −4, anlamsız |

- **Kanıt:** `stage0_results/stage1/stale_suppression_probe_{sh6k,sh32k}.json`,
  `hnav/stage1/stale_suppression_probe.py` (34 test).
- **Koruyucu koşul sağlanıyor:** çakışmayan katman iki yardım kolunda da
  **bozulmuyor** (25/26 ve 35/35 korunuyor) → bu katmanda zarar sıfır.
- **`oracle_recency` token-nötrdür** — hiçbir bilgi silinmez, yalnız konum
  değişir; yine de çakışan doğruluğu 5× (sh_6k) ve 4.7× (sh_32k) artırır.
- **Mekanizma:** çapa **geç konumdur**. LATEST'i sona almak yardım ediyor, başa
  almak (anti) zarar veriyor. Bu, T11'de chunk düzeyi **yukarı** rerank'in neden
  sistematik zararlı olduğunu da açıklar (bkz. `STAGE1_NULL_ANALIZI.md`):
  superseder'ı yardım eden konumdan **uzaklaştırıyordu**, üstelik ~250 olgu
  taşıyan bir chunk granülerliğinde.
- **Sınırlılık (kritik):** bu kollar **oracle**'dır — sorunun anahtarını gold ile
  belirler. Sevk edilebilir politika yalnız dedektör çıktısını kullanabilir;
  **oracle→dedektör boşluğu** ayrıca ölçülmelidir (T13, koşuyor). Tavan budur,
  elde edilen değil.
- **Durum: KESİN (tavan olarak).** Kalibrasyon split'inde iki kez replike;
  sh_64k/sh_262k'ya dokunulmadı.

---

## A3. TAVANIN ~%96–98'i DEDEKTÖRLE, GOLD OLMADAN YAKALANDI

**İddia.** A2'deki tavan oracle'dı (anahtar gold ile belirleniyordu). Aynı
müdahale, **yalnız dedektör çıktısıyla** (gold yok, cevap yok, gelecek olgu yok)
sürüldüğünde tavanın neredeyse tamamı korunuyor — üstelik **daha az token**
harcayarak.

| subset | native | **detector_suppress** | çakışan katman | McNemar | token | dedektör/oracle |
|---|---|---|---|---|---|---|
| sh_6k | 0.290 | **0.900** | 4/74 → **66/74 (%89.2)** | +61, p=1.4e-17 | **−%3.48** | net 61/62 = **0.984**, çakışan kazanç **1.000** |
| sh_32k | 0.420 | **0.860** | 7/65 → **51/65 (%78.5)** | +44, p=1.3e-12 | **−%0.63** | net 44/46 = **0.957** |

- **A/A tabanı yine 0/0 uyuşmazlık** (iki subset), native kolu bağımsız probe
  koşusuyla ve 8 tarihsel koşuyla tutarlı.
- **Koruyucu koşul (tam ve dürüst hâli):** sh_32k'da çakışmayan katman
  **35/35 korunuyor, 0/0 uyuşmazlık**. sh_6k'da **25/26 → 24/26**: tek kayıp,
  gold olgusu silindiği için değil (sh_6k gold-cut = 0), modelin doğru varlığı
  bozuk üretmesi yüzündendir ("Shinzō Abe" → "Sinzō Abe"). Değerlendirici bunu
  yine de kayıp sayar; bu yüzden "zarar sıfır" değil, **"zarar 1/26 ve nedeni
  müdahale değil substrat üretimi"** denmelidir.
- **Yanlışlama kontrolü tutarsız:** `anti` kolu sh_6k'da beklendiği gibi zarar
  verdi (−4) ama sh_32k'da **yardım etti** (+6, p=0.21). Konum hikâyesini
  zayıflatan bu tutarsızlık raporda açıkça yazılmalıdır.
- **Gold'u dedektörle değiştirmenin toplam bedeli 1.000 çağrıda iki çevirmedir.**
- **Dedektör kalitesi (işletim noktası: cos_pair 0.90 · r_min 0.44 ·
  ambiguity none · nli 0.90 · pair_filter True; LLM/gold/doğruluk görmeden
  dondurulmuştur):** çift precision **1.0000** (2.673 doğrulanmış çift, 0 yanlış),
  çakışan-soru recall **133/139 = 0.957**, **bir anahtarın güncel değerini taşıyan
  0 olgu silindi**. `pair_filter=False` yarısında medyan precision 0.137 ve
  medyan hücre 769 güncel-değer olgusunu silerdi — eleme tercih değil,
  zorunluluktur.
- **Beyan edilen sapma:** `ambiguity_mode="none"`, dondurulmuş Stage-0
  `nmargin`/`H_z` ekranını devre dışı bırakır; gerekçe, bunların **512-token
  kesme kusurundan etkilenen tek kapı girdisi** olması ve recall'u 0.957 → 0.403
  → 0.144 boğmasıdır. Politika bu durumda **her soruda** ateşler; kalibrasyonda
  precision 1.00 ile güvenli, ama held-out'ta ayrıca gerekçelendirilmelidir.
- **Bilinen, sayılabilir hata kipi:** gold en yüksek seri değilse dedektör
  gold'lu olguyu siler (kalibrasyonda 2/200; `gold_rule`'a göre sh_262k'da
  73/77 gold-LATEST olduğundan oran orada daha yüksek). Ön-kayda **sayıyla**
  girecek.
- **Kanıt:** `stage0_results/stage1/detector_gap_{sh6k,sh32k}.json`,
  `stage0_results/stage1_operating_point.json`, `hnav/BUILD_NOTES.md` §11,
  409 test.
- **Durum: SAĞLAM (kalibrasyon split'i).** Held-out (sh_64k) tek-atışlık
  doğrulama ön-kayıtla ve denetim sonrası yapılacak.

**Bu ne demek:** kalibrasyon split'inde H-Nav, gold'suz bir dedektörle,
doğruluğu **+61 ve +44 puan** artırıyor, **token harcamasını düşürüyor** ve
korunması gereken katmanda zararı ≤1/26 (nedeni müdahale değil) tutuyor —
tezin üç başarı ölçütü (doğruluk ↑, token verimliliği ↑, harm ≈ 0) aynı anda
sağlanmış durumda. Eksik olan tek şey held-out doğrulamadır.

> **KAPSAM UYARISI (denetçi notu 2 — raporda öne çıkarılacak).** Bu deney
> **bütün-bağlam** koşumudur: istem `Memory 1: <tüm bağlam>` biçimindedir,
> retrieval boru hattının top-10 sayfası değil. Bu, oracle/dedektör oranını
> anlamlı kılan doğru tasarımdır; ama **sevk yolu (`apply_read_decision` ile
> alınan sayfanın düzenlenmesi) doğruluk açısından henüz ölçülmemiştir** —
> yalnız doğruluğu (correctness) test edilmiştir. Dış denetçinin soracağı ilk
> soru budur; keşifsel bir retrieval-yolu kolu ayrıca koşulup **ayrı** olarak
> raporlanacaktır.
>
> **Ayrıca:** işletim noktasında `nmargin`/`H_z` ekranı kapalı olduğu için
> politika **her soruda** değerlendirme yapar; dolayısıyla sevk edilen mekanizma
> "H-Nav'ın dondurulmuş Stage-0 kapısı" DEĞİL, "olgu-düzeyi çakışma dedektörü
> (çift kosinüsü + span artığı + ayrıştırılmış özne elemesi + çift yönlü NLI),
> koşulsuz uygulanmış" hâlidir. Yükü taşıyan şey precision 1.00'dır, kapı
> değildir; ön-koşul katmanı bu konfigürasyonda **doğrulanmamıştır**.

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

- ❌ **"H-Nav doğruluğu artırır."** — *nitelikli:* müdahale **tavanı** artık
  ölçülmüştür (A2: bastırma ile çakışan doğruluk %5.4→%89.2 / %10.8→%81.5,
  yerleşimle token-nötr olarak %27 / %50.8). Ancak bunlar **oracle** kollardır;
  dedektör-tahrikli politikanın bu tavanın ne kadarını yakaladığı ölçülene ve
  ön-kayıtlı doğrulama koşulana kadar "H-Nav doğruluğu artırır" denemez.
  Bugün denilebilecek olan: **"arenanın hata kipi düzeltilebilirdir ve tavanı
  büyüktür."**
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
