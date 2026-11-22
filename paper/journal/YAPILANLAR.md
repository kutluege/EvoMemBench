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

## 2026-11-23

- **Altın ile model etiketinin ayrıştığı çiftler için kör inceleme sayfası hazırlandı.**
  `hnav/labeling/audit_disagreement_review.py` (`build`, `score`), 8 test; dosyalar
  `stage0_results/conflict_pairs/disagreement_review/` (`disagreement_label.html`,
  `disagreement_sheet.csv`, `disagreement_README.md`, `disagreement_key.json`). Sayfa pilotla aynı
  araç ve aynı altı alan; hangi kaynağın ne dediğini göstermez. Henüz doldurulmadı.
  - `update_conflict` için altın (`gold_update`) ile model 57 çiftte ayrışıyor: fork 30, core 2
    (ikisi de altın evet, model hayır; 32'si değerlendirme kümesinde), rejected 11,
    discovered_unverified 14 (altın hayır, model evet).
  - Bu 57 çift 40 ayrı cümle çifti: aynı cümleler farklı alt kümelerde ayrı kimlikle geçiyor. Sayfa
    her cümle çiftini bir kez gösterir (40 satır); yanıt o metni taşıyan bütün kimliklere uygulanır.
  - 40 cümle çiftinin 10'u (57 kimliğin 16'sı) pilotta zaten etiketlenmişti ve yönergede modele
    örnek olarak gösterildi; bu 16'sında insan etiketi modelle aynı, yani orada model insan etiketini
    yineliyor. İnsan için yeni olan 30 cümle çifti (41 kimlik, 22'si değerlendirme kümesinde).
  - 5 cümle çifti farklı alt kümelerde zıt altın etiket taşıyor (4'ü bir yerde core, başka yerde
    rejected; 1'i fork ve rejected): hakem aynı metne çağrıdan çağrıya farklı karar vermiş.
  - Sınır: sayfa yalnızca ayrışan çiftleri içerir; altın ile modelin uyuştuğu çiftler hakkında bir
    şey söylemez. Model pilot etiketleyicinin okumasına göre kalibre edildiği için, incelemeyi aynı
    kişi yaparsa sonuç modelden bağımsız olmaz.
- **Ayrışma sayfası dolduruldu ve puanlandı.** Tek etiketleyici, 40 cümle çifti, boş hücre yok,
  yazılı ölçütün türetme kurallarından sapan satır yok. Dosyalar:
  `stage0_results/conflict_pairs/disagreement_review/disagreement_sheet.filled.csv`,
  `DISAGREEMENT_SUMMARY.md`.
  - `update_conflict`: 40 cümle çiftinin 39'unda (57 kimliğin 56'sında) insan modelle aynı yönde,
    1'inde altınla. Pilotta görülmemiş 30 cümle çiftinde 29 (41 kimliğin 40'ı). Tek istisna D005
    (country music / bluegrass music): model alt tür sayıp "uyumlu" dedi, insan "uyumsuz" dedi.
  - Katmana göre (kimlik): fork 30'da 29, core 2'de 2, rejected 11'de 11, discovered_unverified
    14'te 14 modelden yana.
  - Zıt altın etiket taşıyan 5 cümle çiftinin 5'ine insan "çatışma" dedi.
  - Pilotta etiketlenmiş 10 metinde insan `update_conflict` için kendi pilot etiketiyle 10/10 aynı.
  - `strict_conflict` kararsız: pilottaki P059 ile aynı metinde (D002) insan bu kez "evet" dedi
    (pilotta "hayır"), dil ilişkili üç yeni satırda da "evet" (D003, D007, D014) ve vatandaşlıkta
    bir "evet" (D006). Model bu beşinde "hayır" diyor; yönergedeki tabloda "original language of"
    satırı P059'dan sonra "tek değerli değil"e çevrilmişti. Yeni 30 metinde `strict_conflict` uyumu
    26/30.
  - İnsan etiketi olan her metinde insan, kalanında altın (= model) alınırsa çıkan birleşik
    `update_conflict` seti modelden 1 çiftte, mevcut `gold_update`'ten 65 çiftte ayrılıyor: fork 34 ve
    core 2 "çatışma değil"e (36'sı değerlendirme kümesinde), rejected 12 ve discovered_unverified 17
    "çatışma"ya. Bu set dosyaya yazılmadı; altın veri seti değişmedi.
- **`strict_conflict` kuralı yeniden tanımlandı (etiketleyicinin kararı).** İlk ölçüt bu alanı iki
  ayrı biçimde tanımlıyordu ("iki cümle aynı anda doğru olamaz" ve "ilişki tek değerliyse") ve
  ikisi, ilişki çok değerli olduğu halde iki değerin birbirini dışladığı çiftlerde ayrışıyordu
  (D006: ABD ve antik Roma vatandaşlığı; D024: Lu ve New York'ta çalışmak). Model yönergesi
  yalnızca ikinci okumayı uyguluyordu. Yeni kural: `update_conflict` evet ise ve iki cümle o varlık
  için aynı anda doğru olamıyorsa `strict_conflict` evet; ilişki tablosu kural değil, örnek.
- **`strict_conflict` için tek soruluk referans sayfası hazırlandı.**
  `hnav/labeling/audit_strict_review.py` (`build`, `score`), 5 test; dosyalar
  `stage0_results/conflict_pairs/strict_review/`. 103 cümle çifti: daha önce insanın
  `update_conflict` evet dediği 53 metin (eski yanıtlar belirsiz ölçütle verilmişti) ve hiç
  görülmemiş 50 metin (37 ilişkinin her birinden en az bir). Henüz doldurulmadı. Mevcut model
  etiketleri ve altın veri seti değişmedi.
- **`strict_conflict` referans sayfası geldi, puanlandı ve bağımsız olarak denetlendi; henüz
  referans olarak kullanılmıyor.** Dosyalar: `strict_review/strict_sheet.filled.csv` (alındığı
  hâliyle), `STRICT_REVIEW_SUMMARY.md`. Denetimi ayrı bir alt ajan (Claude Opus 5.5, effort high)
  yaptı; sayılar onun çalıştırdığı betiklerden ve depodaki puanlayıcıdan.
  - 103 satırın 18'i "evet". Yanıt yalnızca ilişki şablonuna bağlı: sayfadaki 42 şablonun hiçbirinde
    iki yanıt birden yok; değer çiftine göre karar verilen tek satır yok.
  - Sayfa, aynı gün kayda geçen kararla ((a) tek değerli ilişki ya da (b) birbirini dışlayan
    değerler) uyuşmuyor: kararı doğuran iki çiftin ikisi de "hayır" (D006 → S045, D024 → S032) ve
    (b) hiçbir satırda uygulanmamış. Yönergenin açıkça "tek değerli" saydığı iki durumda da "hayır":
    başkent (S033, S062) ve hükümet başkanı eş ifadesi (S064, S068, S095).
  - Önceki yanıtlarla: 53 metnin 43'ü aynı, 10'u değişmiş, hepsi evet → hayır; 9'u aynı gece
    doldurulan ayrışma sayfasındaki yanıtı tersine çeviriyor.
  - İç tutarlılık: "birden fazlası düşünülebilir" gerekçesi CEO, başkan ve baş antrenörde "evet",
    başkent, genel merkez, evlilik, kıta ve yönetmende "hayır" veriyor.
  - Kaynak: 103 satırın 91'inde not var, ilk 12 satırda yok. Notların hepsi İngilizce, 28 ayrı
    metinden oluşuyor ve ilk 12 satıra atıf yapıyor ("consistent with S009"); "conservative rule"
    gibi yönergede olmayan terimler içeriyor. Sayfanın üretimi ile dosyanın kaydı arasında 815
    saniye var. Önceki iki sayfada hiç not yoktu. Bunlar notların toplu üretilmiş ya da
    yapıştırılmış olmasıyla uyumlu; kimin ya da neyin yazdığını göstermez. Etiketleyiciye soruldu.
  - **Etiketleyicinin yanıtı (23 Kasım):** S012'den sonraki satırları bir modele doldurtmuş. Buna
    göre bu sayfada insan etiketi yalnızca ilk 12 satırdır (S000–S011); S012–S102 (91 satır) model
    çıktısıdır, hangi model olduğu kayıtlı değil. Bu 91 satır insan referansı olarak kullanılmaz ve
    hiçbir yerde insan etiketi diye sayılmaz. Dosya alındığı hâliyle duruyor.
  - Sonuç: sayfadaki tablo kural sayılırsa `strict_conflict` şablondan türetilir, model koşusu
    gerekmez; mevcut model etiketlerinden 360 çift kimliği (222 cümle çifti) evet → hayır olur
    (evli 91, kıta 71, genel merkez 70, başkent 67, yayıncı 29, yönetmen 26, eş ifade 5, dil 1) ve
    "evet" 776'dan 416'ya iner. Kayıtlı karar geçerliyse sayfanın 7 satırı kararla çelişiyor, 3
    satırı sınırda, altı ilişkinin tek değerli olup olmadığı açık; (b) için yaklaşık 708 cümle
    çiftinde çift düzeyinde karar gerekir ve sayfada (b) örneği hiç yok. Hiçbir koşu yapılmadı;
    model etiketleri ve altın veri seti değişmedi.
- **Model etiketleyici turu için ek kayıt.** Etiketleyen alt ajanlar bu depoda çalıştı; ortam
  belgelerine göre bu tür alt ajanlara deponun `CLAUDE.md` dosyası veriliyor. Orada çift düzeyinde
  etiket yok, ama katmanların ve etiket kurallarının tanımı var. Koşu sırasında denetlenmedi;
  `model_annotation/RUN_LOG.json` içine `context_caveat` olarak yazıldı.
- **Yedi haftalık plan yeniden yazıldı.** `paper/journal/WEEKLY_PLAN.md`: yazarın 21 Kasım planı,
  bu iki günün bulgularına ve 23 Kasım'da verilen kararlara göre güncellendi. Gönderim 14 Ocak
  2027. Beş iddia (C1–C5), her birinin elde olan ve eksik kanıtı, 0–7. haftaların iş listesi.
  Kararlar: LLM karşılaştırması hem uçtan uca hem çift düzeyinde; "küçük model, filtreyle büyük
  model kadar" iddiası için Claude Haiku 5.5 aynı düzenekte koşulacak; veri FactConsolidation
  görevine iki ek olarak sunulacak; iki insan etiketleyici yazarların kendisi, yaklaşık 200 cümle
  çifti. Aynı gün iki ek: büyük model koşusu API yerine yazarın Claude Code aboneliğiyle, depo
  dışında boş bir klasörden tek seferlik komut satırı çağrılarıyla yapılacak (hangi model: Sonnet
  5.5 ve ikinci nokta olarak Haiku 5.5 önerildi, yazarın onayı bekleniyor); `strict_conflict`
  işi, referans sayfasıyla ilgili iki soru yanıtlanana kadar bekliyor.
