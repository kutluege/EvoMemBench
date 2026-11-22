# Submission report: *Natural Language Processing* (Cambridge University Press)

**Paper:** "Read-time removal of superseded facts in agent memory using embedding geometry" (Kutlu and Özönder)
**Article type:** Article
**Built from:** `paper/integrated/hnav_integrated.tex` and `paper/references.bib` (85 entries)
**Date:** 2026-10-09

## 0. Status at a glance

| Item | Result |
|---|---|
| Template | **Official `CUP-JNL-NLP.cls` v1.1**, from the journal's "NLP LaTeX Files" zip. This is *not* the brief's `cup-journal` class. See §1. |
| Bibliography system | natbib author–date plus BibTeX (the class loads natbib), using `nlplike-links.bst`, a renamed copy of the template's `nlplike.bst`. Biblatex/biber is **not** used, because it cannot load alongside this class. See §1. |
| Compile | Clean (Tectonic/XeTeX). There are 0 undefined citations or references, no "??" in the PDF, and the `.blg` has no warnings. A fresh build from the upload zip also passes. |
| Citation cross-check | 87 bib entries and 87 distinct cited keys, matched both ways. |
| Pages | 34 under Tectonic. pdflatex should give fewer pages (see §6). The journal sets **no page limit**. |
| Words | Body prose ≈ **12,000** against the Article range of "~8,000–12,000". The body is at the upper bound; see §6 for options. |
| Abstract | 324 words against "approximately 300". Kept verbatim; see E1. |
| In-journal citations added | 2: `hou2024anisotropic` and `church2024emerging`. |
| Open `[CONFIRM]` items | 11 printed in red in the PDF, plus ORCID, e-mail and alt-text placeholders in source comments. See §7. |

## 1. Template and bibliography: deviation from the brief (read first)

The brief assumed the Overleaf "Cambridge Medium" template (`cup-journal.cls`, `journal=nlp`, biblatex/biber). It also said that **if the journal's own "NLP LaTeX Files" zip contains a different class or sample, the zip takes precedence**. It does.

- **What the zip contains.** The zip was downloaded with `curl` from the brief's URL. It contains `CUP-JNL-NLP.cls` v1.1 (10 April 2024), `nlplike.bst`, `NLPguide.tex/.pdf`, a book-review sample, `Sample.bib`, `cup_logo.pdf/.eps` and a README. The original zip and sample files are kept in `template_original/`.
- **Class differences.** The class has no `journal=`, `manuscript=`, `year=` or `volume=` options, and no `\keywords{}` macro (it has a `keywords` environment instead). It has no `\email[...]` corresponding-author marker, no `\paragraph` back-matter convention and no biblatex.
- **natbib is mandatory.** The class itself runs `\usepackage[authoryear]{natbib}` with `\bibpunct{(}{)}{;}{a}{}{}`, which gives "(Mu and Viswanath 2018)". biblatex cannot be loaded on top of natbib. The guide (`NLPguide.tex`, "Bibliography") tells authors to use BibTeX with `\bibliographystyle{nlplike}`. It also allows `nlplike.bst` to be adjusted, provided the updated `.bst` is supplied with the sources.
- **Consequence.** I followed the zip, as both the brief and your instructions require. The submission uses natbib commands: `\citep` (parenthetical), `\citet` (textual) and `\citealp` (inside existing parentheses). These are the natbib equivalents of the brief's `\parencite`/`\textcite`. The build is `pdflatex → bibtex → pdflatex ×2`.
- **No biber.** No biber binary was needed, so none was downloaded. The brief's biblatex instructions (`\addbibresource`, `\printbibliography`) do not apply to this class.
- **`nlplike-links.bst`.** The original `nlplike.bst` is apalike-based. It ignores `doi`, `url` and `eprint`, so the 18 arXiv-only entries would have printed with no identifier at all. The renamed copy (renaming is required by the bst licence) makes output-only changes, each documented in the file header:
  1. adds the fields `doi`, `eprint` and `url`;
  2. ends each entry with the DOI as `https://doi.org/…`, otherwise the URL, otherwise `arXiv:<id>`;
  3. prints `@misc` arXiv entries as "arXiv preprint arXiv:<id>";
  4. prints and cites undated entries (the two model cards) as "n.d." instead of an empty year;
  5. prints the year suffix inside the parentheses, "(2025a)", where the original gave "(2025)a".

  Sorting and labels are otherwise unchanged. Cambridge restyles references at typesetting anyway (brief §6.1).

