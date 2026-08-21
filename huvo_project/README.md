# Northstar Homes sales bot

Text chatbot for **Northstar Homes / Project Northstar One** (Huvo FDE assignment). The scored artefact is the system prompt. FastAPI and a small tool loop exist to prove behaviour.

## What it does

- Talks in English, Hindi, or Hinglish by mirroring the customer
- Qualifies a lead (config, budget, timeline) and answers only known project facts
- Simulates site-visit booking, callbacks, opt-out, and human escalation
- Recovers when a booking fails (Sundays and past dates are rejected on purpose)
- Builds lead analytics when you end the conversation

Known facts only: Sector 79, Gurugram; 2 BHK from ₹1.35 crore; 3 BHK from ₹1.75 crore.

## How to run

From the project folder (after unzip, that is the folder that contains `README.md`):

1. Create a free API key at [console.groq.com](https://console.groq.com) → API Keys.
2. Copy the example env file and paste the key into **both** `GROQ_API_KEY` and `OPENAI_API_KEY`:

```bash
copy .env.example .env
```

3. Create a virtualenv, install packages, start the server:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On macOS/Linux use `source .venv/bin/activate` and `cp .env.example .env`.

4. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser. You should see the Northstar Homes chat.

The OpenAI Python SDK talks to Groq at `https://api.groq.com/openai/v1`. Default model: `openai/gpt-oss-120b`. For stronger Hindi, set `OPENAI_MODEL=qwen/qwen3.6-27b` in `.env`.

Tests (no API key needed):

```bash
pytest
```

## Prompt approach

One file, [`prompts/northstar_sales_agent.md`](prompts/northstar_sales_agent.md), used for chat and voice. FastAPI injects `CHANNEL=chat` (or `voice`). Replies are written to be speakable: short turns, one question, no markdown.

Side effects go through tools. The model is not allowed to invent a booking, a discount, or a possession date.

## How the agent is structured

`POST /chat` loads the prompt and session history, calls Groq with four tools, runs at most four tool rounds, and returns only the spoken reply.

Tools:

- `book_site_visit` — fails on Sunday or a past date so failure handling is demoable
- `schedule_callback`
- `opt_out`
- `escalate_to_human`

`POST /end` asks the same model for a JSON lead summary.

## Demo script

1. Hinglish: “2 BHK dekhna hai, budget 1.4 crore hai”
2. Ask for a **Sunday** visit (for example 23 Aug 2026) — booking should fail; the bot should offer another day
3. Book a weekday, or say “baad mein call karna”, or “mujhe call mat karo”
4. Click **End & analytics**

A written scenario pack with input / expected / actual is in [`tests/scenarios.md`](tests/scenarios.md).

## Assignment coverage

Part 1 — one system prompt ([`prompts/northstar_sales_agent.md`](prompts/northstar_sales_agent.md)) with `CHANNEL=chat|voice`:

- Natural conversation, qualification, English / Hindi / Hinglish
- Objections (price, location, browsing, competitor, think-about-it)
- Busy, call later, stop contact, unknown questions
- Site visit, booking failure, human escalation, clean endings

Part 2 — FastAPI text bot ([`app/main.py`](app/main.py), [`static/index.html`](static/index.html)):

- Chat + session memory, simulated booking (Sunday/past date fail), analytics on End
- Tests in `tests/` and the scenario pack above

## Key assumptions

- In-memory sessions only; restarting the server drops chats
- Site visits are simulated; nothing is sent to a CRM
- Starting prices are “onwards”, not unit-level quotes
- Groq free-tier rate limits apply (a turn with tools is several model calls)

## Known limitations

- No real calendar, WhatsApp, or phone channel
- No RAG; unknown questions must be refused
- Analytics quality depends on the model’s JSON mode
- Groq 429s: wait a moment and send again
- Hindi quality varies by model; switch `OPENAI_MODEL` if needed
