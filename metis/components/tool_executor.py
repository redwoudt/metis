# --- metis/components/tool_executor.py ---
"""
ToolExecutor handles external tool invocations that enhance prompts with real-time or auxiliary data.

How it works:
- Detects tool type from the requested name.
- Calls the corresponding handler (e.g., weather API).
- Returns processed output suitable for prompt enrichment.

Expansion Ideas:
- Add support for additional tools (e.g., calculators, search, code runners).
- Implement tool chaining or workflows.
- Add error classification and retry logic.
- Support sandboxing or rate limiting per tool.
"""

import re
import requests
from metis.config import Config

class ToolExecutor:
    def execute(self, tool_name, user_input):
        if tool_name.lower() == "weather":
            return self._get_weather(user_input)
        raise Exception(f"Tool '{tool_name}' not supported.")

    def _get_weather(self, user_input: str) -> str:
        import re

        # Extract a location, default to London
        match = re.search(r"in ([A-Za-z ]+)", user_input, re.IGNORECASE)
        location = match.group(1).strip() if match else "London"

        try:
            url = f"{Config.WEATHER_API_URL}/{location}?format=3"
            response = requests.get(url)
            if response.status_code == 200:
                return response.text.strip()
            return f"Weather unavailable for {location}"
        except Exception:
            return "Weather service error"