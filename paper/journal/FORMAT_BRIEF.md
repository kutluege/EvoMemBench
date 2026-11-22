# Natural Language Processing (Cambridge University Press; formerly *Natural Language Engineering*) — LaTeX conversion & adaptation brief
Prepared: 2026-10-09 | Sources accessed: 2026-10-09 (all sources)

> ⚠️ **COST FLAG: the journal is fully gold open access with a mandatory APC.** The fees page gives **APC £2,610 / US$3,655, and "additional taxes may apply"** [S9]. There is no subscription route. The $0 route depends **entirely** on the TÜBİTAK ULAKBİM (EKUAL) – Cambridge Read & Publish agreement for 2026–2028. That agreement **covers gold/fully OA journals, without quota**, for corresponding authors at EKUAL member institutions [S19][S21][S23]. **It is UNVERIFIED whether this journal is on the 2026 "CUP Fonlanan AE Dergi Listesi" (funded-journal list).** That list is an .xlsx file that could not be read [S24]. Before submission, the authors must check that list and the Cambridge eligibility checker [S20] (select Türkiye, then Boğaziçi University). If the journal is not covered, the APC is mandatory and exceeds the authors' ceiling of $0 (or at most $100). In that case the only remaining route is an editorial waiver, which can be requested only after acceptance [S8].
>
> Other flags: (a) **Keywords must be cut from 7 to 3–5** [S1]. (b) The citation style changes from **numbered to author–date** (biblatex/biber) [S1][S13]. (c) Article length is **"~8,000–12,000 words"** [S1], and the paper sits near the top of that range (see §4). (d) The corresponding author **must supply an ORCID iD at submission** [S2]. (e) A **Data availability statement, a Funding statement, a Conflict of interest statement and an Ethics statement are all required** [S1][S10].

---

## 0. How to use this file (for the coding agent)

**Prerequisite:** you need the Cambridge class file `cup-journal.cls` and its support files. Get them from the Overleaf template "Cambridge Medium Template Class File" [S13] or from the journal's "NLP LaTeX Files" zip [S15]. If these files are not in your working directory, **stop and ask the authors for them**. Do not write a substitute class.

Execute these steps in order:

1. Copy the original `.tex` to `main_nlp.tex`. Work only on the copy.
2. **Preamble (§2):** replace the `\documentclass` line with the `cup-journal` line given in §2. Remove layout, bibliography and author-block packages. Add `\addbibresource{refs_nlp.bib}`.
3. **Bibliography (§6):** create `refs_nlp.bib` from the BibTeX given in §6.3, which covers all 18 references plus 2 in-journal references. Delete `thebibliography`, `\bibliographystyle` and `\bibliography`. Put `\printbibliography` in the position shown in §5.
4. **Citations (§6.2):** convert every numbered citation `[n]` or `\cite{…}` to `\textcite{…}` for narrative use or `\parencite{…}` for parenthetical use, following the mapping table in §6.2.
5. **Front matter (§3):** replace the title, author and affiliation block with the snippet in §3. Set the title in sentence case. Delete the corresponding-author footnote. Move the abstract inside `\begin{document}` using the `abstract` environment. Replace the 7 keywords with the 5 given in §3, using `\keywords{…}` in the preamble.
6. **Body (§4):** keep all sections, numbering, figures and tables. Convert tables to the template's `booktabs` form only if this is trivial. Do not change any cell.
7. **Back matter (§5):** rebuild it as the template's `\paragraph{…}` statements, in the order given in §5, using the mapping table there. Move the appendices after `\printbibliography`, after `\appendix`.
8. **Content edits (§8.2):** apply edits E1–E6 exactly. E7 is contingent and must not be applied unless the authors ask for it.
9. Compile with `pdflatex → biber → pdflatex → pdflatex` [S13]. Fix only errors caused by the conversion.
10. Run the checklist in §10. Then produce `main_nlp.pdf` and a short report listing every remaining `[CONFIRM: …]` item and every flag from §12.

