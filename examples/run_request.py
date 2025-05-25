# --- examples/run_request.py ---
import argparse
from metis.handler import RequestHandler


def main():
    parser = argparse.ArgumentParser(description="Metis GenAI CLI")
    parser.add_argument("--user", type=str, default="user_123", help="User ID")
    parser.add_argument("--prompt", type=str, required=True, help="Prompt to send")

    args = parser.parse_args()
    user_id = args.user
    prompt = args.prompt

    handler = RequestHandler()
    response = handler.handle_prompt(user_id, prompt)

    print("\nResponse:")
    print(response)


if __name__ == "__main__":
    main()