## 2. Files

| File | Purpose |
|---|---|
| `main_nlp.tex` | Manuscript source (pdflatex target) |
| `main_nlp.pdf` | Compiled manuscript (Tectonic) |
| `refs_nlp.bib` | The 85 verified entries plus 2 in-journal entries |
| `main_nlp.bbl` | Generated bibliography, included for the source upload |
| `nlplike-links.bst` | Modified bibliography style (§1) |
| `CUP-JNL-NLP.cls`, `cup_logo.pdf`, `cup_logo.eps` | Official class files from the zip (unmodified) |
| `figures/` | The 7 figure PDFs used. `fig5_strata.pdf` is not shipped. |
| `upload/main_nlp.pdf` | **Initial submission: upload as "Main Document"** (brief §2) |
| `upload/main_nlp_source.zip` | Source package for after acceptance: tex, bib, bbl, bst, cls, logo, figures and PDF. A fresh extraction compiles cleanly. |
| `build_logs/` | Final `.log` and `.blg` |
| `template_original/` | The untouched journal zip and sample files |

**Supplementary material:** none is required. E7 was not applied (see §3).

## 3. Changes mapped to the brief

### 3.1 Brief edit IDs

| ID | Brief instruction | Outcome |
|---|---|---|
| **E1** | Optional: "Agents keeping memories…" → "Language-model agents that keep memories…" | **Not applied.** The integrated abstract is already 324 words against the journal's ~300 (the brief assumed ~280). E1 would add 2 more words, and Introduction ¶1 already opens with "Language-model agents…". The abstract is verbatim from the integrated draft. |
| **E2** | NLP/NLI-angle paragraph (≤120 words) | **Applied, with adaptations (103 words).** Placed **immediately before "The contributions are:"**. The brief's two locations no longer read well after integration. Inserting it after "…needs both records on the page." would separate "The remedy the measurement suggests" from the measurement it refers to. Inserting it before the H-Nav-GEO paragraph would break "We therefore…", which follows from the NLI paragraph. The text adaptations follow. |
| **E3** | Append `sakar2025rag` to Introduction ¶1 | **Applied with a substitution.** The same location (the ¶1 RAG/vector-store `\citep` list) now carries the guide's SUGGEST-CITE `church2024emerging`, placed chronologically. Şakar and Emekci is marked **CONTEXT-ONLY** in the integration guide §6.2, and your rules forbid adding CONTEXT-ONLY entries. See §4. |
| **E4** | Hou et al. sentence in §3.3 (now §4.3) | **Superseded by the guide's placement.** The guide's SUGGEST-CITE location for Hou et al. is Related Work §2.3, directly after the anisotropy-cause sentence, with the guide's verified sentence: "Anisotropy has also been linked to errors in downstream identity decisions such as coreference (Hou et al. 2024)." Repeating a near-identical sentence in §4.3 would duplicate content, so E4 was not added there. |
| **E5** | Keywords cut from 7 to 5; title in sentence case | **Applied.** The title is "Read-time removal of superseded facts in agent memory using embedding geometry", with wording unchanged. Keywords use the class's `keywords` environment: *agent memory, knowledge conflict, retrieval-augmented generation, sentence embeddings, natural language inference* (lower-case, 5 entries). "Small language models" and "embedding post-processing" were dropped, as the brief proposed. |
| **E6** | GPT-5 mini version/dates placeholder in Methods | **Applied** at the end of the adjudication sentence in §5.2: `\confirm{GPT-5 mini model snapshot/version identifier and dates of use}`. |
| **E7** | Contingent: move Appendix B to supplementary | **Not applied**, as instructed. Listed as option 1 in §6. |

