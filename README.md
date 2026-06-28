# Conversation Pruner

A CLI chatbot built with Python and the Groq API that lets users explicitly remove specific messages from the conversation history — so the model permanently loses access to that context in all future responses.

---

## The Problem

LLMs don't have an option to remove a particular context from their memory list, which creates a problem when you want to delete something sent in an unstable state that has now taken significant importance in the model's responses.
Large language models have no memory between API calls. To simulate a continuous conversation, every message — both user and assistant — gets stored in a list and re-sent to the model on every call. The model reads that entire list each time and responds as if it has been in the conversation the whole time.

This design works well in stable conversations. But it creates a real problem in longer sessions:

- A user might be in a poor mental state when they send certain messages
- A conversation might go in a wrong or unproductive direction for a few exchanges
- Some context, once introduced, keeps influencing the model's tone and responses for the rest of the session — even if the user has mentally moved on

There was no built-in way to selectively remove those moments. You could start a fresh conversation, but that meant losing all the good context too. The only options were all-or-nothing.

---

## The Solution

Since the conversation history is just a Python list, individual messages can be deleted from it. Once deleted, those messages are gone from the model's context — it will never reference them again, because they are never sent to the API again.

This project builds a simple CLI interface that lets users:

- **View** the full conversation history with numbered indices
- **Prune** specific messages by index — removing them permanently from the model's context
- **Undo** the last prune if the removal was a mistake

The core insight is simple: the model only knows what you send it. Edit the list, and you edit its memory.

---

## Implementation

The conversation history is stored as a Python list of dictionaries:

```python
messages = [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
]
```

Every user message is appended to this list before the API call. Every assistant response is appended after. The full list is sent on every call.

Pruning works by deleting items from this list by index. To avoid index-shift bugs (where deleting item 2 causes item 3 to become item 2, making subsequent deletions hit the wrong message), indices are always sorted highest to lowest and deleted in that order.

An undo system saves a copy of the list before any prune using `list.copy()`. If the user undoes, the saved copy replaces the current list. Only one level of undo is supported.

Commands are intercepted before the API call using a simple `startswith("/")` check. Command inputs never reach the model.

---

## The Time Problem

After building the core pruning system, a second problem became clear.

Even when no messages are manually pruned, the model treats the entire conversation history as one continuous, uninterrupted session. It has no awareness of time passing. If you started a conversation in the morning, went through a difficult few hours, came back the next evening in a completely different headspace and continued — the model has no idea. It picks up exactly where it left off, responding in the same tone, carrying the same assumptions, treating your current messages as if they follow naturally from hours or days ago.

This matters because mental state is not static. A user who was anxious at 11pm and is now calm at 10am the next morning is not the same user in the same context. But the model will respond as if they are.

The question was: what counts as a significant enough gap to be worth flagging?

A few minutes between messages is normal — the user is just thinking. Half an hour is still a single session. But once several hours have passed, there is a reasonable chance the user's context has shifted — they slept, their mood changed, something happened in their life. The model should know that continuity cannot be assumed.

Three hours was chosen as the threshold. It is long enough to filter out natural pauses in conversation, but short enough to catch anything that crosses into a genuinely different time block — an afternoon versus an evening, a night versus a morning.

The implementation works by storing a timestamp on every message when it is appended. Before each API call, the code checks the gap between the previous message's timestamp and the current time. If the gap is 3 hours or more, a system message is injected into the context sent to the model:

```
Note: 4 hours and 12 minutes passed since the last message. The user's context or mental state may have shifted.
```

This system message is never stored in the permanent history — it is built fresh for each API call. The model receives it as background information, not as something the user said. It cannot act on it directly, but it signals that the model should not assume full continuity with what came before.

The timestamps are also displayed in `/history`, so the user can see exactly when each message was sent and make more informed decisions about what to prune.

---

## Setup

**1. Install the Groq library**
```
pip install groq
```

**2. Get a free API key**

Sign up at [console.groq.com](https://console.groq.com) and generate an API key. It's free.

**3. Set your API key as an environment variable**

On Mac/Linux:
```
export GROQ_API_KEY="your_key_here"
```

On Windows:
```
set GROQ_API_KEY=your_key_here
```

On Google Colab:
```python
import os
os.environ["GROQ_API_KEY"] = "your_key_here"
```

**4. Run the script**
```
python main.py
```

---

## Usage

```
Chat started.
Commands: /history | /prune 0 1 2 | /undo | quit
```

| Command | What it does |
|---|---|
| `/history` | Show all messages with index numbers |
| `/prune 2 3 4` | Remove messages at index 2, 3, and 4 |
| `/undo` | Restore the list to before the last prune |
| `quit` | Exit the chat |

---

## Example

```
You: My name is csequenc
Assistant: Nice to meet you, csequenc!

You: Remember the number 2026, only tell me when I say "What is the secret"
Assistant: Got it. I'll only reveal 2026 when you say that exact phrase.

You: What is the secret
Assistant: The secret is: 2026

You: /history
[0] user: My name is csequenc
[1] assistant: Nice to meet you, csequenc!
[2] user: Remember the number 2026, only tell me when I say "What is th...
[3] assistant: Got it. I'll only reveal 2026 when you say that exact phrase.
[4] user: What is the secret
[5] assistant: The secret is: 2026

You: /prune 2 3 4 5
Removed 4 message(s). Type /undo to reverse.

You: What is the secret
Assistant: I'm not sure what secret you're referring to. Could you give me more context?
```

The model has no memory of the number. The context is gone.

---
