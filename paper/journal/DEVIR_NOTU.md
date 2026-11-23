# Devir notu — 24 Kasım 2026

Bu not, 21–23 Kasım oturumunda alınan kararları, yapılanları ve yapılacakları tek yerde toplar.
İş başka bir bilgisayardan sürdürülecek; o bilgisayarda bu oturumun sohbeti ve Claude'un yerel
hafızası olmayacak. Devam etmek için gereken her şey bu notta ve işaret ettiği dosyalarda.

Makale: "Read-time removal of superseded facts in agent memory using embedding geometry"
(Kutlu ve Özönder). Dergi: *Natural Language Processing* (Cambridge). Gönderim hedefi:
**14 Ocak 2027**.

## 1. Öbür bilgisayarda nasıl devam edilir

1. Depoyu al: `https://github.com/kutluege/EvoMemBench.git`, dal `claude/hnav-presentation-evidence`.
2. Claude Code'u depo kökünde aç ve "devam edelim" de. `CLAUDE.md` bu nota yönlendirir.
3. Okuma sırası: bu not → `WEEKLY_PLAN.md` Bölüm 0 (işin durduğu yer) ve Bölüm 8 (açık kararlar)
   → `YAPILANLAR.md`'nin son girişleri.

Depoyla birlikte **gelmeyen** şeyler:

| Ne | Durum | Ne yapılır |
|---|---|---|
| Claude'un yerel hafızası | Yalnız ilk bilgisayarda | İçindeki kurallar aşağıda Bölüm 2'de yazılı |
| `model_annotation/batches/stage2/` (492 parti, 8 MB) | `.gitignore`'da | Gerekirse `python hnav/labeling/audit_model_annotator.py batches --stage 2` yeniden üretir; etiket dosyaları depoda |
| NLI ön ölçümünün çift başına skorları | Bilerek işlenmedi | Betikler ve özet tablo `stage0_results/conflict_pairs/nli_preliminary/` altında; ölçüm makaledeki modelle yeniden yapılacak |
| Test ortamı | Yerel bir sanal ortamdı | `pytest` kurulu bir Python yeter; etiketleme araçlarının 44 testi: `pytest hnav/tests/test_audit_human_pilot.py hnav/tests/test_audit_model_annotator.py hnav/tests/test_audit_disagreement_review.py hnav/tests/test_audit_strict_review.py hnav/tests/test_strict_decision_table.py hnav/tests/test_audit_validation.py -q`. Bütün test takımı ayrıca `numpy` ve `scipy` ister |
| GPU makinesindeki sonuçlar (`hnav/_out/`) | Hiç depoda değildi | Değişiklik yok |
| LaTeX derleyicisi | İlk bilgisayarda yoktu | Makale kaynağı hiç `pdflatex` ile derlenmedi (plan, A1) |

Windows notu: betikleri `python -I` ile çalıştırırken konsol kodlaması yüzünden çıktı bozulabilir;
betiğin başına `sys.stdout.reconfigure(encoding="utf-8")` koymak yeter.

## 2. Çalışma kuralları (yeni oturumdaki Claude için)

- Yanıtlar Türkçe. Plan ve protokoller İngilizce, kayıt (`YAPILANLAR.md`) Türkçe.
- **Commit:** her işten sonra, `Paper:` ya da `Audit:` önekiyle. Git kimliği bu depoda
  ayarlı değilse komut başına şu bayraklarla: `-c user.name="Ege" -c
  user.email="69218899+kutluege@users.noreply.github.com"`. Git ayarı değiştirilmez; yazarın
  kişisel e-postası commit'e ya da dış bir servise yazılmaz.
- **Push:** depo herkese açık. Yalnızca yazar o an açıkça isterse push edilir.
- **Altın veri seti değişmez.** `gold_conflict_dataset.jsonl.gz` ve donmuş katman sayıları
  (core 2.388, fork 282, rejected 12, discovered 105, negative 51.782) yeniden üretilmez; yeni
  etiketler yanına eklenir.
