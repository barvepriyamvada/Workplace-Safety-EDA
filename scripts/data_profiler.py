"""
data_profiler.py
----------------
OSHA Workplace Injury & Illness Data — Phase 1 Data Profiling
Loads the raw CSV, prints a full profile, and saves summary to outputs/data_profile.txt

Usage:
    python scripts/data_profiler.py
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
RAW_DIR    = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Find raw CSV ───────────────────────────────────────────────────────────────
csv_files = list(RAW_DIR.glob("*.csv"))
if not csv_files:
    print("ERROR: No CSV file found in data/raw/. Please download the OSHA dataset first.")
    sys.exit(1)

RAW_FILE = csv_files[0]
print(f"Loading: {RAW_FILE.name}\n")

# ── Load data ──────────────────────────────────────────────────────────────────
df = pd.read_csv(RAW_FILE, low_memory=False)

# ── Helper: write to both stdout and file ──────────────────────────────────────
output_lines = []

def log(text=""):
    print(text)
    output_lines.append(str(text))

# ── SECTION 1: Shape & Columns ─────────────────────────────────────────────────
log("=" * 70)
log("OSHA WORKPLACE INJURY & ILLNESS DATA — PROFILE REPORT")
log("=" * 70)
log(f"\nSource file : {RAW_FILE.name}")
log(f"Shape       : {df.shape[0]:,} rows × {df.shape[1]} columns")
log(f"\n{'─' * 70}")
log("COLUMN NAMES & DTYPES")
log(f"{'─' * 70}")
for col in df.columns:
    log(f"  {col:<45} {str(df[col].dtype)}")

# ── SECTION 2: Sample rows ─────────────────────────────────────────────────────
log(f"\n{'─' * 70}")
log("FIRST 5 ROWS (transposed for readability)")
log(f"{'─' * 70}")
log(df.head(5).to_string())

# ── SECTION 3: Null counts ─────────────────────────────────────────────────────
log(f"\n{'─' * 70}")
log("NULL VALUE COUNTS & PERCENTAGES")
log(f"{'─' * 70}")
null_counts = df.isnull().sum()
null_pct    = (null_counts / len(df) * 100).round(2)
null_df     = pd.DataFrame({"null_count": null_counts, "null_pct": null_pct})
null_df     = null_df[null_df["null_count"] > 0].sort_values("null_pct", ascending=False)
if null_df.empty:
    log("  No null values found.")
else:
    log(null_df.to_string())

# ── SECTION 4: Duplicates ──────────────────────────────────────────────────────
log(f"\n{'─' * 70}")
log("DUPLICATE ROWS")
log(f"{'─' * 70}")
dup_count = df.duplicated().sum()
log(f"  Duplicate rows: {dup_count:,}  ({dup_count/len(df)*100:.2f}%)")

# ── SECTION 5: Numeric summary ────────────────────────────────────────────────
log(f"\n{'─' * 70}")
log("NUMERIC COLUMN SUMMARY STATISTICS")
log(f"{'─' * 70}")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
if numeric_cols:
    log(df[numeric_cols].describe().round(2).to_string())
else:
    log("  No numeric columns detected.")

# ── SECTION 6: Categorical value counts ───────────────────────────────────────
log(f"\n{'─' * 70}")
log("VALUE COUNTS — KEY CATEGORICAL COLUMNS")
log(f"{'─' * 70}")

# Identify likely categorical columns (object dtype with reasonable cardinality)
cat_cols = [c for c in df.select_dtypes(include="object").columns
            if df[c].nunique() <= 200]

# Priority columns to always show if present
priority_keywords = ["state", "naics", "industry", "estab", "size", "year",
                     "establishment_type", "no_injuries_illnesses"]
priority_cols = [c for c in df.columns
                 if any(kw in c.lower() for kw in priority_keywords)]

cols_to_profile = list(dict.fromkeys(priority_cols + cat_cols))  # deduplicate, preserve order

for col in cols_to_profile[:15]:  # cap at 15 columns
    log(f"\n  [{col}]  — {df[col].nunique()} unique values")
    vc = df[col].value_counts(dropna=False).head(10)
    for val, cnt in vc.items():
        log(f"    {str(val):<35} {cnt:>8,}  ({cnt/len(df)*100:.1f}%)")

# ── SECTION 7: Outlier detection ──────────────────────────────────────────────
log(f"\n{'─' * 70}")
log("OUTLIER DETECTION (IQR method, numeric columns)")
log(f"{'─' * 70}")

for col in numeric_cols:
    series = df[col].dropna()
    if len(series) == 0:
        continue
    Q1  = series.quantile(0.25)
    Q3  = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = series[(series < lower) | (series > upper)]
    if len(outliers) > 0:
        log(f"\n  {col}")
        log(f"    IQR range : [{lower:.2f}, {upper:.2f}]")
        log(f"    Outliers  : {len(outliers):,}  ({len(outliers)/len(series)*100:.2f}%)")
        log(f"    Max value : {series.max():.2f}   Min value: {series.min():.2f}")

# ── SECTION 8: Year coverage ───────────────────────────────────────────────────
year_cols = [c for c in df.columns if "year" in c.lower()]
if year_cols:
    log(f"\n{'─' * 70}")
    log("YEAR COVERAGE")
    log(f"{'─' * 70}")
    for yc in year_cols:
        log(f"\n  [{yc}]")
        log(f"    {df[yc].value_counts(dropna=False).sort_index().to_string()}")

log(f"\n{'=' * 70}")
log("END OF PROFILE REPORT")
log("=" * 70)

# ── Save to file ───────────────────────────────────────────────────────────────
out_path = OUTPUT_DIR / "data_profile.txt"
with open(out_path, "w") as f:
    f.write("\n".join(output_lines))

print(f"\nProfile saved to: {out_path}")
