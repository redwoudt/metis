from metis.components.model_manager import ModelManager


def test_model_response():
    manager = ModelManager()
    model = manager.select({"user_id": "user_123"}, "Prompt")
    output = model.generate("Prompt")
    assert "Prompt" in output

