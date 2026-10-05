from metis.examples.chapter18_full_workflow import main


def test_chapter18_example_reports_trace_and_checkpoint_outcome(capsys) -> None:
    main()

    output = capsys.readouterr().out.splitlines()

    assert output[0].startswith(
        "[mock:chapter18] [Tone: concise] [Persona: Helpful Assistant]"
    )
    assert any(line.startswith("correlation_id=") for line in output)
    assert (
        "trace=prompt:user_input -> prompt:dsl_context -> "
        "model:mock:chapter18 -> response"
    ) in output
    assert "checkpoint_saved=True" in output
    assert "checkpoints=1" in output
