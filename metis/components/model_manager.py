"""
ModelManager acts as the Bridge implementor, routing text generation requests to a unified ModelClient adapter.

How it works:
- Delegates model selection and invocation to the provided ModelClient adapter.
- Simplifies integration by unifying diverse model APIs behind a common interface.
- Supports flexible backend switching without changing client code.

Expansion Ideas:
- Extend ModelClient adapters to support new models and APIs.
- Add middleware for logging, caching, or rate limiting.
- Enhance error handling and retries within adapters.
- Support asynchronous generation and streaming responses.
"""


class ModelManager:
    def __init__(self, model_client):
        self.model_client = model_client

    def generate(self, prompt: str) -> str:
        response = self.model_client.generate(prompt)
        return response.get("text", "")
