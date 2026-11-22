# Natural Language Processing (Cambridge): what it expects, and how to bring "Read-time removal of superseded facts" in line before 7 January 2027

The manuscript fits the journal's scope. The main risks are rigour and register, not topic. Do three things before you submit: get human validation of a label sample, add a fact-disjoint test set, and run the cheap end-to-end baselines. Then cut the body from about 15,000 to about 11,500 words by moving the development history and secondary analyses into supplementary material. Rewrite it as a paper, not a project log.

Labels used throughout: **[J]** = stated by the journal or Cambridge; **[S n/M]** = observed in n of M sampled papers; **[I]** = my inference. M = 8 (see Part 9). The sample is smaller than the 15–25 you asked for; see Part 10.

## TL;DR
- **Fit and rules:** the journal is fully gold open access (APC £2,610 / US$3,655). The TÜBİTAK ULAKBİM–Cambridge agreement for 2026–2028 has an unlimited national quota (Istanbul Medipol University Library notice: "National Quota (Türkiye): Unlimited") and should cover a Boğaziçi corresponding author. Review is single-anonymised. The Article guideline is "~8,000–12,000 words" and an abstract of "approximately 300 words". Competing-interest, funding, data-availability and ethics statements are mandatory, and AI use must be declared with tool, version and dates. [J]
- **What accepted papers do:** most of the closest papers build or validate data with human annotators (6/8). Most work on a language other than English (5/8). Typical length is 23–35 printed pages. Received-to-accepted time had a median of 380 days (range 111–453, N = 7). [S]
- **Top fixes, ranked:** (1) two-annotator validation of the GPT-5 mini labels, with agreement figures; (2) a new fact-disjoint test set, so sh_64k stops being the headline "transfer" result; (3) raw-cosine+recency and NLI+recency end-to-end baselines, plus one generative extract-then-keep-newest comparator; (4) remove internal jargon, development narrative and figure–text contradictions; (5) fill every [CONFIRM] placeholder; (6) explain why the work is English-only. LongMemEval and record-level retrieval can be dropped or deferred. [I]

## 1. The journal in half a page

- **What it publishes.** It welcomes "papers reporting research with a clear potential for practical application". Its aim is "to bridge the gap between traditional computational linguistics research and the implementation of practical applications".\[1\] It "particularly encourages contributions reporting findings from multilingual and low-resource language projects" and "welcomes innovative studies employing state-of-the-art deep learning methods and large language models".\[2\] Question answering and information retrieval are listed in scope.\[1\]\[3\]\[4\]\[5\] [J] (journal home page; author instructions; Mitkov 2026 editorial note, doi:10.1017/nlp.2026.10016)
- **Name and access.** Natural Language Engineering (1995–2024) became Natural Language Processing in 2024.\[1\] The journal is now "a fully open-access journal".\[6\]\[7\] [J] (Mitkov 2024 editorial note, doi:10.1017/S1351324924000020)
- **Who decides.** The Executive Editor is Ruslan Mitkov (Lancaster University and University of Alicante).\[1\] In February 2026 the Associate Editors were Asif Ekbal, Saad Ezzini, Hansi Hettiarachchi, Véronique Hoste, Dimitar Kazakov, Salima Lamsiyah, Young-Suk Lee, Aline Paes, Sandra Kübler, Diana Inkpen, Burcu Can and Tharindu Ranasinghe.\[1\]\[5\] Kenneth Church edits the Emerging Trends column and Robert Dale edits Industry Watch.\[2\] [J] (doi:10.1017/nlp.2026.10016)
- **How review works.** Review is single-anonymised: reviewers see your names, and you do not see theirs. The review-process page says all Articles "will be peer-reviewed by **at least 3 external reviewers**". The journal's publishing-ethics page says "generally a minimum of two". Plan for three. Appeals go to the Executive Editor at NLP@cambridge.org.\[8\]\[9\]\[10\] [J] (Review process page; Publishing ethics page)
- **Workflow change.** "The journal will adopt a continuous publication model from 2027 onwards."\[2\] [J] (doi:10.1017/nlp.2026.10016)
- **Metrics.** Scimago SJR 2025 is 0.502 with best quartile Q1 (Scimago, source ID 21101287785).\[11\]\[12\] For the JCR, the journal's own home page shows "2025 Impact Factor: 163 out of 210 Computer Science, Artificial Intelligence – 2025 Journal Citation Reports © Clarivate Analytics". By my calculation that rank is in Q4; the JIF value itself was not in the retrieved text. Wikipedia cites 2.3 from the 2023 JCR, under the old title Natural Language Engineering, and Mitkov's 2024 note says "Impact Factor 2.5" (doi:10.1017/S1351324924000020). Scimago coverage for the new title starts in 2025, so its history is split from Natural Language Engineering.\[12\] [J/I]