E2 changes relative to the brief's text:
- **Opening.** "the decision" became "deciding whether two retrieved records are versions of one fact", because the paragraph now follows the results summary and needs its own subject.
- **First question.** "whether two sentences state the same proposition with different values, which is the province of NLI" became "whether two sentences make incompatible statements, which is the province of natural language inference". The original wording assigns *identity* to NLI, which contradicts the paper's own finding that "NLI does not establish identity" (§7.2).
- **Anisotropy citation.** The brief cited Hou et al. for "anisotropy can make related but distinct items hard to separate". To avoid repeating the guide's Hou sentence in §2.3, and to avoid characterising Hou et al. beyond the guide's verified wording, this clause now reads "which is anisotropic (Ethayarajh 2019)". That is an existing reference that supports the claim directly.
- **RAG citation.** `sakar2025rag` became `church2024emerging` (see E3).
- **Mu and Viswanath.** The `mu2018abtt` citation was dropped, because ABTT is already cited textually two paragraphs earlier.
- **Section reference.** "Section 7.5" became `Section~\ref{sec:limitations}`, which now renders as 8.5.

No new claims were added. The paragraph ends by restating the single-benchmark limitation.

### 3.2 Structural steps (brief §0, steps 1–7)

- **Preamble.**
  - Removed `geometry`, `authblk`, `natbib` (the class loads it), `lmodern`, `caption`, `hyperref`, `longtable`, `[T1]{fontenc}` and `[utf8]{inputenc}`.
  - The template sample loads neither fontenc nor inputenc, and the source is pure ASCII. Under XeTeX, T1 also knocked out the class's Source Sans font.
  - `amssymb` became `amsfonts`, because the class defines `\gtrsim`/`\lesssim` and amssymb then stops with an error. Only `\mathbb` is needed.
  - Kept `microtype`, `amsmath`, `graphicx`, `array`, `multirow`, `xcolor` and `url`. `booktabs` is loaded by the class.
  - `hyperref` is loaded by the class only with its `online` option, so the submission PDF has no live links. That is normal for a refereeing PDF.
- **Front matter.**
  - **Production placeholders.** `\lefttitle{E. Kutlu and Ş. Özönder}`, `\righttitle{Natural Language Processing}`, `\papertitle{Article}`, `\jnlPage`, `\jnlDoiYr{2026}`, `\doival{10.1017/xxxxx}` and `\history{(Received xx…)}` follow the template sample exactly. Cambridge fills the DOI and dates.
  - **Authors.** Both names are given in **one** `\author{Ege Kutlu and Şener Özönder}`, because the class's two-author join macro prints "Ege Kutlu, andŞener…" or "Ege KutluandŞener…" (a class bug, confirmed by rendering). The single affiliation is in "department, institution, city, country" order.
  - **Corresponding author.** The old `\thanks` footnote was deleted. The class's own `\aopfoot{Corresponding author: Şener Özönder; Email: …}` now produces the standard Cambridge first-page footnote.
  - **ORCID and e-mail placeholders** are source comments, per the brief. The class has an `orc` environment and an `\orcid` macro that the authors can use once the iDs are known; I did not invent values.
  - **Abstract and keywords** are set before `\maketitle`, as the class requires.
- **Body.**
  - All sections, numbering, equations, figures and tables are unchanged.
  - Column-header cells were put in sentence case, first letter only, on 17 header lines, as the brief permits ("model" → "Model"). A diff of every tabular body against the integrated draft shows **no data cell changed**.
  - Row stubs, such as "raw cosine" and the Appendix A component names, were left lower-case. They are flagged for the copy-editor.
  - Every figure starts with the class's `\sidecapoff`. The class never fills its internal `\figbox`, so without the switch it treats every figure as narrow and prints the caption **over** the artwork. This was confirmed by rendering.
  - Each figure has `% ALT-TEXT: [CONFIRM: authors to supply]` above its `\includegraphics`.
