"""
Configuration settings loaded from environment or with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        pass

    WEATHER_API_URL = os.getenv("WEATHER_API_URL", "https://wttr.in/?format=3")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", 5))