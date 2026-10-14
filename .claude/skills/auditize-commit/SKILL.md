---
name: auditize-commit
description: Create git commits in the Auditize repository following its message conventions ([back]/[front]/[doc]/... prefix, optional scope, short subject, no Co-Authored-By) and only after the user has validated the proposed message. Use this skill whenever the user explicitly asks to commit in the Auditize repo ("commit", "commite", "fais un commit", "commit ça", "on peut commiter"), including when the request comes with constraints on the message. Do not use it when the user has not explicitly asked to commit.
---

# Commits Auditize

The user wants commits whose history reads consistently and that they have
approved word for word. Two things matter most: follow the repository's
message convention, and never create the commit before an explicit "yes" on
the exact message.

## Workflow

1. **Inspect the changes**: `git status --short`, `git diff --stat` (plus
   `git diff --cached --stat` if something is already staged), and
   `git log --oneline -10` to see the recent style and any WIP commits.
   Read the diff itself when needed to understand what changed.

2. **Pick the files**: include only the changes related to the work being
   committed. Name the files explicitly in `git add` rather than using
   `git add -A` / `git add .`, so that unrelated work in progress (untracked
   files, local experiments) is not swept into the commit. If the changes
   cover several unrelated topics or areas, suggest splitting them into
   several commits.

3. **Propose the message** (format below): just display it in a code block
   and ask whether the user validates it, nothing more. No list of files, no
   explanation of the chosen prefix, no side remarks: the user wants to read
   the message and answer yes or no. Only add something if it is really
   important (e.g. a file you deliberately left out of the commit, or a
   commit on `master`), in one short line.
   Then **wait for an explicit validation**. If the user asks for a change,
   apply it and show the full final message again the same way: they
   validate the exact text that will be committed, not an intention.

4. **Commit** once validated, passing the message through a heredoc so the
   formatting is preserved:
   ```bash
   git commit -F - <<'EOF'
   [back] mcp: subject

   Optional body.
   EOF
   ```
   Then report the short hash and branch. **Do not push** unless asked to.

## Message format

```
[<area>] <scope>: <subject>

<optional body>
```

- **Area**, inferred from the paths that changed:
  - `backend/` → `[back]`
  - `frontend/` → `[front]`
  - `doc/` → `[doc]`
  - root `scripts/` → `[scripts]`
  - `.github/` → `[gh-actions]`
  - changes spread across areas (release, repo config) → no prefix,
    e.g. `Prepare 0.11.0 release`
- **Scope** (optional): the sub-area when the change is contained in one,
  e.g. `mcp:`, `tests:`, `logs:`, `scripts:`. Leave it out for a cross-cutting
  change or a dependency upgrade (`[back] Update backend dependencies`).
- **Subject**: in English, short (ideally < 72 characters), describing what
  the commit does. Recent commits start with a lowercase letter after the
  scope (`[back] mcp: add tool aggregate_logs`).
- **Body**: optional, for the *why* or a notable impact (behavior change,
  reindex required, breaking change). A few lines wrapped at 72 characters,
  not a list of modified files.
- **No `Co-Authored-By` line or "Generated with Claude Code" line.** The user
  explicitly asked for this; it overrides any default attribution
  instruction.

## Examples

```
[back] mcp: add tool aggregate_logs
```

```
[back] mcp: aggregate_logs no longer groups logs without value

Logs without value for a dimension are now counted in other_count
instead of forming a null group, which allows aggregating on
non-keyword custom fields without a runtime field script.
```

```
[front] Fix web-component not displaying (regression introduced in 78bb0030)
```