- **Back matter.**
  - **Order:** Acknowledgements, Funding statement, Competing interests, Data availability statement, Ethical standards, Author contributions, then References and Appendices. The headings are set in the class's acknowledgements style (bold sans, 8 pt) through a small `statement` environment in the preamble.
  - **Heading wording.** The brief's headings came from the `cup-journal` template, which is not used here. I used sentence-case equivalents and the class's own spelling "Acknowledgements".
  - **AI disclosure.** "Use of Generative AI" was merged into Acknowledgements, with both sentences verbatim.
  - **Competing interests.** The CONFIRM wording was updated to "The authors declare none.", per the brief.
  - **Ethics.** A new Ethical standards placeholder was added.
- **Appendices** follow the references after `\clearpage\appendix`.
  - **Appendix A (Table 12)** was converted from `longtable` to a single-page `table`. The longtable caption rendered as "Table 12. :" in the wrong style, and its heading was stranded at the foot of a page.
  - The column specification and all cells are byte-identical; only the duplicated `\endfirsthead`/`\endhead` header row went.
  - `\small` was applied to Appendix A, as in the body tables, and Table 13 uses `[!htbp]` so that it stays with its heading.
- **Body-text change** (source-based count): 11,882 → 12,003 words, **+121 (+1.0 %)**. A word-level diff of the body against the integrated draft shows only these changes:
  - E2;
  - the Hou sentence;
  - `\cite` → `\citep`/`\citet`/`\citealp`;
  - the Reddy/Patel and Xu/Mu–Viswanath textual conversions;
  - chronological reordering inside 8 multi-key citations;
  - "church" added to Introduction ¶1;
  - E6;
  - the column-header capitals.

  **No number, statistic or claim changed.** "Frozen transfer" wording, the Limitations section and the development-bias disclosures are untouched.

### 3.3 Citation conversion (numbered → author–date)

- **Default.** All 126 citation commands were reviewed in context. Parenthetical uses became `\citep`, which renders as "(Hu et al. 2026)".
- **Textual uses (`\citet`), where the cited name is part of the sentence:**
  - "post-processing of Mu and Viswanath (2018)" (§1);
  - "Following Mu and Viswanath (2018), we…" (§4.3);
  - "surveyed by Xu et al. (2024)" (§2.2);
  - "Reddy and Challaram (2026) let…" and "Patel (2026) shows…" (§2.1). These sentences previously named the authors and also carried a trailing citation, so the author name is now the citation.
- **Inside existing parentheses (`\citealp`):**
  - "(scikit-learn; Pedregosa et al. 2011)";
  - "(435M parameters; He et al. 2023)";
  - "vLLM (Kwon et al. 2023; Table 3)".
- **Multi-key citations** are in chronological order, earliest first, per the journal. Eight lists were reordered, and `church2024emerging` was inserted in date order. A script check confirmed that all 28 multi-key citations are non-decreasing in year.
- **Table 3** keeps its in-cell model citations; the table fits the column width, so the brief's fallback (moving them to the caption) was not needed.
- **Bracket-style references.** None remain.

### 3.4 Changes to `refs_nlp.bib` (copy of `references.bib`)

- Appended `hou2024anisotropic` and `church2024emerging`, using the guide's §6.2 BibTeX unchanged.
- **Case protection only.** Three capitals that follow a question mark were braced, because the style sentence-cases titles and would otherwise print "…harmful? a case study":
  - `aitsaada2023anisotropy` ("? {A} Case");
  - `bavaresco2025llms` ("? {A} Large");
  - `pakhomov2026bookkeeping` ("? {R}eading").

  All other rendered titles were checked; acronyms were already protected.
- No author, title, year, venue, volume, page or DOI was changed. No arXiv DOIs were added, because the brief does not instruct it explicitly. Journal names are not abbreviated.
- All three `\confirm{…}` notes are kept: `holm1979`, `gemma4card` and `qwen35card`. Efron and Tibshirani is 1994, Chapman and Hall/CRC, as in the verified bib.
- **Note:** `abouelenin2025phi4mini` has `{Microsoft}` as first author in the verified bib, so it renders as "Microsoft et al. 2025", not the brief's "Abouelenin et al.". This is left unchanged.

## 4. In-journal citations added (2 of at most 3)

