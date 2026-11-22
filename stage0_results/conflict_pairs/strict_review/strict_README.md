# Strict-conflict review — annotator instructions

Every pair in this sheet already counts as an update conflict: both sentences
are about the same entity and the same attribute, and they give two different
values, neither of which contains the other. One question is left.

`strict_conflict`: can the two sentences both be true of that entity at the
same time?

- Answer **yes** (a strict conflict) when they cannot: if one is true, the
  other is definitely false. This holds when the attribute has one value at a
  time (a capital, a birthplace, a head of government). It also holds when the
  attribute can have several values but these two exclude each other, for
  example citizenship of two states that never existed in the same period.
- Answer **no** when both could hold together, however unlikely the
  combination: two languages spoken, two children, two employers, two fields
  of work.

Judge only whether the two values can hold together. Do **not** judge whether
either sentence is true of the real person or thing; many sentences are
counterfactual on purpose. "Confucius is a citizen of the United States" and
"Confucius is a citizen of Canada" are both false in fact, but the two values
can hold together, so the answer is no.

If a pair is hard to decide, use this test: told that the first sentence is
true, would you say the second is definitely false? If so, answer yes.

Answer yes or no for every pair (no blanks, no "unsure"); use `notes` for
anything you want to flag. Do not open `strict_key.json`, your earlier sheets
or anything under `model_annotation/` before you have finished. Hand the
downloaded file over as it is, without re-saving it in a spreadsheet program.

---

## Türkçe çeviri (display translation)

# Katı çatışma incelemesi — etiketleyici yönergesi

Bu sayfadaki her çift zaten bir güncelleme çatışması sayılıyor: iki cümle de
aynı varlık ve aynı özellik hakkında, ve biri diğerini kapsamayan iki farklı
değer veriyor. Geriye tek soru kalıyor.

`strict_conflict`: iki cümle o varlık için aynı anda doğru olabilir mi?

- Olamıyorsa **evet** (katı çatışma) deyin: biri doğruysa diğeri kesinlikle
  yanlıştır. Özellik aynı anda tek değer alıyorsa böyledir (başkent, doğum
  yeri, hükümet başkanı). Özellik birden çok değer alabildiği halde bu iki
  değer birbirini dışlıyorsa da böyledir; örneğin hiç aynı dönemde var olmamış
  iki devletin vatandaşlığı.
- İkisi birlikte geçerli olabiliyorsa, birliktelik ne kadar olası görünmese de
  **hayır** deyin: konuşulan iki dil, iki çocuk, iki işveren, iki çalışma alanı.

Yalnızca iki değerin birlikte geçerli olup olamayacağına bakın. Cümlelerin
gerçek kişi ya da şey için doğru olup olmadığına **bakmayın**; cümlelerin çoğu
bilerek karşıolgusaldır. "Confucius is a citizen of the United States" ile
"Confucius is a citizen of Canada" gerçekte ikisi de yanlıştır, ama iki değer
birlikte geçerli olabilir; yanıt hayırdır.

Karar vermek zorsa şu sınamayı kullanın: ilk cümlenin doğru olduğu söylense,
ikincinin kesinlikle yanlış olduğunu söyler miydiniz? Öyleyse evet deyin.

Her çift için evet ya da hayır deyin (boş bırakmayın, "emin değilim" yok);
belirtmek istediğiniz her şey için notlar alanını kullanın. Bitirmeden önce
`strict_key.json` dosyasını, önceki sayfalarınızı ve `model_annotation/`
altındaki hiçbir şeyi açmayın. İndirilen dosyayı olduğu gibi verin; bir tablo
programında yeniden kaydetmeyin.
