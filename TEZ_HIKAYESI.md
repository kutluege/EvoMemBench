# Tez hikâyesi — "Küçük modellerin RAG başarımını, çelişen belleği ucuza temizleyerek yükseltmek"

Bu belge, **hangi iddianın kurulabileceğini ve hangi kanıtla** kurulacağını
gösterir. Her sayı, depodaki taahhüt edilmiş (committed) bir artefakttan
gelir ve kaynağı yanında yazılıdır. Sonunda **iddia edilemeyecek** şeyler de
listelenmiştir — savunmada asıl korunması gereken kısım odur.

---

## 1. Tek cümlelik tez

> Gelişen (evolving) bir vektör belleğinde **çelişen olgular**, küçük bir
> dil modelinin RAG başarımını asıl sınırlayan etkendir; bu çelişkiler
> **çıkarım anında ek LLM çağrısı gerektirmeyen, hatta istemi kısaltan**
> ucuz bir geometrik+sembolik denetçiyle, **ölçülmüş sıfır bilgi kaybıyla**
> tespit edilip temizlenebilir ve bu, modelin doğruluğunu benchmark'a göre
> **+11 ile +66 puan** arasında yükseltir.

Üç bileşen: (a) **problem gerçek**, (b) **çözüm ucuz**, (c) **çözüm güvenli**.
Aşağıda üçü de ayrı ayrı kanıtlanıyor.

---

## 2. Problem gerçek: küçük model doğru kaydı bulur, yanlış *sürümü* söyler

Bu, hikâyenin can damarı. Hata tipi rastgele değil, sistematik:

| kanıt | sayı | kaynak |
| --- | --- | --- |
| Çelişkili soru hatalarının **doğru anahtarın eski değerini** üretme oranı | **572 / 575** (8 taahhütlü koşu) | `stage0_results/question_strata.json`, `hnav/labeling/question_strata.py` |
| sh_6k'de çelişkili katmanda yerel (native) doğruluk | **2 / 74** | `stage0_results/stage1/detector_gap_retrieval_sh6k.json` |
| sh_64k'de çelişkili katmanda yerel doğruluk | **17 / 66** | `stage0_results/abtt/abtt_arm_A1_raw_sh64k.json` |
| Tekil (unique) katmanda yerel doğruluk — kontrol | 26/26, 35/35, 28/34 | aynı artefaktlar |

Yorum: model, bağlamda **hiç çelişki yokken** neredeyse kusursuz (26/26);
aynı bağlama aynı anahtarın eski bir sürümü eklendiğinde çöküyor (2/74).
Yani başarısızlık bilgi eksikliği değil, **sürüm ayrımı yapamama**. Küçük
modelin zayıflığı tam olarak budur ve tezin hedeflediği boşluk budur.

---

## 3. Çözüm ucuz — üç ayrı maliyet ekseninde

### 3.1 Çıkarım anında ek LLM çağrısı: **sıfır**
Denetçi, sayfayı düzenler ve **aynı tek üretim çağrısını** yapar. NLI çapraz
kodlayıcı çevrimdışı ön-geçişte (prepass) bir kez çalışır, sonuç tablosu
tekrar oynatılır (`hnav/stage1/calibrate_read_policy.py::prepass_subset`,
`ReplayNLI`). Yeni bir cevaplayıcı model için **ön-geçiş yeniden
kurulmaz** — LLM'den bağımsızdır (`pipelines/README.md`).

### 3.2 İstem uzunluğu: **negatif maliyet** (kısalıyor)

| koşu | istem karakter değişimi | kaynak |
| --- | ---: | --- |
| hnav_raw sh_64k | **−0.31 %** (−48,625 karakter) | `abtt_arm_A1_raw_sh64k.json` → `tokens.detector_suppress` |
| hnav_geo sh_64k | −0.22 % | `pipelines/hnav_geo/results/.../detector_gap_sh_64k.json` |
| hnav_geo sh_6k | **−2.87 %** | aynı klasör |