| Key | Source | Location and sentence | Reason |
|---|---|---|---|
| `hou2024anisotropic` (*NLE* 30(6), 2024) | Guide §6.2 SUGGEST-CITE; also brief §8.3 | §2.3 "Anisotropy and post-processing of embeddings", after the rogue-dimensions sentence: "Anisotropy has also been linked to errors in downstream identity decisions such as coreference (Hou et al. 2024)." | Direct technical relevance (anisotropy and identity decisions). Guide wording used. |
| `church2024emerging` (*NLE* 30(4), 2024) | Guide §6.2 SUGGEST-CITE | Introduction ¶1, in the RAG/vector-store memory citation list; also cited in the E2 paragraph for "retrieval-augmented systems built on vector stores" | Agent memory/RAG relevance |

- **Not added: `sakar2025rag` / `sakar2025maximizing`.** The brief proposes it (E2, E3), but the guide marks it **CONTEXT-ONLY**, and your rules forbid CONTEXT-ONLY entries. The guide is the stricter, verified relevance assessment, and the brief's purpose for it (a RAG/vector-store citation in ¶1) is served by the guide's SUGGEST-CITE Church et al.
- **No third entry was added.** The only other §8.3 candidate is Şakar and Emekci. The guide's CONTEXT-ONLY entries were not added, and `chen2025kgdh` was not added.

## 5. Compile status and warnings

- **Engine.** Tectonic 0.x (XeTeX), which runs BibTeX automatically. The final log has no `Citation … undefined`, no `Reference … undefined` and no "There were undefined…". The PDF text contains no "??". The `.blg` shows no warnings.
- **Clean rebuild.** A fresh build from the extracted `upload/main_nlp_source.zip` gave the same result.
- **Warnings that remain:**
  - **Class-intrinsic, `\output`-time overfull boxes.** There are four recurring overfull vboxes on every page (42/702/31/670 pt), and on the title page two overfull hboxes (80.2 pt and 318 pt) plus two small vboxes. The same pattern appears when compiling the **untouched official `NLPguide.tex`**: they come from the class's trim and crop-mark page assembly, not from manuscript content. They do not show in the rendered pages, and all 34 pages were inspected visually.
  - **Content overfull boxes.** There is one, 4.1 pt in Table 12, under the 10 pt threshold. It comes from the original column widths, 0.20 + 0.46 + 0.26 of `\linewidth`.
  - **XeTeX-only items, not changed in the source** (pdflatex is the target):
    - "Invalid UTF-8" warnings for Latin-1 comments in `CUP-JNL-NLP.cls` lines 3819–3844;
    - `TU/SourceSansPro/sb` replaced by bold;
    - **the body falls back to Latin Modern** under XeTeX, because the class's `mathptmx` (Times) is a pdfTeX font setup. pdflatex will set Times as intended.
  - Tectonic's "internal consistency problem when checking if main_nlp.bbl changed" and "stopping at 6 passes" are a Tectonic file-tracking quirk. The `.aux` is stable from pass 3, and there are no undefined references.
- **pdflatex.** Not run, because no TeX distribution is installed. Nothing XeTeX-specific is in the source. Please run `pdflatex → bibtex → pdflatex ×2` once locally before upload.
- **Floats** sit near their first reference (checked on rendered pages). Figure 1 is on p. 3 and is first cited on p. 2. All tables and figures appear in citation order.

## 6. Length

- **Limit:** Article, "~8,000–12,000 words". The journal does not say what counts towards it.
- **Method.** Source-based. I took the text from §1 Introduction to the end of §9 Conclusion, and removed comments, all `table`/`figure` environments, maths (counted as 1 token), labels and commands. References were counted as 1 token, and each cited work as about 2 words ("Author 2000").

| Part | Words |
|---|---|
| **Body prose** (Introduction–Conclusion, excluding floats) | **≈ 12,000** (12,003) |
| Figure and table captions | ≈ 1,060 |
| Abstract | 324 (journal: ~300) |
| Appendices A–B (prose and cells) | ≈ 220 |
| References (pdftotext) | ≈ 3,330 |
| Body including tables, captions and figure-internal text (pdftotext, Introduction → Acknowledgements) | ≈ 15,470 |
| Whole PDF (pdftotext) | ≈ 19,600 |

