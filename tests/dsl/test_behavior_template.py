from metis.dsl import interpret_prompt_dsl


def test_dsl_behavior_expr_sets_template_name() -> None:
    context = interpret_prompt_dsl("[behavior: creative]")
    assert context["behavior"] == "creative"
