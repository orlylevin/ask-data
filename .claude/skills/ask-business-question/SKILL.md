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

5. Pass the SQL agent's full result to the results agent:
   Call the Agent tool with `subagent_type` set to `results-agent`,
   passing:
   - the original business question from the user
   - the clarified business question from step 2
   - the SQL query from the SQL agent's result
   - validation status
   - material warnings
   - the SQL results summary from the SQL agent's result
   - the path to the saved CSV output file from step 4

6. Wait for the results agent to return a structured JSON response
   containing: answer, result_type, confidence, and conditionally:
   kpis, charts, insights, recommendations, follow_up_questions.

7. Return to the user:
   - the results agent's structured JSON response
   - the SQL query used
   - the saved output paths from step 4
   - for analytical results: the report path and chart image paths

Do not answer the analytical question directly.

Do not generate or execute SQL directly.

Do not use Read, Write, Edit, Bash, Grep, or Glob directly for the
business-question workflow. Delegate the workflow only through the
specified agents.

If any agent reports that the question cannot be resolved or executed
safely, return that issue to the user rather than guessing.

