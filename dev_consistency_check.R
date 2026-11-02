# Development check used while building the simulated Pelican Bay data (base R).
#
# R version of dev_consistency_check.py. It confirms the files in clean/ agree
# with each other. It was written to validate the simulator, not as a
# production data quality script: it assumes the simulated layout and the ELC
# name "ELC of Pelican Bay", and it reports pass/fail rather than listing rows.
#
# Usage:  Rscript dev_consistency_check.R <folder with the six CSV files>
#    or, inside R:  folder <- "path/to/clean"; source("dev_consistency_check.R")

args <- commandArgs(trailingOnly = TRUE)
if (length(args) >= 1) folder <- args[1]
if (!exists("folder")) stop("Give the data folder as an argument or set `folder` before sourcing.")

ELC        <- "ELC of Pelican Bay"
STATE      <- "Florida (State-Level)"
THRESHOLDS <- c("4", "45", "5", "6")
SUBGROUPS  <- c("BG1", "TANF", "SWD")
SIZES      <- c("1", "2", "3", "4plus")

# Read everything as text so zip codes keep leading zeros; "NA" stays a string.
read_text <- function(f) {
  read.csv(file.path(folder, f), colClasses = "character", na.strings = character(0),
           check.names = FALSE)
}
sr     <- read_text("SR_child_by_provider.csv")
vpk    <- read_text("VPK_child_by_provider.csv")
flicca <- read_text("Zip_FLICCA_SR.csv")
flipa  <- read_text("Zip_FLIPA_VPK.csv")
hpi    <- read_text("HPI.csv")
churn  <- read_text("ChurnFill.csv")

num <- function(x) suppressWarnings(as.numeric(ifelse(x == "NA", NA, x)))

results <- data.frame(check = character(0), passed = logical(0), stringsAsFactors = FALSE)
check <- function(name, passed) {
  passed <- isTRUE(all(passed))
  results[nrow(results) + 1, ] <<- list(name, passed)
}

# Number of distinct values of `col` within each group (used for "constant within group" checks)
n_distinct_by <- function(values, group) tapply(values, group, function(v) length(unique(v)))

# --- 1. Zip files vs child files, arithmetic, subgroup <= total ----------------
zip_sets <- list(
  list(label = "FLICCA", z = flicca, kids = sr,  age = "Child aged 0-5"),
  list(label = "FLIPA",  z = flipa,  kids = vpk, age = "Child aged 3-5")
)
for (set in zip_sets) {
  z <- set$z; kids <- set$kids
  in_scope <- kids[kids[[set$age]] == "1" & kids[["Child Provider ELC"]] == ELC, ]
  kid_key  <- paste(in_scope[["Child Provider Zipcode"]], in_scope[["Child Provider County"]], sep = "|")
  enr      <- table(kid_key)
  zip_key  <- paste(z[["Provider Zipcode"]], z[["Provider County"]], sep = "|")
  expected <- ifelse(zip_key %in% names(enr), as.integer(enr[zip_key]), 0L)

  for (s in THRESHOLDS) {
    total <- num(z[[paste0("hq_enrollment_", s)]]) + num(z[[paste0("lq_enrollment_", s)]])
    check(sprintf("%s %s: zip enrollment = child-provider records", set$label, s),
          total == expected)

    for (g in c("", paste0(SUBGROUPS, "_"))) {
      col   <- function(v) num(z[[paste0(g, v, "_", s)]])
      infra <- col("hq_capacity") - col("hq_enrollment") - col("lq_enrollment")
      check(sprintf("%s %s: %sInfrastructure arithmetic", set$label, s, ifelse(g == "", "all ", g)),
            infra == col("Infrastructure"))
      if (g != "") {
        check(sprintf("%s %s: %senrollment <= total", set$label, s, g),
              col("hq_enrollment") <= num(z[[paste0("hq_enrollment_", s)]]) &
              col("lq_enrollment") <= num(z[[paste0("lq_enrollment_", s)]]))
      }
    }
  }
  check(sprintf("%s: hq_capacity_6 <= hq_capacity_4", set$label),
        num(z$hq_capacity_6) <= num(z$hq_capacity_4))
}

