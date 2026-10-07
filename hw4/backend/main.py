"""Campus Customs API: products, photos, accounts (with password hashing), and the shop chat agent.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic_ai.exceptions import UsageLimitExceeded

from agent import BLOCKED_REPLY, CHAT_LIMITS, MODEL_NAME, append_audit, is_blocked, now, run_chat, scrub, short
from models import AuthResponse, ChatReply, ChatRequest, ChatTurn, HistoryOut, LoginRequest, RegisterRequest, UserOut
from tools import (DB_PATH, PRODUCTS_DIR, all_products, clear_history, connect, customer_profile, ensure_schema,
                   load_history, page_context, product_info, save_exchange, saved_turns, stock_report)

# ---------- accounts: password hashing and login tokens ----------
# Passwords are stored only as salted PBKDF2-SHA256 hashes, in the same format as the data pack's
# seeded users: pbkdf2_sha256$<salt>$<hex digest>, 120,000 iterations. Login returns a signed token
# (user id + expiry, HMAC-SHA256) that the site sends back as "Authorization: Bearer <token>".

ITERATIONS = 120_000
TOKEN_TTL_S = 7 * 24 * 3600

# Set SESSION_SECRET in .env so logins survive a server restart; otherwise one is made per run.
_SECRET = (os.getenv("SESSION_SECRET") or secrets.token_hex(32)).encode()


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, digest = stored.split("$")
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return hmac.compare_digest(candidate, digest)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_token(user_id: int) -> str:
    payload = _b64(json.dumps({"uid": user_id, "exp": int(time.time()) + TOKEN_TTL_S}).encode())
    sig = _b64(hmac.new(_SECRET, payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}"


def read_token(token: str) -> int | None:
    """Return the user id in a valid, unexpired token, else None."""
    try:
        payload, sig = token.split(".")
        expected = _b64(hmac.new(_SECRET, payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return int(data["uid"]) if data["exp"] > time.time() else None
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


ensure_schema()
app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product photos live in data/products/; the catalogue stores "products/<file>.jpg".
# Only that folder is served, so the database file itself is never downloadable.
app.mount("/media/products", StaticFiles(directory=PRODUCTS_DIR), name="media")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "database": DB_PATH.exists(), "model": MODEL_NAME}


# ---------- products ----------

@app.get("/api/products")
def list_products() -> list[dict]:
    return all_products()


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    info = product_info(product_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Product not found")
    stock = stock_report(product_id)
    return {**info.model_dump(), "inventory": [s.model_dump() for s in stock.sizes],
            "total_stock": stock.total_in_stock}


# ---------- accounts ----------

def _user_out(row: sqlite3.Row) -> UserOut:
    return UserOut(id=row["id"], first_name=row["first_name"] or row["name"].split(" ")[0],
                   last_name=row["last_name"] or "", email=row["email"])


def current_user(authorization: str | None = Header(default=None)) -> UserOut | None:
    """The logged-in user from 'Authorization: Bearer <token>', or None for guests."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    user_id = read_token(authorization.removeprefix("Bearer ").strip())
    if user_id is None:
        return None
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _user_out(row) if row else None


@app.post("/api/auth/register", status_code=201)
def register(body: RegisterRequest) -> AuthResponse:
    email = body.email.strip().lower()
    first, last = body.first_name.strip(), body.last_name.strip()
    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", first, last, email, hash_password(body.password)),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    return AuthResponse(token=make_token(row["id"]), user=_user_out(row))


@app.post("/api/auth/login")
def login(body: LoginRequest) -> AuthResponse:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (body.email.strip().lower(),)).fetchone()
    # Same message for unknown email and wrong password, so emails can't be probed.
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    return AuthResponse(token=make_token(row["id"]), user=_user_out(row))


@app.get("/api/auth/me")
def me(user: UserOut | None = Depends(current_user)) -> UserOut:
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in.")
    return user


# ---------- chat ----------

@app.post("/api/chat")
async def chat(body: ChatRequest, user: UserOut | None = Depends(current_user)) -> ChatReply:
    run_id = uuid.uuid4().hex[:12]
    started = time.monotonic()
    customer = customer_profile(user.id) if user else None
    page = page_context(body.page, body.viewing)
    # Safety guard: card numbers, SSNs, and passwords never reach the model, the log, or the database.
    message, removed = scrub(body.message)
    # Logged in: the saved history in the database is the memory. Guest: only this browser tab's chat.
    history = load_history(user.id) if user else [ChatTurn(role=t.role, content=scrub(t.content)[0]) for t in body.history]
    base = {"run_id": run_id}
    events = [{**base, "time": now(), "event": "run_start", "customer": f"user {user.id}" if user else "guest",
               "page": page.path, "product_on_page": page.product_id, "message": short(message, 200),
               "history_turns": len(history)}]
    if removed:
        events.append({**base, "time": now(), "event": "guard_scrubbed", "removed": removed})

    reply, intent, tools, stop, tokens = None, "", [], "final answer", 0
    try:
        outcome = await run_chat(message, history, customer, page)
        reply, intent, tools, tokens = outcome.reply, outcome.intent, outcome.tools, outcome.tokens
        events += [{**base, **step} for step in outcome.audit]
        if outcome.price_retries:
            events.append({**base, "time": now(), "event": "guard_price_retry", "retries": outcome.price_retries})
    except UsageLimitExceeded as exc:
        stop = f"usage limit ({CHAT_LIMITS.request_limit} model calls / {CHAT_LIMITS.tool_calls_limit} tool calls): {exc}"
        reply = ChatReply(reply="Sorry, that one took me too many steps. Could you ask it a simpler way?")
    except Exception as exc:
        if is_blocked(exc):  # provider content filter: answer politely and keep the chat usable
            stop, intent = "blocked by content filter", "blocked by content filter"
            reply = ChatReply(reply=BLOCKED_REPLY, blocked=True)
        else:
            stop = f"error: {type(exc).__name__}: {short(str(exc), 200)}"
            events.append({**base, "time": now(), "event": "run_end", "stop_reason": stop,
                           "seconds": round(time.monotonic() - started, 2)})
            append_audit(events)
            print(f"chat error: {type(exc).__name__}: {exc}")
            raise HTTPException(status_code=502, detail="The shop assistant is unavailable right now. Please try again.")
    reply.removed = removed
    events.append({**base, "time": now(), "event": "run_end", "stop_reason": stop, "intent": intent,
                   "tools_used": [t.tool for t in tools], "products_shown": len(reply.products),
                   "tokens": tokens, "seconds": round(time.monotonic() - started, 2),
                   "saved_to_history": bool(user)})
    append_audit(events)
    if user:
        save_exchange(user.id, message, reply.reply, page, intent, tools, reply.products)
    return reply


@app.get("/api/chat/history")
def chat_history(user: UserOut | None = Depends(current_user)) -> HistoryOut:
    if user is None:
        raise HTTPException(status_code=401, detail="Log in to see saved chats.")
    return HistoryOut(turns=saved_turns(user.id))


@app.delete("/api/chat/history")
def delete_chat_history(user: UserOut | None = Depends(current_user)) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Log in to manage saved chats.")
    return {"deleted": clear_history(user.id)}
