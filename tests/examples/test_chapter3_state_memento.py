from metis.examples.chapter3_state_memento import run_demo


def test_chapter3_example_restores_state_and_history() -> None:
    result = run_demo("Draft the release note")

    assert result["state_before"] == "GreetingState"
    assert result["state_after_turn"] == "ClarifyingState"
    assert result["state_after_restore"] == "GreetingState"
    assert result["history_after_turn"][-1] == result["response"]
    assert result["history_after_restore"] == ["User: Draft the release note"]
    assert result["restored"] is True
    assert result["remaining_checkpoints"] == 0
