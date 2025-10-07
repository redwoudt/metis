"""
Model Proxy Layer for Metis
---------------------------
This module defines a proxy wrapper around model instances. It intercepts
interactions to enforce cross-cutting policies such as logging, caching,
rate limiting, and input validation (e.g., blocking empty prompts).
"""

import time
import logging
logger = logging.getLogger("metis.models.model_proxy")
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
            logger.info(f"[proxy] Logging prompt (first 40 chars): {prompt[:40]}...")

    # Enforce a basic rate limiting policy based on timestamps
    def _rate_limit(self):
        logger.debug(f"[proxy] Checking rate limit with last_call_ts={self._last_call_ts}")
        max_rps = self.policies.get("max_rps")
        if max_rps:
            now = time.time()
            delta = None
            if self._last_call_ts is not None:
                delta = now - self._last_call_ts
            threshold = 1 / max_rps
            logger.debug(
                f"[proxy] rate limit params: max_rps={max_rps}, now={now}, "
                f"delta={delta}, threshold={threshold}"
            )
            if self._last_call_ts and delta is not None and delta < threshold:
                logger.warning(
                    f"[proxy] Rate limit exceeded: delta={delta} < threshold={threshold}"
                )
                raise Exception("Rate limit exceeded")

    # Retrieve a cached response for a given key if caching is enabled
    def _cache_get(self, key: str) -> Optional[str]:
        logger.debug(f"[proxy] Cache get for key={key}")
        return self.cache.get(key) if self.policies.get("cache") else None

    # Store a response in the cache for a given key if caching is enabled
    def _cache_put(self, key: str, value: str):
        logger.debug(f"[proxy] Cache put for key={key}")
        if self.policies.get("cache"):
            self.cache[key] = value

    # Main proxy method that intercepts generate calls with policy enforcement
    def generate(self, prompt: str, **kwargs: Any) -> str:
        logger.debug(f"[proxy] generate() called with prompt='{prompt[:40]}...', kwargs={kwargs}")
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
        logger.debug(f"[proxy] Setting last_call_ts={self._last_call_ts}")
        return out