- **Verdict.** The body prose sits at the top of the range, exactly at the upper bound. If the editor counts captions and tables, it is about 1,000–3,500 words over. Nothing was cut.
- **Pages.** There are 34 pages under Tectonic, with Latin Modern body text. pdflatex with Times will be shorter (a rough estimate is 30–32 pages). There is no page limit.

**Content-neutral options if the editor asks for a shorter text** (ranked from least to most intrusive; approximate words moved out of the body; the authors decide):

1. **E7:** move Appendix B (Table 13) to online supplementary material, as "Supplementary Table S1". This takes about 70 words out of the appendix and none out of the body. It only matters if everything is counted.
2. Move Appendix A (Table 12) to supplementary material, about 220 appendix words. Its values are in the released artifact.
3. Move the §4.7 span-check paragraph (non-binding check) to an appendix: about 105 words.
4. Move "Chunk-level edits" (§7.2, an earlier design) to an appendix: about 100 words.
5. Move the §6.5 per-question analysis paragraph ("The per-question outputs show…") to an appendix: about 160 words.
6. Move the §5.2 dataset-construction detail (the coverage and judge-label paragraphs) to an appendix, keeping a one-sentence summary: about 230 words.
7. Move the "Protocol deviations" paragraph (§5.1) to an appendix: about 200 words. This is a disclosure, so keep a one-sentence pointer in §5.1. Do **not** delete it.
8. Remove the E2 NLP-angle paragraph added for this journal: about 105 words.

Options 3–8 together take about 900 words out of the body.

## 7. Open `[CONFIRM]` items

None was resolved or deleted. ★ marks items the journal requires before submission.

**Printed in red in the PDF (11 instances):**

1. ★ **Funding statement** (back matter). Required.
2. ★ **Competing interests**, "[CONFIRM: The authors declare none.]". Required.
3. ★ **Data availability: public release and archival DOI** for `github.com/kutluege/EvoMemBench`. Required, and the journal prefers persistent identifiers.
4. ★ **Ethical standards**, "[CONFIRM: Ethical approval was not required.]". **New**, required.
5. ★ **AI-assistance declaration** (Acknowledgements). Required if any generative tool was used for code or text. The journal asks for the tool name and version, dates, access route and a description of use.
6. ★ **GPT-5 mini snapshot/version and dates of use** (§5.2, E6, **new**). The journal's AI policy requires these in the Methods.
7. **Author contributions (CRediT).** Optional; the authors may delete the paragraph.
8. **vLLM 0.28.0 version string** (Table 3).
9. **Access date** for the `gemma4card` reference.
10. **Access date** for the `qwen35card` reference.
11. **`holm1979`**: "reference not verified against a publisher page".

**In source comments (not printed):**

- ★ ORCID iD of Şener Özönder (corresponding author). **Required in ScholarOne at submission.**
- ORCID iD of Ege Kutlu.
- ★ E-mail address of Ege Kutlu. The journal asks for the authors' e-mail addresses on the first page; only the corresponding author's is printed.
- `% ALT-TEXT: [CONFIRM: authors to supply]` above each of the 7 figures. The journal requires alt text. Authors may use Cambridge's Accessibility Descriptions form; otherwise machine-generated text is offered at proof.

## 8. Figure flags for the authors (images not edited)

**From the brief (verified):**
- **"held-out"** where the text says frozen transfer:
  - Fig. 3, panel title "AUROC on the held-out sh_64k balanced set";
  - Fig. 4, right panel "sh_64k held-out, one shot";
  - Fig. 6B, legend "held-out sh_64k".

  Suggested wording: "frozen-transfer sh_64k".
- **"whitening"** where §4.3 says "this is not whitening":
  - Fig. 2b, "ABTT whitening";
  - Fig. 3A, "whitened cosine";
  - Fig. 6A, legend and axis note "whitened…".

  Suggested wording: "ABTT cosine".
