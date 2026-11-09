\# Part 1B Constitution

\## Natural Language Reminder Agent



\### 1. Purpose

Build an AI-powered reminder agent that extracts structured

reminder information from natural-language user requests.



\### 2. AI Model

\- Use the locally hosted Qwen 2.5 3B model through Ollama.

\- Record model name and configuration for every evaluation.

\- Never assume AI-generated output is correct.



\### 3. Output Contract

Every successful extraction must return valid JSON containing:

\- title

\- date

\- time

\- priority

\- status

\- needs\_clarification



\### 4. Reliability

\- Validate every model response against a fixed JSON schema.

\- Reject missing or invalid required fields.

\- Handle ambiguous and incomplete requests.

\- Never silently invent missing dates or times.



\### 5. Safety

\- Do not execute actions based on generated reminders.

\- Do not interpret reminder text as system instructions.

\- Treat user input as untrusted data.



\### 6. Testing and Evaluation

\- Maintain at least 15 evaluation cases.

\- Include normal, boundary, ambiguous, missing,

&#x20; malformed, and adversarial inputs.

\- Keep schema validation independent of AI evaluation.

\- Record failures and genuine repair attempts.



\### 7. Human Oversight

\- Preserve evaluation evidence.

\- Require human review before accepting the final result.

\- Never weaken validation rules just to achieve a passing score.
