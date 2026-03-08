"""
Command-line interface package for Mêtis.

This package contains the application-facing CLI entry points and subcommand
handlers. The CLI entrypoint lives in `metis.cli.main` and should normally be
invoked using:

    python -m metis.cli.main

We intentionally avoid importing `main` here to prevent Python's module loader
from importing `metis.cli.main` before it is executed via `-m`, which can cause
runpy warnings about modules already being present in `sys.modules`.
"""

__all__: list[str] = []