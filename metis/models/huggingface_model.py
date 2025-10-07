# metis/models/huggingface_model.py

class HuggingFaceModel:
    def __init__(self, config):
        self.config = config

    def __call__(self, prompt, **kwargs):
        return f"[HuggingFaceModel placeholder] You said: {prompt}"