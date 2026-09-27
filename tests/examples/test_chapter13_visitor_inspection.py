from metis.examples.chapter13_visitor_inspection import main, run_demo


EXPECTED_SUMMARY = {
    "steps": (
        "prompt:system > prompt:user > tool_command:weather.lookup > "
        "tool_result:weather.lookup:success > model:mock:chapter13 > response"
    ),
    "tokens": 15,
    "latency_ms": 155,
    "slowest": "model:mock:chapter13:121",
    "prompt_sections": 2,
}


def test_chapter13_example_reports_each_focused_analysis() -> None:
    assert run_demo() == EXPECTED_SUMMARY


def test_chapter13_example_prints_a_stable_summary(capsys) -> None:
    assert main() == 0

    assert capsys.readouterr().out.splitlines() == [
        "steps=prompt:system > prompt:user > tool_command:weather.lookup > "
        "tool_result:weather.lookup:success > model:mock:chapter13 > response",
        "tokens=15",
        "latency_ms=155",
        "slowest=model:mock:chapter13:121",
        "prompt_sections=2",
    ]
