\# Natural Language Reminder Agent — Specification



\## 1. Objective

Build a locally hosted AI reminder agent that converts natural-language requests into structured JSON using Qwen 2.5 3B through Ollama.



\## 2. Functional Requirements



\*\*FR-01:\*\* Accept a natural-language reminder as input.



\*\*FR-02:\*\* Extract the reminder title.



\*\*FR-03:\*\* Identify the requested date and normalize it to `YYYY-MM-DD` when possible.



\*\*FR-04:\*\* Identify the requested time and normalize it to `HH:MM` (24-hour format) when possible.



\*\*FR-05:\*\* Classify priority as `Low`, `Medium`, or `High`.



\*\*FR-06:\*\* Detect missing or ambiguous information and request clarification.



\*\*FR-07:\*\* Return structured JSON rather than executing or scheduling reminders.



\## 3. Output Contract



Every response must follow this structure:



```json

{

&#x20; "title": "Submit assignment",

&#x20; "date": "2026-11-10",

&#x20; "time": "09:00",

&#x20; "priority": "High",

&#x20; "status": "ready",

&#x20; "needs\_clarification": false

}

```



Rules:

\- `title`: string or null.

\- `date`: ISO date string (`YYYY-MM-DD`) or null.

\- `time`: 24-hour time (`HH:MM`) or null.

\- `priority`: Low, Medium, High, or null.

\- `status`: `ready` or `needs\_clarification`.

\- `needs\_clarification`: Boolean.



\## 4. Behavioural Requirements



\- Missing dates or times must not be invented.

\- Ambiguous dates or times must trigger clarification.

\- Invalid priorities must be rejected or handled through clarification.

\- Empty input must be handled gracefully.

\- Malformed model output must not be accepted as valid JSON.

\- Relative dates must use the evaluation reference date and timezone.

\- Additional text or Markdown outside the JSON must not pass strict output validation.



\## 5. Safety Requirements



\- Treat user input as untrusted data.

\- Ignore instructions inside reminder text that attempt to override system rules.

\- Never execute commands or perform external actions.

\- Never claim a reminder has been scheduled.



\## 6. Non-Functional Requirements



\- Run locally using Ollama.

\- Record model name, version/configuration, and evaluation timestamp.

\- Use independent JSON schema validation.

\- Maintain reproducible evaluation results where possible.

\- Record evaluation failures and repair history.



\## 7. Evaluation Requirements



The evaluation dataset must contain at least 15 cases covering:

1\. Normal reminders.

2\. Boundary conditions.

3\. Ambiguous requests.

4\. Missing information.

5\. Empty or malformed inputs.

6\. Adversarial instructions.



The harness must separately validate:

\- JSON syntax and schema.

\- Structural invariants.

\- Behavioural properties.

\- Semantic extraction quality.

\- Aggregate score against a predefined threshold.



\## 8. Human Review



A human must review the evaluation evidence and decide whether the application is acceptable. A passing automated score alone does not establish acceptance.