## 2. Hard rules

1. An Article is "~8,000–12,000 words", described as "a detailed and rigorous original study which contributes directly to its field".\[13\] [J] (Preparing your materials)
2. The abstract must be "approximately 300 words".\[13\] [J] (same page)
3. Give 3–5 keywords.\[13\] [J] (same page)
4. The first page must give the title and every author's name and email address.\[13\] [J] (same page)
5. Submit the first version as a single PDF with figures and tables embedded, uploaded as "Main Document". LaTeX with the journal class is "strongly encouraged". LaTeX source is required after acceptance.\[4\] [J] (same page)
6. Submission is through ScholarOne at mc.manuscriptcentral.com/nlp.\[4\] [J] (Submit manuscript panel)
7. The corresponding author must use an ORCID iD when submitting.\[4\] [J] (same page, "ORCID")
8. A conflict-of-interest statement is required. If there is none, use the wording "Competing interests: The author(s) declare none".\[4\] [J] (same page)
9. A funding disclosure statement is required.\[4\] [J] (same page)
10. A data availability statement is required, following the Research transparency page.\[4\] [J] (same page)
11. An ethics statement is required. If no approval was needed, write exactly "Ethical approval was not required."\[4\] [J] (same page)
12. Declare AI use that generated text or images, or that analysed or extracted data. Give the name and version, the dates of use, how others can access it and a full description. Data-analysis use goes in the methods section; writing help goes in the acknowledgements. AI cannot be an author.\[4\] [J] (same page, "Use of AI tools")
13. CRediT and acknowledgements are optional.\[4\] [J] (same page)
14. Use author–date citations, for example (Lee and Devore 1968: 236), with "et al." for three or more authors. Order grouped citations by date. Use minimum capitalisation in titles.\[4\] [J] (same page)
15. Use no more than three levels of numbered subheadings.\[4\] [J] (same page)
16. Write numbers out up to 100 unless they are precise measurements. Write "per cent", not %. Use commas in numbers of four or more digits.\[4\] [J] (same page)
17. Cite every figure in the text in order. Captions must be self-explanatory. "Tables must have sources". Table headings use sentence case.\[4\] [J] (same page)
18. Figures must meet WCAG 2.1 AA, which covers colour, contrast and clarity. Every figure needs alt text. Authors are encouraged to supply it; if they do not, it "will be machine generated" at proof stage.\[4\] [J] (same page, "Accessibility")
19. Supplementary material is published online but is not typeset or copyedited. It is part of the formal record and can only be changed through a correction.\[4\] [J] (same page, "Supplementary materials")
20. Posting a preprint is not prior publication. Follow the Cambridge preprint policy.\[4\] [J] (same page)
21. All authors agree to be invited to review other submissions.\[4\] [J] (same page)
22. The APC is £2,610 / US$3,655 because the journal is wholly gold OA. Editors cannot grant waivers.\[14\]\[15\] [J] (Fees and pricing; Open access options)
23. Türkiye agreement: TÜBİTAK ULAKBİM and Cambridge signed an EKUAL Read & Publish agreement running from 1 January 2026 to 31 December 2028; the signing date was 16 February 2026. Istanbul Medipol University Library's notice says: "National Quota (Türkiye): Unlimited… The agreement covers unlimited Open Access (OA) article publishing in both hybrid journals and gold (fully) open access journals." The corresponding author must be an authorised user at an EKUAL member institution. [J, via Turkish university library notices: Medipol, Bilkent, Adnan Menderes University] Confirm on Cambridge's eligibility checker that Boğaziçi is included and that this journal is on the "Funded Journal List". [I]

## 3. Unwritten expectations