# --- 2. Child-level internal consistency ---------------------------------------
for (set in list(list(label = "SR", df = sr), list(label = "VPK", df = vpk))) {
  df  <- set$df
  pid <- df[["Provider ID"]]
  cid <- df[["Unique Child ID"]]

  loc_cols <- c("Child Provider Zipcode", "Child Provider County", "Child Provider ELC")
  check(sprintf("%s: each Provider ID has one location", set$label),
        sapply(loc_cols, function(cl) all(n_distinct_by(df[[cl]], pid) <= 1)))

  check(sprintf("%s: no duplicate child x provider rows", set$label),
        !any(duplicated(df[, c("Unique Child ID", "Provider ID")])))

  check(sprintf("%s: 'not in home county/ELC' flags match locations", set$label),
        c((df[["Child Provider not in Child Home County"]] == "1") ==
            (df[["Child Provider County"]] != df[["Child Home County"]]),
          (df[["Child Provider not in Child Home ELC"]] == "1") ==
            (df[["Child Provider ELC"]] != df[["Child Home ELC"]])))

  rows_per_child <- ave(rep(1, nrow(df)), cid, FUN = length)
  check(sprintf("%s: multiple-provider flag matches row count", set$label),
        (rows_per_child > 1) == (df[["Child with Multiple Provider Records"]] == "1"))

  attr_cols <- c("Child Home Zipcode", "BG1/at-risk", "TANF Recip", "SWD", "Paying ELC")
  check(sprintf("%s: child attributes constant across rows", set$label),
        sapply(attr_cols, function(cl) all(n_distinct_by(df[[cl]], cid) <= 1)))

  check(sprintf("%s: zip codes are 5 characters", set$label),
        nchar(c(df[["Child Home Zipcode"]], df[["Child Provider Zipcode"]])) == 5)
}

hours_per_child <- tapply(num(vpk[["VPK Hours"]]), vpk[["Unique Child ID"]], sum)
check("VPK: hours per child <= 540", max(hours_per_child) <= 540)

both <- rbind(sr[, c("Unique Child ID", "Child Home Zipcode")],
              vpk[, c("Unique Child ID", "Child Home Zipcode")])
check("SR and VPK: same child has same home zip",
      n_distinct_by(both[["Child Home Zipcode"]], both[["Unique Child ID"]]) <= 1)

# --- 3. HPI roll-ups -------------------------------------------------------------
H <- hpi
value_cols <- names(H)[-(1:3)]
for (cl in value_cols) H[[cl]] <- num(H[[cl]])
n_cols   <- grep("(^N_|_N_)", names(H), value = TRUE)
hpi_cols <- grep("HPI", names(H), value = TRUE)

state    <- H[H[["Home ELC"]] == STATE, ]
elcs     <- H[H[["Home Zipcode"]] == "NA" & H[["Home County"]] == "NA" & H[["Home ELC"]] != STATE, ]
counties <- H[H[["Home County"]] != "NA" & H[["Home Zipcode"]] == "NA", ]
zips     <- H[H[["Home Zipcode"]] != "NA", ]

check("HPI: state N = sum of ELC N",    unlist(state[n_cols]) == colSums(elcs[n_cols]))
check("HPI: state N = sum of county N", unlist(state[n_cols]) == colSums(counties[n_cols]))
check("HPI: Pelican Bay ELC N = sum of its zip N",
      unlist(elcs[elcs[["Home ELC"]] == ELC, n_cols]) == colSums(zips[n_cols]))
check("HPI: Pelican Bay county N = sum of its zip N",
      sapply(c("Heron", "Osprey", "Egret"), function(cn)
        all(unlist(counties[counties[["Home County"]] == cn, n_cols]) ==
            colSums(zips[zips[["Home County"]] == cn, n_cols]))))
check("HPI: state HPI_1 = N-weighted mean of ELC HPI_1",
      abs(state$HPI_1 - sum(elcs$HPI_1 * elcs$N_1) / sum(elcs$N_1)) <= 1e-4)
check("HPI: subgroup N <= total N",
      sapply(SUBGROUPS, function(g) sapply(SIZES, function(k)
        all(H[[paste0(g, "_N_", k)]] <= H[[paste0("N_", k)]]))))
hv <- unlist(H[hpi_cols])
check("HPI: values between 0 and 1", min(hv, na.rm = TRUE) >= 0 && max(hv, na.rm = TRUE) <= 1)

# --- 4. Churn-fill -------------------------------------------------------------------
C <- churn
for (cl in names(C)[-1]) C[[cl]] <- num(C[[cl]])
own <- length(unique(sr[sr[["Paying ELC"]] == ELC & sr[["Child aged 0-5"]] == "1", "Unique Child ID"]))
check("Churn: ELC num_of_children = unique 0-5 SR children paid by ELC",
      C$num_of_children[C$CoalitionName == ELC] == own)

is_fl  <- startsWith(C$CoalitionName, "Florida")
fl     <- C[is_fl, ]
others <- C[!is_fl, ]
check("Churn: Florida row = sum of ELC rows",
      sapply(c("children_in", "children_out", "num_of_children", "total_spend"),
             function(cl) abs(fl[[cl]] - sum(others[[cl]])) < 0.02))
check("Churn: churn_fill = children_in / children_out",
      abs(C$churn_fill - C$children_in / C$children_out) <= 1e-4)

# --- report --------------------------------------------------------------------------
cat(sprintf("%s  %s\n", ifelse(results$passed, "PASS", "FAIL"), results$check), sep = "")
cat(sprintf("\n%d of %d checks passed\n", sum(results$passed), nrow(results)))
