<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Apache-2.0 License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/redwoudt/metis">
    <img src="images/metis_logo.png" alt="Logo" width="80" height="80">
  </a>

  <h1 align="center">Design Patterns in Practice</h1>

  <p align="center">
    <strong>Master essential software patterns by building a GenAI system from scratch</strong>
    <br />
    A companion repository for setting up Mêtis, running the book’s provider-free examples, and learning design patterns through one evolving GenAI system.
    <br />
    <br />
    <a href="https://github.com/redwoudt/metis/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/redwoudt/metis/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-mêtis">About Mêtis</a></li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About Mêtis

[![CI](https://github.com/redwoudt/metis/actions/workflows/ci.yml/badge.svg)](https://github.com/redwoudt/metis/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/redwoudt/metis/branch/main/graph/badge.svg)](https://codecov.io/gh/redwoudt/metis)

Mêtis is the companion reference implementation for *Design Patterns in Practice: Master essential software patterns by building a GenAI system from scratch*. The repository applies software design patterns to one evolving generative-AI orchestration system.

It contains deterministic chapter examples, focused tests, and supporting documentation for the architectural boundaries introduced in the book. The project requires Python 3.10 or later.

### What You Will Learn

- Apply software design patterns in realistic generative-AI workflows
- Design components with explicit responsibilities and stable boundaries
- Build prompt, model, tool, state, event, and background-work pipelines
- Use adapters and bridges to isolate provider-specific behavior
- Govern tool execution through commands and ordered handlers
- Preserve conversation state and recoverable checkpoints
- Inspect completed work through events, traces, and visitors
- Extend the system through an allow-listed plugin boundary

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

- Python 3.10 or later
- Git
- A Python virtual environment

### Installation

Create and activate a virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Install the runtime dependencies, development tools, and Mêtis package:

```sh
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r dev-requirements.txt
python -m pip install -e .
```

Verify the installation:

```sh
python -m metis.examples.chapter2_facade
python -m pytest -q
```

The bundled chapter examples use deterministic mocks or in-memory components unless their documentation explicitly states otherwise. They do not require model-provider credentials.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

### Run Request
The run_request.py script is now a CLI tool! You can run it from the terminal like this:

python -m examples.run_request --user user_123 --prompt "What’s the weather in London today?"
It will send the prompt through the RequestHandler and print the response.

### Check Test Coverage 

To check the current test coverage run: 

make coverage

### Try the Chapter 2 Facade Example

Chapter 2 sends one provider-free request through `RequestHandler`, the public Facade. The example reports the public entry point, lifecycle owner, shared composition root, and response type:

```sh
python -m metis.examples.chapter2_facade
```

To return the immutable request-scoped result instead of compatibility text:

```sh
python -m metis.examples.chapter2_facade --details
```

### Try the Chapter 3 State and Memento Example

Chapter 3 advances a conversation from `GreetingState` to
`ClarifyingState`, then restores the earlier state and history from a scoped
checkpoint. The example uses a deterministic mock model and temporary
storage, so it requires no API key or network access:

```sh
python -m metis.examples.chapter3_state_memento \
  --prompt "Plan a careful route home"
```

### Try the Chapter 4 Prompt Construction Example

Chapter 4 builds the same planning prompt with `DefaultPromptBuilder` and
`PlanningPrompt`, then compares their rendered output before any model call.
The example is deterministic and requires no API key or network access:

```sh
python -m metis.examples.chapter4_prompt_construction
```

To see how both paths handle an optional component, run the comparison with an
empty tool result:

```sh
python -m metis.examples.chapter4_prompt_construction \
  --input "Plan a three-day study sprint." \
  --context "The exam is next Monday." \
  --tool-output "" \
  --tone "Direct" \
  --persona "Study Coach"
```

Both commands end with `MATCH=True` when the two construction paths produce
the same prompt.

### Try the Chapter 5 Prompt DSL Example

Chapter 5 sends a controlled prompt language through the lexer, parser,
expression objects, validator, and Chapter 4 prompt builder. The command is
deterministic and requires no API key or model provider:

See the [Chapter 5 prompt DSL runtime](docs/diagrams/chapter-05/prompt-dsl-runtime.md)
for the compact sequence used in the book and an explanation of the grouped
language-processing stages.

```sh
python -m metis.examples.chapter5_prompt_dsl
```

The JSON output names the tokens and expression classes, shows the validated
context, and displays the constructed prompt. To see semantic validation fail
before prompt construction, run:

```sh
python -m metis.examples.chapter5_prompt_dsl \
  --input "[task: translate][length: 3 bullet points]"
```

### Try the Chapter 6 Model Management Example

Chapter 6 resolves one model role through a registry-backed Factory, reuses the
same governed Proxy for equivalent configuration, and creates a distinct Proxy
when a policy changes. The example uses `MockAdapter`, so it requires no API key
or network access:

```sh
python -m metis.examples.chapter6_model_management
```

The output reports same-configuration reuse, policy-driven separation, two
deterministic responses, and the named failure for an unsupported vendor.

### Try the Chapter 7 Adapter and Bridge Example

Chapter 7 sends one prompt through the public request boundary with the
deterministic OpenAI and Anthropic teaching adapters. Both providers follow the
same application call and return plain text, while an unsupported vendor fails
with a named error. The example requires no API key or network access:

```sh
python -m metis.examples.chapter7_adapter_bridge
```

The two response prefixes identify the selected adapter. The reported response
types remain `str`, showing that provider-specific result dictionaries do not
escape into application code.

### Try the Chapter 8 Governed Weather Tool

Chapter 8 registers a deterministic weather command and executes it through
the same strict validation, permission, quota, audit, and execution pipeline
used by sensitive application tools:

```sh
python -m metis.examples.chapter8_governed_tools --city Ithaca
python -m metis.examples.chapter8_governed_tools --city Ithaca --deny
```

### Try the Chapter 9 Adaptive Response Example

Chapter 9 demonstrates how Strategy controls model-invocation parameters while
Decorator controls optional response presentation. The example uses a
deterministic recording model, so it requires no API key or network access:

```sh
python -m metis.examples.chapter9_adaptive_responses --style concise

python -m metis.examples.chapter9_adaptive_responses \
  --style analytical \
  --format-markdown \
  --include-citations
```

### Try the Chapter 10 Background Task Example

Chapter 10 schedules one provider-free task, verifies that it is not yet due,
advances an injected clock, and lets a worker complete it without sleeping or
creating a database file:

```sh
python -m metis.examples.chapter10_background_tasks --delay-minutes 5
```

### Try the Chapter 11 Event Path Example

Chapter 11 publishes three correlated lifecycle events through the in-process
`EventBus`. Global and typed observers verify routing, while an intentionally
failing observer demonstrates that delivery continues to later subscribers.
The example requires no API key or network access:

```sh
python -m metis.examples.chapter11_event_path
```

The stable summary reports the number of published events, the typed
`prompt.received` count, shared correlation, and continued dispatch.

### Try the Chapter 12 Mediated Request Example

Chapter 12 sends one provider-free prompt through `RequestHandler` and
`ConversationMediator`. The example uses the `Services` composition root, the
deterministic mock adapter, and temporary session storage to demonstrate DSL
tone handling, one completion event, and session persistence without an API
key or network access:

```sh
python -m metis.examples.chapter12_mediator_workflow
```

The summary identifies the public entry point and coordinator, then confirms
that the request returned a response, applied the requested tone, published one
completion event, and persisted its session.

### Try the Chapter 13 Visitor Inspection Example

Chapter 13 builds one provider-free `ExecutionTrace` from prompt, tool, model,
and response records. Four focused visitors then reconstruct the request path,
count tokens, summarize recorded latency, and describe the prompt structure:

```sh
python -m metis.examples.chapter13_visitor_inspection
```

The example uses deterministic records, pre-recorded timings, and the local
`SimpleTokenizer`, so it requires no API key or network access. Its output shows
that each visitor answers one operational question while traversing the same
completed request.

### Try the Chapter 14 Memory Example

Chapter 14 compares full snapshots with lean Mementos backed by shared
Flyweight artifacts. It uses temporary local storage and a deterministic mock
model:

```sh
python -m metis.examples.chapter14_memory
```

The output reports artifact reuse, serialized storage size, restoration, and
reference-aware eviction.

### Try the Chapter 15 Null Object Example

Chapter 15 compares an omitted event publisher with explicit null and real
publishers:

```sh
python -m metis.examples.chapter15_null_object --publisher omitted
python -m metis.examples.chapter15_null_object --publisher null
python -m metis.examples.chapter15_null_object --publisher real
```

Each command completes the same model request. The real publisher captures
lifecycle events, while the null and omitted configurations discard them.

### Try the Chapter 16 Template Strategy Example

Chapter 16 resolves one immutable behavior plan from the selected template and
risk level:

```sh
python -m metis.examples.chapter16_template_strategy
python -m metis.examples.chapter16_template_strategy \
  --behavior balanced \
  --risk high
```

The output reports the selected model role, response style, tool permission,
safety requirement, and citation setting.

### Try the Chapter 17 Plugin Host

Mêtis discovers separately installed capabilities through the
`metis_genai.plugins` entry-point group, but imports only plugins named in the
deployment allow-list. Install the provider-free echo example and compare the
discovered and enabled states:

```sh
python -m pip install -e examples/metis_echo_plugin
python -m metis.examples.chapter17_plugins --list
python -m metis.examples.chapter17_plugins --enable echo --list
```

For application startup, set `METIS_ENABLED_PLUGINS` to a comma-separated list.
Set `METIS_STRICT_PLUGINS=true` when failure of an enabled plugin must stop
startup. See [`docs/plugins.md`](docs/plugins.md) for the versioned contract,
supported contribution types, lifecycle, and trust boundary.

### Run the Chapter 18 Full Workflow

Chapter 18 composes the request façade, mediator, model bridge, state machine,
tools, checkpoints, events, visitors, and background worker into one workflow.
The example is provider-free and returns an immutable, request-scoped result:

```sh
python -m metis.examples.chapter18_full_workflow
```

Existing callers can keep using `RequestHandler.handle_prompt(...)` for a plain
string. New callers can use `RequestHandler.run(...)` to receive the response,
correlation ID, execution trace, and checkpoint outcome. See
[`docs/full_workflow.md`](docs/full_workflow.md) for the lifecycle and operating
guarantees.


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

Track planned work and known defects in the [Mêtis issue tracker](https://github.com/redwoudt/metis/issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Top contributors:

<a href="https://github.com/redwoudt/metis/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=redwoudt/metis" alt="contrib.rocks image" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Except for the project names and branding assets identified in
[`TRADEMARKS.md`](TRADEMARKS.md), the source code and documentation in this
repository are licensed under the Apache License 2.0. See [`LICENSE`](LICENSE)
and [`NOTICE`](NOTICE) for details.

Contributions are submitted under Apache-2.0 as described in
[`CONTRIBUTING.md`](CONTRIBUTING.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Ferdinand Redelinghuys - fcredelinghuys@gmail.com

Project Link: [https://github.com/redwoudt/metis](https://github.com/redwoudt/metis)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [README template](https://github.com/othneildrew/Best-README-Template)
* [GitHub Pages](https://pages.github.com)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/redwoudt/metis.svg?style=for-the-badge
[contributors-url]: https://github.com/redwoudt/metis/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/redwoudt/metis.svg?style=for-the-badge
[forks-url]: https://github.com/redwoudt/metis/network/members
[stars-shield]: https://img.shields.io/github/stars/redwoudt/metis.svg?style=for-the-badge
[stars-url]: https://github.com/redwoudt/metis/stargazers
[issues-shield]: https://img.shields.io/github/issues/redwoudt/metis.svg?style=for-the-badge
[issues-url]: https://github.com/redwoudt/metis/issues
[license-shield]: https://img.shields.io/github/license/redwoudt/metis.svg?style=for-the-badge
[license-url]: https://github.com/redwoudt/metis/blob/main/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/ferdinand-redelinghuys-8a642a10/
