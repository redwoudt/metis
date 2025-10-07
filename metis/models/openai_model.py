# metis/models/openai_model.py

class OpenAIModel:
    def __init__(self, config):
        self.config = config

    def __call__(self, prompt, **kwargs):
        return f"[OpenAIModel placeholder] You said: {prompt}"