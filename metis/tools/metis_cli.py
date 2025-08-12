import argparse
from metis.handler import RequestHandler
from metis.memory.manager import MemoryManager
from metis.conversation_engine import ConversationEngine
from metis.dsl import interpret_prompt_dsl

# Optional memory manager to demonstrate snapshot/restore
memory = MemoryManager()
engine = ConversationEngine()
handler = RequestHandler()  # Allow injecting engine manually if needed

def main():
    # Set up the CLI parser with subcommands
    parser = argparse.ArgumentParser(description="Metis CLI - Chat or Prompt Generation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Chat Subcommand ---
    # This mode runs the full conversation engine with memory and snapshots
    chat_parser = subparsers.add_parser("chat", help="Run chat prompt with snapshot support")
    chat_parser.add_argument("--user", type=str, default="user_123", help="User ID")
    chat_parser.add_argument("--prompt", type=str, required=True, help="Prompt to send to the engine")
    chat_parser.add_argument("--save", action="store_true", help="Save a snapshot before prompt")
    chat_parser.add_argument("--undo", action="store_true", help="Restore last saved snapshot")

    # --- Prompt Subcommand ---
    # This mode directly renders a structured prompt from builder/template
    prompt_parser = subparsers.add_parser("prompt", help="Generate a structured prompt directly")
    prompt_parser.add_argument("--type", required=True, help="Prompt type: summarize, plan, clarify, critique")
    prompt_parser.add_argument("--input", required=True, help="User input or query")
    prompt_parser.add_argument("--context", default="", help="Optional memory or background context")
    prompt_parser.add_argument("--tool_output", default="", help="Optional tool-generated output")
    prompt_parser.add_argument("--tone", default="", help="Tone to apply to the assistant")
    prompt_parser.add_argument("--persona", default="", help="Persona for assistant behavior")
    prompt_parser.add_argument("--dsl", default="", help="Optional DSL [key: value] blocks to merge into the prompt")

    # --- DSL Subcommand ---
    dsl_parser = subparsers.add_parser("dsl", help="Interpret prompt DSL blocks")
    dsl_parser.add_argument("--input", required=True, help="DSL text to interpret, e.g. [persona: Analyst][task: Summarize]")

    args = parser.parse_args()

    if args.command == "chat":
        # Run full chat engine pipeline
        user_id = args.user
        prompt = args.prompt

        # Optionally save a snapshot of the conversation state
        if args.save:
            snapshot = engine.create_snapshot()
            memory.save(snapshot)

        # Optionally restore from last saved snapshot
        if args.undo:
            snapshot = memory.restore_last()
            if snapshot:
                engine.restore_snapshot(snapshot)
                print("✅ Previous snapshot restored.")
            else:
                print("⚠️  No snapshot found to restore.")

        # Handle the prompt using the main engine
        response = handler.handle_prompt(user_id, prompt)
        print("\nResponse:")
        print(response)

    elif args.command == "dsl":
        # Interpret DSL and print context as JSON
        import json
        ctx = interpret_prompt_dsl(args.input)
        print(json.dumps(ctx))

    elif args.command == "prompt":
        # Generate a standalone structured prompt using Builder/Template

        # If a DSL string was provided, merge its fields into the explicit args
        if args.dsl:
            ctx = interpret_prompt_dsl(args.dsl)
            # Map persona/tone directly
            if ctx.get("persona"):
                args.persona = ctx["persona"]
            if ctx.get("tone"):
                args.tone = ctx["tone"]
            # Try to map DSL task into our --type if compatible
            task_map = {
                "summarize": "summarize",
                "summary": "summarize",
                "translate": "clarify",   # choose closest supported type
                "plan": "plan",
                "planning": "plan",
                "critique": "critique",
            }
            if ctx.get("task"):
                dsl_task = ctx["task"].strip().lower()
                if dsl_task in task_map:
                    args.type = task_map[dsl_task]
            # Append remaining fields into context so templates can render them
            extras = []
            if ctx.get("source"):
                extras.append(f"Source: {ctx['source']}")
            if ctx.get("length"):
                extras.append(f"Length: {ctx['length']}")
            if ctx.get("format"):
                extras.append(f"Format: {ctx['format']}")
            if extras:
                args.context = (args.context + ("\n" if args.context else "") + "\n".join(extras)).strip()

        from metis.services.prompt_service import render_prompt

        try:
            result = render_prompt(
                prompt_type=args.type,
                user_input=args.input,
                context=args.context,
                tool_output=args.tool_output,
                tone=args.tone,
                persona=args.persona
            )
            print("\nGenerated Prompt:\n")
            print(result)
        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()