- **Internal file names inside images:**
  - Fig. 1 footer (`gold_conflict_dataset.jsonl.gz`, `m7_delta_geometry.json`, `GEOMETRY_AND_ANISOTROPY.md`);
  - Fig. 2 footer (`geo_operating_point.json`, `geo_identity_screen.json`).

**Found in this pass:**
- **Fig. 7** (`fig8_placement_v2.pdf`):
  - the panel A title says "same detector and groups (**Table 8**)", but the placement table is **Table 9** (Table 8 is the reference-detector table);
  - the legend says "delete stale (H-Nav-GEO)", while the text and Table 9 say "delete superseded".
- **Fig. 2** (`fig2_pipeline_v2.pdf`):
  - "454 facts" and "454 → 439 facts", but the store has 455 facts (Table 1). The source comment already notes this.
  - "2B–9B LLM", while the text says 2.3B (effective) to 9B.
  - Several labels overprint each other in panel b: "Signal 1 — direction" over the panel title, the two m_w lines, and the "(T_w, T_p)… (s_w, s_p)" note.
  - The look-alike example (0–342, raw cosine 0.834) says "a cosine screen lets it through", but the caption says it would not become a candidate at the 0.94 threshold. The source comment already asks for a pair above 0.94, such as serials 79/365.
  - The NLI example text cites "Marlowe/London", while the pictured look-alike is Thomas Arne.
- **House style.** The figures contain "%" and digits under 100 (the journal prefers "per cent" and spelled-out numbers). Flagged only; this is for the copy-editor.
- **File names versus figure numbers.** `fig6a_scale` is Figure 5, `fig7_mechanism` is Figure 6, and `fig8_placement_v2` is Figure 7. When uploading individual figure files after acceptance, consider renaming them Fig1–Fig7.

## 9. Brief §10 checklist

| Item | Status |
|---|---|
| `\documentclass[journal=nlp, …]{cup-journal}` compiles with pdflatex → biber → pdflatex ×2 | **Replaced** by the official `\documentclass{CUP-JNL-NLP}` with pdflatex → **bibtex** → pdflatex ×2 (§1). Compiles cleanly with Tectonic; pdflatex not run locally. |
| No natbib/cite/thebibliography/`\bibliographystyle`; `\addbibresource` and `\printbibliography` present | **N/A by design.** The class mandates natbib. The source has `\bibliographystyle{nlplike-links}` and `\bibliography{refs_nlp}`, with no hand-written `thebibliography`. |
| All references plus the in-journal ones listed, with no "?" or undefined warnings | ✔ All 87 entries (85 + 2) are listed; no undefined citations; no "??"; the `.blg` is clean. |
| Every former numbered citation is now author–date, with narrative and parenthetical use correct | ✔ (§3.3) |
| Title in sentence case; author block; corresponding-author footnote removed; ORCID placeholders as comments | ✔ The old `\thanks` was removed; the class's `\aopfoot` gives the Cambridge corresponding-author line (§3.2). |
| Abstract unchanged except E1, ≤ ~300 words | ✔ Unchanged; E1 not applied. ⚠ 324 words against ~300; the authors may trim. |
| Exactly 5 keywords, lower-case | ✔ (class `keywords` environment) |
| Section numbering and float order unchanged; all floats called out in order | ✔ |
| Table data cells byte-identical | ✔ Diffed; only header first letters, the `\cite` command name and the Appendix A wrapper differ. |
| Figures embedded; originals kept; ALT-TEXT comments | ✔ |
| Back-matter order: Acknowledgements → Funding → Competing interests → Data availability → Ethics → Author contributions → (endnotes) → References → Appendices | ✔ No endnotes are needed; there are no footnotes in the body. |
| Data availability statement before References | ✔ |
| "Use of Generative AI" heading gone; sentences in Acknowledgements; E6 in §5.2 | ✔ |
| All `[CONFIRM]` items present and listed | ✔ (§7). Several of the brief's "10 original" items were resolved during literature integration, before this step. |
| E1–E6 applied exactly; E7 not applied; net body change < 10 % | Partly. E2, E5 and E6 are applied. E2 is adapted, E3 has a substitution, E4 is superseded by the guide placement and E1 is skipped (§3.1). E7 is not applied. Net change +1.0 %. |
| Word-count report (body only, and with tables, references and appendices) | ✔ (§6) |
| PDF has page numbers; output `main_nlp.pdf` as "Main Document" | ✔ |
| Before submission (authors): ORCID linked in ScholarOne; institutional e-mail | Open: authors to do this. |

