"""
Tests for ModelManager behavior including model selection logic and output formatting.
"""

from metis.components.model_manager import ModelManager


def test_model_selection_default():
    manager = ModelManager()
    model = manager.select({"user_id": "user_1"}, "Tell me a story")
    assert model.name == "MockModel"


def test_model_selection_fast():
    manager = ModelManager()
    model = manager.select({"user_id": "user_2"}, "Please summarize this article")
    assert model.name == "FastMockModel"


def test_model_selection_deep():
    manager = ModelManager()
    model = manager.select({"user_id": "user_pro"}, "Explain quantum entanglement")
    assert model.name == "DeepMockModel"


def test_model_generate():
    model = ModelManager().select({}, "Test input")
    output = model.generate("Test input")
    assert "Test input" in output
