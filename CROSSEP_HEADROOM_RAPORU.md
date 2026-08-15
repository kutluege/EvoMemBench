# CROSSEP HEADROOM RAPORU — Yazı-Yolu Enstrümantasyon Onarımı + M5 Ön Ölçümü (T10)

> Dayanak: `HNAV_VISION_GAP.md` §4 adım 4 — "CrossEp instrumentation repair +
> write-side headroom measurement — MEASUREMENT ONLY, NO POLICY". Adım 5-6
> (yazı-kaskadı politikası, arşiv) bu ölçümün besleyeceği **[GATE] insan
> kararının arkasında** ve bu çalışmada İNŞA EDİLMEMİŞTİR.
> Veri: `stage0_results/crossep/m5_crossep_write_headroom_qwen3_embedding_SMOKE.json`
> (box'ta koşuldu, gerçek chunker, `fallback_chunker: false`).

---

## 1. Ne onarıldı: ikincil arenanın kör noktası

`CLBenchAdapter.on_extract` T4'ten beri `geometry=None, diff=None,
retrieval_effect=None` sabitliyordu — modüller enjekte edilse bile ikincil
arena **sıfır yazı-yolu sinyali** üretiyordu. T10 ile:

| Onarım | Detay |
|---|---|
| Sinyal kablolama | `on_extract` artık geometry (sim_max / QR novelty / MD5 exact-dup), nearest-neighbour marginal diff ve provisional-insert etkisini (aday-kendi-probu) hesaplayıp logluyor. Karar değişmedi: koşulsuz `PASS`, `shadow=True`. |
| Uzay tutarlılığı | Native banka vektörleri DashScope text-embedding-v4 (1024d); H-Nav aday vektörü kendi embedder'ından (2560d). Eski kod ikisini çarpsaydı boyut hatası fırlatıp sessizce yutulacaktı. Şimdi banka metinleri adapter'ın KENDİ uzayına memoize edilerek yeniden gömülüyor; hangi uzayın kullanıldığı her kayıtta `bank_space` olarak yazılıyor. `on_retrieve` aynı düzeltmeyi aldı (aynı karışık-uzay tuzağı okuma yolunda da vardı). |
| `context_id` kümeleme | Runner `extract`'a `context_id` geçirmiyor; wrapper bunu backend'in bağlam-başına `memory_dir` adından geri kazanıyor. İç `extract` çağrısına TEK bir ekstra kwarg sızmıyor (test ile sabitlendi). |
| Shadow yasallığı | LLM çağrısı yok (embedder chat modeli değildir), store mutasyonu yok, dönüş nesnesi kimlik (`is`) ile aynı, off modu birebir kimlik. |

Testler kapalı-form standardında (`hnav/tests/test_crossep_adapter_signals.py`):
sim_max/argmax bağımsız numpy kosinüsle, QR artığı **farklı algoritmayla**
(SVD projeksiyonu) doğrulanıyor; MD5 dup iki yazı arasında; karışık-uzay
bankası çökmeden hnav uzayında ölçülüyor; wrapper bayt-nötrlüğü tam modül
enjeksiyonuyla sabitleniyor. **Suite: 175 → 196 test, tümü yeşil (lokal +
box).** Leakage audit ve no-torch-at-import değişmeden geçiyor.

## 2. MemOS triyajı — SONUÇ: kapsam dışı (belgeli)

Kök neden ~10 dakikada bulundu, kesin:

- Depo kökü `.gitignore:90` `memories/` deseni (benchmark'ın çalışma-zamanı
  çıktı klasörleri için konmuş) `EvoMemBench-Memory-Systems/MemOS/src/memos/memories/`
  alt paketini de yutuyor: `git check-ignore` bunu `.gitignore:90` ile
  eşliyor ve `git log --all` o yol için hiç commit göstermiyor — paket
  vendoring anında **hiç commit edilmemiş**. `memos_memory.py`'nin ihtiyacı
  (`memos.memories.factory`, `memos.configs.memory`) bu yüzden her checkout'ta
  `ImportError` → `registry._MEMOS_AVAILABLE=False`.
- Ucuz düzeltme (istenirse): `.gitignore`'a
  `!EvoMemBench-Memory-Systems/MemOS/src/memos/memories/` negasyonu + upstream
  MemOS v2.0.9'dan (`src/memos/__init__.py` sürümüyle eşleşen tag)
  `src/memos/memories/` klasörünü kopyalayıp commit; box'ta
  `pip install -e EvoMemBench-Memory-Systems/MemOS`. Tahmini 15-30 dk + ağ.
- **Kapsam dışı bırakma gerekçesi:** import düzelse bile MemOS'un yazı akışı
  LLM-ekstraksiyonlu (`extractor_llm`) — mem0 ile aynı replay maliyeti — ve
  depoda/box'ta hiç MemOS koşu artefaktı yok. M5'in `generic_jsonl` okuyucusu
  ileride bir MemOS capture'ı geldiğinde ölçümü dosya-bırakma mesafesine
  getiriyor. Vendoring düzeltmesi bu ölçümün ön koşulu değil.

## 3. Serbest-metin probe stratejisi (karar) + kalibrasyon split'i

**Probe kararı:** CrossEp adaylarında key/serial/relation şablonu yok; probe,
**adayın kendi metni** (`simulate_insert`'in belgeli varsayılanı,
`replica.py`). Etki özeti: `rank_self_after` + komşuluk yer değiştirme
istatistikleri (`churn@k`, `rank_shift`, `dH_self`). Ek olarak öncül
(predecessor) **en yakın komşu** ile çözülüyor (karar-anı bilgisi; ileri bakış
yok). Benchmark değerlendirme verisinden türetilmiş hiçbir şey adapter yoluna
girmiyor — AST taraması (`test_leakage_audit.py`) adapters'ı kapsamaya devam
ediyor ve yeşil.

**Split (dondurulmuş artefakt):** `hnav/labeling/crossep_split.json` +
türetici `hnav/labeling/crossep_split.py`:

- Birim **küme = `context_id`** (ICC 0.346, design effect 3.20, etkin
  N ≈ 276/884 — örneklem-düzeyi split sızdırır).
- `context_category` içinde tabakalı, seed `20260815`, küme sayısının %40'ı
  kalibrasyona: **48 kalibrasyon / 72 held-out küme; 347 / 537 örneklem.**
  Tek kümeli kategori held-out'a gider.
- Test (`test_crossep_split.py`): commit edilen artefakt taze türetimle alan
  alan karşılaştırılıyor; ayrıklık, tamlık, oran ve tabakalama sabit.
- **Kural:** CrossEp için herhangi bir eşik YALNIZ kalibrasyon kümelerinde
  fit edilebilir. M5 hiçbir eşik fit etmez (ölçüm-yalnız); grid noktalarında
  oran raporlamak betimseldir, fit değildir.

## 4. M5 ölçümü — ne koşuldu, ne koşulamadı

`hnav/stage0/crossep_m5_write_headroom.py`: bağlam-başına yazı akışını
T10-kablolu shadow enstrümantasyondan geçirir; **backend × split × küme**
tabakalı raporlar; agregatlar KÜME-ÖNCE (per-cluster istatistiklerin
ortalaması/medyanı) — aday-düzeyi havuzlama asla.

**Koşulan (box, CPU, gerçek chunker, HashEmbedder smoke):**
`qwen3_embedding_4b` backend'inin yazı akışı, `context_nomemory` çıktısından
birebir yeniden kuruldu (query + trajectory serileştirme + 1024-token cümle
chunker'ı transkript; `fallback_chunker: false`). 120 bağlam, **7.879 yazı
olayı** (küme başına 32-250). Smoke'ta **MD5 exact-dup ve leksik Jaccard
embedder'dan bağımsızdır ve GERÇEKTİR**; kosinüs-tabanlı her sayı anlamsızdır
ve `_SMOKE` dosyasında işaretlidir.

**Koşulamayan ve nedeni:**

| Ölçüm | Durum | Neden / maliyet |
|---|---|---|
| Gerçek sim_max dağılımları (semantik near-dup) | GPU bekliyor | Qwen3-Embedding-4B fp32, `max_length=8192`; ~7,9k chunk + ~15,8k diff-span gömme. **Tahmin: ≈0,6-1,0 GPU-saat** (T12 sonrası revize — §9.1/2; diff dahil, `--no-diff` ile ≈0,3-0,5). Cache'e ~240MB ekler; T12 ad alanı değişikliği nedeniyle eski 24k MAB girdisi okunmaz (CrossEp metinleri zaten cache'te değildi). Orkestratör planlasın — kendi başıma başlatmadım (GPU1 bu hafta sonu Thrust 1'in). |
| NLI çelişki taban oranları | GPU koşusuyla birlikte | Model box'ta hazır (`cross-encoder/nli-deberta-v3-large`, Faz A'nın indirdiği ağırlıklar — yeniden kullanılıyor). Çift seçimi sim_max'a bağlı olduğundan smoke'ta koşmak yanıltıcı olurdu; gerçek-embedder koşusunda `--nli cpu` (~10-15 dk CPU) veya GPU'da ~1 dk, ön-tanımlı `--nli-splits calibration`. |
| mem0 yazı akışı | Artefakt yok | mem0 akışı LLM-ekstraksiyonlu; hiç mem0 CrossEp koşusu yapılmamış (box'ta `memories/` boş). `iter_mem0_history` hazır: herhangi bir koşunun `history.db`'sinden ADD olaylarını sırayla okur (sentetik sqlite ile test edildi). Bir mem0 koşusu = DeepSeek API maliyeti + saatler → [GATE] öncesi orkestratör kararı. |
| A-mem yazı akışı | Capture gerek | CL-bench A-mem sarmalayıcısı store'u persist etmiyor (in-memory Chroma); akış ancak koşu anında capture edilebilir → `generic_jsonl` okuyucusu bu amaçla var. |

## 5. Headroom göstergeleri — MAB'ın %0-1,6'sının aksine ölçülebilir alan var mı?

**Ön cevap (dedup ekseni, embedder'sız kanıtla): EVET — substrat yapısal
olarak MAB'dan farklı.** MAB Stage-0'da `duplicate_rate` her yerde **0.000**
ölçülmüştü ve veto sonrası müdahale tavanı %0-1,6 idi. CrossEp
`qwen3_embedding` akışında:

| Gösterge (küme-önce ortalama) | Kalibrasyon (48 küme) | Held-out (72 küme) |
|---|---|---|
| **MD5 exact-dup oranı** | **0.117** | **0.072** |
| exact-dup'lı küme sayısı | 38/48 | 51/72 |
| en kötü küme exact-dup | 0.496 | 0.706 |
| Jaccard ≥ 0.90 (leksik near-dup) | 0.164 | 0.112 |
| Jaccard ≥ 0.70 | 0.265 | 0.219 |
| Jaccard ≥ 0.50 | 0.431 | 0.389 |
| Jaccard p50 (küme p50'lerinin ort.) | 0.425 | 0.351 |

> **T12 embedding düzeltmesinden etkilenmezlik (denetim notu).** Thrust 1
> `5240774` ile 512-token kesme kusurunu düzeltti ve embedding cache ad
> alanını değiştirdi. Yukarıdaki tablodaki **tüm manşet sayıları
> embedder'dan BAĞIMSIZDIR**: MD5 exact-dup ham metnin hash'idir, leksik
> Jaccard kelime kümesi üzerindedir — ikisi de HashEmbedder/Qwen ayrımına ve
> `max_length`'e duyarsızdır. Dolayısıyla commit edilmiş SMOKE ölçümü
> (`stage0_results/crossep/…_SMOKE.json`) ve §5'in dedup bulgusu **geçerli
> kalır, yeniden koşulması gerekmez.** Etkilenen tek şey o dosyadaki
> kosinüs-tabanlı alanlardır — zaten `SMOKE_HASH_EMBEDDER: true` ile
> anlamsız işaretli ve hiçbir iddiaya girmiyorlar. Gerçek kosinüs eksenleri
> §9.1 koşusuyla, T12 sonrası ad alanında ölçülecek.

Mekanizma açık: her örneklemin trajektorisi bağlamın **aynı System Context
bloğunu** yeniden içeriyor; chunker bunu her yazıda yeniden kesip bankaya
koyuyor. Küme başına 5-12 örneklem × ~1-3 sistem-bloğu chunk'ı ⇒ yazıların
~%7-12'si bayt-özdeş, ~%11-27'si ağır leksik örtüşmeli. Kategori kırılımı
tutarlı (dup ort. 0.068-0.211; en yüksek "Empirical Discovery & Simulation").

**Bu ne DEĞİL:** (1) "Müdahale faydalı olur" iddiası değil — dedup'un
doğruluğa/maliyete çevrilebilirliği ölçülmedi; bu sayılar yalnız *aday
havuzunun* MAB'dan farklı olduğunu gösteriyor. (2) Semantik çelişki/güncelleme
headroom'u değil — o eksen (gerçek sim_max + NLI) GPU koşusunu bekliyor.
(3) mem0/A-mem için hiçbir şey — onların LLM-süzgeçli akışı bambaşka bir
dağılım üretebilir (mem0 zaten kendi dedup/karar katmanını çalıştırır;
beklenti daha DÜŞÜK ham dup, ama ölçülmeden söylenemez).

**[GATE]'e giden okuma:** MAB NO_GO'sunun ampirik temeli ("müdahale edilecek
bir şey yok: dup 0.000, retrieval zaten LATEST'i buluyor") bu substratta
exact-dup ekseninde GEÇERLİ DEĞİL. Yazı-kaskadı sorusu CrossEp'te artık
"ölçülebilir alan var mı" değil, "alan ne kadar ve maliyete/doğruluğa çevrilir
mi" sorusudur — bunun için sıradaki adım §4'teki ≈0,6-1,0 GPU-saatlik gerçek
koşu + NLI taban oranlarıdır. Karar insanındır.

## 6. Çarpışma listesi durumu (HNAV_VISION_GAP §2'den, bu işe düşenler)

1. **BFCL yasağı**: dokunulmadı; tüm iş CrossEp-Know + `hnav/` içinde.
2. **write_policy NO_GO kapsamı**: bu ölçüm NO_GO'yu ne ihlal etti ne
   genişletti — "unmeasured, not authorized" durumundaki CrossEp yazı-kaskadı
   için gereken Stage-0-tarzı kanıtı üretti/üretmeye hazırladı. Hiçbir policy
   modülü yazılmadı; `hnav/core/*policy*.py` yasağı testte yeşil.
3. **Ekstra çıkarım vs shadow nötrlüğü**: adapter yolunda sıfır LLM çağrısı;
   NLI yalnız offline labeling ayrıcalığıyla, M5 içinde ve ön-tanımlı olarak
   kapalı (`--nli off`).
4. **Probe/leakage**: probe = adayın kendisi; sorular/cevaplar/değerlendirme
   alanları hiçbir online yola girmiyor (M5 çıktı kayıtlarından yalnız
   `messages` + `model_output` + `metadata` okur).
5. **Eşik disiplini**: CrossEp kalibrasyon split'i artık VAR (48/72 küme,
   dondurulmuş, testli). M5 eşik fit etmez; grid oranları betimseldir.
6. **V5 substratı**: değişmedi — bu arenada da yıkıcı fiil yok; mem0'ın uyuyan
   update/delete yüzeyi ancak bir mem0 koşusu artefaktıyla anlamlı olur.

## 7. Beyan edilen sapmalar / sınırlar

1. Yazı akışı `context_nomemory` çıktısından yeniden kuruldu: gerçek bellekli
   koşuda `model_output` (ve dolayısıyla trajektori kuyruğu) farklı olurdu.
   System Context tekrarı — dup sinyalinin ana kaynağı — bundan bağımsızdır;
   yine de bellekli-koşu akışıyla doğrulama, gerçek koşu yapıldığında
   bedavaya gelir.
2. Ölçüm uzayı H-Nav embedder'ı (Qwen3-Embedding-4B fp32), native DashScope
   değil — birincil arenanın Stage-0 metodolojisiyle aynı beyanlı sapma.
   `HFEmbedder.max_length=512`, 1024-token chunk'ların ilk ~yarısını görür
   (tekrarlanan sistem-öneki başta olduğundan dup tespiti lehine; beyan edildi).
3. Smoke kosinüs sayıları anlamsızdır; dosya `_SMOKE` eklidir ve
   `SMOKE_HASH_EMBEDDER: true` taşır. MD5 + Jaccard embedder'dan bağımsızdır.
4. Wrapper canlı yolda trajektori-düzeyi aday görür (backend'in chunk'larını
   göremez — adapters benchmark import edemez); M5 chunk-düzeyini transkript
   chunker'la ölçer. İki granülarite karıştırılmaz.
5. `critical_delta_rate_default_tau` MAB varsayılan taularıyla betimseldir;
   CrossEp için kalibre DEĞİLDİR ve hiçbir karara girmez.

## 8. Sıradaki adımlar (orkestratör onayı gerektirenler işaretli)

1. **[GPU-onay → VERİLDİ, box bekleniyor]** Gerçek-embedder M5 — §9.1 runbook.
2. **[Bütçe-onay → VERİLDİ, box bekleniyor]** mem0 CrossEp koşusu (DeepSeek
   API) + ardından M5-mem0 — §9.2 runbook. A-mem için koşu-anı capture →
   `generic_jsonl` (ayrıca yetkilendirilmedi).
3. [GATE] değerlendirmesi: 1-2'nin çıktılarıyla bu rapor güncellenir; yazı-
   kaskadı kararı (VISION_GAP §4 adım 5) İNSANA sunulur.

## 9. RUNBOOK — box geri gelince koşulacak iki tarif

> **HİÇBİR ŞEY orkestratör "box geri" onayı vermeden başlatılmaz.** Box şu an
> erişilemez (ağ kesintisi); watcher kurulu. İki koşu da supervisor/kullanıcı
> onaylı; aşağıdaki tarifler kopyala-yapıştır hazırlığıdır. Not-1 düzeltmesi
> (`0471d2a`) box'a `git pull` ile alınmalı — M5 sayılarını değiştirmez
> (replay zaten bağlam-başına kapsamlıydı) ama aynı ağaçta koşulsun.

### 9.1 Gerçek-embedder M5 (GPU1, ≈0,6-1,0 GPU-saat, ~35-60 dk duvar)

Ön kontrol (sırayla; herhangi biri düşerse DUR):

```bash
ssh egekutlu@ozonderlab2.bogazici.edu.tr
cd /mnt/nvmes/nvme1/egekutlu/EvoMemBench
git pull --ff-only && git log --oneline -1        # >= 5240774 beklenir (T12 truncation fix)
source hnav/deploy/_activate.sh
python -m pytest hnav/tests/ -q                    # tümü yeşil
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader
#   GPU1 boş olmalı (Thrust 1 sh_64k kampanyasıyla ÇAKIŞMA yasak — orkestratör onayı şart)
grep -E "^HNAV_" .env                              # DEPO KÖKÜ .env — M5'in okuduğu dosya
#   beklenen pinler (Supervisor Not-2):
#     HNAV_EMBED_MODEL=Qwen/Qwen3-Embedding-4B
#     HNAV_EMBED_DEVICE=1
#     HNAV_EMBED_DTYPE=float32                   # fp32 pinli — dtype kayması tüm kosinüsleri oynatır
#     HNAV_EMBED_MAX_LENGTH=8192                 # T12 PİNİ — aşağıya bak; .env.template'te YOK,
#                                                #   satır yoksa config varsayılanı 8192 uygulanır
#     HNAV_CACHE_DIR=hnav/_cache
#     HNAV_MODE: off VEYA shadow fark etmez (aşağıdaki nota bak); live ise M5 durur.
ls hnav/_cache/emb | wc -l                         # eski ad alanından ~24k girdi (BU KOŞU OKUMAYACAK)
```

**Cache anahtarı — T12'den sonra DEĞİŞTİ (önceki metin artık geçersiz).**
Thrust 1 (`5240774`) `HFEmbedder`'ın her metni 512 token'da kesen kusurunu
düzeltti (`DEFAULT_MAX_LENGTH = 8192`) ve **ad alanına uzunluğu ekledi** —
aksi halde 24k kesilmiş vektör geri okunur ve düzeltme "etkisiz" ölçülürdü.
`cache_key` ayrıca `.replace("/", "_")` uygular. Gerçek anahtar artık:

```
sha256("Qwen_Qwen3-Embedding-4B|float32|L8192" + "||" + <text>)
#       ^ Qwen_… (Qwen/… DEĞİL)          ^ L<max_length> — T12'de eklendi
```

dosya adı `<hexdigest>.npy`, dizin `hnav/_cache/emb/`.

**Sonuçları dürüstçe:**

1. **"24k MAB girdisi yeniden kullanılır" iddiam ARTIK YANLIŞ.** O girdiler
   eski `…|float32` ad alanında duruyor; bu koşu `…|float32|L8192` altında
   çalışacağı için onları OKUMAZ. Pratik etkisi yine de küçük: CrossEp
   metinleri zaten cache'te hiç yoktu (farklı korpus), yani bu koşu her
   hâlükârda temiz miss alacaktı. Eski girdiler **silinmez** (Thrust 1'in
   yeniden-fit işine ve denetime ait); disk maliyeti geçici olarak ikiye
   katlanır.
2. **GPU süresi tahmini YUKARI revize edildi: ≈0,6-1,0 GPU-saat** (önceki
   0,3-0,4 örtük olarak 512-token kesmeyi varsayıyordu). Neden: ~7,9k chunk
   metni artık ~1.100-1.400 model token'ıyla işleniyor (1024 tiktoken chunk),
   512 yerine — uzun-metin token hacmi ~2,5x. Diff'in kısa span metinleri
   (~15,8k) etkilenmez, ve diff'in `old`/`new` tam metinleri koşu içinde
   cache'e düşer (aynı stringler), yani ekstra maliyet getirmez.
   `--no-diff` ile ≈0,3-0,5 GPU-saat. İlk 20-bağlam ilerleme satırından
   gerçek hız ölçülüp tahmin doğrulanmalı.
3. Vektör boyutu (2560 float32 ≈ 10KB/girdi) değişmedi → CrossEp yine
   **~240MB** ekler.

**Cache SİLİNMEZ, makineler arası KOPYALANMAZ** (kural aynen geçerli; T12
sonrası ad alanı eşleşmesi artık `model|dtype|L<max_length>` üçlüsüdür).

**`max_length` kararı (CrossEp için açık pin).** CrossEp chunker'ı 1024
*tiktoken* token üretir (`cl_bench_memory/chunking.py`, M5'te transkript);
Qwen tokenizer'ında bu ~1.100-1.400 token, yani **8192 fazlasıyla yeterli —
hiçbir CrossEp metni kesilmez.** Pin olarak repo varsayılanı `8192` seçildi
(Thrust 1'in MAB tarafıyla aynı ad alanında kalmak için: farklı bir değer
ad alanını böler ve iki arena bir daha aynı cache'i paylaşamaz).
**M5 başka bir `HNAV_EMBED_MAX_LENGTH` ile koşulmamalıdır**; koşulursa çıktı
JSON'una not düşülmeli, çünkü sayılar önceki koşuyla karşılaştırılamaz.

**`.env` önceliği — §9.2'deki tuzağın buradaki karşılığı (yön TERS).**
`hnav/config.load_env` **depo kökündeki** `.env`'i okur ve `setdefault`
kullanır: **`os.environ` KAZANIR**, yani kabuktan `export HNAV_EMBED_DTYPE=…`
`.env`'i ezer. (§9.2'deki `load_dotenv(override=True)` bunun tersini yapar.)
M5 benchmark kodu import etmez, dolayısıyla `CROSSEP-KNOW/.env` bu koşuyu
ETKİLEMEZ. Mod duyarlılığı: M5 adapter'ı doğrudan sürer ve `on_extract` moda
bakmaz — `off` ile `shadow` ÖZDEŞ sonuç verir; yalnız `live` `require_not_live()`
ile koşuyu durdurur. Yine de kabuğu temiz tutun:

```bash
env | grep -E "^HNAV_" || echo "(kabukta HNAV_ override yok — temiz)"
```

Koşu (tmux altında):

```bash
tmux new -s m5real
python hnav/stage0/crossep_m5_write_headroom.py --nli cpu --nli-max-pairs 400
#   --nli cpu: DeBERTa-v3-large CPU'da ~10-15 dk (GPU1'i embedder'dan sonra da meşgul
#   etmemek için varsayılan tercih). GPU1 uygunsa alternatif: --nli cuda:1 (~1 dk).
#   NLI çiftleri ön-tanımlı olarak YALNIZ kalibrasyon kümelerinden (--nli-splits).
#   Ağırlıklar box'ta hazır: cross-encoder/nli-deberta-v3-large (Faz A indirdi).
```

Beklenen çıktı + kayıt:

```bash
# hnav/_out/m5_crossep_write_headroom_qwen3_embedding.json  (_SMOKE'suz)
python - <<'EOF'
import json; d=json.load(open("hnav/_out/m5_crossep_write_headroom_qwen3_embedding.json"))
assert d["smoke"] is False and d["fallback_chunker"] is False
print(d["embed_accounting"], d["n_write_events"])
#   ~7.879 yazı olayı beklenir.
#   embed_accounting (T12 ad alanı değişikliğinden SONRA, ilk koşu):
#     cache_misses ~23-24k  (≈7,9k chunk metni + ≈15,8k diff span'i) — MAB'ın eski
#       24k girdisi farklı ad alanında olduğu için HİÇBİRİ hit vermez;
#     cache_hits    koşu-içi tekrarlar (diff'in old/new tam metinleri + bağlam-içi
#       exact-dup'lar) — birkaç bin mertebesi. hits≈0 ise cache dizini yazılamıyor
#       demektir: DUR ve HNAV_CACHE_DIR izinlerini kontrol et.
#   İKİNCİ bir koşu (aynı pinlerle) neredeyse tamamen hit olmalıdır.
EOF
cp hnav/_out/m5_crossep_write_headroom_qwen3_embedding.json stage0_results/crossep/
git add stage0_results/crossep/ && git commit -m "T10: M5 real-embedder measurement" && git push
```

### 9.2 mem0 CrossEp koşusu (DeepSeek API — kullanıcı onaylı) + M5-mem0

Anahtarların okunuşu (koddan doğrulandı): `infer_context_memory.py`
`load_dotenv(override=True)` çağırır; yol verilmediğinden `find_dotenv()`
çağıran dosyanın dizininden yukarı yürür — **`CROSSEP-KNOW/.env`, yoksa depo
kökündeki `.env`** (aşağıdaki bloklayıcı ön koşula bak);
model adı "deepseek" ile başladığında `DEEPSEEK_API_KEY` + `DEEPSEEK_BASE_URL`
kullanılır (`get_api_credentials`); mem0 backend'i `--embed-provider dashscope`
zorunlu kılar → `DASHSCOPE_API_KEY` + `DASHSCOPE_BASE_URL`. `BATCH_MODEL` env
değişkeni set ise Volcengine Ark batch istemcisine geçer — nomemory koşusunda
kullanılmadıysa UNSET bırakılır.

Ön kontrol:

```bash
cd /mnt/nvmes/nvme1/egekutlu/EvoMemBench/Cross-Episode-Knowledge/CROSSEP-KNOW
grep -c "DEEPSEEK_API_KEY\|DEEPSEEK_BASE_URL\|DASHSCOPE_API_KEY\|DASHSCOPE_BASE_URL" .env
#   4 beklenir (nomemory koşusu bu anahtarlarla yapılmıştı; süresi dolmuşsa kullanıcıdan iste)
python -c "import mem0, chromadb" 2>&1               # mem0 kurulu olmalı (registry importu)
```

> **BLOKLAYICI ÖN KOŞUL — t4 §2b tuzağının CrossEp sürümü.** Kabuğu
> denetlemek YETMEZ. `infer_context_memory.py:317` **koşulsuz**
> `load_dotenv(override=True)` çağırır — MAB'ın `main.py:39`'daki
> `override=os.environ.get("HNAV_DOTENV_NO_OVERRIDE") != "1"` koruması bu
> arenada **YOKTUR**. `override=True` kabuktaki değeri EZER, ve yol
> verilmediği için `find_dotenv()` çağıran dosyanın dizininden **yukarı
> doğru yürür**: önce `Cross-Episode-Knowledge/CROSSEP-KNOW/.env`, o yoksa
> (depoda yok, `.gitignore`'lu) **depo kökündeki `.env`** — yani
> `HNAV_MODE`'u tutan dosyanın ta kendisi. Sonuç: tertemiz bir kabukla bile,
> depo kökü `.env` `HNAV_MODE=shadow` diyorsa **API-faturalı mem0 koşusu
> sessizce enstrümanlı gider.** Her İKİ dosya da denetlenmelidir:

```bash
cd /mnt/nvmes/nvme1/egekutlu/EvoMemBench
grep -E "^HNAV_" Cross-Episode-Knowledge/CROSSEP-KNOW/.env 2>/dev/null \
  || echo "(CROSSEP-KNOW/.env yok — find_dotenv depo köküne yürüyecek)"
grep -E "^HNAV_MODE" .env                            # DEPO KÖKÜ — asıl belirleyici
env | grep -E "^HNAV_MODE"                           # kabuk (override=True bunu EZER)
```

**Gerekli durum:** `find_dotenv`'in bulacağı dosyada `HNAV_MODE=off`
(veya satır hiç yok → `config` varsayılanı `off`). `shadow`/`live` görülürse
**koşuyu başlatma**; dosyayı `off`'a çek, commit etme (`.env` gitignore'lu),
koşudan sonra istersen geri al. Gerekçe: akış NATIVE üretilmeli — ölçüm
sonradan `history.db`'den yapılır. (Shadow bayt-nötrlüğü t4/S2'de kanıtlandı;
yine de para harcayan tek-atışlık koşuda enstrümantasyon çalıştırmayız.)

Doğrulama (koşu başladıktan sonra, ilk kayıtlar düşer düşmez): sonuç
kayıtlarında `hnav` alanı **olmamalı** —

```bash
head -1 outputs/context_mem0/*.jsonl | python -c "import json,sys; r=json.load(sys.stdin); print('hnav field:', 'hnav' in r)"
#   False beklenir. True ise koşu enstrümanlı gidiyor: DURDUR, .env'i düzelt, baştan başlat.
```

Koşu (tmux; süre kabaca nomemory koşusunun 2-3 katı — ekstraksiyon örneklem
başına ~1-2 ek LLM çağrısı ekler; 884 örneklem, 8 worker):

```bash
tmux new -s mem0run
python infer_context_memory.py --model deepseek-v3-2-251201 \
  --memory-type mem0 --input CL-bench_context_ge5.jsonl \
  --embed-provider dashscope --embed-model text-embedding-v4 \
  --workers 8 --top-k 10
```

Beklenen artefaktlar:

```
outputs/context_mem0/CL-bench_context_ge5_deepseek-v3-2-251201_ctx_memory_topk10_<ts>.jsonl
memories/context_memory/CL-bench_context_ge5_deepseek-v3-2-251201_mem0_topk10_<ts>/<context_id>/history.db   # M5'in okuduğu
memories/.../<context_id>/qdrant/                                                                            # vektör deposu
```

Ardından M5-mem0 (önce yapı kontrolü smoke, sonra gerçek — mem0 notları kısa,
gömme maliyeti dakikalar mertebesinde):

```bash
cd /mnt/nvmes/nvme1/egekutlu/EvoMemBench
RUN=Cross-Episode-Knowledge/CROSSEP-KNOW/memories/context_memory/<run_dir>
python hnav/stage0/crossep_m5_write_headroom.py --backend mem0_history --source "$RUN" --smoke-embedder
python hnav/stage0/crossep_m5_write_headroom.py --backend mem0_history --source "$RUN" --nli cpu
cp hnav/_out/m5_crossep_write_headroom_mem0_history.json stage0_results/crossep/
git add stage0_results/crossep/ && git commit -m "T10: M5 mem0_history measurement" && git push
```

Yorum notu (şimdiden): mem0 kendi LLM-süzgecini ve dedup'ını koşar — ham
exact-dup oranının qwen3_embedding'dekinden DÜŞÜK çıkması beklenir; sonuç ne
çıkarsa [GATE] raporuna o girer.

## 10. Koşu günlüğü — §9.1'in ilk denemesi, OOM ve embedder düzeltmesi (provenans)

Bu bölüm ölçüm sonucu değil, **sonucun nasıl elde edildiğinin kaydıdır**;
sayıların denetlenebilirliği için tutulur.

### 10.1 Üç özdeş OOM ve yanlış hipotezler

`5240774` (T12, `max_length` 512→8192) sonrası §9.1 üç kez denendi ve **üçünde
de bayt-bayt aynı** hatayla düştü: `Tried to allocate 788.00 MiB`, PyTorch'ta
22,15 GiB ayrılmış, 778 MiB boş.

| Deneme | `HNAV_EMBED_BATCH` | Sonuç |
|---|---|---|
| 1 | 8 (`.env`) | OOM, 20/120 bağlamdan sonra |
| 2 | 2 (süreç-kapsamlı override) | **aynı** OOM, aynı bayt |
| 3 | 1 (süreç-kapsamlı override) | **aynı** OOM, aynı bayt |

Batch'in hiç fark etmemesi teşhisin kilit kanıtıydı: hata `crossep_m5:271` →
`to_candidate` → `encode([content])` yolunda, yani **tek metinlik** bir
çağrıda gerçekleşiyordu — batch parametresi bu yolda tanım gereği etkisiz.
Test edilen iki hipotez de YANLIŞ çıktı: (a) "batch çok büyük" (çürütüldü,
yukarıdaki tablo), (b) "bellek-verimli backend'i zorla" — bu `No available
kernel` ile abort ediyor, çünkü sorun *öncelik* değil **uygunluk**tu.

### 10.2 Gerçek kök neden (embedder sahibi tarafından box'ta ölçüldü)

Qwen3-Embedding-4B **grouped-query attention** kullanır: 32 query head, 8 KV
head. Attention mask `None` olduğunda — ki tek-metinlik `encode([content])`
tam olarak bu durumdur, çünkü hep-birler mask optimize edilip atılır —
transformers SDPA'ya genişletilmemiş K/V'yi `enable_gqa=True` ile verir;
PyTorch'un füzyonlu çekirdekleri bunu **doğrudan reddeder** ve MATH yoluna
düşerek `[1, 32, N, N]` tensörünü maddileştirir. Bellek `N²` ile büyür, bu
yüzden 5.076 token'lık tek bir metin kartı bitirir. Düzeltme uygunluğu geri
kazandırır (`repeat_kv` ile K/V 32 head'e genişletilir), böylece füzyonlu
çekirdeği PyTorch kendisi seçer. İkinci bir OOM daha MLP'de bulundu ve
token-bütçeli batch'leme ile giderildi (9 × ~5.000 token'lık chunk tek bir
45k-token forward'a dolduruluyordu).

**Sayısal nötrlük kanıtlanmış (bizim tarafımızdan tüketilen haliyle):**
eski ve yeni yolun ikisinin de koştuğu yerlerde kosinüsler bit-özdeş,
bileşenler ~1,2e-07; token-bütçeli batch'leme `max|1−cos| = 5,96e-07`.

### 10.3 Düzeltmenin CrossEp üzerinde doğrulanması (öncesi/sonrası)

Saatlerce GPU harcamadan önce, **tam olarak düşen vaka** tek başına sınandı:

| Ölçüt | Düzeltme öncesi | Düzeltme sonrası |
|---|---|---|
| 5.076 token'lık metin (en uzun CrossEp chunk'ı) | 3/3 OOM | `(1, 2560)` vektör ✓ |
| `gqa_expansion_applied` | — | `True` |
| Koşu sırasında GPU1 | OOM @ ~22,7 GiB | **18,7 GiB sabit** |
| `max_length` / `dtype` | 8192 / float32 | **değişmedi** |
| Cache ad alanı | `…|float32|L8192` | **değişmedi** |

Yani düzeltme hiçbir **pinlenmiş bilimsel parametreye** dokunmadı: ne
`max_length`, ne dtype, ne model, ne cihaz, ne de cache ad alanı değişti —
yalnızca aynı matematiğin bellek-verimli çekirdekle koşması sağlandı.

### 10.4 CrossEp token dağılımı (tokenizer-only, GPU'suz ölçüm)

7.879 chunk metni, Qwen3-Embedding-4B tokenizer'ı:

| p50 | p90 | p99 | max | >2048 | >4096 | >8192 |
|---|---|---|---|---|---|---|
| 1.045 | 1.130 | 1.411 | **5.076** | 23 (%0,29) | 2 (%0,03) | **0 (%0,00)** |

İki sonucu var: (1) **`L8192` pini hiçbir CrossEp metnini kesmez** — pin
doğrudur ve toplam token hacmi 2048'de de 8192'de de aynıdır (7,7M);
(2) metinlerin **%92,55'i 512 token'ı aşar**, yani T12 öncesi kesme kusuru
CrossEp'te MAB'dakinden bile daha yıkıcıydı — neredeyse her metin sessizce
kırpılıyordu. Bu, T12 düzeltmesinin bu arena için ne kadar kritik olduğunun
niceliksel kaydıdır.

### 10.5 Etkilenmeyen sonuçlar

§5'in manşet bulgusu (MD5 exact-dup %11,7 kalibrasyon / %7,2 held-out, en kötü
küme 0,706; leksik Jaccard) **embedder'dan bağımsızdır** ve bu bölümdeki
hiçbir olaydan etkilenmemiştir — ne OOM'dan, ne düzeltmeden, ne ad alanı
değişikliğinden. SMOKE ölçümü provenans olarak `stage0_results/crossep/`
altında korunur.
