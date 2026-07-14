---
name: ask-business-question
description: >
  Answers analytical business questions using the approved semantic layer,
  metric definitions, business glossary, and DuckDB database. Use it for
  questions about sales opportunities, customers, products, sales teams,
  revenue, pipeline, win rate, deal size, and sales performance.
---

Use this skill to run the complete Ask Data workflow.

1. Call the Agent tool with `subagent_type` set to
   `clarify-business-question`, passing the user's raw business question.

2. Wait for the clarification agent to return one precise, resolved
   business question.

3. Call the Agent tool with `subagent_type` set to `question-to-sql`,
   passing the resolved question exactly as returned.

4. Wait for the SQL agent to:
   - resolve metrics from `resources/metrics.yaml`
   - use tables and joins from `resources/semantic_layer.md`
   - execute read-only SQL against DuckDB
   - validate the result
   - save the SQL and output files

5. Return the SQL agent's result to the user, including:
   - the business answer
   - the SQL query
   - validation status
   - material warnings
   - saved output paths

Do not answer the analytical question directly.

Do not generate or execute SQL directly.

Do not use Read, Write, Edit, Bash, Grep, or Glob directly for the
business-question workflow. Delegate the workflow only through the
specified agents.

If either agent reports that the question cannot be resolved or executed
safely, return that issue to the user rather than guessing.