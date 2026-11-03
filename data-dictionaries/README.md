# 📚 Data Dictionaries

[← Back to main page](../README.md) · [Give feedback](https://ufl.qualtrics.com/jfe/form/SV_emnNaO06r1S7HKe)

This folder collects the variable definitions for every data source used in the Florida Community Needs Assessment (CNA). Use it to check what a field means, how it is coded, and which report elements use it.

> [!NOTE]
> This page is a template. Replace the `[placeholder]` entries as documents are added.

---

## Contents

| Source | Dictionary | Used in report sections | Last updated |
|---|---|---|---|
| Florida Division of Early Learning (DEL) — School Readiness | [`DEL_SR_DataDictionary.pdf`](./DEL/DEL_SR_DataDictionary.pdf) `[placeholder]` | B, C, E | `[date]` |
| DEL — Voluntary Prekindergarten (VPK) | [`DEL_VPK_DataDictionary.pdf`](./DEL/DEL_VPK_DataDictionary.pdf) `[placeholder]` | B, C, E | `[date]` |
| DEL — Provider and program assessment (CLASS) data | [`DEL_Provider_DataDictionary.pdf`](./DEL/DEL_Provider_DataDictionary.pdf) `[placeholder]` | C | `[date]` |
| DEL — VPK provider performance metrics | [`DEL_VPK_PerformanceMetrics.pdf`](./DEL/DEL_VPK_PerformanceMetrics.pdf) `[placeholder]` | C | `[date]` |
| U.S. Census Bureau — American Community Survey | [Link to ACS table documentation](https://www.census.gov/programs-surveys/acs/technical-documentation.html) `[confirm tables]` | A | `[date]` |
| U.S. Bureau of Labor Statistics — Local Area Unemployment Statistics | [Link to LAUS documentation](https://www.bls.gov/lau/) `[confirm]` | A | `[date]` |
| CNA input files (as received by ECPRG) | [`CNA_Input_Files_DataDictionary.xlsx`](./CNA/CNA_Input_Files_DataDictionary.xlsx) `[placeholder]` | All | `[date]` |

---

## Folder layout

```
data-dictionaries/
├── README.md         ← you are here
├── DEL/              Dictionaries provided by the Division of Early Learning
├── Census/           ACS table notes and variable lists
├── BLS/              LAUS notes
└── CNA/              Dictionary for the CNA input files and Pelican Bay example data
```

---

## Template for each dictionary entry

Copy this block when adding a new source.

```markdown
### [Dataset name]

- **Owner / agency:** [e.g., Florida Division of Early Learning]
- **Description:** [one or two sentences on what the dataset covers]
- **Unit of observation:** [e.g., one row per child × provider]
- **Reporting period:** [e.g., FY 2024–25]
- **How ECPRG receives it:** [e.g., secure transfer from DEL, public download]
- **Report elements that use it:** [e.g., Table 2, Table 7, FLICCA tables]
- **Dictionary file:** [link]
- **Known issues or notes:** [e.g., provider county reflects provider location, not child home]

| Variable | Type | Description | Values / codes | Used in |
|---|---|---|---|---|
| [name] | [text / number / date] | [definition] | [codes] | [report element] |
```

---

## Questions

If a definition is unclear or a field seems inconsistent with your coalition's records, please tell us through the [CNA feedback survey](https://ufl.qualtrics.com/jfe/form/SV_emnNaO06r1S7HKe).
