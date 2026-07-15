---
name: visualization-planner
description: >
  Recommends the most appropriate chart type and specification based on
  the result type and data shape. Returns a chart specification JSON.
  Invoked only for analytical result types.
---

# Visualization Planner Skill

You receive the result type classification, column names, row count, and
data types from the SQL results.

Your job is to recommend the single most appropriate chart type and
return a chart specification.

## Inputs

- `result_type` — the classified result type
- `columns` — list of column names from the CSV
- `row_count` — number of data rows
- `categorical_columns` — columns containing category/label values
- `numeric_columns` — columns containing numeric values

## Chart Type Selection Rules

### comparison

- Default: vertical bar chart
- Use horizontal bar chart when there are more than 5 categories
- Use grouped bar chart when comparing 2+ metrics across categories

### ranking

- Default: horizontal bar chart (sorted by value descending)
- Shows relative magnitudes clearly with natural reading order

### time_trend

- Default: line chart
- Use multiple lines when comparing 2+ metrics or segments over time
- X-axis is always the time dimension

### distribution

- Default: bar chart when categories are discrete
- Use histogram when the variable is continuous with many values

### segmentation

- Default: bar chart
- Use pie chart only when there are 5 or fewer segments and showing
  share of total

### contribution

- Default: Pareto chart (bar + cumulative line)
- Use pie chart when there are 4 or fewer categories

### funnel

- Default: horizontal funnel chart
- Stages ordered from largest to smallest (top-of-funnel first)

## Output Format

Return exactly one primary chart specification. Optionally include one
secondary chart if the data supports a meaningfully different perspective.

```json
{
  "charts": [
    {
      "chart_type": "horizontal_bar",
      "title": "Won Revenue by Product",
      "data": [],
      "x_key": "product",
      "y_keys": ["won_revenue"],
      "reason": "Ranking comparison — horizontal bar shows relative magnitudes with natural reading order"
    }
  ]
}
```

## Field Descriptions

- `chart_type` — one of: bar, horizontal_bar, line, pie, histogram,
  scatter, funnel, pareto, heatmap, grouped_bar
- `title` — clear, descriptive chart title that states the metric and
  dimension
- `data` — leave as empty array (the caller populates from CSV data)
- `x_key` — the column name for the x-axis or category axis
- `y_keys` — array of column names for the value axis (one for single
  metric, multiple for grouped comparisons)
- `reason` — one sentence explaining why this chart type fits the data

## Rules

- Always recommend exactly one primary chart.
- Add a secondary chart only when the data clearly supports a second
  analytical angle (e.g., a trend chart alongside a ranking chart when
  time data is present).
- Never recommend more than 2 charts total.
- The chart title must reference the actual metric and dimension names
  from the data, not generic labels.
- Do not fabricate data values. The `data` field is left empty for the
  caller to populate.
