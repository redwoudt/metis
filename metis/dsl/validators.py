

import re
from typing import Dict
from .errors import ValidationError

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)

def validate_context(ctx: Dict[str, str]) -> None:
    # Example: length should accompany summarization tasks
    if "length" in ctx and ctx.get("task", "").lower() not in {"summarize", "summary"}:
        raise ValidationError("`length` is only valid when task is Summarize.")

    if "source" in ctx and ctx["source"] and not _URL_RE.match(ctx["source"]):
        raise ValidationError("`source` must be an http(s) URL.")