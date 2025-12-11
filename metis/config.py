"""
Configuration settings loaded from environment or with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# NEW IMPORT: services container
from metis.services.services import get_services


def resolve_env(value: str) -> str:
    if value.startswith("env:"):
        return os.getenv(value[4:], "")
    return value


class Config:
    # Weather API config
    WEATHER_API_URL = os.getenv("WEATHER_API_URL", "https://wttr.in")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", 5))

    # Model Registry mapping roles to configuration
    MODEL_REGISTRY = {
        "creative": {
            "vendor": "openai",
            "model": "gpt-4o",
            "api_key": resolve_env("env:OPENAI_KEY"),
            "defaults": {
                "temperature": 0.9,
                "max_tokens": 800
            },
            "policies": {
                "log": True,
                "cache": True,
                "max_rps": 3,
                "block_empty": True
            }
        },
        "analysis": {
            "vendor": "anthropic",
            "model": "claude-3-opus",
            "token": resolve_env("env:ANTHROPIC_TOKEN"),
            "defaults": {
                "temperature": 0.2,
                "max_tokens": 1200
            },
            "policies": {
                "log": True,
                "max_rps": 2
            }
        }
    }

    @staticmethod
    def services():
        """
        Return the shared Services container used during tool execution.

        Example:
            services = Config.services()
            services.quota
            services.audit_logger
        """
        return get_services()