- **NLI skoru hiçbir etiketleyiciye gösterilmez,** insan ya da model. Yöntemin doğrulayıcısı NLI.
- **Hiçbir etiket, olduğundan başka bir kaynağa ait gibi yazılmaz.** Model etiketi "insan" ya da
  "altın" diye geçmez.
- **Cevaplayıcı model koşuları bu depodaki alt ajanlarla yapılmaz:** alt ajanlar `CLAUDE.md`'yi
  görür (benchmark'ın kuralı orada yazılı) ve altın cevapları açabilir.
- Biten ve denetlenen iş `YAPILANLAR.md`'ye, işin güncel durumu `WEEKLY_PLAN.md` Bölüm 0'a yazılır.

## 3. Kararlar

### 22 Kasım

- **Dergi:** *Natural Language Processing* (Cambridge). Gönderim kaynağı
  `paper/nlp_cambridge/main_nlp.tex`.
- **İnsan pilotu:** ayrıştırıcı ile GPT-5 mini'nin ayrıştığı katmanlardan 50 çift ve 10 kontrol
  çifti, altı alan, kör.
- **Model etiketleyici:** insan etiketlerinden yazılan yönergeyle Claude Fable 5.2 kalan bütün
  çiftleri etiketler. 60 çiftin 20'si sınama için ayrı tutulur; geçme ölçütü koşudan önce
  sabitlenir (`update_conflict` için 0,85, diğer alanlar için 0,80). İşçiler paralel alt ajanlar,
  effort medium. "Eğitildi" değil "kalibre edildi" denir: modelin ağırlıkları değişmedi.

### 23 Kasım

- **İddialar** beş başlıkta toplandı (C1–C5); ayrıntı `WEEKLY_PLAN.md` Bölüm 1:
  - C1 sorun: küçük modeller eski değeri okuyor;
  - C2 yöntem ve maliyet: sürüm çiftleri yalnızca gömme geometrisinden, dil modellerinden daha
    hızlı ve ucuza bulunuyor;
  - C3 etki: filtreyle küçük model, çok daha büyük bir model kadar iyi cevap veriyor;
  - C4 kapsam: yöntem çelişkiyi değil, yerini almayı yakalıyor;
  - C5 kaynak: FactConsolidation görevine iki ek (çift veri seti ve olgu-ayrık test seti).
- **LLM karşılaştırması iki düzeyde yapılacak:** uçtan uca (üretici "çıkar ve en yeniyi tut"
  filtresi) ve çift düzeyinde (GPT-5 mini ve Fable 5.2'nin etiket doğruluğu ve maliyeti).
- **Performans iddiası** "LLM filtresiyle aynı ya da daha iyi" diye kurulmayacak; "filtreli küçük
  model, büyük modele yakın" diye kurulacak. Makalede ölçülmüş olan: filtreli Qwen3-4B, filtresiz
  Qwen3.5-9B'ye eşit ya da üstün (77'ye 39, 77'ye 61, 56'ya 51). Büyük model için aynı düzenekte
  yeni koşu gerekiyor.
- **Büyük model koşusu API ile değil, yazarın Claude Code aboneliğiyle** yapılacak: depo dışında
  boş bir klasörden tek seferlik `claude -p` çağrıları, sistem istemi benchmark'ınkiyle
  değiştirilmiş, araçlar kapalı. Hangi model olacağı açık (Bölüm 6).
- **"EvoMemBench'i geliştiriyoruz" denmeyecek;** katkı, MemoryAgentBench'in FactConsolidation
  görevine iki ek olarak yazılacak.
- **İki insan etiketleyici yazarların kendisi** (Ege Kutlu ve ortak yazar), yaklaşık 200 cümle
  çifti. Makalede açıkça yazılacak.
- **Takvim bir hafta kaydı;** gönderim 14 Ocak 2027.
- **`strict_conflict` tanımı** (yazarın kararı): "iki cümle aynı anda doğru olamaz"ı ölçecek.
  `update_conflict` evet ise ve (a) ilişki tek değerliyse ya da (b) ilişki çok değerli olsa bile
  iki değer birlikte geçerli olamıyorsa evet. **Bu karar henüz uygulanmadı ve yeniden açık:**
  yazar ertesi sayfada farklı bir okuma gördü; Bölüm 6'daki ilk karar.
- **NLI etiketin kaynağı olmayacak,** karşılaştırılan sistem olacak. `strict_conflict` NLI'a
  göre tanımlanırsa `update_conflict` ile aynı etikete döner ve yöntem kendi bileşeniyle
  ölçülmüş olur.
- **NLI modelini eğitmek bu makaleye girmeyecek;** gelecek iş. Bu veriyle eğitilen model şablon
  ezberler ve "şema yok" iddiasını zayıflatır.
- **Etiketleme bir protokole bağlandı:** insan tohumu, modelle ölçekleme, ayrışmaların insan
  incelemesi, iki etiketleyiciyle bağımsız denetim (`paper/PROTOCOL_ANNOTATION.md`).
- **İnsan sayfalarının kaynağı** (yazarın beyanı): 60 çiftlik pilot ve 40 çiftlik ayrışma
  sayfasını yazar kendisi doldurdu. `strict_conflict` sayfasının ilk 12 satırı yazarın, kalan 91
  satırı bir modele doldurtuldu; o sayfa hiçbir şey için kullanılmıyor.
- **`strict_conflict` çift çift etiketlenmeyecek, kuralla belirlenecek:** yazarlar bir karar
  tablosu doldurur, kod uygular; model yalnızca çift düzeyinde yargı gereken yerde çalışır.
- **Kör doğrulamada iki soru sorulacak** (`update_conflict`, `strict_conflict`) ve sayfa çift
  başına süreyi kaydedecek.
- **Ana analiz donmuş altınla kalacak;** insan hakemli etiketler ayrı bir dosya ve duyarlılık
  analizi olarak girecek.

## 4. Yapılanlar ve bulgular

Ayrıntı ve dosya yolları `YAPILANLAR.md`'de; burada özet.

| İş | Sonuç |
|---|---|
| İnsan pilotu, 60 çift | Tartışmalı 50 çiftin 38'inde yazar ayrıştırıcıdan, 12'sinde GPT-5 mini'den yana; 10 kontrolde ikisiyle de aynı |
| Ayrı tutulan 20 çiftte model sınaması | `update_conflict` 20/20; altı alanın tamamı 19/20; ölçüt geçildi |
| Model etiketleme, 54.509 çift | 91 işçi, yaklaşık 25 dakika, yaklaşık 10 milyon token; bütün dosyalar geçerli |
| Tutarlılık | 4.920 gizli tekrarın hepsi aynı etiketi aldı; birden çok kez etiketlenen 7.092 metnin 7.091'i aynı |
| Altın ile model ayrışması | `update_conflict` için 57 çift kimliği, 40 ayrı cümle çifti |
| Ayrışmaların insan incelemesi | Yazar 57'nin 56'sında modelden yana; görmediği 30 metinde 29 |
| Altının iç tutarsızlığı | 5 cümle çifti farklı alt kümelerde zıt altın etiket taşıyor |
| Yinelenme | 54.529 etiketli satır 47.052 ayrı cümle çifti |
| Birleşik etiket (hesaplandı, dosyaya yazılmadı) | Modelden 1 çiftte, donmuş altından 65 çiftte ayrılıyor; 36'sı değerlendirme kümesinde (5.340'ta) |
| `strict_conflict` sayfasının denetimi | Yanıt yalnızca ilişkiye bağlı; yazarın kararıyla ve yönergeyle çelişen 7 satır; sayfa kullanılmıyor |
| NLI ön ölçümü (makaledeki model değil) | Aynı özne ve ilişkideki 1.692 çiftin 1.684'ünde "çelişki", tek ve çok değerli ayrımı yok; farklı özneli 150 negatifin 106'sında da "çelişki" |

