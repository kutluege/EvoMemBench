# Haftalık plan için notlar — NLP (Cambridge) gönderimi

Yazım tarihi: 2026-11-22. Hedef gönderim tarihi: 7 Ocak 2027 (hazırlık raporundaki tarih).

Bu dosya bir plan değil, plana girdi. Hafta ataması yok; her iş kaleminin bir kimliği
(K1, M3, …), tahmini süresi ve bağımlılığı var, haftalık plan bunlara kimlikle atıf
yapabilsin diye. Süre tahminleri `READINESS_PLAN.md` Bölüm 4'ten alındı; raporun kendi
çıkarımıdır [I], ölçüm değildir. Aynı rapora göre zorunlu kalemler 18–24 iş günü tutuyor
ve 7 Ocak'a kadar yaklaşık 32 iş günü var.

Etiketler: **[J]** derginin kuralı, **[I]** raporun çıkarımı, **[Ö]** bu oturumda
Claude'un önerisi (yazarların onayını bekliyor).

## 1. Bugünkü durum

- Dergi kararı verildi: *Natural Language Processing* (Cambridge). Diğer beş dergi sürümü
  kapsam dışı.
- Gönderim kaynağı artık bu depoda: `paper/nlp_cambridge/main_nlp.tex`. `tezim_paper`
  deposunun `1e39c8d` commit'inden alındı. PDF 9 Ekim 2026 derlemesi, 34 sayfa.
- Dergi bilgisi `paper/journal/` altında: hazırlık raporu, format brief'i, çalışma
  kuralları (skill).
- Genelleme protokolü `paper/PROTOCOL_GENERALISATION.md`: taslak v0.1, kayıtlı değil.
- İnsan doğrulaması: pilot set hazır (60 çift), etiketlenmeyi bekliyor. Asıl inceleme
  için Laya koşusu henüz yapılmamış (`audit_results_laya.jsonl.gz` depoda yok).
- Bu makinede LaTeX derleyicisi yok. Kaynağın `pdflatex` ile derlemesi hiç yapılmadı
  (PDF Tectonic ile üretilmiş).
- Depo herkese açık. Yerel commit'ler push edilmedi; push etmek hazırlık raporunu ve
  makalenin güncel kaynağını yayımlar.

## 2. Bu oturumda verilen kararlar ve gerekçeleri

### 2.1 İnsan doğrulaması (eski 2. madde)

**Karar [Ö]:** 30 Eylül tasarımı asıl çalışma olarak kalıyor; ondan önce küçük bir pilot
yapılıyor. Pilotun amacı yönergeyi ve formu sınamak, bir de tartışmalı katmanlarda ilk
insan okumasını almak.

Pilot seti (`stage0_results/conflict_pairs/human_pilot/`, tohum 20261122):

| Katman | Sayı | Neden tartışmalı |
|---|---:|---|
| `update_only_fork` | 35 | Ayrıştırıcı "aynı anahtar, güncelleme" diyor; hakem "değerler bağdaşır" diyor |
| `rejected` | 2 | Ayrıştırıcı "aynı anahtar" diyor; hakem "aynı yuva değil" diyor |
| `discovered_unverified` | 13 | Ayrıştırıcı etiketlememiş; hakem "çelişki" diyor |
| kontrol: `core` | 5 | Tartışmasız pozitif |
| kontrol: `negative` | 5 | Tartışmasız negatif (dengeli değerlendirme setinden) |

50 tartışmalı çift, üç katmana büyüklükleriyle orantılı dağıtıldı (282 / 12 / 105).
10 kontrol çifti benim eklememdir: etiketleyenin yönergeyi tartışmasız örneklerde nasıl
okuduğunu gösterir, onlar olmadan "tartışmalı çiftlerde hep hayır dedi" ile "genelde
hayır diyor" ayırt edilemez. İstenmezse `--n-control 0` ile yeniden üretilir.

**Nasıl etiketlenir:**

