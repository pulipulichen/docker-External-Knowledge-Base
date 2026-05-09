---
name: changelog
description: Writes repository changelog entries from recent git changes. Use when updating CHANGELOG.md, recording release notes, or when the user asks to summarize recent commits into the changelog.
---

# Changelog

## Instructions

When the user asks to update the changelog:

1. If the user does not specify what changes to record, summarize the latest commit.
2. If the user specifies a version, create a new section for that version.
3. If the user does not specify a version, add the entry under the latest existing version.
4. Write changelog content in English.
5. Keep entries concise and user-facing; describe behavior and outcome rather than implementation trivia.

## Format

Use this structure in `CHANGELOG.md`:

```markdown
## <version>

- <change summary>
```
