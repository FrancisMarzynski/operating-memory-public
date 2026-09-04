# Operating Memory

[![CI](https://github.com/FrancisMarzynski/operating-memory-public/actions/workflows/ci.yml/badge.svg)](https://github.com/FrancisMarzynski/operating-memory-public/actions/workflows/ci.yml)

A markdown-first operating-memory backend. The database is derived from durable notes; it is not a replacement for them.

This repository is intentionally starting as a clean skeleton. The generalized memory core, tests, and documentation will arrive in reviewed vertical slices.

See [the local memory-core guide](docs/memory-core.md) for the configuration format, invented example corpus, commands, and verification steps.

## Local verification

Install the development toolchain with `uv sync --group dev`, then run the same checks as CI:

```sh
uv run ruff check .
uv run mypy src
uv run pytest
uv run python scripts/check_boundary.py
```

## Status

Private during extraction and security review. No production or client data belongs here.
