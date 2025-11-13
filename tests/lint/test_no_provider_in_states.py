"""
Static lint test: ensure no direct SDK imports or provider references appear in state files.

States must never call provider SDKs (like openai or anthropic) directly.
All model interactions should go through:
    ConversationEngine -> ModelManager (Bridge) -> ModelClient Adapter

This test scans all files in metis/states/ for banned references.
"""

import os
import re
import pytest

# Direct provider references that should never appear in state files.
BANNED_PATTERNS = [
    r"\bopenai\b",
    r"\banthropic\b",
    r"\bhuggingface\b",
    r"\btransformers\b",
    r"\bvertexai\b",
    r"\bcohere\b",
]

STATE_DIR = os.path.join("metis", "states")


@pytest.mark.parametrize("pattern", BANNED_PATTERNS)
def test_no_provider_sdk_imports_in_states(pattern):
    """
    Ensure no state imports or directly references provider SDKs.

    This helps enforce the Adapter + Bridge boundary:
    - States talk only to the engine (engine.generate_with_model).
    - The engine talks to ModelManager and Adapters.
    """
    banned = re.compile(pattern, re.IGNORECASE)
    offending_files = []

    for root, _, files in os.walk(STATE_DIR):
        for filename in files:
            if not filename.endswith(".py"):
                continue

            filepath = os.path.join(root, filename)
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

                if banned.search(content):
                    offending_files.append(filepath)
                    print(f"⚠️ Found banned provider reference: {filepath}")

    assert not offending_files, (
        f"The following state files contain direct SDK references matching '{pattern}':\n"
        + "\n".join(offending_files)
    )