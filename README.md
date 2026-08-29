# Personal Productivity Agent

A FastAPI-based agent that helps a small business owner check sales,
monitor inventory, and get product performance insights — powered by
Gemini (via the OpenAI SDK's compatibility endpoint) with tool calling.

## Project structure

```
productivity_agent/
├── app/
│   ├── main.py           FastAPI app — /chat, /health, /reset, and a static test widget
│   ├── agent.py           The agent loop: calls Gemini, executes tool calls
│   ├── tools.py           Actual tool implementations (SQLite queries)
│   ├── tool_schemas.py    OpenAI-format schemas describing each tool to the model
│   ├── session.py         In-memory per-user conversation history
│   └── static/index.html  Zero-dependency browser chat widget
├── data/
│   ├── generate_data.py   Synthetic sales + inventory data generator
│   └── shop.db            Generated SQLite database (already included)
├── test_client.py         CLI chat client for quick manual testing
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## 1. Setup

```bash
cd productivity_agent
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your Gemini API key (get one free at https://aistudio.google.com/apikey)
```

`data/shop.db` is already generated and committed, so you can start testing
immediately. If you want fresh/different synthetic data:
```bash
python data/generate_data.py
```

## 2. Run it

```bash
export $(cat .env | xargs)   # loads GEMINI_API_KEY into the shell (or use python-dotenv in code)
uvicorn app.main:app --reload
```

The API is now live at `http://localhost:8000`.

## 3. Testing it — as if you were the business owner

You have three ways to test, from quickest to most realistic:

### A. Browser widget (fastest, no setup)
Open `http://localhost:8000` in a browser. Type questions directly.

### B. CLI client (closest to a real chat feel)
```bash
python test_client.py
```

### C. Raw curl (useful for debugging what the API actually returns)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "owner_1", "message": "What were my sales this week?"}'
```

### Suggested test script — run through these in order

This exercises every part of the agent, not just the happy path:

1. **Basic read query** — "What was my total revenue in the last 7 days?"
   → Should call `get_sales_summary` and answer with real numbers, not vague text.

2. **Low stock check** — "Which products are running low?"
   → Should surface Canvas Backpack and Wireless Earbuds specifically (they're seeded low).

3. **Follow-up using conversation memory** — after the above, ask "What about wireless earbuds specifically?"
   → Should understand "wireless earbuds" refers to the item just discussed and call `get_product_details`, without you repeating context.

4. **Top performers** — "What are my best sellers this month?"

5. **The write-confirmation flow** — "Update the earbuds stock to 40, we just got a delivery."
   → The agent should NOT silently update. It should describe the change and ask you to confirm.
   Reply "yes, go ahead" and confirm it actually updates (`get_product_details` again to verify).

6. **Ambiguous / underspecified request** — "How's business?"
   → See whether it asks a clarifying question or makes a reasonable assumption (e.g. defaults to last 30 days) rather than failing silently.

7. **Out-of-scope request** — "Can you file my taxes?"
   → It should say plainly that it can't do this, not hallucinate an answer.

8. **Reset and re-test** — `python test_client.py` then type `reset`, or `POST /reset` — confirms session isolation works and old context doesn't leak.

If all eight behave as described, the core loop, tool calling, memory, and
the write-safety pattern are all working — that's the actual bar for "this
agent is usable," not just "the API returns 200."

### Things to watch for while testing
- **Wrong tool chosen** — if the model calls `get_top_selling_products` when you asked about stock, your tool descriptions in `tool_schemas.py` are probably too similar; tighten the wording.
- **Silent write** — if `update_stock_level` changes data without asking, check that your system prompt's confirmation instruction is intact and that the model isn't defaulting `confirm` to `true`.
- **429 rate limit errors** — the Gemini free tier has real per-minute/per-day caps; if you hit these while testing rapidly, wait a minute or switch `AGENT_MODEL` to `gemini-2.5-flash-lite` in `.env`.
- **Numbers that don't match `data/shop.db`** — if the model states figures without matching a tool call in your terminal logs, it's answering from guesswork, not the data — tighten the system prompt's "never invent numbers" line or check the tool actually got called.

## 4. Deploying to Cloud Run

```bash
gcloud secrets create gemini-key --data-file=<(echo -n "YOUR_KEY_HERE")

gcloud run deploy productivity-agent \
  --source . \
  --region asia-south1 \
  --set-secrets GEMINI_API_KEY=gemini-key:latest \
  --allow-unauthenticated=false
```

`--allow-unauthenticated=false` is deliberate — this endpoint calls a
billed API and has a write-capable tool, so it shouldn't be open to the
public internet without at least an API key check in front of it.

## 5. Known limitations / natural next steps

- Session memory is in-process only — restarts and multi-instance scaling lose history. Swap `app/session.py` for Firestore before treating this as production.
- No auth on `/chat` yet — add an API key header check or Cloud Run IAM before deploying publicly.
- Data lives in a local SQLite file baked into the container — fine for a demo, but a real deployment should point `tools.py` at Cloud SQL or the Google Sheets API where the owner's real data actually lives.
- No proactive daily digest yet — wire Cloud Scheduler to hit a new `/digest` endpoint that runs a fixed set of tool calls and pushes the result via Telegram/email.
