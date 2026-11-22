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
  dosyalarını doğrular ve puanlar), 8 test, alt ajan tanımı `.claude/agents/pair-annotator.md`.
  1. aşama için 5.397 çiftlik 54 kör parti üretildi
  (`stage0_results/conflict_pairs/model_annotation/batches/stage1/`): dengeli değerlendirme
  kümesi ile `rejected` ve `discovered_unverified` katmanları, pilot çiftleri hariç.
  Etiketleme henüz yapılmadı.