1. **Build or validate the data with human annotators.** Seen in 6/8, e.g. the Finnish corpus "fully manually annotated" (doi:10.1017/S1351324923000086) and the Polish dataset with expert linguists (doi:10.1017/S1351324923000220).\[16\]\[17\]\[18\] Only 1/8 relied on LLM-generated references (GPT-4 reference answers, doi:10.1017/nlp.2024.53), and it reported no human check.\[19\] None of the 8 used LLM-only gold labels for a classification resource.
2. **Release data and code.** Release was verified in 4/8, e.g. the Turku Paraphrase Corpus (CC-BY-SA, GitHub and Hugging Face)\[16\] and the Urdu corpus, models and code (doi:10.1017/S1351324923000189).\[16\]\[20\] It was not checked in the other 4.
3. **Work on a language other than English.** Seen in 5/8: Polish, Finnish, Urdu, Turkish and Russian, e.g. doi:10.1017/S1351324923000505 and doi:10.1017/nlp.2024.38.\[21\]\[22\]\[23\] I did not verify how the English-only papers justified the choice.
4. **Run long.** Seen in 8/8: 23–35 printed pages, median about 29.5. By my estimate of about 440 words per page, which includes references, 5/8 are above 12,000 words. [I] So the guideline is a target, not a hard cap. But nothing in the sample is as dense as 34 pages with 20 figures and tables.
5. **Expect a long review.** Received to accepted took a median of 380 days, with a range of 111–453 (N = 7). Accepted to online took a median of 58 days, with a range of 34–113. Fastest: doi:10.1017/nlp.2024.53 at 111 days.\[19\] Slowest: doi:10.1017/S1351324923000220 at 453 days.
6. **Frame the contribution as a resource or as practical use.** 4/8 lead with a new resource (Polish, Finnish, Urdu, CoAT) and 3/8 with a method (thought flow, semantic-similarity rewards, lightweight clinical models). 1/8 is a practical comparison of RAG configurations that also reports runtime, tokens and hardware use (doi:10.1017/nlp.2024.53).\[19\]
7. **Report efficiency or cost when the method is practical.** Seen in 2/8 verified: Şakar and Emekci on runtime and tokens, and the compact clinical models (doi:10.1017/S1351324923000542).\[19\]\[24\]
8. **Keep abstracts short and plain.** Verified in 4/8, at roughly 150–300 words, with at most a few numbers each. Example: the RAG paper's abstract is about 150 words with one number.\[25\]

## 4. Suggestions, ordered by effect on acceptance

| # | What to change | Where | Why | Days | Label |
|---|---|---|---|---|---|
| 1 | Have two annotators label a stratified sample of 400–600 pairs (all 282 update-only, all 105 quarantined, core pairs and hard negatives). Report Cohen's κ, the agreement of each annotator with GPT-5 mini, and how many label flips change AUROC. | §5.2, §6.1, Limitations | Pattern 1. LLM-only gold labels are absent from the sample. | 4–6 | must |
| 2 | Build an independent fact-disjoint test store of about 400 questions with no subject–relation overlap with calibration. Make it the headline result and keep sh_64k as "partial overlap". | §5.1, §6, abstract | The "frozen transfer" wording invites a rigour rejection under rule 1 ("rigorous original study"). | 7–10 | must |
| 3 | Add end-to-end raw cosine + recency, NLI-only + recency, and serial-sorted page baselines. They reuse existing components. | §6.4, Table 8 | Missing baselines are a standard reviewer objection [I]. They are cheap. | 3–4 | must |
| 4 | Remove project vocabulary: "H-Nav", campaign, arms, page, pool, plan, A/A floor, CES, gold_update, quarantined, "the runner refuses". Use standard terms: condition, retrieved context, deletion set, etc. Rename the method descriptively. | Whole text, figures | Scope stresses bridging research and practice. None of the sampled papers reads like a project log. [I] | 2–3 | must |
| 5 | Fix the figure–text contradictions: no "held-out sh_64k"; "ABTT cosine", not "whitened cosine"; the Fig. 7A table reference; remove file names from Figs 1–2; do not use colour alone; drop logo icons; larger text. | Figs 1–7 | Rule 17 (self-explanatory captions) and rule 18 (WCAG 2.1 AA). | 2 | must |
| 6 | Fill every [CONFIRM] placeholder: AI declaration (GPT-5 mini snapshot and dates of use in §5.2, writing help in acknowledgements), funding, competing interests, an archival DOI (Zenodo) for the code and data, ethics, CRediT, vLLM version, Holm (1979) reference. | End matter, §5.2 | Rules 8–12. | 1–2 | must |
| 7 | State the missed preregistered endpoint in Results §6.3 and in the abstract's final clause, not only in §5.1. | §6.3, abstract | A buried miss reads as concealment; stated openly it shows integrity. [I] | 0.5 | must |
| 8 | Add a paragraph explaining English-only: templated English benchmark, encoder language coverage. Optionally run a 100-pair translated Turkish probe of the pair-level geometry. | §3.2, Limitations | The journal "particularly encourages" multilingual work;\[5\] 5/8 papers are non-English. | 0.5 (paragraph); 4 (probe) | must / nice to have |
| 9 | Add a generative "extract then keep newest" comparator with one small LLM, reported on accuracy and cost. | §6.4 | Reviewers will ask whether an LLM call is cheaper and better. [I] | 3–5 | should |
| 10 | Add a second, non-Qwen encoder at pair level, e.g. bge-m3 or e5. | §6.1 | One encoder means a single point of failure. | 2 | should |
| 11 | Measure wall-clock latency and memory for the filter against an LLM call. | §4.9 | Pattern 7; your practical framing needs a number. | 1–2 | should |
| 12 | Cut the abstract to ≤300 words with at most 5 numbers. Lead with the problem and the practical outcome. | Abstract | Rule 2; pattern 8. | 0.5 | must |
| 13 | Cite 8–10 papers from this journal (list below). | §1, §2, §8 | Shows fit; editors read the reference list. [I] | 0.5 | should |
| 14 | LongMemEval feasibility check. | — | High effort and a new pipeline. Mention it as future work. | 5–10 | can drop |
| 15 | Record-level retrieval. | — | Changes the system under test; save it for a follow-up paper. | 5+ | can drop |

