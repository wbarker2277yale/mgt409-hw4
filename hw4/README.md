# Campus Customs Shop + Chatbot — Homework 4

A Yale apparel storefront (React + Vite + TypeScript) with a shop assistant, "the clerk": a
PydanticAI agent behind FastAPI that answers from the real catalogue and stock in
`campus_customs.db`. MGT 409 AI Foundations for Managers, Homework 4.

## Layout

```
hw4/
├── AI_prompts.md          # every prompt used, in my own words
├── requirements.txt       # backend Python packages
├── .env.example           # placeholder settings; copy to .env
├── .gitignore             # keeps .env, data/, the database, and images out of git
├── README.md
├── frontend/              # Vite React TypeScript app
├── backend/
│   ├── main.py            # FastAPI app — run with: uvicorn main:app --reload --port 8000
│   ├── agent.py           # the agent: model, prompt, context, safety guard, audit trail
│   ├── models.py          # Pydantic types for tools, chat, accounts, memory
│   ├── tools.py           # database access, the agent's 5 read-only tools, customer memory
│   └── prompts/
│       └── prompt.md      # system prompt: voice, tool use, safety rules
└── output/
    ├── harness.md         # how the whole system works
    ├── design.md          # the look, and why it should help customers buy
    ├── usability.md       # 2 front-end + 2 backend improvements
    ├── app_check.html     # screenshots of the live site (double-click to open)
    ├── app_check_images/
    └── audit_trail.json   # append-only log of agent-loop activity
```

**Local-only data pack (not in git).** Put it in `hw4/data/`:

```
data/
├── campus_customs.db
└── products/              # images referenced by the catalogue
```

## Run it

1. **Settings.** Copy `.env.example` to `.env` and fill in `PORTKEY_API_KEY` and any long random
   `SESSION_SECRET`. The backend also finds a `.env` in a parent folder.
2. **Backend** (port 8000):
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   cd backend
   ../.venv/bin/uvicorn main:app --reload --port 8000
   ```
3. **Frontend** (port 5173), in a second terminal:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Open http://localhost:5173. Test login: `test@campuscustoms.yale.edu` / `password`.

If those ports are taken: `PORT=5174 BACKEND_URL=http://127.0.0.1:8001 npm run dev`, with the
backend on `--port 8001`.

## How the two ends work together

The frontend (bow) and backend (stern) talk only over JSON on `/api`.

```
 Browser (React, port 5173)                      FastAPI (port 8000)                   SQLite + model
 ─────────────────────────                       ───────────────────                   ──────────────
 Catalogue, item pages  ── GET /api/products ──▶  main.py routes ──────────────────▶   campus_customs.db
 Product photos         ── GET /media/products/…▶ (photos folder only)                 data/products/
 Log in / Create acct   ── POST /api/auth/… ───▶  hash + check password, sign token ─▶ users
 The clerk (chat)       ── POST /api/chat ─────▶  guard → agent.py → tools.py ───────▶ catalogue, inventory
     message, page,         Authorization:            │  model: gpt-6-astra via Portkey
     cards on screen        Bearer <token>            ▼
                         ◀── reply + product cards ── AgentAnswer → cards rebuilt from DB
                                                       │ audit_trail.json (append) · chat_messages (logged in)
```

1. **Same-origin proxy.** The browser only ever calls its own address. Vite's dev server forwards
   `/api` and `/media` to FastAPI (`frontend/vite.config.ts`), so there is no CORS and no backend
   URL in the page.
2. **Products.**
   - The website loads the catalogue once from `GET /api/products` and filters it in the browser (department, size in stock, sort, keyword).
   - Item pages call `GET /api/products/{id}` for stock by size.
   - Photos come from `/media/products/…`. Only that folder is served, never the database.
3. **Accounts.**
   - `POST /api/auth/register` and `/login` return a signed token.
   - The website keeps the token in the browser and sends it as `Authorization: Bearer …`.
   - `GET /api/auth/me` restores the session on reload.
4. **Chat.** The clerk sends `POST /api/chat` with the message, the page path, and the cards on
   screen. The backend then:
   - scrubs card numbers, SSNs, and passwords;
   - loads the shopper's saved history (if logged in) and the product on the page;
   - runs the agent. The agent calls read-only tools and returns `{reply, intent, product_ids}`.
   - turns each id into a `ProductCard` from the database, checks every quoted price against the tools' results, logs each step to `output/audit_trail.json`, and saves the turn for logged-in shoppers.
   - returns `{reply, products}`.

   Several products open the Products page as cards. Clicking a card opens its item page.
5. **Memory.** On login, the clerk calls `GET /api/chat/history` to reload the conversation.
   `DELETE` clears it.

Full details: `output/harness.md`.

## Security

- `.env` (keys), `data/`, `campus_customs.db`, and the store's product images are in `.gitignore`
  and never committed. Only `.env.example`, with placeholders, is in git.
- Passwords are stored as salted PBKDF2-SHA256 hashes.
- The database file can't be downloaded through the site.