İlk ölçütte bulunan beş belirsizlik (tartışmalı katmanların kaynağı): birlikte var olabilen
değerler "bağdaşır" mı; bağlam ne zaman örtüşmez; "aynı varlık" yazıldığı gibi özne mi; hangi
unvanlar aynı ilişki; `strict_conflict`'in iki ayrı tanımı.

Yazılan araçlar (hepsi `hnav/labeling/` altında, testleriyle): `audit_human_pilot.py`,
`audit_model_annotator.py`, `audit_disagreement_review.py`, `audit_strict_review.py`,
`strict_decision_table.py`, `audit_validation.py`.

Yazılan belgeler: `paper/PROTOCOL_ANNOTATION.md` (taslak v0.1), `paper/RUBRIC_V2.md` (taslak),
`paper/PROTOCOL_GENERALISATION_ADDITIONS.md` (taslak), `paper/journal/WEEKLY_PLAN.md`,
`paper/journal/YAPILANLAR.md`.

## 5. Yapılacaklar

### Önce yazarlar (sırayla)

1. **Karar tablosunu doldurmak.** `stage0_results/conflict_pairs/strict_review/DECISION_TABLE.md`
   okunur, `decision_table.csv` doldurulur: altı kural kararı (D1–D6) ve 40 ilişki. Asıl soru D4.
