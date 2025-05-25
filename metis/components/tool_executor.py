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

import requests
from metis.config import Config

class ToolExecutor:
    def execute(self, tool_name, user_input):
        if tool_name.lower() == "weather":
            return self._get_weather()
        raise Exception(f"Tool '{tool_name}' not supported.")

    def _get_weather(self):
        try:
            response = requests.get(Config.WEATHER_API_URL)
            if response.status_code == 200:
                return response.text.strip()
            return "Weather unavailable"
        except Exception:
            return "Weather service error"
