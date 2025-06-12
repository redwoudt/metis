import argparse
from metis.handler import RequestHandler
from metis.memory.manager import MemoryManager
from metis.conversation_engine import ConversationEngine

# Optional memory manager to demonstrate snapshot/restore
memory = MemoryManager()
engine = ConversationEngine()
handler = RequestHandler()  # Allow injecting engine manually if needed

def main():
    parser = argparse.ArgumentParser(description="Metis GenAI CLI with Snapshot Support")
    parser.add_argument("--user", type=str, default="user_123", help="User ID")
    parser.add_argument("--prompt", type=str, required=True, help="Prompt to send")
    parser.add_argument("--save", action="store_true", help="Save a snapshot before prompt")
    parser.add_argument("--undo", action="store_true", help="Restore last saved snapshot")

    args = parser.parse_args()
    user_id = args.user
    prompt = args.prompt

    # Optional snapshot save
    if args.save:
        snapshot = engine.create_snapshot()
        memory.save(snapshot)

    # Optional snapshot restore
    if args.undo:
        engine.restore_snapshot(memory.restore_last())

    # Handle prompt
    response = handler.handle_prompt(user_id, prompt)

    print("\nResponse:")
    print(response)


if __name__ == "__main__":
    main()