**Verdicts on the eight planned items, ranked:** (1) two-annotator validation: must. (2) new ~400-question test set: must. (3) stronger end-to-end baselines: must. (4) generative comparator: should. (5) cost/latency measurement: should. (6) second encoder: should. (7) LongMemEval: can drop. (8) record-level retrieval: can drop. [I]

The must items take about 18–24 working days. There are about 32 working days to 7 January. That leaves room for two of the should items. [I]

**Papers from this journal to cite, and where:**
- §1 / §2.1, RAG: Church et al. 2024, "Emerging trends: a gentle introduction to RAG" (doi:10.1017/S1351324924000044), already cited. Şakar and Emekci 2025, "Maximizing RAG efficiency" (doi:10.1017/nlp.2024.53), for vector stores, embedding models and cosine filters.\[19\]
- §1 / §8.2, small models: Church 2026, "Emerging trends: Supercomputers and clouds are so last century" (NLP 32(2):224–231).\[26\] Rohanian et al. 2024, "Lightweight transformers for clinical natural language processing" (doi:10.1017/S1351324923000542).\[24\]
- §1 / §2.2, hallucination and evaluation: Church and Yue 2023, "Emerging trends: Smooth-talking machines" (doi:10.1017/S1351324923000463).\[27\] Church and Alonso 2024, "Emerging trends: evaluating general purpose foundation models" (doi:10.1017/S1351324924000068).\[28\]
- §2.3, embeddings: Hou et al. 2024 (doi:10.1017/S1351324924000019), already cited. Yang et al. 2025, "Semantic enrichment of neural word embeddings" (doi:10.1017/nlp.2025.10005).\[29\]
- §2.5, identity, NLI and similarity: Beken Fikri, Oflazer and Yanıkoğlu 2024 (doi:10.1017/S1351324923000505), which uses NLI- and STS-fine-tuned cross- and bi-encoders.\[21\] Kanerva et al. 2024, Finnish paraphrase (doi:10.1017/S1351324923000086).\[16\] Ziembicki et al. 2024, Polish NLI (doi:10.1017/S1351324923000220).\[17\]\[18\]
- §8.1, evaluation culture: Church and Kordoni 2022, "Emerging Trends: SOTA-chasing" (doi:10.1017/S1351324922000043).\[30\] Use it to frame the result as diagnosis rather than leaderboard gain.

