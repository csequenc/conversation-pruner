# Conversation Pruner

A CLI chatbot built with Python and the Groq API that lets users explicitly remove specific messages from the conversation history — so the model permanently loses access to that context in all future responses.

---

## The Problem

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

## Planned Features

- Timestamps on each message, shown in `/history`
- Automatic system message inserted when more than 3 hours pass between messages, to signal a possible change in user context