1. `stage0_results/conflict_pairs/human_pilot/pilot_label.html` dosyasını tarayıcıda aç.
2. Her çift için altı soruyu evet/hayır olarak yanıtla. İlerleme tarayıcıda saklanır.
3. "Download CSV" ile `pilot_sheet.filled.csv` dosyasını indir, aynı klasöre koy.
4. Puanla: `python hnav/labeling/audit_human_pilot.py score --sheet stage0_results/conflict_pairs/human_pilot/pilot_sheet.filled.csv`
5. Bitirmeden `pilot_key.json` dosyasını açma.

Sayfa Türkçe açılır; sağ üstteki düğme İngilizceye çevirir. Dil yalnızca arayüzü
değiştirir: cümle çiftleri çevrilmez, kaydedilen dosyada sütun adları ve yanıtlar
(`yes` / `no`) her zaman İngilizcedir. Türkçe metin İngilizce yönergenin çevirisidir,
ölçüm aracı İngilizce yönergedir. Türkçe arayüzle yapılan etiketler makalede
kullanılırsa bu belirtilmeli (K3, B3).

**Pilotun sınırı:** tek etiketleyici ve yalnızca tartışmalı katmanlar. Uyum katsayısı (κ)
vermez, hakemin veri kümesi genelindeki doğruluğunu tahmin etmez. Makalede "insan
doğrulaması" olarak raporlanamaz. Aynı formu ikinci bir kişi de doldurursa puanlayıcı κ
hesaplar (`--sheet-b`), ama 60 çiftlik κ makale için yine yetersizdir.

