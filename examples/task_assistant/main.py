from __future__ import annotations

from dotenv import load_dotenv

from bounded.agent import Thread
from bounded.observability import configure_logging
from task_assistant.agent import build_agent


def main() -> None:
    load_dotenv()
    configure_logging()

    agent = build_agent()
    thread: Thread | None = None

    print("Task assistant. Type a message, or 'quit' to exit.")
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            break

        thread = agent.run(user_input, thread=thread)
        print(thread.final_answer)


if __name__ == "__main__":
    main()
