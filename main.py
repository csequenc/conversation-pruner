import os
from groq import Groq
from datetime import datetime

client = Groq()
messages = []
backup = None

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def minutes_since(time_str):
    # Useful for displaying how long ago a message was sent in /history
    past = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    diff = datetime.now() - past
    return diff.total_seconds() / 60

def gap_between(time_str1, time_str2):
    # Calculates minutes between two message timestamps
    t1 = datetime.strptime(time_str1, "%Y-%m-%d %H:%M")
    t2 = datetime.strptime(time_str2, "%Y-%m-%d %H:%M")
    return (t2 - t1).total_seconds() / 60

def format_gap(minutes):
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} and {mins} minute{'s' if mins != 1 else ''}"
    return f"{mins} minute{'s' if mins != 1 else ''}"

def build_api_messages():
    cleaned = []
    for i, msg in enumerate(messages):
        if i > 0 and msg["role"] == "user":
            gap_minutes = gap_between(messages[i-1]["time"], msg["time"])
            if gap_minutes >= 180:
                gap_text = format_gap(gap_minutes)
                cleaned.append({
                    "role": "system",
                    "content": f"Note: {gap_text} passed since the last message. The user's context or mental state may have shifted."
                })
        cleaned.append({"role": msg["role"], "content": msg["content"]})
    return cleaned

def show_history():
    if len(messages) == 0:
        print("No messages yet.")
        return
    print("\n--- Conversation History ---")
    for index, message in enumerate(messages):
        role = message["role"]
        content = message["content"]
        time = message["time"]
        preview = content if len(content) <= 60 else content[:60] + "..."
        print(f"[{index}] {time} | {role}: {preview}")
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

    messages.append({"role": "user", "content": user_input, "time": get_time()})
    api_messages = build_api_messages()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=api_messages
    )

    assistant_message = response.choices[0].message.content
    messages.append({"role": "assistant", "content": assistant_message, "time": get_time()})
    print(f"\nAssistant: {assistant_message}")