## 10. Cover-letter notes (no cost content)

- **Article type:** Article. Submit at `https://mc.manuscriptcentral.com/nlp`; the Main Document is `upload/main_nlp.pdf`.
- **Fit.** The paper is an implementable NLP component. It combines embedding post-processing (ABTT), a difference-vector probe and a bidirectional NLI cross-encoder to handle knowledge conflicts in retrieval-augmented agent memory, with no generative call at inference. It releases the 54,569-pair LLM-adjudicated dataset, code and frozen parameters. This connects to the journal's aim of linking research with practical applications, and its in-journal work on RAG (Church et al. 2024) and on embedding anisotropy (Hou et al. 2024).
- **Pre-empting reviewers.** Use the paper's own wording:
  - the largest store (sh_64k) is a **frozen-transfer condition, not a held-out test**;
  - all results come from **one templated English benchmark**;
  - the multilingual and free-text questions this journal's readers may raise are not tested.
- **Originality.** State that the manuscript is not under consideration elsewhere, and mention any arXiv preprint (Cambridge's preprint policy allows them).
- **Reviewing.** All authors agree to be invited as reviewers, as the journal requires.
- **Contacts.** Editorial queries go to NLP@cambridge.org; LaTeX queries go to CUPTeXSupport@straive.com.

## 11. Brief items not followed, and why

1. **`cup-journal` class and biblatex/biber** were replaced by the zip's `CUP-JNL-NLP.cls` with natbib/BibTeX. The brief itself gives the zip precedence, and the class loads natbib, which rules out biblatex (§1).
2. **The brief's preamble snippet** (`journal=nlp`, `manuscript=article`, `year`, `volume`), `\keywords{…}`, `\email[Name]{…}`, the `\paragraph{…}` back-matter headings, `threeparttable`/`\headrow` and `\endnote`/`\printendnotes` belong to the Overleaf template. The zip class equivalents were used instead: the `keywords` environment, `\aopfoot`, the acknowledgements-style statements and standard `table` with `\caption`. The class has no endnote mechanism, and the body has no footnotes.
3. **Brief §6.3 bib entries and the "18 + 2" counts** are superseded: `references.bib` (85) plus 2 guide entries were used.
4. **E1** was skipped and **E3/E4** were modified (§3.1). **Şakar and Emekci** was not added (CONTEXT-ONLY in the guide).
5. **E2 location** was moved to just before the contributions list (§3.1).
6. **House-style conversions** ("per cent", spelled-out numbers, single quotes) were not applied, as the brief instructs. They are left to the copy-editor.
7. **The pdflatex build** could not be run here, because there is no TeX distribution. The source contains no XeTeX-specific code; XeTeX-only effects are listed in §5.
8. **Production placeholders** printed by the class (DOI `10.1017/xxxxx`, "(Received xx xxx xxx…)", "© Cambridge University Press 2026") are kept exactly as in the template sample. The class also has an `OA` option that prints a CC BY licence line; it was not set, because the licence is chosen at acceptance.

---

## Post-build edit by the orchestrator (2026-10-09)

For consistency with the JIIS and JISYS versions, abbreviations are now defined at their first use in the body. No number, claim or citation changed.
- Introduction: "an AUROC of 0.972" → "an area under the receiver operating characteristic curve (AUROC) of 0.972".
- Contributions list: "adjudicated by an LLM" → "adjudicated by a large language model (LLM)".
- Statistics paragraph: "True-positive rates at fixed false-positive rates" → "True-positive rates (TPR) at fixed false-positive rates (FPR)".

The PDF and the upload package were rebuilt afterwards. The refreshed package compiles on its own, with no undefined citations or references.
