# Yapılanlar

*Natural Language Processing* (Cambridge) başvurusu için tamamlanan işlerin tarihli kaydı.
Buraya yalnızca bitmiş ve kontrol edilmiş iş yazılır; planlanan ve süren işler
`WEEKLY_PLAN_NOTES.md` dosyasındadır. Her maddede işin nerede durduğu (dosya, commit) yazar.

## 2026-11-21

- **Genelleme protokolü depoya alındı.** `paper/PROTOCOL_GENERALISATION.md`, taslak v0.1,
  kayıt edilmedi (commit `f757817`).
- **Dergi hazırlık planı ve çalışma kuralları.** `paper/journal/READINESS_PLAN.md` ve bundan
  yazılan `paper/journal/SKILL.md` (`.claude/skills/nlp-journal/` üzerinden yüklenir)
  (commit `8c507e2`).

## 2026-11-22

- **Başvuru kaynağı depoya alındı.** `tezim_paper@1e39c8d` deposundan yalnızca Cambridge
  sürümü: `paper/nlp_cambridge/` (`main_nlp.tex`, sınıf dosyası, kaynakça, şekiller, derlenmiş
  PDF). Düzenlenecek tek dosya `main_nlp.tex` (commit `d044265`).
- **Hafta planı için notlar.** `paper/journal/WEEKLY_PLAN_NOTES.md`: açık kararlar ve iş
  kalemleri (commit `d044265`).
- **İnsan incelemesi pilotu hazırlandı.** Ayrıştırıcı ile GPT-5-mini hakeminin ayrıştığı
  katmanlardan 50 çift ve 10 kontrol çifti, kör etiketleme sayfası (Türkçe arayüz, İngilizce
  kayıt) ve puanlayıcı: `hnav/labeling/audit_human_pilot.py`,
  `stage0_results/conflict_pairs/human_pilot/` (commit `370e271`, `a06f47b`).
- **Model etiketleyici hattı kuruldu.** `hnav/labeling/audit_model_annotator.py` (insan
  etiketlerini kalibrasyon ve ayrı tutulan kısım olarak böler, kör partileri üretir, etiket
  dosyalarını doğrular ve puanlar, partileri paralel işçilere dağıtır), 10 test, alt ajan
  tanımı `.claude/agents/pair-annotator.md` (Claude Fable 5.2, effort medium; yalnızca dosya
  okur ve yazar, kod çalıştıramaz). Geçme ölçütü etiketlemeden önce sabitlendi: ayrı tutulan
  20 çiftte insanla uyum `update_conflict` için en az 0,85, diğer beş alanın her biri için en
  az 0,80.
  1. aşama için 5.397 çiftlik 54 kör parti üretildi
  (`stage0_results/conflict_pairs/model_annotation/batches/stage1/`): dengeli değerlendirme
  kümesi ile `rejected` ve `discovered_unverified` katmanları, pilot çiftleri hariç.
  (commit `1ece964`, `61295b6`).
