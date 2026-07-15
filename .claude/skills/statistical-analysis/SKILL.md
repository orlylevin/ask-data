---
name: statistical-analysis
description: >
  Runs Python-based statistical analysis on CSV query results.
  Computes descriptive statistics, detects patterns (Pareto, concentration,
  outliers, trend breaks), and validates data quality. Returns structured
  JSON findings. Invoked only for analytical result types.
---

# Statistical Analysis Skill

You receive a path to a CSV file containing SQL query results and the
result type classification.

Your job is to run a self-contained Python script that analyzes the data
and outputs structured JSON findings to stdout.

Do not perform calculations yourself. All numbers must come from the
Python script output.

## Inputs

- `csv_path` — absolute path to the CSV output file
- `result_type` — the classified result type (comparison, ranking,
  time_trend, distribution, segmentation, contribution, funnel)

## Execution

Run a single Python script via Bash that performs all analysis steps
below. The script must:

- Read the CSV using pandas
- Print only valid JSON to stdout
- Print nothing else to stdout (use stderr for debug messages)
- Handle edge cases: empty files, single-row results, non-numeric columns

## Analysis Steps

### 1. Data Profiling

For every column:

- row count
- null count and null percentage
- unique value count (cardinality)
- data type (numeric, categorical, date)

For numeric columns additionally:

- min, max
- mean, median
- standard deviation

### 2. Descriptive Statistics

For each numeric column:

- mean
- median
- standard deviation
- 25th and 75th percentiles
- coefficient of variation (std / mean)

### 3. Contribution Analysis

When the result contains a categorical column and a numeric value column:

- compute each category's percentage share of total
- compute cumulative percentage (sorted descending by value)
- identify the minimum number of categories that account for 80% of total

### 4. Concentration and Pareto Detection

- compute top-1, top-3, and top-5 share of total
- flag concentration risk when top-3 share exceeds 60%
- flag Pareto effect when fewer than 30% of categories account for more
  than 70% of total value

### 5. Outlier Detection

For numeric columns with more than 5 values:

- compute z-scores
- flag values with absolute z-score greater than 2.0
- report the outlier values, their z-scores, and the associated category

### 6. Trend Analysis (time_trend only)

When the result type is time_trend:

- compute period-over-period growth rates
- compute overall growth (first period to last period)
- detect trend direction changes (breaks)
- compute average growth rate

### 7. Data Quality Assessment

- total rows in the result
- total null values across all columns
- whether the data is aggregated (detect by checking for columns whose
  names suggest counts or sums — e.g., columns containing "count",
  "total", "sum", "opportunities", "deals", or integer columns with
  values much larger than the row count)
- if aggregated: compute `underlying_sample_size` as the sum of the
  largest count-like or opportunity-count column; otherwise set it equal
  to the row count
- whether sample size is sufficient: use `underlying_sample_size`, not
  row count — flag only when `underlying_sample_size` is fewer than 30
- whether any single category dominates more than 90% of values

### 8. Confidence Score

Compute a confidence score from 0 to 100. Start at 100 and apply
deductions. Track each deduction as a named factor with its point
impact so the explanation can list them.

Deduction rules:

- **Underlying sample size** (use `underlying_sample_size`, not row
  count):
  - fewer than 30: deduct 25 points
  - 30 to 99: deduct 10 points
  - 100 to 499: deduct 5 points
  - 500 or more: no deduction
- **Null percentage** across all columns:
  - more than 20%: deduct 20 points
  - 5% to 20%: deduct 10 points
  - less than 5%: no deduction
- **Cardinality**:
  - single unique value in the primary metric column: deduct 15 points
  - two unique values: deduct 5 points
- **Outlier severity**:
  - any value with absolute z-score above 3.0: deduct 10 points
  - any value with absolute z-score between 2.0 and 3.0: deduct 5
    points
- **Group count** (number of rows / categories):
  - fewer than 3 groups: deduct 10 points (too few to compare)
  - 3 or more: no deduction

Minimum score is 0. Do not deduct below 0.

The explanation must list each factor that caused a deduction and its
impact. Example:

"Score: 80. Deductions: group count below 3 (-10), one outlier with
z-score 2.4 (-5), null rate 8% (-10). Base: 6,711 underlying
opportunities across 7 product groups."

If no deductions apply, the explanation should confirm why the score is
high. Example:

"Score: 95. No significant issues. 6,711 underlying opportunities,
0% null rate, 7 product groups with no extreme outliers."

## Output Format

The Python script must output exactly one JSON object:

```json
{
  "statistics": {
    "row_count": 7,
    "columns": {
      "column_name": {
        "type": "numeric",
        "count": 7,
        "nulls": 0,
        "unique": 7,
        "mean": 150000,
        "median": 140000,
        "std": 35000,
        "min": 95000,
        "max": 220000,
        "p25": 120000,
        "p75": 175000
      }
    }
  },
  "contributions": [
    {
      "category": "GTX Pro",
      "value": 500000,
      "share_pct": 42.1,
      "cumulative_pct": 42.1
    }
  ],
  "patterns": {
    "pareto_detected": true,
    "pareto_detail": "Top 2 of 7 products (29%) account for 71% of revenue",
    "concentration_risk": false,
    "concentration_detail": "Top 3 share is 58%, below 60% threshold",
    "outliers": [
      {
        "category": "MG Special",
        "column": "won_revenue",
        "value": 12000,
        "z_score": -2.4,
        "direction": "below"
      }
    ],
    "trend_breaks": []
  },
  "data_quality": {
    "total_rows": 7,
    "is_aggregated": true,
    "underlying_sample_size": 6711,
    "total_nulls": 0,
    "null_pct": 0.0,
    "sample_sufficient": true,
    "single_dominant_category": false
  },
  "confidence": {
    "score": 95,
    "deductions": [
      {"factor": "one outlier with z-score 2.4", "points": -5}
    ],
    "explanation": "Score: 95. Deductions: one outlier with z-score 2.4 (-5). Base: 6,711 underlying opportunities across 7 product groups, 0% null rate."
  }
}
```

## Rules

- Do not add interpretation or narrative. Return only the raw statistical
  findings.
- If pandas is not available, fall back to the csv and statistics modules
  from Python standard library.
- If the CSV file is empty or unreadable, return a JSON with
  `confidence.score` of 0 and an explanation.
- Round all floating point values to 2 decimal places.
