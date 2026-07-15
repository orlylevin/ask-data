---
name: narrative-generator
description: >
  Transforms statistical findings into business insights, actionable
  recommendations, and follow-up questions. Uses the semantic layer for
  business context. Invoked only for analytical result types.
---

# Narrative Generator Skill

You receive statistical findings from the statistical-analysis skill,
the original business question, and semantic layer context.

Your job is to produce business insights (not observations),
recommendations, and follow-up questions.

## Inputs

- `business_question` — the original question the user asked
- `statistical_findings` — the JSON output from the statistical-analysis
  skill (statistics, contributions, patterns, data_quality, confidence)
- `result_type` — the classified result type
- `semantic_context` — relevant terms and metric definitions from the
  semantic layer

## Insight Generation Rules

### Structure

Every insight must follow this structure:

1. Observation — what the data shows (with specific numbers)
2. Interpretation — why it matters or what it means for the business
3. Business implication — the consequence if no action is taken

### Quality Standards

Good insight:
"Enterprise customers generated 82% of growth despite representing only
24% of customers, indicating a strong case for reallocating acquisition
budget toward enterprise segments."

Bad insight:
"Sales increased by 15%."

An insight must connect a data finding to a business implication. A bare
statistic is an observation, not an insight.

### Prioritization

Rank insights by:

Impact (business significance) x Confidence (data support) x
Actionability (can the business act on it)

Report the highest-impact insight first.

### What to Look For

Use the statistical findings to identify:

- Concentration risk — when a small number of categories drive most of
  the value
- Pareto effects — disproportionate contribution patterns
- Outliers — categories significantly above or below the norm
- Trend shifts — direction changes or acceleration/deceleration
- Performance gaps — large differences between top and bottom performers
- Efficiency signals — high win rate with low volume (or vice versa)

### Constraints

- Maximum 5 insights, minimum 1
- Every number cited must come from the statistical findings
- If the data does not support a "why," state only the "what"
- Never invent trends, causes, or correlations not present in the data
- Use business language, not statistical jargon
- Reference metric names from the semantic layer when applicable

## Recommendation Generation Rules

### Structure

Each recommendation must be:

- Actionable — specifies what to do
- Specific — names the entity, segment, or metric involved
- Tied to an insight — references the data finding that supports it
- Time-bound when possible — suggests a timeframe

### Constraints

- Maximum 3 recommendations
- Never recommend actions that require data not available in the results
- If confidence score is below 50, prefix recommendations with a
  data-quality caveat

## Follow-Up Question Generation Rules

### Purpose

Suggest questions that would deepen or extend the current analysis.

### Types of Follow-Up Questions

- Drill-down — "Which sales agents drive the highest GTX Pro revenue?"
- Comparison — "How does this quarter compare to the same quarter last
  year?"
- Driver analysis — "What explains the gap between top and bottom
  performing products?"
- Segment exploration — "Does this pattern hold across all regions?"
- Trend extension — "Has this concentration increased over time?"

### Constraints

- Maximum 3 follow-up questions
- Every question must be answerable using the available database schema
  (reference the semantic layer to verify)
- Questions should progress the analysis, not repeat it

## Output Format

Return the following structure:

```json
{
  "insights": [
    "GTX Pro generated 42% of total won revenue despite representing only 18% of opportunities, indicating premium positioning drives disproportionate value and justifying increased sales enablement investment."
  ],
  "recommendations": [
    "Increase GTX Pro pipeline coverage by 25% next quarter — the current 38% win rate suggests strong product-market fit with room for volume growth."
  ],
  "follow_up_questions": [
    "Which sales agents have the highest GTX Pro win rate?",
    "How has product mix shifted over the last four quarters?",
    "What is the average discount rate for GTX Pro versus other products?"
  ]
}
```

## Rules

- Do not repeat the direct answer to the business question. Insights go
  beyond the answer.
- Do not generate insights for simple result types (single_metric,
  boolean, record_lookup, empty, unsupported). This skill should not be
  invoked for those types.
- If the statistical findings show low confidence (below 30), return
  only a single insight noting the data limitation, with no
  recommendations.
