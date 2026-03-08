#!/usr/bin/env python3
"""
Compatibility wrapper for the Mêtis CLI.

The main CLI implementation now lives in metis.cli.main. This wrapper keeps
existing invocation paths and tests working while allowing the CLI code to
grow in its own dedicated package.
"""

from __future__ import annotations

import sys

from metis.cli.main import main


if __name__ == "__main__":
    sys.exit(main())