2. **Ölçütün ikinci sürümünü onaylamak.** `paper/RUBRIC_V2.md` içindeki dört seçim: [R1] iki
   ifade tek ilişki mi, [R2] unvanlar, [R3] kapsama tanımı (bluegrass / country çifti buna bağlı),
   [R4] bilinmeyen kapsama.
3. **İki protokolü ortak yazarla onaylayıp 26 Kasım'da kaydetmek.** Genelleme protokolüne ekler
   birleştirilir ve beş değer sabitlenir: `[MODEL]`, `[ENCODER]`, `[HARDWARE]`, `[HOSTED]`,
   `[MARGIN]`. Her birinin yanında öneri var.
4. **Büyük modeli seçmek** ve aboneliğin otomatik koşuya (model başına yaklaşık 1.800 çağrı) izin
   verip vermediğine bakmak.
5. **Dergiye e-postayı göndermek** (kelime sınırı neyi sayıyor, hakem önerisi soruluyor mu).
6. **Ana metin bütçesi etiketleri, yöntemin adı, bundan sonraki push'lar.**

### Sonra Claude (yukarıdakilere bağlı)

- Karar tablosu dolunca: `strict_conflict`'i tablodan türetmek; D4 "evet" ise yaklaşık 708 cümle
  çiftinde, ilişkiye göre partilerle ve her değerin dönemini gerekçe yazdırarak model koşusu.
- Ölçüt onaylanınca: Türkçe çevirisiyle birlikte son hâlini yazmak, doğrulama örneklemini çekmek
  (kuru koşuda 150 cümle çifti; 50 test seti çifti sonra eklenir) ve sayfayı üretmek.
- Kayıttan sonra, 1. hafta: olgu-ayrık test setini ve kalibrasyon bölmesini kurmak; büyük model
  için komut satırı koşucusunu yazıp on soruluk deneme yapmak.
- 4.–5. hafta: uyum raporu, hakemli etiket dosyası, nihai veri tablosu ve veri kartı.

### Haftalar (ayrıntı `WEEKLY_PLAN.md` Bölüm 4)

| Hafta | Tarih | İş | Kapı |
|---|---|---|---|
| 0 | 23–25 Kas | Ölçüt, protokol metni, dergiye e-posta, karar tablosu | — |
| 1 | 26 Kas – 2 Ara | Protokol kaydı, test ve kalibrasyon setleri, doğrulama örneklemi | Kayıt veri üretiminden önce |
| 2 | 3–9 Ara | Olgu denetimleri, aktarım, büyük model koşusu | Çerçeve kararı: 9 Aralık |
| 3 | 10–16 Ara | Baseline'lar, çift düzeyinde tablo, etiketleme biter | İlk tablolar makalede |
| 4 | 17–23 Ara | Maliyet, uyum raporu, üretici karşılaştırıcı | Metin 11.100 kelimeye iner |
| 5 | 24–30 Ara | Doğrulama, nihai veri seti, veri yayını hazırlığı | Deney dondurma: 30 Aralık |
| 6 | 31 Ara – 6 Oca | Yeniden yazım | Taslak ortak yazara: 4 Ocak |
| 7 | 7–13 Oca | Yeniden üretilebilirlik, gönderim | Karar: 11 Ocak; gönderim: 14 Ocak |

