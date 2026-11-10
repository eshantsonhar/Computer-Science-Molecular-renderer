# Organic chemistry textbook study ledger

Status: **in progress; neither book is completely studied.**

The CSV companion, [`textbook-page-ledger.csv`](./textbook-page-ledger.csv), has one metadata row for every physical PDF page (2,657 rows total). It records extraction length, embedded raster-image references, chapter assignment, and separate visual/chemistry-review states. A page scan is not a page study: the CSV deliberately marks chemistry understanding incomplete throughout and marks only the 23 pages visually reviewed during this audit as reviewed.

## Source identity and page inventory

| Book | File found | Physical pages | Bookmarks | Numbered chapters | Automated page inventory |
|---|---|---:|---:|---:|---|
| Bruice, *Organic Chemistry*, 7th ed. | `Organic Chemistry -- Paula Yurkanis Bruice -- 7.pdf` | 1,392 | 656 | 28 | Scanned page-by-page for extracted-text length and embedded-image references. Page 1 has no extractable text; 10 pages have fewer than 100 extracted characters. 393 pages contain embedded image references. |
| Clayden, Greeves & Warren, *Organic Chemistry*, 2nd ed. | `organic chemistry clayden 2nd edition -- Jonathan Clayden; Nick Greeves; Stuart G Warren -- 2_ ed .pdf` | 1,265 | 549 | 43 | Scanned page-by-page for extracted-text length and embedded-image references. Pages 1 and 1,265 have no extractable text; 3 pages have fewer than 100 extracted characters. 85 pages contain embedded image references. |

The Clayden filename as specified in the task (`... Jonathan Clayden; Nick Greeves; Stuart S Warren -- 2_ed .pdf`) does not exist exactly. The similarly named supplied PDF is spelled `Stuart G Warren` and has an extra space in `2_ ed`; that file was opened and inventoried. SHA-256 digests and per-page extraction counts are in the CSV. Image-reference counts are not counts of all figures: vector drawings and inline structures may not appear as embedded raster images.

## Chapter inventory

Chapter starts and physical-page ranges are recorded in the CSV. Bruice has chapters 1–28 (starting at PDF page 43; Chapter 28 starts at page 1,307). Clayden has chapters 1–43 (starting at PDF page 28; Chapter 43 starts at page 1,196). The final range in each book extends through that PDF's last page, including any chapter-ending material.

## Direct visual review completed in this audit

Each of these pages was rendered from the actual PDF and visually examined, including its diagrams. The CSV marks these 23 pages as visually reviewed; it does not mark a chapter complete.

| Book | Physical PDF page | Printed page / location | Material inspected |
|---|---:|---|---|
| Bruice | 303 | 262; Chapter 6, section 6.11 begins on page | Epoxide nomenclature and the start of the alkene ozonolysis section; this page alone does not establish the full ozonolysis scheme. |
| Bruice | 304–305 | 263–264; Chapter 6 | Ozonide formation and cleavage, reductive work-up, carbonyl products, and examples where multiple double bonds produce multiple fragments. |
| Bruice | 307 | 266; Chapter 6 | Catalytic hydrogenation, Pd/C, and the surface-mediated addition model. |
| Bruice | 339 | 298; end of Chapter 6 | Ozonolysis exercises and worked product-cleavage examples; this is not the alkyne chapter. |
| Bruice | 340–341 | 299–300; Chapter 7 | Alkyne introduction and functional-group examples; the multistep synthesis context connects the chapter to preceding functional-group chemistry. |
| Bruice | 355 | 314; Chapter 7, section 7.9 | Alkyne catalytic hydrogenation proceeds through an alkene to an alkane with Pd/C; Lindlar poisoning is the distinct partial-reduction method. |
| Bruice | 611 | 570; Chapter 13 | Radical-chain propagation, anti-Markovnikov HBr addition, the stable-radical rationale, and the contrast with HCl/HI. |
| Bruice | 778 | 737; Chapter 16 | Acyl-chloride substitution examples and the curved-arrow alcoholysis mechanism. |
| Bruice | 779 | 738; Chapter 16 | Ammonia equivalents, ammonium chloride formation, and competing amine examples. |
| Bruice | 787–788 | 746–747; Chapter 16 | Hydroxide-promoted ester hydrolysis, tetrahedral-intermediate collapse, carboxylate formation, and distinction from acid-catalyzed reversible hydrolysis. |
| Bruice | 812–813 | 771–772; Chapter 16 | SOCl2 conversion to acyl chloride, leaving-group activation, sulfur dioxide/HCl products, and subsequent nucleophilic acyl substitutions. |
| Clayden | 232 | 205; Chapter 10 | Nucleophile strength/basicity discussion and the acyl-substitution context. |
| Clayden | 233 | 206; Chapter 10 | Relative carboxylic-acid-derivative reactivity and resonance explanation. |
| Clayden | 241–242 | 214–215; Chapter 10 | SOCl2/PCl5 acid activation, the sulfur-containing intermediate, gas-forming collapse, and derivative interconversion limits. |
| Clayden | 454–455 | Chapter 19 opening | Electrophilic alkene addition and bromonium-ion mechanism; reinforces why a generic HX/addition rule is not interchangeable with radical HBr chemistry. |
| Clayden | 476 | Chapter 20 opening | Enol/enolate chapter connections and the displayed cyclic dicarbonyl example. |
| Clayden | 997 | Chapter 37 opening | Radical chapter connections and the radical reaction overview. |

These 23 pages are a deliberately small, traceable visual sample, not exhaustive figure coverage. Earlier development notes mention selected schemes and sparse-text pages but do not preserve a page-by-page visual-review record; they are not counted as complete in this ledger.

## Remaining work and completion rules

- Every page in both books remains pending individual chemistry review unless its row in the CSV is explicitly marked reviewed. Automated extraction does not satisfy this requirement.
- Most reaction diagrams, tables, worked examples, problems, appendices, glossary entries, footnotes, and references have not been individually inspected as rendered pages.
- Sparse-text pages require review to determine whether they are blank, image-based, or extraction failures. The ledger records their page numbers and extraction lengths.
- No chapter is marked complete. A chapter can only be marked complete after its prose, diagrams, tables, mechanisms, examples, exceptions, and relevant end matter have been reviewed and the ledger is updated.
- Add reaction-family knowledge to the implemented-rule evidence only after documenting its scope, mechanism, atom/charge/stereochemical consequences, conditions, contraindications, and source pages. Do not copy textbook passages or treat an educational example as universal experimental validation.

The current implemented-rule evidence and the limitations of this audit are summarized in [`ORGANIC_REACTIONS_CHEMISTRY_STUDY.md`](./ORGANIC_REACTIONS_CHEMISTRY_STUDY.md). The production testing corpus is maintained separately in [`ORGANIC_REACTIONS_PRODUCTION_TEST_CORPUS.csv`](./ORGANIC_REACTIONS_PRODUCTION_TEST_CORPUS.csv).
