

"""
Model Proxy Layer for Metis
---------------------------
This module defines a proxy wrapper around model instances. It intercepts
interactions to enforce cross-cutting policies such as logging, caching,
rate limiting, and input validation (e.g., blocking empty prompts).
"""

import time
from typing import Any, Optional


class ModelProxy:
    # Initialize proxy with backend model and policy settings
    def __init__(self, backend: Any, policies: dict):
        self.backend = backend
        self.policies = policies or {}
        self._last_call_ts = None
        self.cache = {}

    # Optionally log the prompt if logging is enabled
    def _log(self, prompt: str):
        if self.policies.get("log"):
            print(f"[proxy] Prompt: {prompt[:40]}...")

    # Enforce a basic rate limiting policy based on timestamps
    def _rate_limit(self):
        max_rps = self.policies.get("max_rps")
        if max_rps:
            now = time.time()
            if self._last_call_ts and now - self._last_call_ts < 1 / max_rps:
                raise Exception("Rate limit exceeded")

    # Retrieve a cached response for a given key if caching is enabled
    def _cache_get(self, key: str) -> Optional[str]:
        return self.cache.get(key) if self.policies.get("cache") else None

    # Store a response in the cache for a given key if caching is enabled
    def _cache_put(self, key: str, value: str):
        if self.policies.get("cache"):
            self.cache[key] = value

    # Main proxy method that intercepts generate calls with policy enforcement
    def generate(self, prompt: str, **kwargs: Any) -> str:
        self._log(prompt)
        self._rate_limit()

        cache_key = f"{prompt}|{kwargs}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        if self.policies.get("block_empty") and not prompt.strip():
            return "[blocked: empty prompt]"

        out = self.backend.generate(prompt, **kwargs)
        self._cache_put(cache_key, out)
        self._last_call_ts = time.time()
        return out