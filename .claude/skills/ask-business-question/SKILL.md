---
name: ask-business-question
description: Runs the full business-question flow — clarifies the question, then turns it into SQL and runs it.
---

Use this to answer a business question about customers/prospects.

1. Call the Agent tool with subagent_type "clarify-business-question", passing the user's raw question. Wait for it to return the final confirmed question.
2. Call the Agent tool with subagent_type "question-to-sql", passing the confirmed question returned in step 1.
3. Report the result back to the user, including the SQL query used and where the output was saved.

Do not answer the question yourself. Do not use Read/Write/Edit/Bash/Grep/Glob directly for this — only delegate via the Agent tool as above.
