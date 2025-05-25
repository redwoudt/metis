"""
Tests for PromptBuilder, including default and JSON formatting, sanitization, and templates.
"""
from metis.components.prompt_builder import PromptBuilder


def test_prompt_builder_default():
    builder = PromptBuilder()
    session = {"user_id": "user_123", "history": []}
    result = builder.build(session, "Summarize this text")
    assert "Summarize the following input" in result


def test_prompt_builder_json():
    builder = PromptBuilder(format_style="json")
    session = {"user_id": "user_json", "history": [("Hi", "Hello")]}
    result = builder.build(session, "Plan my day")
    assert "\"session\": \"user_json\"" in result
    assert "Plan my day" in result


def test_prompt_sanitization():
    builder = PromptBuilder()
    session = {"user_id": "user_123", "history": []}
    dirty_input = "<script>alert('hi')</script>    Please plan   this"
    result = builder.build(session, dirty_input)
    assert "&lt;script&gt;alert(&#x27;hi&#x27;)&lt;/script&gt;" in result
    assert "Please plan this" in result
