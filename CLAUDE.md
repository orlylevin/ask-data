# Project Context

This project answers analytical business questions using the CRM Sales
Opportunities dataset stored in DuckDB.

The currently supported domain is sales analysis, including:

- opportunities
- accounts and customers
- products
- sales agents and managers
- regional offices
- won revenue
- win rate
- pipeline
- deal size
- sales-cycle performance

# Workflow Rules

- Act as a router and delegate business questions to the
  `ask-business-question` skill.
- Do not answer dataset-based analytical questions directly.
- Do not generate SQL outside the approved agent workflow.
- Reject questions that require data outside the supported scope.
- Do not approximate unavailable metrics using unrelated fields.
- Keep business summaries concise and evidence-based.
- Use DuckDB as the active analytical source.
- Do not inspect the original CSV files during normal question execution.
- Show the generated SQL before execution.

# Project Structure

- `.claude/agents/` - specialized workflow agents
- `.claude/skills/` - end-to-end workflow orchestration
- `resources/` - scope, metrics, terminology, and semantic definitions
- `output/results/` - query results
- `output/validation/` - validation records
- `output/answers/` - interpreted business answers
- `scripts/` - database loading, querying, and validation scripts
- `Database/` - original source CSV files
- `ask_data.duckdb` - active analytical database

# Sources of Truth

- Scope: `resources/data_scope.yaml`
- Metrics: `resources/metrics.yaml`
- Semantic model: `resources/semantic_layer.md`
- Terminology: `resources/business_glossary.yaml`
- Database configuration: `config/database.yaml`

# Agent Flow (3-agent pipeline)

The `/ask-business-question` skill orchestrates three agents in sequence:

1. **clarify-business-question** — resolves ambiguity using semantic layer,
   metrics, and glossary. Returns one precise question.
2. **question-to-sql** — converts the clarified question to DuckDB SQL,
   executes it, validates the result, saves SQL and CSV to `output/`.
3. **results-agent** — transforms SQL results into a structured JSON
   response. Classifies results into one of 12 types (5 simple, 7
   analytical). Simple types get a direct answer only. Analytical types
   invoke 4 skills for full treatment.

## Results-agent skills (analytical types only)

- `statistical-analysis` — Python/pandas: descriptive stats, Pareto
  detection, outliers, confidence scoring with aggregated-data awareness
- `visualization-planner` — selects chart type based on result type and
  data shape
- `narrative-generator` — produces insights, recommendations, follow-up
  questions
- `vis-creator` — renders matplotlib PNG charts with business styling

## JSON output schema

Every response includes: `answer`, `result_type`, `confidence`,
`sql_query`, `kpis[]`, `charts[]`, `insights[]`, `recommendations[]`,
`follow_up_questions[]`. Simple types return empty arrays for
kpis/charts/insights/recommendations/follow_up_questions.

## Number formatting

- `single_metric` direct answer: 5 significant figures
- KPIs, chart labels, insights: 3 significant figures
- Currency >= 1M abbreviated (e.g., $3.51M)

## Known limitation

Custom agent types (`clarify-business-question`, `question-to-sql`,
`results-agent`) are not available as `subagent_type` values when
calling the Agent tool programmatically. They work when Claude Code
runs the `/ask-business-question` skill directly. For manual testing,
pass each agent's full instructions in the Agent prompt instead.

# Session summary (2026-07-15/16)

## What was built

Added the results-agent and 4 supporting skills to the existing
2-agent flow (clarify → SQL), creating a 3-agent pipeline
(clarify → SQL → results).

## Files added/modified

- `.claude/agents/results-agent.md` — new agent
- `.claude/skills/statistical-analysis/SKILL.md` — new skill
- `.claude/skills/visualization-planner/SKILL.md` — new skill
- `.claude/skills/narrative-generator/SKILL.md` — new skill
- `.claude/skills/vis-creator/SKILL.md` — new skill
- `.claude/skills/ask-business-question/SKILL.md` — updated from 5
  steps to 7 steps to integrate the results-agent; fixed "either agent"
  → "any agent"

## Files NOT modified

All existing agents (`clarify-business-question.md`,
`question-to-sql.md`), resources, scripts, and database files were
left untouched.

## Tests run

- Simple question ("What is the total won revenue?") — single_metric
  type, no skills invoked, direct answer with 5 sig figs
- Analytical question ("Won revenue and win rate by product?") —
  comparison type, all 4 skills invoked, 2 charts rendered, full
  markdown report generated
- Fresh clone test — cloned repo from GitHub and ran the simple
  question end-to-end to verify committed files work independently

## Commits pushed to orlylevin/ask-data main

1. `73ab07a` — Add results-agent and supporting skills (6 files)
2. `d9731c0` — Add sql_query field to results-agent JSON output
