from metis.behavior import (
    BehaviorContext,
    BehaviorPlan,
    build_default_behavior_strategy,
)
from metis.commands.base import ToolCommand, ToolContext
from metis.events import Event
from metis.models.model_client import ModelClient
from metis.plugins import PluginMetadata
from metis.services.services import Services

from .conftest import FakeEntryPoint


class EchoCommand(ToolCommand):
    name = "demo.echo"

    def execute(self, context: ToolContext):
        return {"echo": context.args.get("message", "")}


class DemoModel(ModelClient):
    def __init__(self, model: str):
        self.model_name = model

    def generate(self, prompt: str, **kwargs):
        return {"text": f"[demo:{self.model_name}] {prompt}"}


class CapturingObserver:
    def __init__(self) -> None:
        self.events = []

    def notify(self, event) -> None:
        self.events.append(event)


class FullPlugin:
    metadata = PluginMetadata("demo", "2.0.0")

    def __init__(self) -> None:
        self.observer = CapturingObserver()

    def register(self, registrar) -> None:
        registrar.command("demo.echo", EchoCommand)
        registrar.behavior_template(
            BehaviorPlan(
                name="demo.evidence-first",
                model_role="analysis",
                response_style="analytical",
                allow_tools=True,
                require_safety=True,
                include_citations=True,
            )
        )
        registrar.model_adapter(
            "demo.model",
            lambda *, model, **kwargs: DemoModel(model),
        )
        registrar.observer("demo.event", lambda: self.observer)


def test_services_wires_all_supported_contribution_types(monkeypatch) -> None:
    monkeypatch.setenv("METIS_TASK_SCHEDULER", "inmemory")
    plugin = FullPlugin()
    services = Services(
        plugin_config={"enabled_plugins": ["demo"], "strict_plugins": True},
        plugin_candidates=[FakeEntryPoint("demo", plugin, version="2.0.0")],
    )

    assert services.plugin_report.loaded[0].plugin_id == "demo"
    assert services.extension_registries.frozen is True

    result = services.tool_executor.execute_tool(
        "demo.echo",
        args={"message": "hello"},
        user="reader",
    )
    assert result == {"echo": "hello"}

    strategy = build_default_behavior_strategy(
        {},
        templates=services.extension_registries.behavior_templates,
    )
    plan = strategy.choose(BehaviorContext(requested_template="demo.evidence-first"))
    assert plan.include_citations is True

    client = services.model_factory.resolve(
        "analysis",
        {"vendor": "demo.model", "model": "v1", "policies": {}},
    )
    assert "[demo:v1] evidence" in client.generate("evidence")["text"]

    event = Event.create(
        event_type="demo.event",
        source="test",
        correlation_id="chapter-17",
    )
    services.event_bus.publish(event)
    assert plugin.observer.events == [event]
