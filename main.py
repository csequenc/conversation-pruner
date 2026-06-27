import os
from groq import Groq

client = Groq()
messages = []
backup = None

def show_history():
    if len(messages) == 0:
        print("No messages yet.")
        return
    print("\n--- Conversation History ---")
    for index, message in enumerate(messages):
        role = message["role"]
        content = message["content"]
        preview = content if len(content) <= 60 else content[:60] + "..."
        print(f"[{index}] {role}: {preview}")
    print("----------------------------")

def prune(indices_to_remove):
    global messages, backup

    for i in indices_to_remove:
        if i < 0 or i >= len(messages):
            print(f"Index {i} doesn't exist. No changes made.")
            return

    backup = messages.copy()

    for i in sorted(indices_to_remove, reverse=True):
        del messages[i]

    print(f"Removed {len(indices_to_remove)} message(s). Type /undo to reverse.")

def undo():
    global messages, backup
    if backup is None:
        print("Nothing to undo.")
        return
    messages = backup
    backup = None
    print("Undo successful. Last prune has been reversed.")

print("Chat started.")
print("Commands: /history | /prune 0 1 2 | /undo | quit")

while True:
    user_input = input("\nYou: ")

    if user_input.lower() == "quit":
        break

    if user_input.startswith("/"):

        if user_input.strip() == "/history":
            show_history()

        elif user_input.strip() == "/undo":
            undo()

        elif user_input.startswith("/prune"):
            parts = user_input.split()
            if len(parts) < 2:
                print("Usage: /prune 0 1 2  (specify at least one index)")
            else:
                try:
                    indices = [int(p) for p in parts[1:]]
                    prune(indices)
                except ValueError:
                    print("Invalid input. Use numbers only: /prune 0 1 2")

        else:
            print("Unknown command. Available: /history, /prune, /undo")

        continue

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )

    assistant_message = response.choices[0].message.content
    messages.append({"role": "assistant", "content": assistant_message})
    print(f"\nAssistant: {assistant_message}")
