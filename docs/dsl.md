

# Metis Prompt DSL

The Metis Prompt DSL is a lightweight, bracket-based syntax for expressing structured instructions to the GenAI system.  
It enables separating *intent* and *parameters* from freeform user input, allowing consistent interpretation and formatting across prompt builders.

## Syntax

The DSL is a sequence of bracketed **key-value** expressions:

```
[key: value][key: value]...
```

Keys are case-insensitive. Whitespace around keys, colons, and values is ignored.

### Example

```
[persona: Research Assistant]
[task: Summarize]
[length: 3 bullet points]
[format: bullets]
[tone: optimistic]
[source: https://example.com/data]
```

### Grammar (EBNF)

```
prompt      ::= expression*
expression  ::= "[" key ":" value "]"
key         ::= IDENT                   ; canonical: persona|task|length|format|tone|source
value       ::= VALUE                   ; any run of characters without ']' (trimmed)
```

## Supported Keys

- `persona` — Role or identity the assistant should adopt.
- `task` — High-level action, e.g., *summarize*, *plan*, *critique*.
- `length` — Desired length of the output (only valid with summarization tasks).
- `format` — Preferred output structure, e.g., *bullets*, *paragraphs*, *JSON*.
- `tone` — Emotional tone or style of the response.
- `source` — External resource (must be an `http(s)` URL).

## Validation Rules

- **Length** is only valid if `task` is `summarize` or `summary`.
- **Source** must be a valid `http://` or `https://` URL.
- Unknown keys will raise an error unless registered via the DSL registry.

## Extensibility

New keys can be added dynamically using the registry:

```python
from metis.dsl.registry import register_key
from metis.dsl.ast import Expression

class AudienceExpr(Expression):
    def __init__(self, value: str):
        self.value = value.strip()

    def interpret(self, context: dict) -> None:
        context["audience"] = self.value

register_key("audience", AudienceExpr)
```

## Workflow in Metis

1. **Lexing** — The `lexer.py` module scans the DSL string into tokens.
2. **Parsing** — The `parser.py` module builds an AST of `Expression` objects.
3. **Interpreting** — The `interpreter.py` walks the AST, filling a `PromptContext` dictionary.
4. **Validation** — `validators.py` ensures semantic rules are met.
5. **Prompt Building** — Builders (e.g., `DefaultPromptBuilder`, `OpenAIPromptBuilder`) map the context into final prompt formats.
6. **Execution** — The request handler sends the built prompt to the selected model.

## CLI Usage

Interpret a DSL string directly:
```
python metis_cli.py dsl --input "[persona: Analyst][task: summarize][length: short]"
```

Use DSL with the prompt command:
```
python metis_cli.py prompt --input "Summarize the report" --dsl "[persona: Analyst][tone: friendly][task: summarize]"
```

## Error Handling

- **LexError** — Raised for unexpected characters during lexing.
- **ParseError** — Raised for malformed bracket expressions.
- **UnknownKeyError** — Raised for keys not in the known registry.
- **ValidationError** — Raised when semantic rules are violated.

## Testing

Related test files:
- `tests/dsl/test_lexer.py`
- `tests/dsl/test_parser.py`
- `tests/dsl/test_interpreter.py`
- `tests/dsl/test_validators.py`
- `tests/integration/test_prompt_flow_with_dsl.py`