**Likely handling editors** [I, from my general knowledge of their published work, not verified in this research]: Young-Suk Lee (IBM Research; QA, conversational and retrieval-augmented systems), Hansi Hettiarachchi or Tharindu Ranasinghe (semantic similarity, embeddings), and Diana Inkpen (semantic similarity, text classification). All of them would value clear baselines, human-validated data and reusable resources.

## 5. What to cut or move to supplementary material

Target: body about 11,500 words including tables, abstract ≤300 words. [J for the guideline; I for the plan]

| Item | Action | Saving (words) |
|---|---|---|
| Development history: span check "for fidelity", 81 chunk-reranking points, write-time gate, fp8 KV-cache incident | Move to Supplement S1 "Development log"; one sentence in the main text | ~900 |
| §2 Related Work, 5 subsections | Merge into 3: memory and conflicts; embedding geometry; identity and NLI | ~1,000 |
| §3.1 formal definitions | Keep key, version pair and look-alike; move the rest to S2 | ~300 |
| §4.7–4.8 artifact freezing and SHA-256 | One sentence; details to S2 | ~300 |
| §6.5 deletion vs placement (Table 9), §6.6 plan statistics (Table 10) | Move to S3; keep one summary sentence | ~700 |
| §7.2 component analysis | Keep the four headline numbers; move the rest | ~400 |
| §8.1–8.4 discussion | Merge into one "Implications" subsection | ~600 |
| Appendices A–B (Tables 12–13) | Move to S4 | ~300 |
| **Total** | | **~4,500** |

This brings the body to about 10,500–11,000 words and about 14 figures and tables. The journal does not say whether tables, captions, references or appendices count toward the limit. Ask the office (Part 10). [J/I]

## 6. Risks: the three likeliest reasons for desk rejection or a negative review

1. **The evidence does not support the claim.** One templated benchmark, labels from one LLM, and a largest store that overlaps calibration. Pre-empt: items 1–3 in Part 4. Say "fact-disjoint test" in the abstract. Report κ. Put the oracle gap (50–81 per cent recovered) up front as an honest ceiling. [I]
2. **It reads as an internal engineering report.** Jargon, development narrative, preregistration deviations scattered through the text, and figures that contradict the text. Pre-empt: items 4, 5 and 7. Put a single "Protocol and deviations" paragraph in §5 and keep everything else in the supplement. [I]
3. **Administrative return.** Placeholders, length well above the guideline, a missing AI declaration or missing statements. Pre-empt: item 6, the cuts in Part 5, and the checklist in Part 7. [J/I]

**Reliance on preprints.** I could not verify the reference-list profiles of the sampled papers. One sampled paper cites blogs and framework documentation (doi:10.1017/nlp.2024.53),\[19\] so non-archival sources alone are not disqualifying. Still, replace preprints with peer-reviewed versions wherever they exist: cite MemoryAgentBench as Hu, Wang and McAuley 2026, "Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions", ICLR 2026 (openreview.net/forum?id=DT7JyQC3MR), not the arXiv version. Keep 2026 arXiv comparators to Related Work, not to your core claims. [S 1/8; I]

## 7. Pre-submission checklist

- [ ] PDF built from the journal LaTeX class; figures and tables embedded; pages numbered.
- [ ] Title page has both names and emails; affiliation format "Institute…, Boğaziçi University, İstanbul, Türkiye".
- [ ] Abstract ≤300 words; 3–5 keywords.
- [ ] Body about 11,500 words; no more than three heading levels.
- [ ] Author–date references; Holm (1979) checked; preprints upgraded to published versions.
- [ ] Every table has a source; headings in sentence case; captions self-explanatory.
- [ ] Figures readable in greyscale; no file names; no "held-out" or "whitened" labels; alt text drafted for all 7 figures.
- [ ] Numbers style: "per cent" written out; numbers up to 100 in words where they are not measurements (or leave for copyediting).
- [ ] Competing interests ("The author(s) declare none" if true).
- [ ] Funding statement; list grant or project numbers for the TÜBİTAK ULAKBİM and BSC compute allocations if they were awarded competitively [I].
- [ ] Data availability with an archival DOI and the MIT-licence note for MemoryAgentBench-derived data.
- [ ] Ethics: "Ethical approval was not required." Annotator consent noted if you add human annotators.
- [ ] AI declaration: GPT-5 mini snapshot, dates and access in §5.2; any writing assistance in acknowledgements.
- [ ] CRediT roles.
- [ ] Corresponding author's ORCID linked in ScholarOne.
- [ ] Supplementary file(s) final as-is, because they are not copyedited.
- [ ] EKUAL eligibility confirmed for Boğaziçi and this journal.

