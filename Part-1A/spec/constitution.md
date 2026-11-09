# Smart Todo Manager — Project Constitution

## 1. Purpose
Build a deterministic, reliable Python command-line application for managing personal tasks with persistent JSON storage.

## 2. Core Principles

### Principle 1 — Deterministic Behaviour
- Identical inputs and stored state must produce identical application results.
- No random task IDs or unpredictable ordering.

### Principle 2 — Input Validation
- Task titles must not be empty.
- Priority must be Low, Medium, or High.
- Status must be Pending or Completed.
- Invalid inputs must produce clear errors without corrupting stored data.

### Principle 3 — Data Integrity
- Tasks must persist in JSON format.
- Existing data must not be silently overwritten when storage is invalid.
- Task IDs must remain unique and must not be reused after deletion.

### Principle 4 — Modularity
- Separate CLI, task-management, and storage responsibilities.
- Keep application logic independently testable.

### Principle 5 — Testability
- All core operations must have automated tests.
- Tests must cover normal, boundary, and invalid-input cases.
- No test may be weakened simply to obtain a passing result.

### Principle 6 — Code Quality and Security
- Ruff must report no lint errors.
- Ruff formatting check must pass.
- Bandit must scan the actual application source files.
- No unresolved high-severity security findings are acceptable.

## 3. Technical Constraints
- Language: Python.
- Interface: Command-line.
- Storage: Local JSON file.
- Testing: pytest.
- Static analysis: Ruff and Bandit.
- No database or external network dependency.

## 4. Acceptance Criteria
- Users can add, list, update, delete, filter, and sort tasks.
- Tasks persist across application restarts.
- Invalid input is handled safely.
- Automated tests pass.
- Quality and security checks are reproducible.

## 5. Human Review
Automated results support but do not replace human review. The final implementation must be reviewed against the specification before acceptance.