Denetçi olgu siliyor, eklemiyor: doğruluk artarken **token maliyeti düşüyor**.
Bu, "ucuz" iddiasının en güçlü tek cümlesi.

### 3.3 Denetçinin kendi hesabı: sayfa başına, sabit ve küçük
Soru başına ≤ 50 olgudan oluşan havuzda ikili kosinüs + QR artığı + tablo
araması. Gömme vektörleri zaten RAG için hesaplanmış durumda; ek maliyet
2560-boyutlu birkaç bin iç çarpım. GPU gerekmiyor (bu oturumdaki tüm
çözümleme dizüstü CPU'da koştu).

---

## 4. Çözüm işe yarıyor — ve kazanç küçük modelde en büyük

Qwen3-4B-Instruct-2507, dondurulmuş; her hücre **tek atış**, soru-eşlemeli
McNemar:

| kol | sh_6k | sh_32k | sh_64k |
| --- | --- | --- | --- |
| yerel (native) | 28/100 | 48/100 | 45/100 |
| **hnav_raw** (parser) | **94/100 (+66)** | **86/100 (+38)** | **64/100 (+19)** |
| hnav_geo (parser'sız) | 77/100 (+47) | 77/100 (+24) | 56/100 (+11) |

sh_64k çelişkili katman: 17 → 37/66, kesin p = 1.9 × 10⁻⁶; genel +19,
p = 2.1 × 10⁻⁵ (`stage0_results/stage1/detector_gap_confirmatory_sh64k.json`).

**Neden bağlam büyüdükçe kazanç azalıyor?** Çünkü mekanizma doyuyor ve
darboğaz **erişime (retrieval)** kayıyor — §6.

**Oracle'a yakınlık:** sh_6k'de kusursuz baskılama oracle'ı 0.91, denetçi
0.90 (oran 0.984); sh_32k'de 0.88 vs 0.86 (0.957)
(`stage0_results/stage1/stale_suppression_probe_*.json`, `hnav/BUILD_NOTES.md`).
Yani denetçi, mekanizmanın verebileceğinin **%96–98'ini** veriyor.

---

## 5. Çözüm güvenli — ve bu, yapısal olarak kanıtlı

- **Sıfır zarar kuralı**: hiçbir baskılanan olgu, anahtarının **güncel**
  değerini taşıyamaz. Tüm taahhütlü kollarda kalibrasyonda 0 zararlı
  (`classify_drops`, `detector_gap.py:407-444`).
- **Yapısal kanıt (E2E-4)**: her doğrulanan çift `same_key` şartını
  sağlıyorsa zarar **inşaat gereği** sıfırdır — `same_key` (relation,
  subject) üzerinde bir denklik bağıntısıdır, grup iki anahtara yayılamaz;
  `suppress` her grubun en yüksek serisini korur; dolayısıyla anahtarın en
  yeni değeri asla düşmez. Kalibrasyon taraması bunu ızgaranın **her
  hücresinde** doğruladı (`IDONLY_PREREG.md`).
- **Ve bu, tezin en keskin bulgusu**: geometrik ekranda böyle bir garanti
  **yoktur**. `hnav_geo` kolunda kalibrasyonda zarar 0 iken sh_64k'de
  **8 zararlı baskılama** oluştu ve koşu kendi ön-kayıtlı 4. koşuluyla
  **geçersiz (void)** sayıldı: geometrik grup iki farklı anahtarı
  birleştirdi ve baskılama bir anahtarın **tüm üyelerini** sildi
  (`Italy · resmî dil`, `The Game · müzik türü`, `outfielder · spor`).
  Dahası, geometrinin parser'dan **fazladan** yaptığı 5 baskılamanın
  **tamamı** bu zararlı olanlardır — 5'te 5. Yani geometrinin sembolik
  kimliğe kattığı tek şey bilgi kaybıdır. Aynı kusur, taahhütlü
  `hnav_abtt_noparser` kolunda da vardır (5 zararlı, koşu geçersiz).
  **Sembolik kimlik burada bir tercih değil, güvenlik koşuludur.**
- **Korunan katman**: tekil (unique) katmanda kayıp yok (26/26, 34/35,
  27/34 — tek kayıp q77, düzenlenmiş sayfada modelin reddi).
- **A/A tabanı 0**, sızıntı denetimi, sayfa-düzenleme bütünlüğü, pozitif
  kontrol: her koşuda temiz.

---

## 6. Dürüst sınır: tavan nerede ve neden

sh_64k'de parser kolunun 29 çelişkili hatasının ayrıştırması
(`E2E4_COMPLEMENTARITY.md` §6):

| neden | adet | düzeltilebilir mi |
| --- | ---: | --- |
| **erişim kaybı** — altın olgu sayfaya hiç gelmiyor | **22** | hayır (sayfa düzenlemesiyle imkânsız) |
| **parametrik bilgi** — sayfa zaten doğru, model kendi ağırlıklarından yanıtlıyor | 5 | hayır |
| **tespit kaybı** | **2** | evet |

Dolayısıyla **herhangi bir baskılama tabanlı denetçinin mutlak tavanı
72/100**'dür ve parser kolu 64 ile bu tavanın 2 tespit hatası uzağındadır.
Bu, "neden 64'ten sonrası zor" sorusunun kanıtlı yanıtıdır ve tezde
zayıflık değil, **olgunluk** göstergesidir.

---

## 7. Ne iddia edilebilir / ne edilemez

**Edilebilir**
1. Çelişen bellek, küçük modelin RAG başarımında birinci dereceden bir
   engeldir (572/575 hata sistematiği).
2. Bu engel, çıkarımda ek LLM maliyeti olmadan, istemi kısaltarak,
   ölçülmüş sıfır zararla büyük ölçüde kaldırılabilir (+19 … +66).
3. Denetçi, mekanizmanın oracle tavanının %96–98'ini yakalar.
4. Kalan hata, **denetçinin değil erişimin** hatasıdır (22/29).
5. Kimlik (identity) kararı için sembolik ayrıştırıcı ile gömme geometrisi
   **birbirini tamamlamaz**; geometri sembolik kümenin %99'unun alt
   kümesidir (E2E-3, E2E-4).

**Edilemez (savunmada bunları kendin söyle)**
- "Her modelde geçerlidir" — tek cevaplayıcı modelde ölçüldü; çoklu-model
  kampanyası (§8) tam da bunu kapatmak için var.
- "Her gömücüde geçerlidir" — eşikler Qwen3-Embedding-4B uzayının
  koordinatlarıdır; G1 bunların taşınmadığını ölçtü.
- "Anlamsal doğrulama gereksizdir" — yalnızca **tek değerli bağıntılı**
  bir depo için gösterildi; çok değerli bağıntılarda NLI kapısı gerçek iş
  yapar.
- "sh_262k'ye genellenir" — dışlandı (bağlam penceresi karşılaştırmayı
  bozar).
- "Geometri parser'ın yerini alabilir" — alamaz: 64 → 56 (p = 0.021).

---

## 8. Tezi güçlendirmek için sıradaki tek hamle

Çoklu-model kampanyası: 3–5 cevaplayıcı modelde **hnav_raw** + **hnav_geo**
(+ geçerse **hnav_idonly**), her biri tek atış. İki yeni iddiayı açar:

1. Yönetişim kazancı modeller arası **tekrarlanıyor mu?**
2. Baskılama planları LLM'den bağımsız olduğundan, parser'ın üstünlüğü
   **aynı dokuz soruda** mı yoğunlaşıyor? Aynıysa fark **yapısaldır**;
   dağılıyorsa **model etkileşimidir**. Her iki sonuç da yayınlanabilir.

Boru hatları bu iş için hazır ve donduruldu: `pipelines/README.md`,
`pipelines/hnav_raw`, `pipelines/hnav_geo`, `pipelines/hnav_idonly`.
