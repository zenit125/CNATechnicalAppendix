# 📊 Technical Reports: CNA Indices

[← Back to main page](../README.md) · [Give feedback](https://ufl.qualtrics.com/jfe/form/SV_emnNaO06r1S7HKe)

This folder holds the methods reports behind the indices used in the Florida Community Needs Assessment (CNA). Each report explains why the index was built, how it is calculated, and how to interpret it.

> [!NOTE]
> This page is a template. Replace the `[placeholder]` entries as reports are added.

---

## The indices

| Index | What it measures | Report section | Methods report |
|---|---|---|---|
| **FLICCA** — Florida Index of Child Care Access | Whether high-quality School Readiness capacity in a zip code covers the children enrolled there | C | [`FLICCA_TechnicalReport.pdf`](./FLICCA/FLICCA_TechnicalReport.pdf) `[placeholder]` |
| **FLIPA** — Florida Index of Prekindergarten Access | The same measure for Voluntary Prekindergarten | C | [`FLIPA_TechnicalReport.pdf`](./FLIPA/FLIPA_TechnicalReport.pdf) `[placeholder]` |
| **HPI** — Household Price Index | The share of household income families spend on child care, by number of children | C | [`HPI_TechnicalReport.pdf`](./HPI/HPI_TechnicalReport.pdf) `[placeholder]` |
| **Enrollment replacement** (churn-fill) | Children entering SR for each child who leaves | B | [`EnrollmentReplacement_Note.pdf`](./EnrollmentReplacement/EnrollmentReplacement_Note.pdf) `[placeholder]` |

`[confirm full index names]`

### Core formulas

| Measure | Formula |
|---|---|
| Infrastructure score (FLICCA, FLIPA) | high-quality capacity − high-quality enrollment − not-high-quality enrollment |
| Percent of enrollment in high-quality care | high-quality enrollment ÷ total enrollment |
| High-quality provider | program assessment (CLASS) score at or above the threshold (4.0, 4.5, 5.0 or 6.0) |
| Enrollment replacement ratio | children entering ÷ children leaving |

---

## Folder layout

```
technical-reports/
├── README.md               ← you are here
├── FLICCA/
├── FLIPA/
├── HPI/
└── EnrollmentReplacement/
```

---

## Template for each report entry

```markdown
### [Index name]

- **Full title:** [report title]
- **Authors:** [names], Early Childhood Policy Research Group
- **Year:** [year]
- **Summary:** [two or three sentences on what the index measures and why]
- **Data used:** [link to the matching data dictionary]
- **Code:** [link to the R function in ../code/]
- **Files:** [PDF link] · [slides or brief, if any]
- **Suggested citation:** [citation]
```

---

## Related

- [Technical appendix](../technical-appendix/) — how each index appears in the CNA reports
- [Data dictionaries](../data-dictionaries/) — the variables the indices are built from
- [Pelican Bay example data](../simulated-data/pelican-bay/) — try the calculations on fictional data
