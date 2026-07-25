# APS / PRD submission checklist — paper_lambda

## 1. REVTeX 4.2 format

| Item | Status | Notes |
|------|--------|-------|
| `\documentclass[aps,prd,...]{revtex4-2}` | OK | `twocolumn` for submission; switch to `reprint,onecolumn` if editor requests |
| Roman section numerals (I, II, …) | OK | Automatic with `prd` |
| Subsections A, B, … | OK | Automatic |
| Acknowledgments before Appendices | **Fixed** | Moved before `\appendix` |
| Appendices A, B, … | OK | `\appendix` + `\section{...}` |

## 2. Abstract (APS filter)

| Item | Status |
|------|--------|
| No `\cite{}` | **Fixed** |
| No `\eqref{}` / numbered displays | **Fixed** |
| Acronyms defined or avoided | **Fixed** (no undefined EFT/ΛCDM in abstract) |

## 3. Bibliography

| Item | Status |
|------|--------|
| Numeric [1] style | OK (`revtex4-2` + manual `\bibitem`) |
| Order of appearance | **Fixed** (reordered `\bibitem` list) |
| Peer-reviewed refs preferred | OK (Planck, Cassini, GW170817, etc.) |
| Zenodo companions labeled | **Fixed** (“Data set and preprint companion” + DOI) |

## 4. Testability (PRD desk rejection)

| Item | Status |
|------|--------|
| Sec. I B Observables & falsifiable targets | **Added** |
| Cover letter | `COVER_LETTER_PRD.md` |
| Table I scope disclaimer | OK (`sec:test_scope`) |

## 5. Before upload to APS Editorial Manager

- [ ] Compile clean PDF: `bash compile.sh`
- [ ] Line numbers for review: add `\usepackage{lineno}` + `\linenumbers` if required
- [ ] Submit **source** (.tex + fig PDFs + no auxiliary files)
- [ ] Suggest 3–5 referees (optional)
- [ ] Data availability statement (reproducibility URL / Zenodo DOI)
- [ ] Confirm no retracted references (Crossref / Retraction Watch)

## 6. Optional upgrades

- Migrate to `\bibliography{paper_lambda}` + `apsrev4-2.bst` + `.bib` file
- Register GitHub repo URL in APS “Data Availability” field
- arXiv preprint after journal acceptance policy check
