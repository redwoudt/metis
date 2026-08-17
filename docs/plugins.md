# Mêtis plugin API

Mêtis discovers installed plugins through the `metis_genai.plugins` entry-point
group. Discovery reads package metadata only. Plugin code is imported only when
its entry-point name appears in `enabled_plugins` or `METIS_ENABLED_PLUGINS`.

## Contract

A plugin exposes an object with `PluginMetadata` and one `register()` method:

```python
class ExamplePlugin:
    metadata = PluginMetadata("example", "1.0.0", api_version="1")

    def register(self, registrar):
        registrar.command("example.echo", EchoCommand)
```

External command names, behaviour-template names, and model vendors must begin
with `<plugin_id>.`. The first API supports four contribution types:

- `registrar.command(name, factory)`
- `registrar.behavior_template(plan)`
- `registrar.model_adapter(vendor, factory)`
- `registrar.observer(event_type, factory)`

All declarations from one plugin are staged, validated, and committed as one
batch. Registries freeze before Mêtis accepts requests. The DSL registry and the
durable scheduled-task executor registry are not public plugin APIs.

## Activation

Set a comma-separated allow-list before starting Mêtis:

```console
METIS_ENABLED_PLUGINS=echo METIS_STRICT_PLUGINS=true python -m examples.run_request
```

`METIS_STRICT_PLUGINS=true` stops startup when a named plugin is missing or
invalid. Permissive mode keeps built-ins available and exposes the rejection in
`Services.plugin_report`.

## Example distribution

Install the provider-free example alongside Mêtis, then compare discovery and
activation:

```console
python -m pip install -e examples/metis_echo_plugin
python -m metis.examples.chapter17_plugins --list
python -m metis.examples.chapter17_plugins --enable echo --list
```

An in-process plugin is trusted application code. The registrar constrains the
supported API but is not a security sandbox. Use a subprocess or service
boundary for untrusted execution.
