"""The Campus Customs shop agent: one PydanticAI agent, its model, and how a chat turn runs.

- The system prompt is read from prompts/prompt.md; a live "Right now" block (who is chatting,
  which page and product they're on) is added by code on every turn.
- The model is gpt-6-astra, reached through Portkey with PORTKEY_API_KEY from .env.
- The tools come from tools.py and read real data from campus_customs.db.
- Safety guard: sensitive-data scrubbing, content-filter recovery, and a price fact-check.
- Audit trail: every loop step is appended to output/audit_trail.json, never wiped.
"""

import json
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.messages import (ModelMessage, ModelRequest, ModelResponse, TextPart, ToolCallPart,
                                  ToolReturnPart, UserPromptPart)
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from models import AgentAnswer, ChatReply, ChatTurn, CustomerProfile, PageContext, ToolUse
from tools import BACKEND, ROOT, SHOP_TOOLS, ShopDeps, product_card

MODEL_NAME = "gpt-6-astra"
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1").rstrip("/")
PROMPT_PATH = BACKEND / "prompts" / "prompt.md"

# One customer message may take several tool calls, but never an open-ended loop.
CHAT_LIMITS = UsageLimits(request_limit=8, tool_calls_limit=12)


# ---------- safety guard ----------
# 1. scrub() removes card numbers, SSNs, and passwords before the model or database sees them.
# 2. is_blocked() recognises the model provider's content-filter refusal, so the chat can recover.
# 3. check_prices() finds dollar amounts in a reply that no tool (or the shopper) supplied.

CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
PASSWORD = re.compile(r"\b(password|passcode|passwd|pwd|pin)\b(\s*(is|:|=)\s*|\s+)\S+", re.IGNORECASE)
PRICE = re.compile(r"\$\s?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)")

BLOCKED_REPLY = ("I can only help with Campus Customs products, sizes, prices, and stock. "
                 "What can I help you find today?")


def _luhn(digits: str) -> bool:
    total, alt = 0, False
    for d in reversed(digits):
        n = int(d)
        if alt:
            n = n * 2 - 9 if n > 4 else n * 2
        total, alt = total + n, not alt
    return total % 10 == 0