## 8. Five points for the cover letter

1. The problem is practical: superseded facts in agent memory make small models answer with stale values. That matches the journal's aim of bridging research and practice.
2. The method needs no schema, parser or generative call at read time. It suits small and on-device models, the setting Church (2026) predicts will grow.
3. The evidence: pair-level AUROC 0.972 against 0.893 for raw cosine; a fact-disjoint test (new); five answering models; Holm-corrected tests.
4. A released, human-validated resource of 54,569 adjudicated fact pairs, with κ reported.
5. Limits stated plainly: English-only templated facts, a gap to the schema-keyed oracle, and one missed preregistered endpoint.

## 9. Evidence table of sampled papers

Dates are as printed on page 1. R = received, Rev = revised, A = accepted, O = first online. "nv" = not verified.

| Paper (DOI) | R / Rev / A / O | R→A (days) | Pages | Data and language | Human annotation | Release | Framing |
|---|---|---|---|---|---|---|---|
| Şakar and Emekci, Maximizing RAG efficiency (10.1017/nlp.2024.53) | 29 May 24 / 17 Sep 24 / 17 Sep 24 / 30 Oct 24 | 111 | 25 | 3 datasets, English; GPT-3.5, GPT-4o-mini, Command-R; no significance tests seen | None; GPT-4 reference answers\[19\] | nv | Practical comparison |
| Schuff, Adel and Vu, Thought flow nets (10.1017/nlp.2024.41) | 2 May 23 / 19 Apr 24 / 16 May 24 / 6 Sep 24 | 380 | 32 | QA; language nv | Crowdsourcing user study\[31\] | nv | Method |
| Shamardina et al., CoAT (10.1017/nlp.2024.38) | 1 Jun 23 / 19 May 24 / 19 May 24 / 6 Sep 24 | 353 | 26 | Russian, 6 domains, 13 generators | Human detection baseline | Yes | Resource\[23\] |
| Ziembicki, Seweryn and Wróblewska, Polish NLI (10.1017/S1351324923000220) | 4 Jan 22 / 27 Feb 23 / 2 Apr 23 / 1 Jun 23 | 453 | 32 | Polish, 2,432 + 3,035 pairs | Expert linguists\[18\] | nv | Resource and linguistic insight |
| Kanerva et al., Finnish paraphrase (10.1017/S1351324923000086) | 1 Jul 22 / 21 Dec 22 / 17 Jan 23 / 16 Mar 23 | 200 | 35 | Finnish, 104,645 pairs | Fully manual | Yes | Resource\[16\] |
| Iqbal et al., Urdu paraphrase (10.1017/S1351324923000189) | 9 Mar 22 / 16 Mar 23 / 17 Apr 23 / 29 May 23 | 404 | 31 | Urdu, 3,147 pairs\[32\] | Manual tags | Yes | Resource and method |
| Beken Fikri, Oflazer and Yanıkoğlu, summarization with similarity rewards (10.1017/S1351324923000505) | 15 Aug 22 / 12 Sep 23 / 27 Sep 23 / 31 Oct 23 | 408 | 23 | Turkish; NLI-TR and STS | Human-evaluation correlation\[21\] | nv | Method |
| Rohanian et al., Lightweight clinical transformers (10.1017/S1351324923000542) | nv / nv / nv / 12 Jan 24 | nv | 28 | Clinical; NLI, RE, NER | nv | Yes | Method (efficiency)\[24\] |

**Summary.** Received to accepted: median 380 days, range 111–453, N = 7. Accepted to online: median 58 days, range 34–113. Note that 5 of the 7 dated papers were received before 2024 but appeared in 2024 issues (vol. 30). [S]

**Also seen, metadata only** (fields not verified): DocSpider (10.1017/nlp.2024.63); low-resource QA (10.1017/nlp.2024.13); EHMMQA (10.1017/nlp.2024.12); in-context example selection (10.1017/nlp.2025.10010); LLMs in judicial assistance (10.1017/nlp.2026.10014);\[33\] semantic enrichment of embeddings (10.1017/nlp.2025.10005, 27 pp).\[34\] A Crossref search found no 2025–2026 Articles in this journal on hallucination, knowledge conflicts or agent memory.\[35\] Your topic is therefore new to the journal. That is a plus, but it also means a small reviewer pool. [I]

