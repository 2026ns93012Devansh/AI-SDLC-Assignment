\# Part-1A Feedback Review



\*\*Date:\*\* 9 November 2026  

\*\*Application:\*\* Smart Todo Manager  

\*\*Review method:\*\* GitHub Copilot code review



\## Finding 1 — Empty tags do not display as specified



\- \*\*File:\*\* `smart\_todo/cli.py`

\- \*\*Function:\*\* `\_render\_tasks`

\- \*\*Severity:\*\* Medium



\### Requirement



The specification requires missing tags to be displayed as `-`.



\### Observed behaviour



The renderer serializes every tag collection as JSON. An empty tag collection therefore displays as `\[]` instead of `-`.



\### Recommended correction



Render an empty tag collection as `-`, while retaining a readable representation for non-empty tags.



\### Regression test



Add a CLI list test for an untagged task and verify that the tags column contains `-` rather than `\[]`.



\### Initial validation



\- Pytest: 23 passed

\- Ruff lint: passed

\- Ruff formatting: passed

\- Bandit: 622 lines scanned, zero issues



\### Review decision



The finding is accepted for correction. Existing tests and specification requirements must remain unchanged.

