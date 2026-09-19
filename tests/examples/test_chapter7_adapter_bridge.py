import inspect

from metis.examples.chapter7_adapter_bridge import ask, main, run_demo


def test_one_caller_uses_two_adapters_and_receives_text() -> None:
    result = run_demo("Keep the caller stable.")

    assert isinstance(result["openai_text"], str)
    assert isinstance(result["anthropic_text"], str)
    assert "[openai mock:chapter-7-openai]" in result["openai_text"].lower()
    assert "[anthropic mock:chapter-7-anthropic]" in result["anthropic_text"].lower()


def test_application_caller_contains_no_provider_dependency() -> None:
    source = inspect.getsource(ask).lower()

    assert "openai" not in source
    assert "anthropic" not in source
    assert ".handle_prompt(" in source


def test_unsupported_adapter_fails_by_name() -> None:
    result = run_demo()

    assert result["unsupported_vendor_error"] == "Unsupported vendor: unsupported"


def test_example_cli_reports_the_stable_contract(capsys) -> None:
    assert main([]) == 0

    output = capsys.readouterr().out
    assert "OPENAI_TYPE=str" in output
    assert "ANTHROPIC_TYPE=str" in output
    assert "UNSUPPORTED_VENDOR_ERROR=Unsupported vendor: unsupported" in output
