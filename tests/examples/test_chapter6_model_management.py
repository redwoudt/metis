from metis.examples.chapter6_model_management import main, run_demo


def test_chapter6_example_demonstrates_reuse_and_separation() -> None:
    result = run_demo()

    assert result["same_config_reused"] is True
    assert result["changed_policy_creates_new_proxy"] is True
    assert result["first_response"] == result["second_response"]
    assert "[mock:chapter-6]" in result["first_response"].lower()
    assert result["unsupported_vendor_error"] == "Unsupported vendor: missing"


def test_chapter6_example_cli_reports_the_contracts(capsys) -> None:
    assert main([]) == 0

    output = capsys.readouterr().out
    assert "SAME_CONFIG_REUSED=True" in output
    assert "CHANGED_POLICY_CREATES_NEW_PROXY=True" in output
    assert "UNSUPPORTED_VENDOR_ERROR=Unsupported vendor: missing" in output
