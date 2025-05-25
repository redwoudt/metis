"""
ModelManager handles the selection and invocation of language models for text generation.

How it works:
- Provides mock models simulating production behavior.
- Selects a model based on task heuristics (e.g., keywords in prompt).
- Supports user-specific routing (e.g., "pro" users get deeper models).

Expansion Ideas:
- Integrate real APIs (e.g., OpenAI, Anthropic, LLaMA).
- Add support for multi-model fallback (retry on failure).
- Track model latency and error rates.
- Allow dynamic routing via configuration or feature flags.
- Implement token counting and budget enforcement.
"""

class Model:
    def __init__(self, name="MockModel"):
        self.name = name

    def generate(self, prompt: str) -> str:
        return f"[{self.name} Output]\n{prompt}"


class ModelManager:
    def __init__(self):
        self.models = {
            "default": Model(),
            "fast": Model("FastMockModel"),
            "deep": Model("DeepMockModel"),
        }

    def select(self, session, prompt) -> Model:
        user_id = session.get("user_id", "")
        task_type = self._infer_task_type(prompt)

        if "summarize" in prompt.lower():
            return self.models["fast"]
        elif "explain" in prompt.lower() or user_id.endswith("_pro"):
            return self.models["deep"]
        return self.models["default"]

    def _infer_task_type(self, prompt: str) -> str:
        if "summarize" in prompt.lower():
            return "summary"
        if "explain" in prompt.lower():
            return "explanation"
        return "general"
