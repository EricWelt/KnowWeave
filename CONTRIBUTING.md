# Contributing

Thanks for taking a look. Any fix or improvement is welcome.

## Getting started

```bash
# Backend (Python 3.10 or later)
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env    # then fill in one provider's API key
uvicorn backend.main:app --reload --port 8000

# App
cd app && flutter pub get
```

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/), one logical change
per commit: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

## Tests

Both suites should pass before you open a pull request.

```bash
cd backend && pytest
cd app && flutter test
```

## Working with two languages

The project ships English and Simplified Chinese. Language tags follow
[BCP 47](https://www.w3.org/International/articles/language-tags/): `en` for English,
`zh-Hans` for Simplified Chinese (script subtag, not the `zh-CN` region form).

| Layer | Where | Rule |
|---|---|---|
| Documentation | `README.md`, `docs/*.md` | English by default, with a `*.zh-Hans.md` sibling. Keep the section structure of both files in step. |
| App UI | `app/lib/l10n/app_*.arb` | Every key must exist in all three ARB files with the same placeholders. `app/test/unit/l10n_parity_test.dart` fails the build otherwise. |
| Prompts and other model-facing text | `backend/agent/prompts/` | One `TEXTS` dict per language. Keys and `$placeholders` must match. `backend/tests/test_prompts.py` enforces this. |
| Code comments | anywhere | Written in Chinese today, which is fine. New comments may be English. Prefer translating a docstring as you touch its file over a dedicated sweep. |

Keep these language-neutral, always: type and function names, JSON field names, tool
names, `action` values, and the `[工具 X 返回]` marker that the backend writes into the
conversation and the app parses back out. That marker looks like UI text but is a
protocol constant; translating it breaks quiz extraction.