## 10. Unknowns and questions for the editorial office (NLP@cambridge.org)

- Does the 8,000–12,000-word guideline include references, tables, captions and appendices? Will a body of about 11,500 words plus a supplement be acceptable?
- What criteria and form do reviewers get? I could not open the "Instructions for peer reviewers" page.
- What are the desk-rejection grounds, the median time to first decision and the acceptance rate? None of these is published.
- Does the ScholarOne form ask for suggested or opposed reviewers? Not verified.
- Is Boğaziçi an EKUAL member, and is this journal on the 2026–2028 Funded Journal List? Ask ULAKBİM (ukg@ulakbim.gov.tr) or use the Cambridge eligibility checker.
- What is the official 2025 JIF value? The journal home page gives only the JCR rank ("163 out of 210 Computer Science, Artificial Intelligence"), which I calculate as Q4.
- Sample gaps: I verified only 8 Articles, and only 7 have dates. These fields were not verified for most papers: statistical tests, agreement figures, limitations and ethics sections, abstract length, and reference profiles. The editorial-board web page and the research-transparency page rendered without their body text.

## Kaynaklar

1. [Natural Language Processing](https://www.cambridge.org/core/journals/natural-language-processing)
2. [Natural Language Processing (2026), 32, pp. 111–112 doi:10.1017/nlp.2026.10016](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/4BA42158B1E3455E23DDB8C131FEB2E3/S2977042426100168a.pdf/editorial_note.pdf)
3. [Natural Language Engineering](https://www.cambridge.org/core/journals/natural-language-engineering/emerging-trends)
4. [Preparing your materials](https://cambridge.org/core/journals/natural-language-processing/information/author-instructions/preparing-your-materials)
5. [Editorial note](https://www.cambridge.org/core/journals/natural-language-processing/article/editorial-note/4BA42158B1E3455E23DDB8C131FEB2E3)
6. [Editorial Note](https://www.cambridge.org/core/journals/natural-language-engineering/article/editorial-note/7A063400A61FADF7FE38FAB0D32F7EE1)
7. [Natural Language Processing (journal)](<https://en.wikipedia.org/wiki/Natural_Language_Processing_(journal)>)
8. [Review process](https://www.cambridge.org/core/journals/natural-language-processing/information/peer-review-information/review-process)
9. [Peer review information](https://www.cambridge.org/core/journals/natural-language-processing/information/peer-review-information)
10. [Publishing ethics](https://www.cambridge.org/core/journals/natural-language-processing/information/journal-policies/publishing-ethics)
11. [Natural Language Processing](https://library.wur.nl/WebQuery/rubrowser/96471)
12. [Natural Language Processing - SJR, Quartile, H-index](https://www.scimagojr.com/journalsearch.php?q=21101287785&tip=sid&clean=0)
13. [Natural Language Processing](https://www.cambridge.org/core/journals/natural-language-processing/information/author-instructions/preparing-your-materials)
14. [Fees and pricing](https://www.cambridge.org/core/journals/natural-language-processing/information/author-instructions/fees-and-pricing)
15. [Open access options](https://www.cambridge.org/core/journals/natural-language-processing/information/journal-policies/open-access-options)
16. [Natural Language Engineering (2024), 30, pp. 319–353](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/540F08D91022FE4221476D4FBFB9417C/S1351324923000086a.pdf/towards_diverse_and_contextually_anchored_paraphrase_modeling_a_dataset_and_baselines_for_finnish.pdf)
17. <https://www.cambridge.org/core/services/aop-cambridge-core/content/view/3B630FD89EA9B9F0AD6B430D8976CBA2/S1351324923000220a.pdf/polish-natural-language-inference-and-factivity-an-expert-based-dataset-and-benchmarks.pdf>
18. <https://api.crossref.org/works/10.1017/S1351324923000220>
19. <https://www.cambridge.org/core/services/aop-cambridge-core/content/view/D7B259BCD35586E04358DF06006E0A85/S2977042424000530a.pdf/maximizing_rag_efficiency_a_comparative_analysis_of_rag_methods.pdf>
20. <https://www.cambridge.org/core/services/aop-cambridge-core/content/view/62AF020B1B9BD7DAAE4F7B6262E81CA6/S1351324923000189a.pdf/urdu_paraphrase_detection_a_novel_dnnbased_implementation_using_a_semiautomatically_generated_corpus.pdf>
21. [Natural Language Engineering (2024), 30, pp. 554–576](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/740B4B5903AE80FE14709F5DAEE7AD41/S1351324923000505a.pdf/abstractive-summarization-with-deep-reinforcement-learning-using-semantic-similarity-rewards.pdf)
22. <https://www.cambridge.org/core/services/aop-cambridge-core/content/view/7E2CA97E21663CC031FB6BAFE56E0046/S2977042424000384a.pdf/coat_corpus_of_artificial_texts.pdf>
23. [CoAT: Corpus of artificial texts | Natural Language Processing | Cambridge Core](https://www.cambridge.org/core/journals/natural-language-processing/article/coat-corpus-of-artificial-texts/7E2CA97E21663CC031FB6BAFE56E0046)
24. [Lightweight transformers for clinical natural language processing | Natural Language Engineering | Cambridge Core](https://www.cambridge.org/core/journals/natural-language-engineering/article/lightweight-transformers-for-clinical-natural-language-processing/BEF81FDE6E12B9DC5AD4906AE67CDDEB)
25. [\[PDF\] Maximizing RAG efficiency: A comparative analysis of RAG methods](https://www.semanticscholar.org/paper/Maximizing-RAG-efficiency:-A-comparative-analysis-%C5%9Eakar-Emekci/4fe445a1df3b73ccf1e71c1a93256202302de78c)
26. [Natural Language Processing: Volume 32 - Issue 2](https://www.cambridge.org/core/journals/natural-language-processing/issue/304A4EDA5CB70EE755D14932E639A68B)
27. [Natural Language Engineering (2023), 29, pp. 1402–1410](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/D57E0ADD8DE8118BBE1627DEB3809DB4/S1351324923000463a.pdf/emerging-trends-smooth-talking-machines.pdf)
28. [Emerging trends: evaluating general purpose foundation models](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/9FB501345FDE2593D710E05C270E21C5/S1351324924000068a.pdf/emerging-trends-evaluating-general-purpose-foundation-models.pdf)
29. [Semantic enrichment of neural word embeddings: Leveraging taxonomic similarity for enhanced distributional semantics](https://www.cambridge.org/core/journals/natural-language-processing/article/semantic-enrichment-of-neural-word-embeddings-leveraging-taxonomic-similarity-for-enhanced-distributional-semantics/09D7B4F2C73301E31D7514A69C19C953)
30. [Natural Language Engineering (2022), 28, pp. 249–269](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/5E9F9F796159040973053C52C443C1D6/S1351324922000043a.pdf/emerging_trends_sotachasing.pdf)
31. [Thought flow nets: From single predictions to trains of model thought | Natural Language Processing | Cambridge Core](https://www.cambridge.org/core/journals/natural-language-processing/article/thought-flow-nets-from-single-predictions-to-trains-of-model-thought/774534FA02B29DFF7C142BEBBA42991F)
32. [(PDF) Urdu paraphrase detection: A novel DNN-based implementation using a semi-automatically generated corpus](https://www.researchgate.net/publication/371144244_Urdu_paraphrase_detection_A_novel_DNN-based_implementation_using_a_semi-automatically_generated_corpus)
33. <https://api.crossref.org/journals/2977-0424/works?query.bibliographic=question+answering+retrieval+large+language+models+evaluation&filter=from-pub-date:2024-01-01&select=DOI,title,author,published-online,page,volume,issue&rows=40>
34. [Natural Language Processing (2025), 31, pp. 1423–1449](https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/09D7B4F2C73301E31D7514A69C19C953/S2977042425100058a.pdf/semantic_enrichment_of_neural_word_embeddings_leveraging_taxonomic_similarity_for_enhanced_distributional_semantics.pdf)
35. <https://api.crossref.org/journals/2977-0424/works?query=retrieval-augmented+hallucination+question+answering+self-correction&filter=from-pub-date:2025-01-01&select=DOI,title,author,published-online,page,volume,issue&rows=25&sort=score>