def scrub(text: str) -> tuple[str, list[str]]:
    """Return the text with sensitive data replaced, and what was removed (labels only)."""
    removed: list[str] = []

    def card(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn(digits):
            removed.append("card number")
            return "[card number removed]"
        return m.group()

    text = CARD.sub(card, text)
    if SSN.search(text):
        removed.append("SSN")
        text = SSN.sub("[SSN removed]", text)
    if PASSWORD.search(text):
        removed.append("password")
        text = PASSWORD.sub(lambda m: f"{m.group(1)} [removed]", text)
    return text, removed


def is_blocked(exc: Exception) -> bool:
    return "content_filter" in str(exc) or "content management policy" in str(exc)


def prices_in(text: str) -> set[float]:
    return {float(m.replace(",", "")) for m in PRICE.findall(text)}


def check_prices(reply: str, allowed: set[float]) -> list[float]:
    """Dollar amounts in the reply that don't match any allowed price (to the cent)."""
    return sorted(p for p in prices_in(reply) if not any(abs(p - a) < 0.005 for a in allowed))


# ---------- audit trail ----------
# output/audit_trail.json is one JSON array. New events are appended in place (the closing "]"
# is overwritten and re-added), so earlier events are never rewritten or wiped.

AUDIT_PATH = ROOT / "output" / "audit_trail.json"
PREVIEW_CHARS = 300  # tool results are shortened to this
_lock = threading.Lock()


def short(value, limit: int = PREVIEW_CHARS) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= limit else text[:limit] + f"… (+{len(text) - limit} chars)"


def append_audit(events: list[dict]) -> None:
    if not events:
        return
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size < 2:
            AUDIT_PATH.write_text("[\n]\n", encoding="utf-8")
        body = ",\n".join(json.dumps(e, ensure_ascii=False, default=str) for e in events)
        with open(AUDIT_PATH, "r+b") as f:
            f.seek(0, os.SEEK_END)
            end = f.tell()
            # Find the final "]" and write the new events just before it.
            f.seek(max(0, end - 64))
            tail = f.read()
            close = tail.rfind(b"]")
            pos = end - len(tail) + close
            f.seek(0)
            empty = f.read(pos).strip() == b"["
            f.seek(pos)
            f.truncate()
            f.write(((body if empty else ",\n" + body) + "\n]\n").encode("utf-8"))


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ---------- the agent ----------

def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def build_model() -> OpenAIResponsesModel:
    key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is not set. Add it to .env in hw4/ or a parent folder.")
    client = AsyncOpenAI(api_key=key, base_url=PORTKEY_BASE_URL,
                         default_headers={"x-portkey-api-key": key}, timeout=60, max_retries=1)
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def describe_context(deps: ShopDeps) -> str:
    """The live context block added to the instructions on every turn: who is chatting and where they are."""
    lines = ["## Right now"]
    c = deps.customer
    if c:
        lines.append(
            f"- Customer: {c.first_name} {c.last_name} ({c.email}), logged in, member since {c.member_since}. "
            f"Use their first name naturally. Their earlier chats with the shop are in the history"
            f" ({c.past_messages} past messages)."
        )
    else:
        lines.append("- Customer: a guest (not logged in). You don't know their name; nothing they say is saved. "
                     "If they want the shop to remember them, they can create an account.")
    p = deps.page
    if p and p.product_id:
        lines.append(
            f"- Page: the product page for **{p.product_name}** (product_id `{p.product_id}`, ${p.product_price:.2f}). "
            "When they say \"this\", \"it\", or \"this one\" without naming an item, they mean this product."
        )
    elif p:
        lines.append(f"- Page: the {p.kind} ({p.path}).")
    if p and p.cards_on_screen:
        shown = ", ".join(p.cards_on_screen[:12]) + (" …" if len(p.cards_on_screen) > 12 else "")
        lines.append(f"- Cards on screen ({len(p.cards_on_screen)}): {shown}. \"These\" or \"the second one\" refer to them.")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def build_agent() -> Agent[ShopDeps, AgentAnswer]:
    agent = Agent(
        build_model(),
        deps_type=ShopDeps,
        output_type=AgentAnswer,
        instructions=load_prompt(),
        tools=SHOP_TOOLS,
        retries=2,  # a failed price check or bad tool call may be retried twice
    )

    @agent.instructions
    def right_now(ctx: RunContext[ShopDeps]) -> str:
        return describe_context(ctx.deps)

    @agent.output_validator
    def prices_must_be_real(ctx: RunContext[ShopDeps], answer: AgentAnswer) -> AgentAnswer:
        """Price fact-check: every $ amount must be a price a tool returned this turn, the price of
        the product on screen, or a number the shopper said themselves."""
        allowed = set(ctx.deps.seen_prices) | prices_in(ctx.deps.user_message)
        if ctx.deps.page and ctx.deps.page.product_price is not None:
            allowed.add(ctx.deps.page.product_price)
        bad = check_prices(answer.reply, allowed)
        if bad:
            ctx.deps.price_retries += 1
            raise ModelRetry(
                f"Your reply states {', '.join(f'${b:.2f}' for b in bad)}, but no tool returned that price "
                "this turn. Look the price up with a tool, or remove it. Never estimate or add up prices."
            )
        return answer

    return agent


def to_messages(history: list[ChatTurn]) -> list[ModelMessage]:
    """Turn the chat so far (from the website) into PydanticAI message history."""
    messages: list[ModelMessage] = []
    for turn in history:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


@dataclass
class ChatOutcome:
    reply: ChatReply
    intent: str = ""
    tools: list[ToolUse] = field(default_factory=list)
    audit: list[dict] = field(default_factory=list)  # loop steps for the audit trail
    stop_reason: str = "final answer"
    price_retries: int = 0
    tokens: int = 0


def loop_steps(messages: list[ModelMessage]) -> list[dict]:
    """One audit event per tool call and tool result, in the order the loop ran them."""
    steps = []
    for msg in messages:
        for part in msg.parts:
            if isinstance(part, ToolCallPart) and part.tool_name != "final_result":
                when = getattr(msg, "timestamp", None)
                steps.append({"time": when.isoformat(timespec="milliseconds") if when else now(),
                              "event": "tool_call", "tool": part.tool_name, "args": part.args_as_dict()})
            elif isinstance(part, ToolReturnPart) and part.tool_name != "final_result":
                steps.append({"time": part.timestamp.isoformat(timespec="milliseconds"), "event": "tool_result",
                              "tool": part.tool_name, "result": short(part.model_response_str())})
    return steps


async def run_chat(message: str, history: list[ChatTurn], customer: CustomerProfile | None,
                   page: PageContext) -> ChatOutcome:
    """Run one turn of the agent loop and report what happened."""
    deps = ShopDeps(customer=customer, page=page, user_message=message)
    result = await build_agent().run(
        message, deps=deps, message_history=to_messages(history), usage_limits=CHAT_LIMITS,
    )
    answer = result.output
    new = result.new_messages()
    # Each product_id becomes a card built from the catalogue; unknown ids are dropped.
    cards = [c for pid in dict.fromkeys(answer.product_ids) if (c := product_card(pid))]
    tools = [ToolUse(tool=part.tool_name, args=part.args_as_dict())
             for msg in new if isinstance(msg, ModelResponse)
             for part in msg.parts if isinstance(part, ToolCallPart) and part.tool_name != "final_result"]
    return ChatOutcome(reply=ChatReply(reply=answer.reply, products=cards), intent=answer.intent, tools=tools,
                       audit=loop_steps(new), price_retries=deps.price_retries,
                       tokens=result.usage.total_tokens or 0)
