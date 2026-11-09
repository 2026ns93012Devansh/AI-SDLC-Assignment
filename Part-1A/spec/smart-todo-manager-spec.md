# Smart Todo Manager Specification

**Status:** Approved  
**Version:** 1

## 1. Purpose

Smart Todo Manager is a deterministic Python command-line application for
creating and managing daily tasks. It stores task data in a local JSON file and
does not use a database, network service, or third-party runtime dependency.

## 2. Scope and interpretation

The application supports adding, listing, updating, deleting, filtering, and
sorting tasks.

Task grouping is represented by tags. There is no separate category field; a
user who wants a category can use a tag for it. Tags are optional.

The interface is non-interactive and uses subcommands so commands can be
scripted. Filtering and sorting are options of `list`, not separate commands.

## 3. Invocation and commands

The application is invoked as:

```text
python -m smart_todo [--file PATH] COMMAND
```

`--file PATH` selects the JSON storage file. If omitted, the application uses
`tasks.json` in the current working directory. `--help` and command-specific
help are provided by the command-line parser.

### 3.1 Add a task

```text
python -m smart_todo [--file PATH] add --title TITLE
    [--description DESCRIPTION]
    [--priority Low|Medium|High]
    [--status Pending|Completed]
    [--tag TAG ...]
```

- Title is required and must contain a non-whitespace character.
- Description defaults to an empty string.
- Priority defaults to `Medium`.
- Status defaults to `Pending`.
- Tags default to an empty list. `--tag` may be repeated.
- Title and description are trimmed at their boundaries.
- Priority and status input is case-insensitive and stored/displayed with the
  canonical capitalization shown above.
- Tags are trimmed, must be non-empty, and are deduplicated case-insensitively.
  The first spelling and order are retained.
- A successful add assigns the next ID, saves the task, and reports its ID.

### 3.2 List, filter, and sort tasks

```text
python -m smart_todo [--file PATH] list
    [--status Pending|Completed]
    [--priority Low|Medium|High]
    [--tag TAG]
    [--sort priority]
```

- With no filters, all tasks are displayed.
- If multiple filters are supplied, a task must match every supplied filter.
- Tag matching is case-insensitive.
- The default ordering is ascending task ID (creation order).
- `--sort priority` orders tasks `High`, `Medium`, then `Low`; ties are ordered
  by ascending task ID.
- A list result shows ID, title, priority, tags, and status. A non-empty
  description is also shown. Missing tags are displayed as `-`.
- An empty result prints a clear “No tasks found” message.

### 3.3 Update a task

```text
python -m smart_todo [--file PATH] update ID
    [--title TITLE]
    [--description DESCRIPTION]
    [--priority Low|Medium|High]
    [--status Pending|Completed]
    [--tag TAG ... | --clear-tags]
```

- Only supplied fields are changed; omitted fields retain their current values.
- At least one update option is required.
- A supplied title must remain non-blank after trimming.
- An explicitly empty description clears the description.
- Supplying one or more `--tag` values replaces the complete tag list and uses
  the same trimming and deduplication rules as `add`.
- `--clear-tags` removes every tag and cannot be combined with `--tag`.
- An unknown ID is an error and does not change storage.

### 3.4 Delete a task

```text
python -m smart_todo [--file PATH] delete ID
```

- The task matching ID is deleted immediately; no interactive confirmation is
  requested.
- An unknown ID is an error and does not change storage.

## 4. IDs and determinism

- IDs use the format `T-0001`, `T-0002`, and so on. The numeric part has a
  minimum width of four digits and expands as needed.
- The next numeric ID is persisted in the storage file and is incremented only
  when a new task is successfully saved. Deleting a task never makes its ID
  available again.
- IDs contain no random component. The application stores no timestamps.
- For the same initial storage and sequence of valid commands, task data,
  IDs, ordering, and command output are deterministic.

## 5. JSON storage

The storage file is UTF-8 JSON with this version 1 shape:

```json
{
  "schema_version": 1,
  "next_id": 2,
  "tasks": [
    {
      "id": "T-0001",
      "title": "Example task",
      "description": "",
      "priority": "Medium",
      "tags": [],
      "status": "Pending"
    }
  ]
}
```

- A missing file or a zero-byte file is treated as an empty task list with the
  next ID set to 1.
- A valid initialized empty store has an empty `tasks` array and `next_id` 1.
- Non-empty storage must be valid JSON with a supported schema version and
  valid task fields, values, and unique IDs. Invalid or unsupported storage is
  reported as an error; it is never silently treated as empty or overwritten.
- Successful mutations are written atomically by writing a temporary file
  beside the storage file and replacing the target. A failed operation must not
  leave a partially written JSON file.
- Read, validation, and write failures are reported to standard error. Existing
  storage is preserved when a mutation cannot be completed.

## 6. Input validation and process results

- Invalid commands, malformed arguments, invalid field values, blank titles,
  empty tags, and unknown task IDs produce clear error messages.
- Expected user/input errors return exit status 2. Storage or persistence
  errors return exit status 1. Successful operations and help return exit
  status 0.
- Errors do not report success and do not modify storage.
- The command-line parser's usage/help output is readable and includes the
  available commands and options.

## 7. Quality and testing requirements

- Keep the implementation modular and maintainable.
- Application functionality uses only the Python standard library.
- Automated tests use pytest and cover add/list/update/delete, validation,
  filters, priority ordering and tie-breaking, ID persistence/non-reuse, and
  missing, empty, malformed, unsupported, and unwritable storage cases.
- Run Ruff for linting and Bandit for security checks. These are development
  tools and are not runtime dependencies.
- Tests must verify deterministic behavior and that failed operations preserve
  stored data.

## 8. Decisions recorded from review

- Use subcommands rather than an interactive menu.
- Default storage is `tasks.json` in the current working directory.
- Use a persisted sequential ID counter; never reuse deleted IDs.
- Combine simultaneous filters with AND.
- Delete immediately without prompting.
- Preserve and report malformed or unsupported non-empty storage.
- Place the specification and eventual project work in `Part-1A`.

## 9. Approval record

The user reviewed and explicitly approved this specification before
implementation began.
