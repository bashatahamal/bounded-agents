# Security Policy

## Reporting a vulnerability

Please report security issues privately via
[GitHub Security Advisories](https://github.com/bashatahamal/bounded-agents/security/advisories/new)
rather than opening a public issue. If that's not available, email
bashatahamal@gmail.com.

Include what you found, how to reproduce it, and its potential impact. Expect
an acknowledgment within a few days — this is a personal open-source project,
not a funded security team, so response time is best-effort.

## Credentials

This repo never hardcodes or logs API keys, service account credentials, or
spreadsheet IDs — see `.env.sample` for what's expected and
`bounded.credentials.load_json_credentials` for how the Google service
account JSON is loaded (file path, base64, or raw JSON; never returns an
empty/placeholder credential silently).

If you find a code path that would log a secret (e.g. via `structlog` fields,
an exception message, or a LangSmith trace), please report it the same way —
that's a vulnerability, not just a bug.

## Supported versions

This is a reference implementation, not a maintained service with an LTS
policy. Security fixes land on `main`; there's no backport commitment to
older tags.