- **İnsan etiketlemesi 60 çifte yapıldı.** Tek etiketleyici (Ege Kutlu), kör, altı alan;
  Türkçe arayüz, İngilizce kayıt. Tartışmalı 50 çiftin 38'inde `update_conflict` ayrıştırıcıyla,
  12'sinde GPT-5-mini hakemiyle aynı yönde; 10 kontrol çiftinin 10'unda ikisiyle de aynı.
  Hakemle en çok ayrışılan alan `values_incompatible` (60'ta 27 uyum). Dosyalar:
  `stage0_results/conflict_pairs/human_pilot/pilot_sheet.filled.csv`, `PILOT_SUMMARY.md`.
  Alınan dosyada her satır fazladan bir tırnak katmanına sarılıydı (bir tablo programında
  yeniden kaydedilmiş); katman kaldırıldı, cümleler boş formla birebir doğrulandı, alınan hâli
  `pilot_sheet.filled.as_saved.csv` olarak duruyor (commit `c6cf01b`).
- **Claude Fable 5.2 insan seçimlerine göre kalibre edildi ve yönerge bir skill dosyasına
  kaydedildi.** `.claude/skills/pair-labelling/SKILL.md`: insanın kararlarından çıkarılan
  kurallar ve 60 çiftin tamamı örnek olarak. "Kalibre" burada yönerge ve örnekle yönlendirme
  demektir; modelin ağırlıkları değişmedi, ince ayar yapılmadı. Her kural "insan etiketinde
  gözlendi" ya da "yazılı ölçütten çıkarıldı" diye işaretli; `strict_conflict` tablosundaki 37
  ilişkiden 15'i gözleme, 22'si çıkarıma dayanıyor.
- **Ayrı tutulan 20 çiftte kör sınama geçti.** Yönerge önce 60 çiftin 40'ından yazıldı ve
  sınamadan önce commit edildi (`c6cf01b`); bir alt ajan (Fable 5.2, effort medium) kalan 20
  çifti insan etiketini görmeden etiketledi. İnsanla uyum: `update_conflict` 20/20, altı alanın
  tamamı 19/20 (tek fark `strict_conflict`, P059). Önceden sabitlenen ölçüt (0,85 ve 0,80)
  geçildi. Örnek küçük: 20/20 için Wilson %95 alt sınırı 0,84. Sınamadan sonra yönergeye 20
  çift örnek olarak eklendi ve `strict` tablosunda bir satır değişti (commit `1920811`); bu son
  sürüm görülmemiş insan etiketiyle ayrıca sınanmadı.
- **Alt ajanlar 1. aşamadaki bütün çiftleri bu yönergeyle etiketledi.** Arka planda paralel
  çalışan 9 alt ajan (Fable 5.2, effort medium), her biri 6 parti, toplam 5.397 çift; 54 etiket
  dosyasının hepsi geçerli (commit `0699a61`). Her ajan bir partiyi (100 çift) okuyup 100
  satırını tek adımda yazdı; ajan başına süre 159–172 saniye. Ajanlar genel amaçlı tipteydi
  (kısıtlı `pair-annotator` tipi oturumda yüklenmedi); "kod çalıştırma, başka dosya açma"
  kuralı talimata ve ajanların kendi raporuna dayanıyor. Sonuç
  (`stage0_results/conflict_pairs/model_annotation/MODEL_ANNOTATION_SUMMARY.md`; sayılar ayrı
  tutulan 20 çifti de içerir):

  | Katman | Etiketlenen | Model `update_conflict` = evet | Ayrıştırıcıyla uyum | Hakemle uyum |
  |---|---|---|---|---|
  | core | 2.385 | 2.383 | 0,999 | 0,999 |
  | update_only_fork | 259 | 229 | 0,884 | 0,116 |
  | rejected | 11 | 11 | 1,000 | 0,000 |
  | discovered_unverified | 96 | 14 | 0,854 | 0,146 |
  | negative (değerlendirme kümesi) | 2.666 | 0 | 1,000 | 1,000 |

  Tutarlılık: aynı cümle çifti farklı alt kümelerde farklı kimlikle yer aldığı için 1.164 çift
  farklı partilerde birden çok kez etiketlendi; altı etiketin tamamı 1.164'ünde aynı. İki cümlenin
  de ayrıştığı 5.400 çiftte `same_referent` her zaman "özne dizgesi aynı" ile, `same_relation`
  5.394'ünde "şablon aynı" ile örtüşüyor. Yani model etiketi, insanın kuralının ölçekli
  uygulamasıdır; ayrıştırıcıdan ayrıldığı yer kapsama ve eş ad durumlarıdır (aynı şablon, farklı
  değer olan 3.473 çiftin 55'i uyumlu sayıldı).
  Sınırlar: bunlar model etiketidir, insan etiketi değildir; altın veri seti değişmedi.
  `strict_conflict` hakemin `gold_strict` etiketiyle core katmanında yalnızca 0,496 uyumlu,
  çünkü insan "tek değerli" ilişkiyi dar tanımlıyor ve tablonun çoğu çıkarım.
- **Alt ajanlar kalan bütün çiftleri de etiketledi (2. aşama).** Değerlendirme kümesi dışındaki
  49.112 negatif çift, 492 parti, 82 paralel alt ajan (Fable 5.2, effort medium; iş akışıyla, aynı
  anda en çok 16), aynı yönerge. 492 etiket dosyasının hepsi geçerli. Süre yaklaşık 22 dakika,
  yaklaşık 9 milyon alt ajan token'ı. 49.112 çiftin hepsinde `update_conflict` = hayır; hakem ve
  ayrıştırıcıyla tam uyum.
  Partiler tek katmandan olduğu için her partiye, 1. aşamada etiketlenmiş çiftlerden 10 tanesi yeni
  kimlikle ve rastgele sırayla karıştırıldı (toplam 4.920 kontrol satırı; ajan bunları ayırt
  edemez). 4.920'sinin hepsi altı alanda da 1. aşamadaki etiketin aynısını aldı.
- **Sonuç: altın veri setindeki 54.569 çiftin hepsinin bu açıdan bir etiketi var.** 60 çift insan
  (20'si ayrıca model), 54.509 çift yalnızca model. Birleşik dosya:
  `stage0_results/conflict_pairs/model_annotation/MODEL_LABELS.csv` (54.529 model satırı), özet
  `MODEL_ANNOTATION_SUMMARY.md`, çalıştırma kaydı `RUN_LOG.json`.
  - Tutarlılık (bütün tur): 54.529 satır 47.052 ayrı cümle çifti. Farklı partilerde birden çok kez
    etiketlenen 7.092 cümle çiftinin 7.091'i altı alanda aynı. Tek fark bir alandaki tek bir
    hata (`b24776`, `same_referent`; `update_conflict` etkilenmiyor), `RUN_LOG.json`'da kayıtlı,
    etiket dosyası düzeltilmedi.
  - Model `update_conflict` = evet: 2.637 çift, tamamı 1. aşama katmanlarında.
  - Yazılı ölçütün türetme kurallarından sapan satır yok (`update_conflict` dört denetimin
    kesişimi; `strict_conflict` yalnızca `update_conflict` evet iken).
  - Altın veri seti ve makaledeki sayılar değişmedi. Bu etiketler model etiketidir; insan
    kanıtı 60 çifttir ve modelin insanı izlediğine dair bağımsız kanıt ayrı tutulan 20 çifttir.
