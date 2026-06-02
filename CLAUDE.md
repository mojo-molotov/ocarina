# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Pull requests

When opening a PR, the working branch name **must** match one of the branch
trigger patterns declared in [`.github/workflows/dev_ci.yml`](.github/workflows/dev_ci.yml)
so that CI runs on push. Treat that workflow as the single source of truth and
keep branch naming in sync with it — if those patterns change, follow the new
ones.

As currently defined in `dev_ci.yml`:

```yaml
on:
  push:
    branches:
      - dev
      - 'feature/**'
      - 'fix/**'
```

Therefore branch names must be:

- `feature/<short-kebab-description>` for features and enhancements.
- `fix/<short-kebab-description>` for bug fixes.
- `dev` for the integration branch.

Do **not** use abbreviated prefixes such as `feat/` — they are not matched by
the workflow and CI will not run.
