# ToolExecutor subsystem
import requests

import requests
from metis.config import Config

class ToolExecutor:
    def execute(self, tool_name, user_input):
        if tool_name == "weather":
            return self._get_weather()
        raise Exception("Tool not supported")

    def _get_weather(self):
        try:
            response = requests.get(Config.WEATHER_API_URL)
            if response.status_code == 200:
                return response.text.strip()
            else:
                return "Weather unavailable"
        except Exception:
            return "Weather service error"