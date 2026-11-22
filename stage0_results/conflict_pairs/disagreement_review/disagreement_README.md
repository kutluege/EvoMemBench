# Human review — annotator instructions

You are labelling pairs of sentences from a fact store. Do **not** check whether
either sentence is true in the real world; decide whether the two sentences
express conflicting propositions. Work alone, do not consult the other
annotator, and do not open `disagreement_key.json`.

For each pair, first identify what each sentence asserts — subject, attribute
(relation), value, and any validity context (time, place, population,
organization, condition) — then answer yes/no in each column:

- `same_referent`: both sentences are about the same real-world entity
  (aliases, abbreviations and different surface strings can name one entity).
- `same_relation`: both assert the same attribute or relation, even if phrased
  differently.
- `context_overlap`: the propositions apply under compatible or overlapping
  validity conditions.
- `values_incompatible`: the two values cannot both occupy the same slot under
  the same context. Paraphrases, aliases, one value containing the other, and
  values that can coexist are **compatible** (answer no). Do not answer yes
  merely because the strings differ.
- `update_conflict`: under a memory-store convention with one current value
  per (entity, attribute) slot, one sentence replaces the other's value. This
  is yes exactly when the four checks above are all yes, even if the relation
  is naturally multi-valued (citizenships, children, languages, ...).
- `strict_conflict`: the two sentences cannot both be true at the same time in
  the real world. This is yes only when `update_conflict` is yes **and** the
  relation admits a single value at a time.

Write `yes` or `no` in every label cell (no blanks, no "unsure"); use `notes`
for anything you want to flag. Save the file with the same columns.

---

## Disagreement review sheet

Every sentence pair in this sheet has received two different `update_conflict`
answers from two earlier label sources. The sheet does not say which source
said what, and about half of the pairs go each way. Label each pair on its own
reading, exactly as the instructions above say. Each sentence pair appears
once, even if it occurs in several subsets.

Who should fill it: preferably someone who did not label the pilot. One of the
two sources was calibrated on the pilot annotator's labels, so that
annotator's review is not independent of it.

Two ways to fill it:

1. Open `disagreement_label.html` in a browser, answer every question for
   every pair, and press "Download CSV". Progress is kept in the browser.
2. Or fill `disagreement_sheet.csv` directly and save it as comma-separated
   UTF-8.

Hand the downloaded file over as it is. Opening and re-saving it in a
spreadsheet program can wrap every row in extra quotes, which the scorer
rejects.

Then score it:

    python hnav/labeling/audit_disagreement_review.py score --sheet <the filled file>

Do not open `disagreement_key.json`, the gold dataset or anything under
`model_annotation/` before you have finished.

---

## Türkçe çeviri (display translation)

# İnsan incelemesi — etiketleyici yönergesi

Bir olgu deposundan alınmış cümle çiftlerini etiketliyorsunuz. Cümlelerin gerçek
dünyada doğru olup olmadığını **kontrol etmeyin**; iki cümlenin çelişen
önermeler dile getirip getirmediğine karar verin. Tek başınıza çalışın, diğer
etiketleyiciye danışmayın ve anahtar dosyasını (`disagreement_key.json`) açmayın.

Her çift için önce her cümlenin ne ileri sürdüğünü belirleyin — özne, özellik
(ilişki), değer ve varsa geçerlilik bağlamı (zaman, yer, topluluk, kurum,
koşul) — sonra her sütunu evet/hayır olarak yanıtlayın:

- `same_referent`: iki cümle de aynı gerçek dünya varlığı hakkındadır (takma
  adlar, kısaltmalar ve farklı yazımlar tek bir varlığı adlandırabilir).
- `same_relation`: ikisi de aynı özelliği ya da ilişkiyi bildirir; ifade biçimi
  farklı olsa bile.
- `context_overlap`: önermeler bağdaşan ya da örtüşen geçerlilik koşulları
  altında geçerlidir.
- `values_incompatible`: iki değer, aynı bağlamda aynı yuvada birlikte
  bulunamaz. Aynı anlama gelen farklı ifadeler, takma adlar, bir değerin
  diğerini kapsaması ve birlikte var olabilen değerler **bağdaşır** (hayır
  deyin). Yalnızca yazımlar farklı diye evet demeyin.
- `update_conflict`: her (varlık, özellik) yuvası için tek bir güncel değer
  tutan bir bellek deposu kuralında, cümlelerden biri diğerinin değerinin
  yerini alır. Yukarıdaki dört kontrolün hepsi evet olduğunda, ve yalnızca o
  zaman, evettir; ilişki doğası gereği çok değerli olsa bile (vatandaşlıklar,
  çocuklar, diller, ...).
- `strict_conflict`: iki cümle gerçek dünyada aynı anda doğru olamaz. Yalnızca
  `update_conflict` evet ise **ve** ilişki aynı anda tek bir değer kabul
  ediyorsa evettir.

Her soruyu evet ya da hayır olarak yanıtlayın (boş bırakmayın, "emin değilim"
yok); belirtmek istediğiniz her şey için notlar alanını kullanın.

---

## Ayrışma incelemesi sayfası (çeviri)

Bu sayfadaki her cümle çifti, daha önceki iki etiket kaynağından iki farklı
`update_conflict` yanıtı almıştır. Sayfa hangi kaynağın ne dediğini söylemez ve
çiftlerin yaklaşık yarısı bir yönde, yarısı öbür yöndedir. Her çifti yukarıdaki
yönergeye göre, kendi okumanızla etiketleyin. Bir cümle çifti birden çok alt
kümede geçse bile bir kez gösterilir.

Kim doldurmalı: tercihen pilotu etiketlememiş biri. İki kaynaktan biri pilot
etiketleyicinin etiketlerine göre kalibre edildi; bu yüzden o etiketleyicinin
incelemesi o kaynaktan bağımsız değildir.

İndirilen dosyayı olduğu gibi verin. Bir tablo programında açıp yeniden
kaydetmek her satırı fazladan tırnağa sarabilir; puanlayıcı bunu kabul etmez.

Bitirmeden önce `disagreement_key.json` dosyasını, altın veri setini ve
`model_annotation/` altındaki hiçbir şeyi açmayın.