**Constraints on content adaptation (verbatim from the authors' spec):**

The agent may make **small, scope-motivated wording changes only**:
- Reframe 1–3 sentences in the abstract and introduction toward the journal's readership.
- Adjust terminology to the journal's community.
- Add one short paragraph (≤ about 150 words) connecting the work to the journal's themes, for example an information-systems angle for JIIS, a knowledge-systems angle for KAIS, an applied or deployment angle for Applied Intelligence, a data-technology/practical-implications angle for DTA (also needed for its structured abstract), an NLP/NLI angle for NLP Cambridge, and a claims-and-evidence clarity angle for TMLR.
- Add the verified in-journal citations from H.
- Shorten or move material to an appendix or supplement only if a length limit requires it.
- Optionally propose at most one alternative title. The default is to keep the current title.

The total net change to body text should stay roughly within 5–10% of the word count.

The agent must NEVER:
- change any number, statistic, p-value, CI, count, table cell or figure;
- add experiments, results or claims, or strengthen claims. Specifically, "frozen transfer" must not become "held-out", and limitations and development-bias disclosures must not be softened or removed;
- delete the Limitations section;
- resolve or delete `[CONFIRM: ...]` placeholders on its own. It keeps them and lists the ones the journal requires to be resolved before submission;
- regenerate figure images. If text embedded in a figure conflicts with the journal's rules or with the manuscript's own terminology, the agent flags it for the authors.

---

## 1. Journal snapshot

| Item | Value | Source |
|---|---|---|
| Current name | **Natural Language Processing** (abbreviated "NLP" on Cambridge pages) | [S3] |
| Rename | Formerly ***Natural Language Engineering*** (NLE). The rename was announced in an Editorial Note in *NLE* 30 (2024), pp. 215–216 (DOI 10.1017/S1351324924000020). The note says the journal "is now called *Natural Language Processing*" and "is a fully open-access journal". The note gives no exact effective date. The first issue under the new title is **Vol. 31, Issue 1 (January 2025)**. Articles published online from 2024 already carry DOIs of the form `10.1017/nlp.2024.x`. | [S11][S26][S29] |
| ISSN | **2977-0424 (online)**. No print ISSN is listed. The old NLE title page lists 1351-3249 (print) and 1469-8110 (online) and states that it is "now called Natural Language Processing". *Conflict:* Wikipedia attributes 1351-3249/1469-8110 to the current title. **Follow Cambridge: use 2977-0424.** | [S3][S12] |
| URL | `https://www.cambridge.org/core/journals/natural-language-processing`. The URL changed; the old `/natural-language-engineering` page remains as a past-title page. | [S3][S12] |
| Editor | Ruslan Mitkov (Lancaster University / University of Alicante) | [S3] |
| Publisher | Cambridge University Press; 6 issues per year | [S4] |
| Indexing (as listed by the journal) | Web of Science (Science Citation Index Expanded, Social Sciences Citation Index, Arts & Humanities Citation Index), Scopus, DBLP, INSPEC, Compendex, EBSCO, ProQuest LLBA, ERIH PLUS, PsycINFO, PubMed. The homepage shows a 2025 Impact Factor of 1.6. **Quartile: UNVERIFIED.** Coverage of the new ISSN 2977-0424 in the Clarivate MJL was also **UNVERIFIED**; see §12. | [S5][S3] |
| OA model | **Gold OA only.** "All articles are published as Gold Open Access under a Creative Commons licence". Authors choose one of the six CC licences. | [S8] |
| APC | **£2,610 / US$3,655**, plus tax where applicable. No colour, page or submission charges are mentioned. | [S9] |
| Cost on the $0 route | **$0 only if the TÜBİTAK–CUP R&P agreement covers this article.** That agreement runs 1 Jan 2026 – 31 Dec 2028, covers hybrid **and gold** journals, has no quota, and applies when the corresponding author is an authorised user of an EKUAL member institution. Use an institutional e-mail address. Eligible article types are research articles. The article must be accepted from 1 Jan 2026. TÜBİTAK ULAKBİM gives final approval after acceptance. **Journal-level inclusion is UNVERIFIED** [S24]. Boğaziçi's own library announced the agreement, which strongly suggests membership, but the EKUAL member list was not read. | [S19][S21][S22][S23] |
| Peer review | **Single-anonymous**: reviewers know the authors. Articles receive at least three external reviewers. | [S6][S7] |
| Submission system | ScholarOne: `https://mc.manuscriptcentral.com/nlp`. It needs an account separate from Cambridge Core. Overleaf also offers a "Submit to Journal" route. | [S2][S1] |
| Article type to choose | **Article** ("~8,000–12,000 words", abstract required). The other types are Squib (≤8,000), Survey Paper (~10,000–16,000) and Position Paper (≤8,000); the remaining types are by invitation. | [S1] |
| Reviewing obligation | "All authors … agree to be invited to peer review other journal submissions in their area(s) of expertise." | [S2][S7] |

---

## 2. Template & build

**Template.** The template is "Cambridge Medium Template Class File" by Cambridge University Press and Overleaf, licensed CC BY 4.0. Overleaf shows it as "last updated a year ago"; no version number is stated. URL: `https://www.overleaf.com/latex/templates/cambridge-medium-template-class-file/zshzqdxjjqkq` [S13]. The journal's author-instructions page links to this Overleaf template and to an "NLP LaTeX Files" zip (`https://www.cambridge.org/core/services/aop-file-manager/file/6616a846ff18e014ad92efd6`, served as `NLP-AuthorMacro-1-.zip`) [S1]. **The zip could not be read (binary).** If it contains a different class or sample from the Overleaf one, the zip's sample takes precedence. Report any difference to the authors.

The instructions say: "Authors are strongly encouraged to compose their manuscripts in LaTeX, using the style file provided" [S1]. **LaTeX is accepted and preferred.**

**Exact `\documentclass` line.** The template header says: "To select a journal, use its code for the journal= option … Natural Language Processing: nlp" [S13]. Use:

```latex
\documentclass[
  journal=nlp,
  manuscript=article,
  year=2026,
  volume=32,
]{cup-journal}
```

- The sample uses `journal=medium, manuscript=article-type, year=2020, volume=37` [S13]. The sample PDF prints the `manuscript` value as an "ARTICLE TYPE" label [S14]. **It is UNVERIFIED whether the class validates `manuscript=` values.** If `manuscript=article` causes an error, revert to `manuscript=article-type`.
- `year` and `volume` only fill the placeholder running header. Volume 32 is the 2026 volume, as shown on the article page of DOI 10.1017/nlp.2026.10025 [S31]. These values are cosmetic.
- If `journal=nlp` gives "unknown option", stop and report it. Do not silently fall back to `journal=medium`.

**Packages.**
- The template loads these explicitly: `\usepackage{amsmath}`, `\usepackage[nopatch]{microtype}`, `\usepackage{booktabs}` [S13].
- The template uses these without loading them, so the class appears to provide them (inferred, not documented): `\includegraphics` (graphicx), the `threeparttable`/`tablenotes` environments, `\headrow`, `\endnote`/`\printendnotes`, and biblatex (`\addbibresource`, `\printbibliography`, `\autocite`) [S13].
- **Remove from the preamble.** Remove `natbib`, `cite`, `biblatex` (if loaded with its own options), `geometry`, `fancyhdr`, `titlesec`, `authblk`, `setspace`, `abstract`, `lineno`, and any `\bibliographystyle`, `\bibliography{…}` or `thebibliography`. Remove font-changing packages such as `times`, `mathptmx` and `lmodern`. The class sets layout and fonts.
- **Keep** content packages the body needs, for example `amssymb`, `multirow`, `xcolor`, `siunitx`, `subcaption` and `url`. Keep `hyperref` only if it loads without an option clash; if it clashes, delete it.
- Neither the template nor the journal names any forbidden package beyond the above, so there is **no stated list of forbidden packages**.
- **UTF-8 names:** if Ş, ğ, İ or Ö fail to render, add `\usepackage[T1]{fontenc}` or use the ASCII macros shown in §3.

**Bibliography system.** The template uses biblatex with the biber backend. The template text says: "By default, this template uses biblatex and adopts the Chicago referencing style. However, the journal you're submitting to may require a different reference style; specify the journal … with the class' journal option" [S13]. The journal requires **author–date** citations [S1]. Do not set `style=` yourself; let `journal=nlp` choose.

**Citation commands.** The template shows `\autocite{key}` [S13]. Use the standard biblatex commands (biblatex manual §3.9, "Citation Commands" [S33]):
- `\parencite{key}` gives "(Mu and Viswanath 2018)".
- `\textcite{key}` gives "Mu and Viswanath (2018)".
- `\autocite` behaves like `\parencite` under author–date styles.

**Engine.** `pdflatex` → `biber` → `pdflatex` → `pdflatex` [S13].

**Upload package.**
- **Initial submission:** one PDF uploaded as **"Main Document"**, with all figures and tables embedded [S1][S2].
- **After acceptance:** LaTeX source files, individual figure files, and a PDF of the final version [S1][S2].
- **Images:** "authors should flatten their image files before uploading them to Overleaf and the journal's submission system" [S1].
- **Figure formats and resolution:** no figure format or resolution is stated on the journal page, which points to Cambridge's Artwork Guide. Its specifics are **UNVERIFIED** because the guide was not read. Vector PDF figures are fine to embed in the submission PDF.
- Keep each figure as a separate `.pdf` file in a `figures/` folder, ready for acceptance.

---

## 3. Front matter

**Title.** The journal asks for "minimal capitalisation" [S1], and published titles use sentence case (e.g. "Maximizing RAG efficiency: A comparative analysis of RAG methods" [S25]). This changes case only, not wording. Use:

```latex
\title{Read-time removal of superseded facts in agent memory using embedding geometry}
```

**Running head.** The class generates it ("F. Author et al." on even pages, the journal name on odd pages) [S14]. There is no short-title macro in the template, and **no stated requirement** for one.

**Author block.** Place this in the preamble, following the template pattern `\author` / `\affiliation` / `\email[Name]{address}` [S13]. The `\email` author is rendered as "\*Corresponding author. Email: …" [S14].

```latex
\author{Ege Kutlu}
\affiliation{Institute for Data Science \& Artificial Intelligence, Bo\u{g}azi\c{c}i University, \.{I}stanbul, T\"{u}rkiye}
% ORCID (Ege Kutlu): [CONFIRM: ORCID iD] -- no ORCID macro exists in the template; enter it in ScholarOne

\author{\c{S}ener \"{O}z\"{o}nder}
\affiliation{Institute for Data Science \& Artificial Intelligence, Bo\u{g}azi\c{c}i University, \.{I}stanbul, T\"{u}rkiye}
\email[\c{S}ener \"{O}z\"{o}nder]{sener.ozonder@bogazici.edu.tr}
% ORCID (Ş. Özönder, corresponding): [CONFIRM: ORCID iD] -- REQUIRED in ScholarOne at submission [S2]
```

- Delete the existing corresponding-author footnote (`\footnote{Corresponding author: …}` / `\thanks{…}`). The class marks the corresponding author through `\email`.
- The journal says the first page should give "the name(s) and email address(es) of the author(s)" [S1]. The template uses `\email` only for the corresponding author. Do **not** add a second `\email`, because it may mark Kutlu as corresponding too. Instead, flag Ege Kutlu's e-mail as an open question (§12). ScholarOne collects it anyway.
- The affiliation format follows the journal's "department, institution, city, … country" order [S1]. "Türkiye" is kept as written; the copyeditor may anglicise it to "Turkey", as in the 2025 article by Şakar and Emekci [S25].
- **Do not invent an ORCID macro.**

**Abstract.**
- The journal asks for "Approximately 300 words" [S1]. The abstract is **unstructured**; no headings are required.
- The current ~280-word abstract **fits. Keep it verbatim**, except for the optional E1 terminology tweak in §8.2.
- Put it inside `\begin{document}`:

```latex
\begin{document}
\begin{abstract}
<current abstract text, unchanged except E1>
\end{abstract}
```

  If the class needs `\maketitle`, keep it only if the template build shows the title missing. The template sample has **no** `\maketitle` [S13].

**Keywords.** The journal asks for "3-5 relevant keywords" [S1]. The template uses `\keywords{keyword entry 1, keyword entry 2, keyword entry 3} %% First letter not capped` in the preamble [S13]. Replace the 7-keyword line in the body with this preamble line:

```latex
\keywords{agent memory, knowledge conflict, retrieval-augmented generation, sentence embeddings, natural language inference}
```

This drops "small language models" and "embedding post-processing". The authors may swap one in; 5 is the maximum.

**Highlights, graphical abstract, impact statement:** **no stated requirement** [S1].

---

## 4. Body

**Structure.** The journal sets no mandated section structure. Subheadings are "numbered 1, 1.1, 1.1.1", with "no more than three levels" normally [S1]. The paper uses 2 levels, so it complies. Keep all sections (1 Introduction … 8 Conclusion) and the numbering unchanged. Recent articles include a "Limitations" section [S31]; the paper's §7.5 Limitations stays where it is.

**Length.**
- Limit: Article, "~8,000–12,000 words" [S1]. The journal does not say what counts towards it (references, tables, appendices) — **UNVERIFIED**.
- Estimate: body prose is about 10,500–11,500 words (an *estimate*). The whole PDF, including tables, figure text and references, is about 14,000 words.
- Verdict: the body probably **fits** the upper part of the range. If the editor counts everything, the paper is about 2,000 words over.
- Action: **do not shorten now.** E7 (§8.2) is a contingency the authors can trigger: move Appendix B to online supplementary material.

**Figures and tables.**
- Rules from the journal [S1]:
  - Call out every figure and table in sequential order; all are already called out.
  - Captions are required.
  - Table column and row headings use **sentence case**.
  - Diagrams, graphs and code snippets are numbered "Figures" with Arabic numerals.
  - "Figures may have sources, and tables must have sources." This is a general rule; for the authors' own results, flag it (§12) rather than adding source lines.
- Template conventions [S13]:
  - Table caption **above** the table, inside `threeparttable`, with `\toprule/\midrule/\bottomrule` and an optional `\headrow` on the header row.
  - Figure caption **below** the figure.
  - Use `figure*` for full-width figures.
- Conversion actions:
  - Keep every `tabular` body byte-identical. You may wrap it as follows:

    ```latex
    \begin{table}[hbt!]
    \begin{threeparttable}
    \caption{...}\label{...}
    <existing tabular, unchanged>
    \end{threeparttable}
    \end{table}
    ```

  - You may capitalise only the first letter of a header cell ("model" → "Model"). Never change any data cell.
  - If a table is too wide, use `\small`/`\footnotesize` or `\resizebox{\linewidth}{!}{…}`. Do not split or prune tables.
- Accessibility: the journal requires WCAG 2.1 AA and alt text for all figures [S1]. Authors may submit their own descriptions through Cambridge's Accessibility Descriptions form; otherwise machine-generated ones are provided at proof stage. **Action:** add a comment above each `\includegraphics`, `% ALT-TEXT: [CONFIRM: authors to supply]`. Do not write alt text that interprets results.

**Style conventions** [S1]:
- British or American spelling, used consistently. The draft uses British "-ise" spellings ("recognise", "randomised"), so keep British.
- Single quotation marks.
- "Numbers should be written out up to 100, except where they refer to precise measurements."
- "per cent" instead of "%".
- Minimal footnotes. The template uses `\endnote{…}` with `\printendnotes`.

**Agent rule for style:**
- **Do NOT convert digits to words and do NOT replace "%"** in body, tables or figures. These are copyediting matters handled after acceptance, and touching them risks changing numbers. Flag them in §12.
- Convert any remaining `\footnote{…}` to `\endnote{…}` and place `\printendnotes` as in §5. If the class renders `\endnote` as a footnote, that is expected [S13].

**Equations.** amsmath is loaded, so no change is needed. Colour has no stated restriction.

**Appendices vs supplementary material.**
- In the template, appendices come **after** `\printbibliography`, introduced by `\appendix` [S13]. Move Appendix A (frozen parameters, Table 12) and Appendix B (Table 13) there.
- Supplementary material is published online without typesetting or copyediting [S1]. Use it only for E7.

---

## 5. Back matter & declarations

**Requirements** [S1] (journal "Reporting requirements"; the page states no order):
- Acknowledgements (optional), including any AI-use disclosure in manuscript preparation.
- Authorship contribution statement, CRediT (optional).
- Conflict of interest statement (required). The standard wording when there are none is "The author(s) declare none."
- Funding disclosure statement (required).
- Data availability statement (required). It must be placed "in the back matter … before the References" [S10].
- Ethics statement (required). If no approval was needed, use "Ethical approval was not required."

**Headings conflict.** The journal page names are "Conflict of interest statement", "Funding disclosure statement" and "Ethics statement". The template uses `\paragraph{Competing Interests}`, `\paragraph{Funding Statement}` and `\paragraph{Ethical Standards}` [S13]. Recent articles print "Competing interests" [S28]. **Follow the template headings.** They are the class's typeset convention and match published practice, and the content requirement is the same.

**Order and snippet.** Use the template order. Insert this after the Conclusion; it replaces the current back matter:

```latex
\paragraph{Acknowledgments}
The numerical calculations reported in this paper were partially performed at Barcelona Supercomputing Center (BSC) and TUBITAK ULAKBIM, High Performance and Grid Computing Center.
GPT-5 mini was used as the annotator of the gold conflict dataset, as described in Section~4.2.
[CONFIRM: declare any AI assistance used in writing code or preparing the manuscript, and state that the authors reviewed all content and take responsibility for it.]

\paragraph{Funding Statement}
[CONFIRM: funding statement, or ``This research received no specific grant from any funding agency.'']

\paragraph{Competing Interests}
[CONFIRM: The authors declare none.]

\paragraph{Data Availability Statement}
The detector, the frozen artifact with its fingerprint, the campaign outputs for all five answering models, the gold conflict dataset with its builder and a test that re-derives its tier counts and AUROCs from the raw adjudication files, and the scripts that regenerate every table are available at \url{https://github.com/kutluege/EvoMemBench} [CONFIRM: public release and archival DOI]. A file in the repository maps every number in this paper to the artifact it comes from.

\paragraph{Ethical Standards}
[CONFIRM: Ethical approval was not required.]

\paragraph{Author Contributions}
[CONFIRM: CRediT roles, e.g. E.K.: conceptualisation, methodology, software, investigation, data curation, writing (original draft); \c{S}.\"{O}.: conceptualisation, supervision, resources, writing (review and editing)]

\printendnotes

\printbibliography

\appendix
\section{Frozen parameters}          % former Appendix A, content unchanged
...
\section{Answer changes on the unique stratum}   % former Appendix B, content unchanged
...
\end{document}
```

**Mapping table.**

| Current draft section | Target heading / location | Action |
|---|---|---|
| Data and Code Availability | `\paragraph{Data Availability Statement}` (required; before References) | Text verbatim; keep the CONFIRM |
| Author Contributions | `\paragraph{Author Contributions}` (optional, CRediT) | Keep the CONFIRM verbatim |
| Funding | `\paragraph{Funding Statement}` (required) | Keep the CONFIRM verbatim |
| Declaration of Competing Interests | `\paragraph{Competing Interests}` (required) | Keep it as a CONFIRM, but update the suggested wording inside it to the journal's standard "The authors declare none." [S1] |
| Use of Generative AI | Merged into `\paragraph{Acknowledgments}`. The research-use description stays in Section 4.2 (see E6). | Move both sentences verbatim; delete the old heading |
| Acknowledgements | `\paragraph{Acknowledgments}` (template spelling) | Verbatim |
| *(none)* | `\paragraph{Ethical Standards}` (**new, required**) | Insert "[CONFIRM: Ethical approval was not required.]". The authors must confirm, because the study uses no human participants and the benchmark data are public. |
| Appendix A, Appendix B | After `\printbibliography`, under `\appendix` | Move; content unchanged |
| References | `\printbibliography` (biblatex) | Rebuild from `refs_nlp.bib` (§6) |

**AI-use disclosure guidance** (journal "Artificial intelligence" section [S1]):
- AI used "to generate text" is declared "in a separate acknowledgments section or in a footnote".
- AI used to analyse data or extract insights must be "described in your methods section".
- Figures generated or modified by AI are declared in the figure captions.
- The declaration must include the tool name and version, the dates of use, how others can access the tool, and "a full description of how you used the tool".
- Minimal non-generative uses (spelling, grammar, formatting) need no declaration.
- AI tools cannot be authors.

Applied to this paper:
1. GPT-5 mini as the **annotator** is a research use, so the **primary disclosure belongs in Section 4.2 (Methods)**, which already describes it. E6 adds a placeholder for the version and dates.
2. The Acknowledgments sentence stays as a cross-reference.
3. Any writing or coding assistance goes into Acknowledgments through the existing CONFIRM.

**[CONFIRM] items that the journal requires to be resolved before submission:**
- (4) Archival DOI and public release of the repository. A Data availability statement is required, and the journal prefers repositories with persistent identifiers [S10].
- (5) CRediT roles. These are optional, so the authors may delete the paragraph instead; the agent must not.
- (6) Funding statement (required).
- (7) Competing interests (required).
- (8) AI-assistance declaration, required if any generative use occurred [S1].
- The new GPT-5 mini version/dates placeholder (E6).
- The new Ethics placeholder.
- (9) and (10) Model-card access dates. These are needed for the reference entries.
- (1), (2), (3) are factual checks the authors must still do. The journal does not specifically require them, but they must not ship unresolved.

---

## 6. References

### 6.1 Style rules
- **In-text** [S1]: "In-text bibliographical references should be given in parentheses in standard author-date form in the body of the text: (Lee and Devore 1968: 236)."
  - Three or more authors: first author + "et al."
  - Same author and same year: add a, b, c.
  - Several works in one citation are ordered by date, earliest first. In biblatex, write the keys in chronological order inside one `\parencite{…,…}`.
- **Reference list** [S1]: alphabetical by surname. The journal's examples:
  - "Akmajian A. and Lehrer A. (1976). NP-like quantifiers and the problem of determining the head of an NP. *Linguistic Analysis* 2, pp. 295-313."
  - "Salton G., Zhao Z. and Buckley C. (1990). … Technical Report 90-1137. …"
  - Titles use minimal capitalisation; journal and book titles are in italics.
- **In practice** (2025 NLP article [S25]):
  - Entries look like "Devlin J., Chang M.-W., Lee K. and Toutanova K. (2019). …".
  - arXiv entries end with "arXiv." plus a `https://doi.org/10.48550/arXiv.…` DOI.
  - Journal entries look like "*Communications of the ACM* 18, 509–517" with a DOI.
  - Web entries look like "LangChain. (n.d.) … Available at: <URL>".
  - DOIs are shown as full `https://doi.org/…` links.
- **Template rendering:** biblatex's default Chicago author–date style renders e.g. "Adade, Camila M, … and Maurilio J Soares. 2007. … *Micron* 38 (3): 252–256" [S14].
  - *Conflict:* the house style (initials after the surname, year in parentheses) differs from the template's default Chicago rendering.
  - *Recommendation:* **do not hand-format.** Supply clean `.bib` data and let `journal=nlp` choose the style. The initial submission is a PDF that is refereed, not typeset, and Cambridge restyles references at typesetting.
- **arXiv:** citing arXiv preprints is allowed in practice; the journal's own articles cite them [S25]. DOIs are **not stated as mandatory**, but they are used when available [S25]. Add a `doi` only where it is certain. For arXiv, the standard DataCite DOI form is `10.48550/arXiv.<id>`; the authors should spot-check that each one resolves.

### 6.2 Citation conversion map (numbered → author–date)
Rule: if the bracket follows a name that acts as a grammatical subject or object ("Mu and Viswanath [12]"), use `\textcite`. Otherwise ("MemoryAgentBench [9]", "vLLM [10]", "arm [11]", "resamples [3]", "Wilson intervals [16]"), use `\parencite`. If the source already uses `\cite{key}` with its own keys, keep those keys and only change the command. Inside Table 3, `\parencite` makes the model column wider. If the table overflows, remove the in-cell citations and append to the caption: "Model sources: \textcite{gemma3}; \textcite{gemma4card}; \textcite{phi4mini}; \textcite{qwen3}; \textcite{qwen35card}."

| # | key (suggested) | renders as |
|---|---|---|
| 1 | phi4mini | Abouelenin et al. 2025 |
| 2 | clopper1934 | Clopper and Pearson 1934 |
| 3 | efron1993 | Efron and Tibshirani 1993 |
| 4 | gemma3 | Gemma Team 2025 |
| 5 | gemma4card | Google n.d. |
| 6 | hanley1983 | Hanley and Lippman-Hand 1983 |
| 7 | he2023debertav3 | He et al. 2023 |
| 8 | holm1979 | Holm 1979 |
| 9 | hu2026memoryagentbench | Hu et al. 2026 |
| 10 | kwon2023vllm | Kwon et al. 2023 |
| 11 | mcnemar1947 | McNemar 1947 |
| 12 | mu2018abtt | Mu and Viswanath 2018 |
| 13 | pedregosa2011 | Pedregosa et al. 2011 |
| 14 | qwen35card | Qwen Team n.d. |
| 15 | wang2026evomembench | Wang et al. 2026 |
| 16 | wilson1927 | Wilson 1927 |
| 17 | qwen3 | Yang et al. 2025 |
| 18 | zhang2025qwen3emb | Zhang et al. 2025 |
| new | sakar2025rag | Şakar and Emekci 2025 |
| new | hou2024anisotropic | Hou et al. 2024 |

### 6.3 `refs_nlp.bib`
Data are taken only from the paper's reference list, plus the 2 verified in-journal papers. Placeholders are kept.

```bibtex
@misc{phi4mini, author={Abouelenin, A. and others}, title={{Phi-4-Mini} Technical Report: Compact yet Powerful Multimodal Language Models via Mixture-of-{LoRAs}}, year={2025}, eprint={2503.01743}, eprinttype={arXiv}}
@article{clopper1934, author={Clopper, C. J. and Pearson, E. S.}, title={The Use of Confidence or Fiducial Limits Illustrated in the Case of the Binomial}, journaltitle={Biometrika}, year={1934}, volume={26}, pages={404--413}}
@book{efron1993, author={Efron, B. and Tibshirani, R. J.}, title={An Introduction to the Bootstrap}, publisher={Chapman \& Hall}, location={New York}, year={1993}}
@misc{gemma3, author={{Gemma Team}}, title={{Gemma 3} Technical Report}, year={2025}, eprint={2503.19786}, eprinttype={arXiv}}
@online{gemma4card, author={{Google}}, title={gemma-4-{E2B}-it, model card}, url={https://huggingface.co/google/gemma-4-E2B-it}, note={[CONFIRM: access date]}}
@article{hanley1983, author={Hanley, J. A. and Lippman-Hand, A.}, title={If Nothing Goes Wrong, Is Everything All Right? Interpreting Zero Numerators}, journaltitle={JAMA}, year={1983}, volume={249}, pages={1743--1745}}
@inproceedings{he2023debertav3, author={He, P. and Gao, J. and Chen, W.}, title={{DeBERTaV3}: Improving {DeBERTa} using {ELECTRA}-Style Pre-Training with Gradient-Disentangled Embedding Sharing}, booktitle={International Conference on Learning Representations (ICLR)}, year={2023}}
@article{holm1979, author={Holm, S.}, title={A Simple Sequentially Rejective Multiple Test Procedure}, journaltitle={Scandinavian Journal of Statistics}, year={1979}, volume={6}, pages={65--70}}
@misc{hu2026memoryagentbench, author={Hu, Y. and Wang, Y. and McAuley, J.}, title={Evaluating Memory in {LLM} Agents via Incremental Multi-Turn Interactions}, year={2026}, eprint={2507.05257v4}, eprinttype={arXiv}}
@inproceedings{kwon2023vllm, author={Kwon, W. and Li, Z. and Zhuang, S. and Sheng, Y. and Zheng, L. and Yu, C. H. and Gonzalez, J. E. and Zhang, H. and Stoica, I.}, title={Efficient Memory Management for Large Language Model Serving with {PagedAttention}}, booktitle={Proceedings of the 29th Symposium on Operating Systems Principles (SOSP)}, year={2023}, pages={611--626}}
@article{mcnemar1947, author={McNemar, Q.}, title={Note on the Sampling Error of the Difference between Correlated Proportions or Percentages}, journaltitle={Psychometrika}, year={1947}, volume={12}, pages={153--157}}
@inproceedings{mu2018abtt, author={Mu, J. and Viswanath, P.}, title={All-but-the-Top: Simple and Effective Postprocessing for Word Representations}, booktitle={International Conference on Learning Representations (ICLR)}, year={2018}}
@article{pedregosa2011, author={Pedregosa, F. and others}, title={Scikit-learn: Machine Learning in {Python}}, journaltitle={Journal of Machine Learning Research}, year={2011}, volume={12}, pages={2825--2830}}
@online{qwen35card, author={{Qwen Team}}, title={{Qwen3.5-9B}, model card}, url={https://huggingface.co/Qwen/Qwen3.5-9B}, note={[CONFIRM: access date]}}
@misc{wang2026evomembench, author={Wang, Y. and Zhang, Z. and Chi, M. and others}, title={{EvoMemBench}: Benchmarking Agent Memory from a Self-Evolving Perspective}, year={2026}, eprint={2605.18421v2}, eprinttype={arXiv}}
@article{wilson1927, author={Wilson, E. B.}, title={Probable Inference, the Law of Succession, and Statistical Inference}, journaltitle={Journal of the American Statistical Association}, year={1927}, volume={22}, pages={209--212}}
@misc{qwen3, author={Yang, A. and others}, title={{Qwen3} Technical Report}, year={2025}, eprint={2505.09388}, eprinttype={arXiv}}
@misc{zhang2025qwen3emb, author={Zhang, Y. and Li, M. and Long, D. and others}, title={{Qwen3 Embedding}: Advancing Text Embedding and Reranking Through Foundation Models}, year={2025}, eprint={2506.05176}, eprinttype={arXiv}}
@article{sakar2025rag, author={{\c{S}}akar, Tolga and Emekci, Hakan}, title={Maximizing {RAG} efficiency: A comparative analysis of {RAG} methods}, journaltitle={Natural Language Processing}, year={2025}, volume={31}, number={1}, pages={1--25}, doi={10.1017/nlp.2024.53}}
@article{hou2024anisotropic, author={Hou, F. and Wang, R. and Ng, S.-K. and Zhu, F. and Witbrock, M. and Cahan, S. F. and Chen, L. and Jia, X.}, title={Anisotropic span embeddings and the negative impact of higher-order inference for coreference resolution: An empirical analysis}, journaltitle={Natural Language Engineering}, year={2024}, volume={30}, number={6}, pages={1301--1322}, doi={10.1017/S1351324924000019}}
```

Notes on these entries:
- Journal abbreviations are expanded ("Scand. J. Stat." → full title, and so on). This does not change content.
- The model cards have no year in the draft. Do not invent one; biblatex prints "n.d.". Once the access date is confirmed, add `urldate={YYYY-MM-DD}` and remove the note.

### 6.4 Four examples in the journal's house style
Pattern from [S1][S25]. Italics are shown as *…*.
1. **arXiv:** Hu Y., Wang Y. and McAuley J. (2026). Evaluating memory in LLM agents via incremental multi-turn interactions. arXiv preprint arXiv:2507.05257v4. *(The house style also appends `https://doi.org/10.48550/arXiv.2507.05257` [S25]; check that it resolves.)*
2. **Journal article:** McNemar Q. (1947). Note on the sampling error of the difference between correlated proportions or percentages. *Psychometrika* 12, 153–157.
3. **Conference:** Mu J. and Viswanath P. (2018). All-but-the-top: simple and effective postprocessing for word representations. In *International Conference on Learning Representations (ICLR)*.
4. **Model card:** Qwen Team (n.d.). Qwen3.5-9B, model card. Available at: https://huggingface.co/Qwen/Qwen3.5-9B [CONFIRM: access date].

In text these appear as (Hu et al. 2026), (McNemar 1947), Mu and Viswanath (2018), and (Qwen Team n.d.).

---

## 7. Anonymization

**Not required (single-anonymous review).** The peer-review page says: "This journal uses a single-anonymous peer review model" [S6]. The review-process page says: "the reviewers know the identity of the author" [S7].
- Keep the author block, the GitHub link, the acknowledgements and the funding text.
- Cambridge's anonymising guide applies only to journals with double-anonymous review [S16].

---

## 8. Content adaptation

### 8.1 Aims & scope (paraphrased) and fit
**Scope** [S4][S11]: the journal is an open-access venue for researchers and practitioners across NLP. It aims to connect computational-linguistics research with implementable applications that have real-world potential. Listed areas include IR, QA, MT, summarisation and others. It explicitly invites novel methods, including deep learning and LLMs, multilingual and low-resource work, and surveys. Theoretical papers should be detailed enough to implement [S1].

**Strong fit:**
- The paper combines NLP building blocks in a deployable read-time component:
  - sentence-embedding geometry (ABTT post-processing),
  - an NLI cross-encoder as a verifier,
  - knowledge conflicts in retrieval-augmented LLM memory.
- It is implementable: frozen parameters (Appendix A), a public code and data release, and no generative call at inference. This matches "practical applications with potential real-world use".
- It releases a resource (54,569 adjudicated pairs). Resources and datasets are common in the journal [S26].
- The journal has published RAG engineering work [S25] and embedding-anisotropy analysis [S28].

**Weak points:**
- The evaluation uses one templated English benchmark; the paper's own Limitations say so. Expect reviewers in this venue to ask about free text and other languages, given the journal's multilingual emphasis. Do not add any claims about this.
- The journal's in-house literature on agent memory and knowledge conflicts is thin.
- The statistics-heavy presentation is fine, but the house style (written-out numbers, "per cent") will need copyediting later.

### 8.2 Edit list

| ID | Location | Type | Max length | Rationale (scope) | Source |
|---|---|---|---|---|---|
| E1 | Abstract, sentence 1 | reword (terminology) | ±3 words | Make the subject explicit for an NLP readership: "Agents keeping memories in a vector store" → "Language-model agents that keep memories in a vector store". **Optional.** The abstract is otherwise unchanged and stays ≈280 words, under the ~300 limit. | [S1][S4] |
| E2 | Introduction, end of paragraph 3 (after "…the error needs both records on the page."), **or** immediately before the paragraph that introduces H-Nav-GEO | add | ≤ 120 words | NLP/NLI angle connecting to the journal's themes. Insert exactly the text after this table, which restates existing content and adds no new claim. | [S4] |
| E3 | Introduction, paragraph 1, after "…retrieved by similarity when it is needed." | add citation | 1 citation | Tie to the journal's RAG/vector-store literature: append " \parencite{sakar2025rag}" before the full stop. | [S25] |
| E4 | Section 3.3 (ABTT cosine), after the sentence beginning "Following Mu and Viswanath…" | add citation clause | ≤ 25 words | In-journal evidence that embedding anisotropy hampers separating related but distinct items. Append the sentence after this table. | [S27][S28] |
| E5 | Front matter | replace | — | Keywords 7 → 5 (§3); title in sentence case (§3). | [S1] |
| E6 | Section 4.2, after "…were adjudicated by GPT-5 mini through the API, …" (end of that sentence) | add placeholder | 1 placeholder | The journal's AI policy requires tool version, dates of use and access route in the **methods**. Insert " [CONFIRM: GPT-5 mini model snapshot/version identifier and dates of use]". Do not fill it in. | [S1] |
| E7 | Appendix B (Table 13) | move (**contingent; do not apply by default**) | — | Only if the editor or authors judge the ~8,000–12,000-word limit exceeded. Move to an online "Supplementary material" file and replace the "Appendix B" references with "Supplementary Table S1". | [S1] |

**E2 text (insert verbatim):**
> Viewed as a natural language processing problem, the decision combines three established questions: whether two sentences state the same proposition with different values, which is the province of natural language inference; how the geometry of contextual embeddings, whose anisotropy can make related but distinct items hard to separate \parencite{hou2024anisotropic}, shapes similarity-based decisions; and how retrieval-augmented systems built on vector stores \parencite{sakar2025rag} should treat conflicting evidence. H-Nav-GEO uses an embedding post-processing step \parencite{mu2018abtt} and a natural language inference cross-encoder as components of a read-time filter for one practical setting, the memory of an agent built around a small local model; the evaluation reported here is limited to one templated benchmark (Section~7.5).

(≈110 words. If `\ref` labels exist, replace "Section~7.5" with `Section~\ref{<label of Limitations>}`.)

**E4 text (append):**
> A related effect has been reported for contextual span embeddings in coreference resolution, where anisotropy makes related but distinct mentions harder to separate \parencite{hou2024anisotropic}.

The net body change is about 170 words, which is under 2%.

### 8.3 Verified in-journal references (2)

1. **Şakar T. and Emekci H. (2025).** Maximizing RAG efficiency: A comparative analysis of RAG methods. *Natural Language Processing* 31(1), 1–25. **DOI 10.1017/nlp.2024.53**.
   - Verified from the Cambridge-hosted PDF header and the issue page [S25][S26].
   - Relevance: a comparative study of RAG pipelines with vector databases and embedding models.
   - Cite in: Introduction ¶1 (E3) and E2.
2. **Hou F., Wang R., Ng S.-K., Zhu F., Witbrock M., Cahan S. F., Chen L. and Jia X. (2024).** Anisotropic span embeddings and the negative impact of higher-order inference for coreference resolution: An empirical analysis. *Natural Language Engineering* 30(6), 1301–1322. **DOI 10.1017/S1351324924000019**.
   - Verified through the Crossref listing for ISSN 1351-3249, institutional repository records and the Cambridge core-reader page [S27][S28][S29].
   - Relevance: anisotropic embeddings make related but distinct items hard to separate, which mirrors the paper's version-vs-look-alike problem and its ABTT motivation.
   - Cite in: §3.3 (E4) and E2.

Considered and **rejected** as not relevant enough:
- Yang et al. 2025, "Semantic enrichment of neural word embeddings…", DOI 10.1017/nlp.2025.10005: word-level retrofitting [S30].
- Wu et al. 2026, "Skeleton-based approach for semantic textual similarity", DOI 10.1017/nlp.2026.10025: an LSTM model for STS [S31].
- "Polish natural language inference and factivity…" (2023), DOI 10.1017/s1351324923000220: seen only as a Crossref title, not read [S29].

No in-journal papers on agent memory or knowledge conflicts were found. Coverage is incomplete because several Crossref queries were rate-limited and the web-search budget ran out (§12).

### 8.4 Title
**Keep** the wording. Set it in sentence case per the journal's "minimal capitalisation" rule (§3): "Read-time removal of superseded facts in agent memory using embedding geometry".

Optional alternative (for the authors to decide; the agent must not apply it): "Read-time removal of superseded facts in agent memory using embedding geometry and natural language inference". It surfaces the NLI component for this readership.

---

## 9. Do-not-change list

Verbatim from the authors' constraints:

The agent must NEVER:
- change any number, statistic, p-value, CI, count, table cell or figure;
- add experiments, results or claims, or strengthen claims. Specifically, "frozen transfer" must not become "held-out", and limitations and development-bias disclosures must not be softened or removed;
- delete the Limitations section;
- resolve or delete `[CONFIRM: ...]` placeholders on its own. It keeps them and lists the ones the journal requires to be resolved before submission;
- regenerate figure images. If text embedded in a figure conflicts with the journal's rules or with the manuscript's own terminology, the agent flags it for the authors.

The total net change to body text should stay roughly within 5–10% of the word count.

Journal-specific additions:
- **Do not apply the house rules on numbers and per cent** ("numbers … written out up to 100", "per cent" not "%") to the body, tables or figures. Converting digits to words risks altering numbers. Leave this to the copyeditor and flag it.
- Do not change double to single quotation marks inside quoted example facts (e.g. "Thomas Kyd was born in the city of London"). Flag it only.
- Do not apply E7 unless the authors ask for it.
- Do not add an ORCID macro or invent e-mails, ORCIDs, DOIs, years or access dates.
- Keep the GitHub URL (single-anonymous review).

---

## 10. Pre-submission checklist

- [ ] `\documentclass[journal=nlp, manuscript=article, year=2026, volume=32]{cup-journal}` compiles with pdflatex → biber → pdflatex ×2.
- [ ] No `natbib`/`cite`/`thebibliography`/`\bibliographystyle` remains; `\addbibresource{refs_nlp.bib}` and `\printbibliography` are present.
- [ ] All 18 original references plus 2 new ones appear in the list; there are no "?" or undefined-citation warnings in the biber/LaTeX logs.
- [ ] Every former `[n]` is now `\textcite`/`\parencite`; narrative vs parenthetical use is correct.
- [ ] The title is in sentence case. The author block matches §3. The corresponding-author footnote is removed. ORCID placeholders are present as comments.
- [ ] The abstract is unchanged except E1, and has ≤ ~300 words. Check the count by running `detex` and `wc -w` on the abstract.
- [ ] `\keywords{…}` has exactly 5 entries, comma-separated, lower-case first letter.
- [ ] The body section numbering and the order of figures and tables are unchanged. Every figure and table is called out in order.
- [ ] Table data cells are byte-identical to the source; diff each `tabular` body.
- [ ] Figures are embedded in the PDF. Original figure files are kept separately for acceptance. `% ALT-TEXT: [CONFIRM]` comments are added.
- [ ] Back matter is in the order Acknowledgments → Funding Statement → Competing Interests → Data Availability Statement → Ethical Standards → Author Contributions → (endnotes) → References → Appendices.
- [ ] The Data Availability Statement comes before the References.
- [ ] The "Use of Generative AI" heading is gone, and its two sentences are in Acknowledgments. E6 placeholder is in Section 4.2.
- [ ] All `[CONFIRM: …]` items are still present (10 original + E6 + Ethics + alt-text). A list of them is given to the authors.
- [ ] Edits E1–E6 are applied exactly; E7 is not applied. Net body change is under 10%.
- [ ] A word-count report is given to the authors: body only, and body plus tables, references and appendices.
- [ ] The PDF has page numbers. The output file is `main_nlp.pdf`, to upload as "Main Document".
- [ ] Before submission (authors): the funded-journal list and the eligibility checker confirm APC coverage; the corresponding author's ORCID is linked in ScholarOne; the submission uses the institutional e-mail.

---

## 11. Cover letter notes

- **No cover-letter requirement is stated** on the journal pages [S1][S2]. **No stated requirement** for suggested or opposed reviewers either; ScholarOne may ask, which is UNVERIFIED.
- Recommended content (not mandated):
  1. Article type: **Article**.
  2. Fit:
     - a practical, implementable NLP component combining sentence-embedding post-processing and an NLI verifier for knowledge conflicts in retrieval-augmented agent memory;
     - a released 54,569-pair adjudicated dataset with code;
     - a link to the journal's aim of bridging research and real-world applications.
  3. Statement that the manuscript is not under consideration elsewhere [S1]. Mention any arXiv preprint; preprints do not count as prior publication under Cambridge's preprint policy [S1][S17].
  4. State the frozen-transfer (not held-out) nature of the sh_64k evaluation and the single-benchmark limitation, to pre-empt reviewer concerns. Use the same wording as the paper.
  5. Note that the corresponding author is at Boğaziçi University, an EKUAL institution, so that OA funding can be checked at acceptance.
  6. Acknowledge that all authors agree to be invited as reviewers [S2].
- Submit through `https://mc.manuscriptcentral.com/nlp` [S2]. Editorial queries go to NLP@cambridge.org; LaTeX issues go to CUPTeXSupport@straive.com [S1].

---

## 12. Open questions / UNVERIFIED items

1. **APC coverage (critical).** It is UNVERIFIED whether *Natural Language Processing* is on the 2026 TÜBİTAK-funded CUP OA list.
   - Tried: the `.xlsx` lists at cabim.ulakbim.gov.tr [S24] and on the Boğaziçi library site. Both came back as binary content that could not be read.
   - Also tried: Cambridge's waivers page and eligibility checker [S20]. Both load the journal list dynamically, so no list was visible.
   - Supporting evidence: the agreement covers gold/fully OA journals without quota [S19][S21][S23], and Cambridge says R&P agreements "in the majority of cases … cover the full costs of Gold OA" [S8].
   - Action for the authors: open the funded-journal list, search for "Natural Language Processing" / 2977-0424, and keep a screenshot. If it is absent, the APC of £2,610 / $3,655 is mandatory and the journal is not a $0 route.
2. **Boğaziçi EKUAL membership.** Not checked against the EKUAL member list `.xlsx`. Supporting evidence: Boğaziçi library's own announcement [S21].
3. **NLP LaTeX zip contents** (`NLP-AuthorMacro-1-.zip`, [S15]). Not readable. It is unknown whether it ships `cup-journal.cls` or another class, and which biblatex style `journal=nlp` loads (journal house style vs Chicago). Follow the zip's sample if it differs from Overleaf.
4. **`manuscript=` option values.** Not documented. `article` is a reasonable guess; fall back to the template default.
5. **Word-count basis.** It is unknown whether the ~8,000–12,000 words include references, tables, captions or appendices. The journal page is silent [S1].
6. **Indexing of the renamed title.**
   - The journal's A&I page lists SCIE/SSCI/AHCI and Scopus [S5], and the homepage shows a 2025 Impact Factor of 1.6 [S3].
   - Not checked: Clarivate MJL and Scopus source records for ISSN 2977-0424, and the quartile. The web-search budget was exhausted. The authors' DSAI rule needs Q1–Q3, so check JCR/Scopus directly.
7. **Artwork guide.** Accepted figure formats and resolution were not read.
8. **Ege Kutlu's e-mail** on the first page, which the journal requests [S1], and both ORCIDs.
9. **"Tables must have sources."** It is unclear how this applies to tables of the authors' own results. Ask the editorial office or leave as is.
10. **House style** (numbers under 100 written out, "per cent", single quotes) is not applied, by design. The authors may apply it to prose only, by hand.
11. **Embedded figure text:** figures may contain "%" and digits under 100, which conflict with the house style. Flagged only; figures must not be regenerated.
12. **In-journal literature search** is incomplete. Several Crossref queries (ISSN 1351-3249 / 2977-0424) and a doi.org lookup were rate-limited (HTTP 429), and the web-search budget ran out. More relevant papers may exist.
13. **Licence choice:** the authors must pick a CC licence at acceptance [S8]. TÜBİTAK funding may expect CC BY; this is unverified.

---


### Figure-text flags for the authors (journal-independent; verified against the PDF by the coordinator, 2026-10-09)
The coding agent must NOT regenerate figures. It lists these in its hand-back report so the authors can fix the figure sources before any submission:
- **"held-out" vs "frozen transfer":** Fig. 3A panel title "AUROC on the held-out sh_64k balanced set"; Fig. 4 third panel label "sh_64k held-out, one shot"; Fig. 6B legend "held-out sh_64k". The manuscript text calls sh_64k "a frozen-transfer condition, not a held-out test" (Sections 1, 4.1, 7.5, 8). Suggested figure wording: "frozen-transfer sh_64k".
- **"whitening" vs "not whitening":** Fig. 2b box "ABTT whitening"; Fig. 3A row label "whitened cosine"; Fig. 6A legend "whitened cosine (mean + 128 shared directions removed)" and axis note "whitened +0.0015/+0.0041". Section 3.3 states "The covariance is not rescaled, so this is not whitening" and uses "ABTT cosine". Suggested figure wording: "ABTT cosine".
- **Internal file names inside images:** Fig. 1 footer ("Sources: gold_conflict_dataset.jsonl.gz …, m7_delta_geometry.json …, GEOMETRY_AND_ANISOTROPY.md §2"); Fig. 2 footer ("geo_operating_point.json, geo_identity_screen.json"). Recommend removing them; under double-anonymous review they may also aid de-anonymization together with the repository.

## Sources
All sources accessed 2026-10-09.

1. [S1] NLP — Preparing your materials. https://www.cambridge.org/core/journals/natural-language-processing/information/author-instructions/preparing-your-materials
2. [S2] NLP — Submitting your materials. https://www.cambridge.org/core/journals/natural-language-processing/information/author-instructions/submitting-your-materials
3. [S3] NLP — Journal homepage. https://www.cambridge.org/core/journals/natural-language-processing
4. [S4] NLP — About this journal (aims & scope). https://www.cambridge.org/core/journals/natural-language-processing/information/about-this-journal
5. [S5] NLP — Abstracting and indexing. https://www.cambridge.org/core/journals/natural-language-processing/information/about-this-journal/abstracting-and-indexing
6. [S6] NLP — Peer review information. https://www.cambridge.org/core/journals/natural-language-processing/information/peer-review-information
7. [S7] NLP — Review process. https://www.cambridge.org/core/journals/natural-language-processing/information/peer-review-information/review-process
8. [S8] NLP — Open access options. https://www.cambridge.org/core/journals/natural-language-processing/information/open-access-options
9. [S9] NLP — Fees and pricing. https://www.cambridge.org/core/journals/natural-language-processing/information/author-instructions/fees-and-pricing
10. [S10] NLP — Research transparency. https://www.cambridge.org/core/journals/natural-language-processing/information/journal-policies/research-transparency
11. [S11] Mitkov R., Editorial Note, *Natural Language Engineering* 30 (2024) 215–216, DOI 10.1017/S1351324924000020. https://www.cambridge.org/core/services/aop-cambridge-core/content/view/7A063400A61FADF7FE38FAB0D32F7EE1/S1351324924000020a.pdf/editorial_note.pdf
12. [S12] Natural Language Engineering — past-title page. https://www.cambridge.org/core/journals/natural-language-engineering
13. [S13] Overleaf — Cambridge Medium Template Class File (source). https://www.overleaf.com/latex/templates/cambridge-medium-template-class-file/zshzqdxjjqkq
14. [S14] Overleaf — Cambridge Medium template, rendered PDF. https://www.overleaf.com/latex/templates/cambridge-medium-template-class-file/zshzqdxjjqkq.pdf
15. [S15] NLP LaTeX Files (NLP-AuthorMacro-1-.zip; not readable). https://www.cambridge.org/core/services/aop-file-manager/file/6616a846ff18e014ad92efd6
16. [S16] Cambridge — Anonymising your manuscript. https://www.cambridge.org/core/services/authors/anonymising-your-manuscript
17. [S17] Cambridge — Preprint policy. https://www.cambridge.org/core/services/open-access-policies/preprint-policy
18. [S18] Cambridge — Research transparency (general). https://www.cambridge.org/core/services/authors/research-transparency
19. [S19] Cambridge — TÜBİTAK ULAKBİM Read and Publish agreement. https://www.cambridge.org/core/services/open-access-policies/read-and-publish-agreements/oa-agreement-tubitak
20. [S20] Cambridge — OA eligibility checker. https://www.cambridge.org/core/eligibility-checker
21. [S21] Boğaziçi University Library — TÜBİTAK–CUP Read and Publish Agreement. https://library.bogazici.edu.tr/en/news/academic/1/tubitak-cambridge-university-press-cup-read-a/3853
22. [S22] TÜBİTAK ULAKBİM EKUAL — Universities e-databases page (CUP entry). https://cabim.ulakbim.gov.tr/ekual/e-veri-tabanlari/universiteler/
23. [S23] TÜBİTAK ULAKBİM — Açık Erişim Yayın Anlaşması Kapsamı (PDF). https://cabim.ulakbim.gov.tr/wp-content/uploads/sites/4/2026/03/TUBITAK-Acik-Erisim-Yayin-Anlasmasi-Kapsami.pdf
24. [S24] TÜBİTAK ULAKBİM — 2026 CUP Fonlanan AE Dergi Listesi (xlsx; not readable). https://cabim.ulakbim.gov.tr/wp-content/uploads/sites/4/2026/02/2026-CUP-Fonlanan-dergi-listesi-AE.xlsx
25. [S25] Şakar & Emekci (2025), NLP 31, 1–25, PDF. https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/D7B259BCD35586E04358DF06006E0A85/S2977042424000530a.pdf/maximizing-rag-efficiency-a-comparative-analysis-of-rag-methods.pdf
26. [S26] NLP Volume 31, Issue 1 (January 2025) contents. https://www.cambridge.org/core/journals/natural-language-processing/issue/5D21C25A324F9B13FF72F0E218D281C2
27. [S27] Hou et al. (2024) repository records. https://mro.massey.ac.nz/handle/10179/71617 ; https://unnc.globalimpact.cn/en/publications/anisotropic-span-embeddings-and-the-negative-impact-of-higher-ord/
28. [S28] Hou et al. (2024), Cambridge core reader. https://core-prod.cambridgecore.org/core/product/E59F426F59F86445BD3A0B9EA24EBB4A/core-reader
29. [S29] Crossref API queries for ISSN 2977-0424 and 1351-3249. https://api.crossref.org/works?filter=issn:2977-0424&query.bibliographic=sentence+embeddings+semantic+similarity+contradiction ; https://api.crossref.org/works?filter=issn:1351-3249,from-pub-date:2023-01-01&query.bibliographic=natural+language+inference+sentence+embeddings
30. [S30] Yang et al. (2025), NLP 31(6), core reader. https://www.cambridge.org/core/product/09D7B4F2C73301E31D7514A69C19C953/core-reader
31. [S31] Wu et al. (2026), NLP 32(4), core reader. https://www.cambridge.org/core/product/C5DBD2E941C9ABAAB04C6343A0F3D88F/core-reader
32. [S32] Zhu et al. (2026), NLP, core reader (back-matter practice check). https://www.cambridge.org/core/product/C3F61269E92774BACA37B01C840AAD0E/core-reader
33. [S33] CTAN biblatex package page and manual. https://ctan.org/pkg/biblatex ; https://latex.us/macros/latex/contrib/biblatex/doc/biblatex.pdf
