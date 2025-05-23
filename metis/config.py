import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

class Config:
    WEATHER_API_URL = os.getenv("WEATHER_API_URL", "https://wttr.in/?format=3")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")  # Optional placeholder
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", 5))