## 6. Açık kararlar

1. **`strict_conflict` kuralı.** Karar tablosundaki D4: çok değerli bir ilişkide birbirini
   dışlayan iki değer (ABD ve antik Roma vatandaşlığı) katı çatışma mı, yoksa yalnızca ilişki mi
   belirler? 23 Kasım kararı "evet" diyordu; yazar emin olamadığını söyledi.
2. **Büyük model:** Sonnet 5.5 ve ikinci nokta olarak Haiku 5.5 (öneri), ya da yalnızca Haiku 5.5.
3. **"Karşılaştırılabilir" için sınır:** öneri 5 puan.
4. **Protokoldeki yer tutucular:** `[MODEL]`, `[ENCODER]`, `[HARDWARE]`.
5. **Yöntemin adı** (9 Aralık toplantısı).
6. **Gönderim günü ön baskı** yayımlanacak mı (7. hafta).

## 7. Dosya haritası

| Yol | Ne |
|---|---|
| `paper/journal/WEEKLY_PLAN.md` | Plan: Bölüm 0 durum, Bölüm 1 iddialar, Bölüm 4 haftalar, Bölüm 8 açık kararlar |
| `paper/journal/YAPILANLAR.md` | Biten işlerin tarihli kaydı |
| `paper/journal/READINESS_PLAN.md` | Derginin ne beklediğine dair araştırma |
| `paper/journal/WEEKLY_PLAN_NOTES.md` | Eski notlar ve iş kalemi kimlikleri; planla ayrışırsa plan geçerli |
| `paper/PROTOCOL_ANNOTATION.md` | Etiketleme protokolü, taslak |
| `paper/PROTOCOL_GENERALISATION.md`, `…_ADDITIONS.md` | Genelleme protokolü ve kayıttan önce eklenecekler |
| `paper/RUBRIC_V2.md` | Etiketleyici yönergesinin ikinci sürümü, taslak |
| `paper/nlp_cambridge/main_nlp.tex` | Makalenin kaynağı |
| `stage0_results/conflict_pairs/human_pilot/` | 60 çiftlik pilot: sayfa, doldurulmuş dosya, özet |
| `stage0_results/conflict_pairs/model_annotation/` | Model etiketleri (`MODEL_LABELS.csv`), partiler, özet, koşu kaydı |
| `stage0_results/conflict_pairs/disagreement_review/` | 40 cümle çiftlik ayrışma incelemesi |
| `stage0_results/conflict_pairs/strict_review/` | Kullanılmayan referans sayfası, denetimi, **karar tablosu** |
| `stage0_results/conflict_pairs/nli_preliminary/` | NLI ön ölçümünün betikleri ve özeti |
| `.claude/skills/pair-labelling/SKILL.md` | Modelin izlediği ilk yönerge |

## 8. Makalede söylenmeyecekler ve bilinen zayıflıklar

- Veri setinin insan etiketli olduğu, model etiketlerinin altın olduğu, etiketleyicilerin
  yazarlardan bağımsız olduğu söylenmez.
- 1.–4. aşamalar önceden kayıtlı değildi; yalnızca sınama ölçütü koşudan önce sabitlenmişti.
- Model birinci yazarın etiketlerine göre kalibre edildi; onunla uyumu bağımsız kanıt değil.
  Bağımsız kanıt ikinci etiketleyiciden gelecek.
- Model işçilerinin körlüğü talimata dayanıyor; depoda çalıştılar ve büyük olasılıkla
  `CLAUDE.md`'yi gördüler (çift düzeyinde etiket içermiyor, etiket kurallarını anlatıyor).
- İki insan sayfasında çift başına süre kaydı yok; yazarın doldurduğu, kendi beyanına dayanıyor.
- NLI ile ilgili hiçbir şey, ölçüm makaledeki modelle tekrarlanmadan yazılmaz.
- Büyük model filtreli küçük modelin epey önünde çıkabilir; o durumda iddia "aradaki farkın şu
  kadarını kapatıyor" olur.
