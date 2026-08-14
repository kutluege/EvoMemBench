# KAPI KARARI — H-Nav Stage-0 → Stage-1 Geçiş Değerlendirmesi

> **KARAR DURUMU: `TASLAK / BEKLEMEDE`** — m3'ün son subset'i (sh_262k), m4 ve
> `report.py --strict` henüz tamamlanmadı (box'a erişim 14 Ağustos ~18:20'den beri
> kesik; m3 nohup altında box'ta koşuyor/koştu). Bu dosya, eksik hücreler
> doldurulup **KARAR: GO / NO_GO** satırı yazılana kadar Stage-1'i TETİKLEMEZ.
> Tarih: 2026-08-15 (gece taslağı). Kaynaklar: `DURUM_RAPORU_STAGE0.md`,
> `stage0_results/`, commit geçmişi.

---

## 1. Bileşen bazında ön-değerlendirme tablosu

| # | Bileşen | Ölçüm | Sonuç | Ön-verdikt | Verdikt tipi |
|---|---|---|---|---|---|
| 1 | Geometri öncülü (çakışan çiftler ayrışır) | T1/M1 | median sim ~0.964 vs kontrol ~0.60; AUC ≥ 0.9999, 4/4 subset; S3 ateşlemedi | **GO** | detection |
| 2 | Geometri gruplama (regex-oracle'a karşı) | T2/M1b | F1: 0.892 (6k) → 0.757 (262k); precision 0.83–0.90 | **GO (beyanlı)** — F1 mağaza büyüklüğüyle düşüyor, 262k'daki 0.757 açıkça raporlanacak | detection |
| 3 | Replika sadakati (canlı indeksle özdeşlik) | m0 | top1=topk=τ=1.0000, 400/400 çift, 4/4 subset (fp32 düzeltmesi sonrası) | **GO** | benchmark |
| 4 | Retrieval sinyalleri dejenere mi? | m2 | **NOT_DEGENERATE 4/4** — önceki BFCL dejenerasyon bulgusunu bu arenada ÇÜRÜTÜR. Margin p50 1.235→0.318, etkin komşuluk 1.44→36.41 (6k→262k) | **GO** | detection |
| 5 | Shadow-mode nötrlüğü | t4/S2 | off↔shadow fark %2.42 < off↔off gürültü tabanı %3.04; TOST ±2.0 marjda eşdeğerlik (p=0.0008/0.017). Kullanıcı kararı (14 Ağu): **PASS-by-statistical-equivalence** | **GO (uyarlanmış kriter, tam beyan)** | benchmark |
| 6 | Müdahale tavanı (headroom) | m3 | `BEKLİYOR — sh_262k + nihai JSON'lar`. Kısmi (sh_32k): yazıların %36,1'i bayat-çakışan; would-intervene %10,4 → veto sonrası %1,6; READ_CONFLICT=1.00, READ_STALE=1.00 | `BEKLİYOR` | policy |
| 7 | Marginal-diff testi | m4 | `BEKLİYOR` (yalnız kalibrasyon split'i) | `BEKLİYOR` | detection |
| 8 | Bütünleşik rapor | report --strict | `BEKLİYOR` | — | — |

**Kalibrasyon eşikleri (dondurulmuş, yalnız sh_6k+sh_32k):** `nmargin<0.0048`,
`H_z>1.9569`, `r_min<0.1924`. Held-out (sh_64k/sh_262k) üzerinde hiçbir eşik
ayarlanmadı ve ayarlanmayacak.

## 2. Nihai karar için eksikler

1. **M3 headroom (4/4 subset):** could-change-correctness oranları = Stage-1'de
   kazanılabilecek MAKSİMUM. Karar ancak bu tavan görülünce verilebilir — tavan
   gürültü tabanının (±2–4 puan) altındaysa NO_GO/REDESIGN tartışılır.
2. **M4** kalibrasyon-split sonucu.
3. **`report.py --strict`** çıktısı (`STAGE0_REPORT.md`).

## 3. Substrat bulguları (tez için, karar bağlamı)

- **S1/bf16 olayı:** :8001 embed sunucusu bf16'ya düşünce top-k özdeşliği 0.24'e
  çöktü; fp32 ile 1.0000. Kapının gerçek bir hassasiyet hatasını yakalaması —
  metodolojinin çalıştığının kanıtı olarak teze girecek (kullanıcı onayı 14 Ağu).
- **Değerlendirme substratı deterministik DEĞİL:** temperature=0'da iki özdeş
  baseline koşusu 100 çıktının 5'inde farklı, exact_match 26.0 vs 30.0
  (±2–4 puan gürültü tabanı). vLLM sürekli-batçleme + prefix-cache kaynaklı;
  seri özdeş istekler bitwise deterministik, çapraz-istek durumu değil.
  **Stage-1 karşılaştırma tasarımı tek-koşu FARKINI sonuç sayamaz** — çok-koşu
  ortalaması + eşleştirilmiş analiz + gürültü tabanının üstünde etki büyüklüğü şart.
- **Bağlam penceresi:** benchmark istemleri sh_64k'da ~56k, sh_262k'da 100k+
  token'a ulaşıyor; 32k'lık sunucuda bu subset'ler hiç koşamazdı. Stage-1
  sunucu konfigürasyonu buna göre boyutlandırılmalı.

## 4. Beyan edilecek sapmalar (şimdiye kadar birikenler)

1. Embed sunucusu fp32 servis (checkpoint native bf16) — kampanya dtype sabitlemesi gereği; kullanıcı onaylı.
2. S2 kriteri bayt-özdeşlikten istatistiksel eşdeğerliğe uyarlandı (ön-kayıtlı protokol `7cb8323`; deterministik substrat fiziksel olarak kurulamadı — kanıtıyla).
3. m3 LLM'i :8000 yerine özel :8003 sunucusunda (pencere gereksinimi); subset başına `max-model-len` farkları katmanlı raporda beyanlı.
4. M0 kapsamı 400/400 (protokol hedefi 1.000; arena eksiksiz tarandı) — kullanıcı onaylı.
5. `--max-model-len 16384` embed sunucu bayrağı (fp32 OOM önlemi; davranışsal etkisi yok).
6. Chunker sınır mekanizması: fact 307 kaybı + sarkan seri düzeltmesi (`explode_facts`), test edilmiş.
7. Kullanıcının :8000 sunucusu 14 Ağu akşamı kullanıcı talimatıyla durduruldu (gürültü tabanı karakterizasyonu ÖNCE tamamlandı; Stage-1 karşılaştırmaları kendi kontrol ettiğimiz sunucuda koşacak).

## 5. Stage-1 ilk adım önerisi (karar GO ise — TASLAK)

- **Tek bileşen:** okuma-yolu (read-path) müdahalesi DEĞİL, önce **yazma-yolu
  stale-conflict tespiti** — M1b geometri F1'i (0.76–0.89) + m3 yazı sinyalleri
  (%36 bayat-çakışan taban oranı) en güçlü kanıt burada. (m3 nihai sayıları bu
  öneriyi değiştirebilir — read-side READ_STALE=1.00 sinyali de aday.)
- **Eşikler:** yukarıdaki dondurulmuş kalibrasyon eşikleri; held-out'a TEK ATIŞ.
- **Karşılaştırma protokolü (Agent C):** aynı ajan/retriever/LLM, HNAV_MODE=off
  vs live; N≥5 koşu/kol; eşleştirilmiş analiz; başarı = doğruluk artışı + token
  verimliliği BİRLİKTE, harm≈0; ön-kayıt zorunlu.

## 6. KARAR

> **BEKLEMEDE.** m3/m4/report tamamlanınca bu bölüm doldurulacak:
> bileşen 6–8 verdiktleri + nihai GO/NO_GO + gerekçe. Stage-1 ajanı ancak bu
> bölümde açık "**KARAR: GO**" satırı yazılıysa otomatik başlar
> (kullanıcı yetkilendirmesi 2026-08-14).
