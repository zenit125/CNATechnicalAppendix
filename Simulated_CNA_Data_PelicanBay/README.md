# Simulated CNA data: "ELC of Pelican Bay" (fictional, multi-county)

All names, zip codes and values are invented. The files follow the layouts in
Example_Data_Structure.xlsx (2025-26) and agree with each other, so they can be
used to build and test data quality scripts.

- `clean/` — internally consistent datasets (every cross-file relationship below holds).
- `with_errors/` — the same files with 12 planted errors, listed in `with_errors/planted_errors.csv`
  (file, location, error, and the check that should catch it).
- `simulate.py` — regenerates everything (fixed random seed): `python3 simulate.py <output_folder>`.

## The fictional geography

| ELC | Counties | Zip codes |
|---|---|---|
| ELC of Pelican Bay (the simulated ELC) | Heron, Osprey, Egret | Heron 90101–90107; Osprey 90121–90125; Egret 09141–09143; **90118 is split between Heron and Osprey** |
| ELC of Gator Ridge (neighbor) | Cypress | 90201–90203 |
| ELC of Sandhill (neighbor) | Palmetto | 90301–90302 |
| 27 more ELCs ("ELC of Region 04"–"Region 30") | "County 06"–"County 67" | Appear only in the HPI and churn-fill state/ELC/county rows |

That makes 30 ELCs and 67 counties statewide, as in Florida.

## Files

| File | One row per | Rows | Notes |
|---|---|---|---|
| SR_child_by_provider.csv | Child × provider | 2,051 (1,918 children) | Children paid by Pelican Bay (wherever they attend) plus 45 children paid by neighbor ELCs who attend Pelican Bay providers |
| VPK_child_by_provider.csv | Child × provider | 1,875 (1,813 children) | Same rule as SR; school-year VPK only; `VPK Hours` = hours at that provider |
| Zip_FLICCA_SR.csv | Provider zip × provider county | 17 | Pelican Bay provider zips; 90118 has two rows (Heron, Osprey) |
| Zip_FLIPA_VPK.csv | Provider zip × provider county | 16 | Same layout for VPK |
| HPI.csv | State, ELC, county, or home zip | 115 | 1 state row, 30 ELC rows, 67 county rows, 17 Pelican Bay home-zip rows |
| ChurnFill.csv | Coalition | 31 | "Florida (State-level)" + 30 ELCs |

Zip codes are 5-character text (Egret zips start with 0). Missing values are written as `NA`.

## Small departures from the spreadsheet layout (to make the files machine-readable)

- **SR and VPK zip files are separate** (`Zip_FLICCA_SR.csv`, `Zip_FLIPA_VPK.csv`); the spreadsheet showed one block for both.
- **Zip-file thresholds use suffixes `_4`, `_45`, `_5`, `_6`** (CLASS 4.0, 4.5, 5.0, 6.0), each with `hq_capacity`, `hq_enrollment`, `lq_capacity`, `lq_enrollment`, `Infrastructure`; subgroup columns are prefixed `BG1_`, `TANF_`, `SWD_`.
- **HPI columns are flattened** to `HPI_1, HPI_2, HPI_3, HPI_4plus` and `N_1 … N_4plus`, then the same eight columns with `BG1_`, `TANF_`, `SWD_` prefixes. HPI values are proportions (0.0696 = 6.96%). N = number of households. Small cells are **not** suppressed (the report code does that).
- **Location placeholders** follow the spreadsheet: state and ELC rows have `NA` for zip and county; county rows have `NA` for zip and ELC.
- The Florida label differs between files exactly as in the spreadsheet: "Florida (State-Level)" in HPI, "Florida (State-level)" in churn-fill.

## How the files are built (relationships the checks can test in `clean/`)

**Child-level files**
- Each `Provider ID` has one zip, county and ELC.
- Each child's home zip/county/ELC, paying ELC and subgroup flags are the same on all of that child's rows, and in both the SR and VPK files.
- `Child Provider not in Child Home County/ELC` = 1 exactly when the counties/ELCs differ.
- `Child with Multiple Provider Records` = 1 exactly when the child has more than one row.
- TANF is a family-level flag (all children in a family share it); BG1 and SWD are child-level.
- VPK hours summed across a child's providers are between 60 and 540; about 88% of children reach 378.

**Zip files vs. child files**
- `hq_enrollment + lq_enrollment` for a zip/county row = number of child × provider records at Pelican Bay providers in that zip/county, counting **SR children aged 0–5** (FLICCA) or **all VPK children** (FLIPA), regardless of paying ELC. A child with two providers counts once at each.
- Enrollment totals are the same at every threshold; only the high-quality/not-high-quality split changes.
- A provider is high quality at a threshold when its CLASS score ≥ that threshold; providers with no CLASS score are never high quality. So `hq_capacity_6 ≤ hq_capacity_5 ≤ hq_capacity_45 ≤ hq_capacity_4`.
- `Infrastructure = hq_capacity − hq_enrollment − lq_enrollment`, for all children and for each subgroup.
- Subgroup capacity columns repeat the all-children capacity; subgroup enrollment ≤ all-children enrollment.
- Capacities come from a provider list that is not one of the requested files, so capacity can't be checked against the child files.

**HPI**
- State N = sum of the 30 ELC rows = sum of the 67 county rows, for every column.
- Pelican Bay's ELC row N = sum of its 17 home-zip rows; each Pelican Bay county row = sum of its zip rows.
- State and ELC HPI values are N-weighted means of the rows beneath them (to 4 decimals).
- Subgroup N ≤ all-households N in every cell; subgroup values are computed from their own households (not copied).
- Pelican Bay households are the families of the SR children in `SR_child_by_provider.csv`. Rows are by **home** location. The child file has no family ID, so household counts can't be rebuilt exactly from it.
- All HPI values are between 0.008 and 0.20.

**Churn-fill**
- Pelican Bay `num_of_children` (1,037) = unique SR children aged 0–5 with `Paying ELC` = Pelican Bay in the SR file (the check in the spreadsheet).
- `churn_fill = children_in ÷ children_out`; `avg_spend = total_spend ÷ num_of_children`.
- The Florida row = sum of the 30 ELC rows (ratios recomputed from the sums).

## Edge cases included on purpose (all valid)

- Zip 90118 has providers in two counties, so it has two zip-file rows.
- Zip 09143 (Egret) has no high-quality SR providers at any threshold: `hq_capacity = 0` and negative Infrastructure.
- Egret zips have leading zeros.
- Some children attend providers outside Pelican Bay (Cypress, Palmetto), and some neighbor-paid children attend Pelican Bay providers.
- About 20 provider IDs serve both SR and VPK.
- Several subgroup cells are 0 or very small, and some HPI subgroup cells have N = 0 (value `NA`).
