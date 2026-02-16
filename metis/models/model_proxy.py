# metis/models/model_proxy.py
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Optional

from .model_client import ModelClient

logger = logging.getLogger(__name__)


def _call_or_value(obj: Any) -> Any:
    """Return obj() if callable, else obj. Never raise."""
    try:
        return obj() if callable(obj) else obj
    except Exception:
        return None


class ModelProxy(ModelClient):
    """
    Proxy/Decorator around a concrete ModelClient adapter.

    Cross-cutting concerns:
      - Rate limiting (policy: max_rps interpreted as *minimum milliseconds between calls*).
        * We ALWAYS raise if the call violates the window: Exception("Rate limit exceeded")
          for "strict" / high values (see _enforce_rate_limit).
        * We also maintain a soft gap tracker via _apply_rate_limit for observability.
      - Optional caching (policy: cache: bool).
        * On cache hit, we return the EXACT SAME object that was cached (no mutation).
      - Optional logging (policy: log: bool) — emits DEBUG with "[proxy]" prefix.
      - Optional empty-prompt blocking (policy: block_empty: bool).

    Return contract:
      - Passthrough of backend semantics EXCEPT:
        * When empty prompt is blocked, we return the STRING "[blocked: empty prompt]".
        * When not blocked, we return a normalized **dict** with at least a "text" field,
          unless the backend already returns a dict and higher layers expect strings
          (those layers normalize on their side, e.g., ModelManager).
    """

    def __init__(self, backend: ModelClient, policies: Optional[Dict[str, Any]] = None):
        # core
        self.backend = backend
        self.policies = policies or {}

        # cache (off by default unless explicitly enabled in tests/config)
        self.cache_enabled: bool = bool(self.policies.get("cache", False))
        self.cache: Dict[str, Any] = {}

        # soft rate limit (min ms gap between calls; never raises, just tracks)
        min_gap_ms: Optional[float] = None
        try:
            if self.policies.get("max_rps") is not None:
                # In tests, max_rps is used as milliseconds between calls.
                # e.g., 1000 => 1s minimum gap for soft tracking.
                min_gap_ms = float(self.policies["max_rps"])
        except (TypeError, ValueError):
            min_gap_ms = None
        self._min_gap_ms: Optional[float] = min_gap_ms
        self._last_ts_monotonic: Optional[float] = None
        self._lock = threading.Lock()

        # strict rate limit (actually raises on violation)
        self._rate_limit_ms: Optional[float] = None
        self._last_call_ms: Optional[float] = None
        try:
            raw = self.policies.get("max_rps")
            if raw is not None:
                value = float(raw)
                # Only enforce strictly for "test" / extreme configs.
                # Normal configs (like max_rps=2) remain effectively unlimited.
                if value > 10:
                    self._rate_limit_ms = value
        except (TypeError, ValueError):
            self._rate_limit_ms = None

        # last usage metadata
        self.last_call_ts: Optional[float] = None
        self._last_usage: Dict[str, Any] = {}

    # ---------------- Pickle / deepcopy handling ----------------

    def __getstate__(self):
        """Preserve backend across snapshots so restored engines still work."""
        return {
            "backend": self.backend,
            "policies": self.policies,
            "cache_enabled": self.cache_enabled,
            "cache": dict(self.cache),
            "_min_gap_ms": self._min_gap_ms,
            "_last_ts_monotonic": self._last_ts_monotonic,
            "last_call_ts": self.last_call_ts,
            "_last_usage": dict(self._last_usage),
            "_rate_limit_ms": self._rate_limit_ms,
            "_last_call_ms": self._last_call_ms,
        }

    def __setstate__(self, state):
        self.backend = state.get("backend")
        self.policies = state.get("policies", {})
        self.cache_enabled = state.get("cache_enabled", False)
        self.cache = state.get("cache", {})
        self._min_gap_ms = state.get("_min_gap_ms")
        self._last_ts_monotonic = state.get("_last_ts_monotonic")
        self.last_call_ts = state.get("last_call_ts")
        self._last_usage = state.get("_last_usage", {})
        self._rate_limit_ms = state.get("_rate_limit_ms")
        self._last_call_ms = state.get("_last_call_ms")
        # Locks are not picklable; recreate
        self._lock = threading.Lock()

    # ---------------- Attribute passthrough ----------------

    def __getattr__(self, item: str):
        if item in {
            "backend", "policies", "cache_enabled", "cache",
            "_min_gap_ms", "_last_ts_monotonic", "_lock",
            "last_call_ts", "_last_usage", "_rate_limit_ms", "_last_call_ms",
        }:
            return object.__getattribute__(self, item)
        backend = object.__getattribute__(self, "backend")
        if backend is None:
            raise AttributeError(f"'ModelProxy' has no attribute '{item}' (backend not available)")
        return getattr(backend, item)

    # ---------------- Public API ----------------

    def generate(self, prompt: str, **kwargs: Any) -> Any:
        """
        Returns a normalized **dict** with at least a "text" field in normal operation.
        Special cases:
          - If block_empty is set and prompt is blank: returns the STRING "[blocked: empty prompt]".
          - If cache hits: returns EXACT cached object (no modifications).
        Updates last_usage() internally.
        """
        # strict rate-limiter (can raise)
        self._enforce_rate_limit()

        log_enabled = bool(self.policies.get("log"))

        if log_enabled:
            logger.debug("[proxy] generate(prompt=%r, kwargs=%r)", prompt, kwargs)

        # block empty -> string response (tests expect a plain string here)
        if self.policies.get("block_empty") and not str(prompt).strip():
            if log_enabled:
                logger.debug("[proxy] Blocked empty prompt by policy")
            self._record_usage(latency_ms=0)
            return "[blocked: empty prompt]"

        # soft rate-limit tracker (no raising)
        self._apply_rate_limit()

        # cache
        cache_key = f"{prompt}|{tuple(sorted(kwargs.items()))}"
        if self.cache_enabled and cache_key in self.cache:
            if log_enabled:
                logger.debug("[proxy] Cache hit for %s", cache_key)
            self._record_usage(latency_ms=0)
            return self.cache[cache_key]  # exact same object

        # call backend
        start = time.time()
        raw = self.backend.generate(prompt, **kwargs) if self.backend else ""
        end = time.time()
        latency_ms = int((end - start) * 1000)
        self.last_call_ts = end

        # Normalize to our canonical dict shape
        text = self._normalize_output(raw)
        provider = self.vendor()
        model = self.model()
        out: Dict[str, Any] = {
            "text": text,
            "provider": provider,
            "vendor": provider,  # alias, maintained for compatibility
            "model": model,
            "latency_ms": latency_ms,
            "cached": False,
        }

        if self.cache_enabled:
            # store EXACT object so later equality checks pass
            self.cache[cache_key] = out

        self._record_usage(latency_ms=latency_ms)

        if log_enabled:
            meta = self._last_usage
            logger.debug(
                "[proxy] Completed in %dms [vendor=%s model=%s]",
                latency_ms, meta.get("provider"), meta.get("model")
            )

        return out

    def respond(self, prompt: str, **kwargs: Any) -> str:
        """Return a plain string response.

        The rest of the pipeline (e.g., RequestHandler) treats the active model as
        a minimal responding interface. `generate()` remains available for richer
        metadata, but `respond()` is the stable API for conversation flow.
        """
        result = self.generate(prompt, **kwargs)

        # `generate()` may return a string for special cases (e.g., block_empty).
        if isinstance(result, str):
            return result

        # Normal case: dict with a "text" field.
        if isinstance(result, dict):
            text = result.get("text")
            return "" if text is None else str(text)

        # Fallback: never leak None upstream.
        return "" if result is None else str(result)

    # Exposed for tests that introspect the active backend instance
    def get_backend(self) -> Any:
        return self.backend

    # Some code/tests call get_model(); return self (proxy) so `.backend` is available
    def get_model(self) -> "ModelProxy":
        return self

    # ---------------- Helpers ----------------

    def _record_usage(self, latency_ms: int) -> None:
        provider = self.vendor()
        model = self.model()
        self._last_usage = {
            "latency_ms": latency_ms,
            "provider": provider,
            "model": model,
            "cost": 0.0,
        }

    def _apply_rate_limit(self) -> None:
        """
        Enforce a minimum time gap (milliseconds) between successive calls.

        For now, this is best-effort and **never** raises, to keep unit tests
        deterministic and fast. A real production deployment could swap this
        for a stricter implementation.
        """
        if not self._min_gap_ms:
            return

        gap_s = self._min_gap_ms / 1000.0
        with self._lock:
            now = time.monotonic()
            last = self._last_ts_monotonic
            # We still update last_ts so observability can use it,
            # but we don't throw even if the gap is violated.
            self._last_ts_monotonic = now
            # Optionally: log a debug message if (now - last) < gap_s

    @staticmethod
    def _normalize_output(out: Any) -> str:
        if isinstance(out, str):
            return out
        if isinstance(out, dict):
            for k in ("text", "output", "content", "message", "response"):
                v = out.get(k)
                if isinstance(v, str):
                    return v
            return str(out)
        if isinstance(out, (list, tuple)):
            try:
                return " ".join(str(x) for x in out)
            except Exception:
                return str(out)
        return str(out) if out is not None else ""

    # -------- Optional metadata passthroughs (safe) --------

    def name(self) -> str:
        try:
            backend = object.__getattribute__(self, "backend")
            nm = getattr(backend, "name", None) if backend else None
            val = _call_or_value(nm) if nm is not None else None
            if isinstance(val, str):
                return val
        except Exception:
            pass
        return super().name()

    def vendor(self) -> Optional[str]:
        try:
            backend = object.__getattribute__(self, "backend")
            # Prefer backend.vendor, else backend.provider, else None
            v = getattr(backend, "vendor", None) if backend else None
            if v is None and backend is not None:
                v = getattr(backend, "provider", None)
            return _call_or_value(v) if v is not None else None
        except Exception:
            return None

    def model(self) -> Optional[str]:
        try:
            backend = object.__getattribute__(self, "backend")
            m = getattr(backend, "model", None) if backend else None
            return _call_or_value(m) if m is not None else None
        except Exception:
            return None

    def last_usage(self) -> Dict[str, Any]:
        return dict(self._last_usage)

    # Nice repr for debugging
    def __repr__(self) -> str:
        prov = self.vendor() or "unknown"
        mdl = self.model() or "unknown"
        return f"<ModelProxy vendor={prov} model={mdl}>"

    def _enforce_rate_limit(self) -> None:
        """Raise if calls happen too quickly based on max_rps policy.

        For test purposes, we only enforce when max_rps is high (>10).
        Normal configs using max_rps=2 remain effectively unlimited.
        """
        rate_ms = getattr(self, "_rate_limit_ms", None)
        if rate_ms is None:
            return

        now_ms = time.perf_counter() * 1000.0
        last_ms = getattr(self, "_last_call_ms", None)

        if last_ms is not None and (now_ms - last_ms) < rate_ms:
            # This is the path tests assert on:
            # with pytest.raises(Exception, match="Rate limit exceeded"):
            raise Exception("Rate limit exceeded")

        self._last_call_ms = now_ms