**Asıl inceleme için açık karar (K1'e bağlı):** rapor 400–600 çiftlik tabakalı örneklem
öneriyor; depodaki tasarım Laya–hakem anlaşmazlıklarını hedefliyor. Önerim [Ö], pilot
sonucunu gördükten sonra karar vermek ve iki seçenekten birini seçmek:

- **A. Mevcut tasarım + büyütülmüş temsili tabaka.** Laya koşusu gerekir. Hakemin genel
  doğruluğu için kontrol tabakası 100'den, katman başına sabit kotalara çıkarılır.
- **B. Laya'dan bağımsız tabakalı tasarım.** 282 fork'un tamamı, 12 rejected, 105
  discovered, 50 core, 50 zor negatif: yaklaşık 500 çift. GPU koşusu gerektirmez; Laya
  isteğe bağlı ikinci makine okuyucusu olarak kalır.

B daha az bağımlılık taşıyor ve raporun istediği sayıları doğrudan veriyor; A hakem
hatalarını bulmakta daha verimli. İkisinde de etiketleyiciler birbirini görmeden çalışır
ve altın veri kümesi değişmez.

Makale için ayrıca gerekenler: etiketleyicilerin kim olduğu ve onayları (etik beyanı),
yazar-etiketleyici varsa bunun açıkça yazılması, ve etiket düzeltmelerinin AUROC'u ne
kadar oynattığını veren bir duyarlılık analizi (rapor istiyor, mevcut `ingest` yapmıyor).

### 2.2 Protokole eklenecekler (eski 3. madde)

**Karar [Ö]:** üç "should" kalemi protokole **kayıttan önce** ikincil analiz olarak
eklensin. Protokol dosyasına dokunmadım: taslak ortak yazarla tartışılmak üzere yazılmış
ve kayıt yazarların işi. Aşağıdaki metin taslağa yapıştırılmaya hazır; köşeli parantez
içindekiler kayıttan önce sabitlenmeli.

```text
§4 Arms, end to end — add:
  Generative comparator. One call per question to [MODEL] that reads the same retrieved
  records and lists those stating a superseded value; the listed records are deleted
  (each group keeps its highest serial) and the answering step is unchanged. The prompt
  is written and frozen on the calibration split; no test example is used.

§4 Arms, pair level — add:
  Second encoder [ENCODER]. The screen is refitted for it by the C3 procedure on the
  calibration split. Pair-level AUROC and TPR at FPR 10^-3 only; no end-to-end run.

§5 Secondary — add:
  Generative comparator against native and against H-Nav-GEO under C3 (exact McNemar,
  exact p, no success claim); its harmful-deletion rate as in P2.
  Cost: wall-clock time and peak memory per question for the H-Nav-GEO filter and for the
  generative comparator, median and interquartile range over the test questions, on
  [HARDWARE], with prompt and generated tokens for the comparator.

§7 Decisions — add:
  P3 remains restricted to non-generative baselines (H5). The generative comparator is
  reported beside it with its cost. If it is significantly ahead on accuracy, the paper
  says so and states the method's contribution as cost and independence from a
  generative call.
```

Gerekçe:

- **Üretici karşılaştırıcı** en çok sonradan eklenmekten zarar gören kalem. Sonuç iki
  yönde de çıkabilir; hangi uç noktaya girdiği veri görülmeden yazılmazsa her iki sonuç
  da tartışmalı olur. `[MODEL]` için önerim referans yanıt modelini (Qwen3-4B) kullanmak:
  çalışmaya yeni bir model girmez.
- **Gecikme ve bellek** bir hipotez testi değil, ölçüm. Eklemesi ucuz ve makaledeki
  "ucuz yöntem" iddiasına sayı verir; şu an sınırlamalarda "ölçülmedi" yazıyor.
- **İkinci encoder** takvim sıkışırsa ilk bırakılacak kalem. Bırakılırsa makalede "tek
  encoder" sınırlaması olarak kalır. `[ENCODER]` için rapor bge-m3 ya da e5 öneriyor.

## 3. İş kalemleri

Süre: iş günü. "Kim": Y = yazarlar, C = Claude oturumu, GPU = GPU makinesinde koşu.

### K — Kanıt (deney ve veri)

| Kimlik | İş | Kaynak | Süre | Bağımlılık | Kim |
|---|---|---|---|---|---|
| K0 | Pilot etiketleme (60 çift) ve puanlama | [Ö] | <1 | — | Y, C |
| K1 | Asıl insan doğrulaması tasarım kararı (A ya da B) | [Ö] | 0,5 | K0 | Y |
| K2 | Laya koşusu (yalnız A seçilirse) | depo | <1 | K1 | GPU |
| K3 | İki etiketleyiciyle asıl inceleme, uzlaşma turu, κ ve hakem doğruluğu | [I] #1, zorunlu | 4–6 | K1 (K2) | Y, C |
| K4 | Etiket düzeltmelerine AUROC duyarlılık analizi | [I] #1 | 1 | K3 | C |
| K5 | Protokole §2.2 eklemeleri, ortak yazar onayı, **kayıt commit'i** | protokol | 1 | — | Y |
| K6 | Olgu-ayrık test deposu ve kalibrasyon bölmesinin üretimi, 50 örnek denetimi, hash | [I] #2, zorunlu | 7–10 (K7 ile) | K5 | C, Y |
| K7 | Yeni sette koşular: C1/C2/C3, iki model, tüm kollar | [I] #2, zorunlu | K6 ile birlikte | K6 | GPU |
| K8 | Uçtan uca baseline'lar (ham kosinüs + NLI, yalnız NLI, sıralı sayfa) | [I] #3, zorunlu | 3–4 | K5 | GPU, C |
| K9 | Üretici karşılaştırıcı | [I] #9, isteğe bağlı | 3–5 | K5 | GPU, C |
| K10 | Gecikme ve bellek ölçümü | [I] #11, isteğe bağlı | 1–2 | K5 | GPU |
| K11 | İkinci encoder, çift düzeyinde | [I] #10, isteğe bağlı | 2 | K5 | GPU, C |
| K12 | Türkçeye çevrilmiş 100 çiftlik geometri yoklaması | [I] #8, isteğe bağlı | 4 | — | C, GPU |

Bırakılanlar (rapor "can drop" diyor): LongMemEval, kayıt düzeyinde erişim. Makalede
gelecek iş olarak anılır.

Not: protokol taslağının §6'sında "record-level page" adlı bir olgu denetimi var; rapor
kayıt düzeyinde erişimi bırakmayı öneriyor. İkisi aynı şey değil ama örtüşüyor; K5'te
netleştirilmeli.

### M — Makale metni

| Kimlik | İş | Kaynak | Süre | Bağımlılık |
|---|---|---|---|---|
| M1 | Yöntemin adı: H-Nav-GEO kalacak mı, betimleyici bir ad mı | [I] #4 | karar | — |
| M2 | Proje jargonunun temizlenmesi (campaign, arms, page, pool, plan, quarantined, …) | [I] #4, zorunlu | 2–3 | M1 |
| M3 | Gövdeyi kısaltma: geliştirme geçmişi ve ikincil analizler ek malzemeye | [I] Bölüm 5 | 2 | — |
| M4 | Özet: 324 kelimeden ≤300'e, en fazla beş sayı | [J] kural, [I] ayrıntı | 0,5 | K7 |
| M5 | Kaçırılan ön kayıt uç noktasını sonuçlar bölümünde ve özetin son cümlesinde anmak | [I] #7, zorunlu | 0,5 | — |
| M6 | "Yalnız İngilizce" gerekçe paragrafı | [I] #8, zorunlu | 0,5 | — |
| M7 | Yeni sonuçların yazılması: olgu-ayrık test başlık sonuç, sh_64k "kısmi örtüşme" | [I] #2 | 2 | K7, K8 |
| M8 | İnsan doğrulamasının §5.2'ye ve sınırlamalara yazılması | [I] #1 | 0,5 | K3 |
| M9 | Dergiden atıflar: rapordaki liste tek tek doğrulanarak | [I] #13 | 0,5 | — |
| M10 | Ön baskıları yayımlanmış sürümlerle değiştirmek | [I] | 0,5 | — |
| M11 | Ek malzeme dosyası (S1–S4), son hâliyle | [J]: düzeltilemez | 1 | M3 |
| M12 | Kapak mektubu | [I] Bölüm 8 | 0,5 | K7, K3 |

Uzunluk için iki sayım var: floatlar hariç gövde yaklaşık 12.000 kelime, tablo ve
başlıklarla yaklaşık 15.500. Derginin hangisini saydığı bilinmiyor (S1).

### Ş — Şekiller

Şekillerin üretim dosyaları bu depoda değil; düzeltme yazarlardan gelmeli.

| Kimlik | İş | Kaynak |
|---|---|---|
| Ş1 | "held-out" → "frozen transfer" (Şekil 3, 4, 6B) | `SUBMISSION_REPORT.md` §8 |
| Ş2 | "whitening / whitened" → "ABTT cosine" (Şekil 2b, 3A, 6A) | aynı |
| Ş3 | Şekil 1 ve 2'deki dosya adlarını kaldırmak | aynı, [J] |
| Ş4 | Şekil 2: 454 → 455, "2B–9B" → "2.3B–9B", üst üste binen etiketler, benzer çift örneği | aynı |
| Ş5 | Şekil 7: "Table 8" → "Table 9", "delete stale" → "delete superseded" | aynı |
| Ş6 | Yedi şekil için alt metin; yalnız renge dayanmayan kodlama (WCAG 2.1 AA) | [J] |
| Ş7 | Yöntem adı değişirse şekillerdeki ad (M1'e bağlı) | — |

### B — Beyanlar ve açık `[CONFIRM]` kalemleri (yalnız yazarlar doldurabilir)

| Kimlik | Kalem |
|---|---|
| B1 | Fon beyanı; TÜBİTAK ULAKBİM ve BSC hesaplama tahsisleri için proje numaraları |
| B2 | Çıkar çatışması beyanı |
| B3 | Etik beyanı (etiketleyici onayı dahil) |
| B4 | Yapay zekâ beyanı: GPT-5 mini sürümü ve kullanım tarihleri (§5.2); kod ve metin için kullanılan araçlar, sürümler, tarihler (teşekkür bölümü) |
| B5 | Veri erişilebilirliği: arşiv DOI'si (Zenodo), depo sürümü, MemoryAgentBench lisans notu |
| B6 | CRediT rolleri (isteğe bağlı) |
| B7 | İki yazarın ORCID'i; Ege Kutlu'nun e-postası ilk sayfada |
| B8 | vLLM 0.28.0 sürüm dizgesi; iki model kartının erişim tarihi; Holm (1979) kaynağı |

### A — Altyapı

| Kimlik | İş |
|---|---|
| A1 | Bir kez `pdflatex → bibtex → pdflatex ×2` derlemesi; sayfa sayısı ve yazı tipi değişecek |
| A2 | `PROVENANCE.md` güncellemesi: 23 Eylül'den sonra eklenen sayılar (ör. §5.1'deki 800 ve 370) izlenmiyor |
| A3 | `tezim_paper` ile eşitleme kararı: çalışma kopyası artık burada; orada değişiklik yapılırsa yeniden içe aktarılmalı |
| A4 | Push kararı (depo herkese açık) |
| A5 | `test_audit_laya.py` içindeki bir test Windows'ta kodlama yüzünden düşüyor (`read_text()` kodlamasız); Linux'ta etkilenmez |

### S — Dergiye ve kuruma sorulacaklar

| Kimlik | Soru | Kime |
|---|---|---|
| S1 | 8.000–12.000 kelime sınırı tablo, başlık, kaynakça ve ekleri kapsıyor mu | NLP@cambridge.org |
| S2 | Dergi 2026–2028 EKUAL "fonlanan dergi" listesinde mi; Boğaziçi kapsamda mı | ULAKBİM, Cambridge uygunluk sorgusu |
| S3 | "Tables must have sources" yazarların kendi sonuç tablolarına nasıl uygulanıyor | NLP@cambridge.org |
| S4 | ScholarOne önerilen ya da istenmeyen hakem soruyor mu | gönderim sırasında |

## 4. Kaynaklar arasında tutarsızlıklar

- **Etki faktörü.** Format brief'i ana sayfada "2025 Impact Factor 1.6" gördüğünü yazıyor;
  hazırlık raporu yalnızca JCR sırasını (210'da 163) bulabilmiş. İkisi de doğrulanmalı;
  enstitünün çeyreklik koşulu varsa JCR'den bakılmalı.
- **Kelime sayısı.** Rapor "yaklaşık 15.000" diyor (tablolar dahil), gönderim raporu gövde
  metni için 12.003 veriyor. İkisi de doğru, sayım yöntemi farklı.
- **Şakar ve Emekci (2025).** Hazırlık raporu atıf yapılmasını öneriyor; gönderim
  raporuna göre literatür kılavuzu bu makaleyi "yalnız bağlam" diye işaretlemiş ve
  eklenmemiş. M9'da karara bağlanmalı.
- **Sayı ve "per cent" biçimi.** Dergi kuralı [J]; yazarların talimatı ise bunu
  redaktöre bırakmak. Skill ikincisini uyguluyor.

## 5. Yazarların kararını bekleyenler

1. Asıl insan doğrulaması tasarımı: A mı B mi (K1).
2. §2.2'deki protokol eklemeleri ve üç yer tutucu: `[MODEL]`, `[ENCODER]`, `[HARDWARE]` (K5).
3. Yöntemin adı (M1).
4. İkinci etiketleyici kim olacak (K3).
5. Push ve deponun kamuya açık durumu (A4, B5).
6. İsteğe bağlı kalemlerden hangileri takvime girecek (K9–K12); rapora göre iki tanesine
   yer var.
