"""Data access and the shop agent's tools, all over campus_customs.db.

- Paths and the database connection (and two schema additions for customer memory).
- Plain catalogue/stock queries, shared by the website's product routes.
- The five agent tools: find_products, get_product_info, check_stock, suggest_alternatives,
  list_categories. Every tool is read-only, so the agent never guesses a price, a
  description, or a stock count, and can't change anything.
- Customer memory: saved chat history for logged-in shoppers, and page context for every chat.
"""

import difflib
import json
import os
import re
import sqlite3
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import RunContext

from models import (
    CategorySummary,
    ChatTurn,
    CustomerProfile,
    PageContext,
    ProductCard,
    ProductInfo,
    ProductMatch,
    SavedTurn,
    SearchResult,
    StockLine,
    StockReport,
    ToolUse,
)


# ---------- paths and database ----------

BACKEND = Path(__file__).resolve().parent
ROOT = BACKEND.parent

# Closest .env wins: hw4/.env, then Homework 4/.env, then AI Foundations/.env.
for folder in reversed([ROOT, *ROOT.parents][:3]):
    load_dotenv(folder / ".env", override=True)

DATA_DIR = Path(os.getenv("DATA_DIR") or ROOT / "data")
if not DATA_DIR.is_absolute():
    DATA_DIR = ROOT / DATA_DIR
DB_PATH = DATA_DIR / "campus_customs.db"
PRODUCTS_DIR = DATA_DIR / "products"

# Customer memory records what a shopper did (content, products), when (created_at),
# where (page), why (intent), and how (tools). The data pack's chat_messages table has the
# first parts; these columns add the rest. Added on startup if missing, so a fresh data pack works.
CHAT_COLUMNS = {"page": "TEXT", "product_id": "TEXT", "intent": "TEXT", "tools_json": "TEXT"}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema() -> None:
    with connect() as conn:
        have = {r["name"] for r in conn.execute("PRAGMA table_info(chat_messages)")}
        for name, kind in CHAT_COLUMNS.items():
            if name not in have:
                conn.execute(f"ALTER TABLE chat_messages ADD COLUMN {name} {kind}")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id, id)")


# ---------- shop queries and agent tools ----------

SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
SIZE_ORDER = "CASE size " + " ".join(f"WHEN '{s}' THEN {i}" for i, s in enumerate(SIZES)) + " ELSE 9 END"
SIZE_WORDS = {"xs": "XS", "extra small": "XS", "s": "S", "small": "S", "m": "M", "medium": "M",
              "l": "L", "large": "L", "xl": "XL", "extra large": "XL", "xxl": "XXL", "2xl": "XXL"}
STOP_WORDS = {"a", "an", "the", "do", "you", "have", "any", "in", "of", "for", "with", "and", "or",
              "me", "show", "i", "want", "looking", "some", "is", "are", "there", "what", "your"}


@dataclass
class ShopDeps:
    """Per-chat context passed to the agent's instructions and every tool."""
    customer: CustomerProfile | None = None
    page: PageContext | None = None
    user_message: str = ""
    seen_prices: set[float] = field(default_factory=set)  # every price a tool returned this turn
    price_retries: int = 0


# ---------- plain queries (shared with main.py) ----------

def _card(row: sqlite3.Row) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"], name=row["name"], garment_type=row["garment_type"],
        price=row["price"], image_url=f"/media/{row['image_file_path']}", description=row["description"],
    )


def _info(row: sqlite3.Row) -> ProductInfo:
    return ProductInfo(
        product_id=row["product_id"], name=row["name"], garment_type=row["garment_type"],
        description=row["description"], colors=json.loads(row["colors"]), price=row["price"],
        image_url=f"/media/{row['image_file_path']}",
    )


def normalize_size(size: str | None) -> str | None:
    if not size:
        return None
    s = size.strip().lower()
    return SIZE_WORDS.get(s, size.strip().upper())


def all_products() -> list[dict]:
    """Every product with its total stock and the sizes that are in stock (for the website's filters)."""
    with connect() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        inv = conn.execute(f"SELECT product_id, size, quantity FROM inventory ORDER BY {SIZE_ORDER}").fetchall()
    stock: dict[str, int] = {}
    sizes: dict[str, list[str]] = {}
    for i in inv:
        stock[i["product_id"]] = stock.get(i["product_id"], 0) + i["quantity"]
        if i["quantity"] > 0:
            sizes.setdefault(i["product_id"], []).append(i["size"])
    return [{**_info(r).model_dump(), "total_stock": stock.get(r["product_id"], 0),
             "sizes_in_stock": sizes.get(r["product_id"], [])} for r in rows]


def product_info(product_id: str) -> ProductInfo | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    return _info(row) if row else None


def product_card(product_id: str) -> ProductCard | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    return _card(row) if row else None


def stock_report(product_id: str, size: str | None = None) -> StockReport | None:
    with connect() as conn:
        name = conn.execute("SELECT name FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if name is None:
            return None
        rows = conn.execute(
            f"SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY {SIZE_ORDER}", (product_id,)
        ).fetchall()
    lines = [StockLine(size=r["size"], quantity=r["quantity"], in_stock=r["quantity"] > 0) for r in rows]
    report = StockReport(
        product_id=product_id, name=name["name"], sizes=lines,
        total_in_stock=sum(l.quantity for l in lines),
        sold_out_sizes=[l.size for l in lines if not l.in_stock],
    )
    wanted = normalize_size(size)
    if wanted:
        report.requested_size = wanted
        match = next((l for l in lines if l.size == wanted), None)
        if match is None:
            report.note = f"{wanted} is not a size we carry for this item. Sizes: {', '.join(l.size for l in lines)}."
        else:
            report.requested_size_quantity = match.quantity
            if match.quantity == 0:
                report.note = f"{wanted} is sold out."
    return report


# Shop vocabulary: words shoppers use -> how the catalogue says it (any alternative may match).
SYNONYMS = {
    # Yale rowing gear says "YALE CREW"; plain "crew" would also catch crew-neck shirts.
    "row": ["rowing", "yale crew", "crew left chest"], "rowing": ["rowing", "yale crew", "crew left chest"],
    "rower": ["rowing", "yale crew", "crew left chest"],
    "tee": ["t shirt", "t-shirt", "tee"], "tshirt": ["t shirt", "t-shirt"], "shirt": ["shirt", "tee"],
    "quarter": ["1 4 zip", "quarter-zip", "quarter zip"], "quarterzip": ["1 4 zip", "quarter-zip"],
    "sweatshirt": ["sweatshirt", "crewneck", "hoodie"], "sweater": ["sweatshirt", "crewneck", "sweater"],
    "hoody": ["hoodie", "hooded"], "hoodie": ["hoodie", "hooded"], "crewneck": ["crewneck", "crew neck", "creqneck"],
    "jacket": ["jacket", "fleece", "bomber"], "coat": ["jacket", "fleece", "bomber"],
    "fleece": ["fleece"], "zip": ["zip"], "bulldog": ["bulldog", "handsome dan"],
    "law": ["law school"], "med": ["medicine", "medical"], "medical": ["medicine", "medical"],
    "nurse": ["nursing"], "engineer": ["engineering"], "grey": ["gray", "grey", "heather"],
    "gray": ["gray", "grey", "heather"], "blue": ["blue", "navy"], "football": ["football", "the game"],
}
FILLER = STOP_WORDS | {"gift", "gifts", "dad", "mom", "father", "mother", "brother", "sister", "friend",
                       "my", "who", "under", "over", "below", "above", "something", "stuff", "thing",
                       "things", "got", "need", "like", "would", "please", "anything", "item", "items",
                       "clothes", "apparel", "merch", "cheap", "nice", "good", "can", "get", "buy", "find",
                       "size", "sizes", "stock", "available", "color", "colors", "kind", "type", "sort",
                       "xs", "s", "m", "l", "xl", "xxl", "small", "medium", "large", "extra", "price", "dollars"}


@lru_cache(maxsize=1)
def _vocabulary() -> tuple[str, ...]:
    with connect() as conn:
        rows = conn.execute("SELECT name, garment_type, colors, search_tags FROM catalogue").fetchall()
    words = set()
    for r in rows:
        words.update(re.findall(r"[a-z]+", " ".join(r).lower()))
    return tuple(sorted(w for w in words if len(w) > 2))


def _interpret(query: str) -> list[list[str]]:
    """Turn the shopper's words into groups of alternatives the catalogue might use."""
    q = query.lower().replace("1/4", " quarter ").replace("t-shirt", "tshirt").replace("t shirt", "tshirt")
    groups = []
    for w in re.findall(r"[a-z0-9]+", q):
        if w in FILLER or w.isdigit():
            continue
        if w not in SYNONYMS and len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]  # hoodies -> hoodie, rows -> row
        if w in SYNONYMS:
            groups.append(SYNONYMS[w])
            continue
        vocab = _vocabulary()
        if w not in vocab and len(w) >= 4:  # typo: hoddie -> hoodie, crewnek -> crewneck
            close = difflib.get_close_matches(w, list(vocab) + list(SYNONYMS), n=1, cutoff=0.78)
            if close:
                w = close[0]
                groups.append(SYNONYMS.get(w, [w]))
                continue
        groups.append([w])
    return groups


def _has(text: str, phrase: str) -> bool:
    return re.search(r"\b" + re.escape(phrase) + r"(s|es)?\b", text) is not None


def search_products(query: str = "", max_price: float | None = None, min_price: float | None = None,
                    size_in_stock: str | None = None, limit: int = 40) -> SearchResult:
    """Rank catalogue rows by how many of the shopper's words (or their shop-vocabulary
    alternatives) appear in the name, type, colors, tags, or description."""
    groups = _interpret(query)
    size = normalize_size(size_in_stock)
    sql = "SELECT c.* FROM catalogue c WHERE 1=1"
    params: list = []
    if max_price is not None:
        sql += " AND c.price <= ?"; params.append(max_price)
    if min_price is not None:
        sql += " AND c.price >= ?"; params.append(min_price)
    if size:
        sql += " AND EXISTS (SELECT 1 FROM inventory i WHERE i.product_id = c.product_id AND i.size = ? AND i.quantity > 0)"
        params.append(size)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    exact, partial = [], []
    for r in rows:
        name = r["name"].lower()
        text = " ".join([name, r["garment_type"], r["colors"], r["search_tags"], r["description"]]).lower()
        hits = [g for g in groups if any(_has(text, alt) for alt in g)]
        score = sum((3 if any(_has(name, a) for a in g) else 1) for g in hits)
        if len(hits) == len(groups):
            exact.append((score, r))
        elif hits:
            partial.append((len(hits), score, r))
    if exact or not groups:
        ranked = [r for _, r in sorted(exact, key=lambda t: (-t[0], t[1]["name"]))]
        is_exact = True
    else:  # nothing matched every word: closest matches, most words matched first
        ranked = [r for *_, r in sorted(partial, key=lambda t: (-t[0], -t[1], t[2]["name"]))]
        is_exact = False
    matches = [ProductMatch(product_id=r["product_id"], name=r["name"], garment_type=r["garment_type"],
                            price=r["price"]) for r in ranked[:limit]]
    return SearchResult(exact=is_exact, total_matches=len(ranked), showing=len(matches),
                        understood_as=[" / ".join(g) for g in groups], matches=matches)


def category_summary() -> list[CategorySummary]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT lower(garment_type) AS t, COUNT(*) AS n, MIN(price) AS lo, MAX(price) AS hi
               FROM catalogue GROUP BY lower(garment_type) ORDER BY n DESC"""
        ).fetchall()
    return [CategorySummary(garment_type=r["t"], product_count=r["n"], min_price=r["lo"], max_price=r["hi"])
            for r in rows]


# ---------- agent tools ----------

def find_products(ctx: RunContext[ShopDeps], query: str = "", max_price: float | None = None,
                  min_price: float | None = None, size_in_stock: str | None = None) -> SearchResult:
    """Search the catalogue by the shopper's words (sport, color, style, garment, team, school),
    optionally within a price range and only items with a given size in stock. Understands shop
    vocabulary (rowing = crew, tee = t-shirt, 1/4 zip) and typos. Use it to answer 'what X do you
    have?' and to get a product_id whenever the shopper names or describes an item.
    exact=false means nothing matched every word and these are the closest matches; say so.
    total_matches is the full count even when fewer are shown."""
    result = search_products(query, max_price, min_price, size_in_stock)
    ctx.deps.seen_prices.update(m.price for m in result.matches)
    return result


def get_product_info(ctx: RunContext[ShopDeps], product_id: str) -> ProductInfo | str:
    """Get the real description, colors, and price of one product by product_id."""
    info = product_info(product_id)
    if info is None:
        return f"No product with id '{product_id}'. Use find_products to look it up."
    ctx.deps.seen_prices.add(info.price)
    return info


def check_stock(ctx: RunContext[ShopDeps], product_id: str, size: str | None = None) -> StockReport | str:
    """Get how many units are in stock for one product, size by size. Pass size (XS, S, M, L, XL, XXL)
    when the customer asks about one size; requested_size_quantity of 0 means that size is sold out."""
    report = stock_report(product_id, size)
    if report is None:
        return f"No product with id '{product_id}'. Use find_products to look it up."
    return report


def suggest_alternatives(ctx: RunContext[ShopDeps], product_id: str, size: str) -> list[ProductMatch] | str:
    """When an item is sold out in the customer's size, find up to 5 items of the same garment type
    that do have that size in stock, closest in price first."""
    info = product_info(product_id)
    wanted = normalize_size(size)
    if info is None or wanted is None:
        return f"No product with id '{product_id}'."
    with connect() as conn:
        rows = conn.execute(
            """SELECT c.product_id, c.name, c.garment_type, c.price FROM catalogue c
               JOIN inventory i ON i.product_id = c.product_id
               WHERE lower(c.garment_type) = lower(?) AND c.product_id != ? AND i.size = ? AND i.quantity > 0
               ORDER BY ABS(c.price - ?), c.name LIMIT 5""",
            (info.garment_type, product_id, wanted, info.price),
        ).fetchall()
    matches = [ProductMatch(**dict(r)) for r in rows]
    ctx.deps.seen_prices.update(m.price for m in matches)
    return matches


def list_categories(ctx: RunContext[ShopDeps]) -> list[CategorySummary]:
    """List the kinds of garments we carry, how many products of each, and their price range.
    Use for broad questions like 'what do you sell?' or 'what's your cheapest sweatshirt?'."""
    summary = category_summary()
    ctx.deps.seen_prices.update(p for c in summary for p in (c.min_price, c.max_price))
    return summary


SHOP_TOOLS = [find_products, get_product_info, check_stock, suggest_alternatives, list_categories]


# ---------- customer memory ----------
# Guests can chat, but nothing they say is stored. For a logged-in shopper, each turn is saved
# to chat_messages with when, where (page and product), why (the agent's one-line intent),
# what (message and products shown), and which tools the agent used.

HISTORY_TURNS = 20  # how many saved turns the agent sees on each new message
PRODUCT_PAGE = re.compile(r"^/products/([a-z0-9-]{1,120})/?$")
KNOWN_PAGES = {"/": "home page", "/products": "products page", "/about": "About Us page",
               "/login": "log in page", "/create-account": "create account page"}


def customer_profile(user_id: int) -> CustomerProfile | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return None
        stats = conn.execute(
            "SELECT COUNT(*) AS n, MIN(created_at) AS first FROM chat_messages WHERE user_id = ? AND role = 'user'",
            (user_id,),
        ).fetchone()
    return CustomerProfile(
        id=row["id"], first_name=row["first_name"] or row["name"].split(" ")[0],
        last_name=row["last_name"] or "", email=row["email"], member_since=row["created_at"][:10],
        past_messages=stats["n"], first_chat=stats["first"][:10] if stats["first"] else None,
    )


def page_context(path: str | None, viewing: list[str] | None = None) -> PageContext:
    """Work out where the shopper is from the site path. Only known page shapes are trusted;
    the product on a product page is looked up in the catalogue, never taken from the browser's text."""
    path = (path or "").split("?")[0][:200]
    ctx = PageContext(path=path or "/", kind="other page")
    if path in KNOWN_PAGES:
        ctx.kind = KNOWN_PAGES[path]
    elif m := PRODUCT_PAGE.match(path):
        with connect() as conn:
            row = conn.execute("SELECT product_id, name, price FROM catalogue WHERE product_id = ?",
                               (m.group(1),)).fetchone()
        if row:
            ctx.kind = "product page"
            ctx.product_id, ctx.product_name, ctx.product_price = row["product_id"], row["name"], row["price"]
    if viewing:
        with connect() as conn:
            q = ",".join("?" * len(viewing[:40]))
            ctx.cards_on_screen = [r["name"] for r in conn.execute(
                f"SELECT name FROM catalogue WHERE product_id IN ({q})", viewing[:40])]
    return ctx


def load_history(user_id: int, limit: int = HISTORY_TURNS) -> list[ChatTurn]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT role, content FROM chat_messages
               WHERE user_id = ? AND (intent IS NULL OR intent NOT LIKE 'blocked%')
               ORDER BY id DESC LIMIT ?""", (user_id, limit)
        ).fetchall()
    return [ChatTurn(role=r["role"], content=r["content"]) for r in reversed(rows)]


def saved_turns(user_id: int, limit: int = 50) -> list[SavedTurn]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
    turns = []
    for r in reversed(rows):
        products = []
        for p in json.loads(r["products_json"] or "[]"):
            try:
                products.append(ProductCard.model_validate(p))
            except ValueError:
                pass
        turns.append(SavedTurn(role=r["role"], content=r["content"], created_at=r["created_at"],
                               page=r["page"], products=products))
    return turns


def save_exchange(user_id: int, message: str, reply: str, page: PageContext, intent: str,
                  tools: list[ToolUse], products: list[ProductCard]) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, page, product_id, intent) VALUES (?, 'user', ?, ?, ?, ?)",
            (user_id, message, page.path, page.product_id, intent),
        )
        conn.execute(
            """INSERT INTO chat_messages (user_id, role, content, products_json, page, product_id, intent, tools_json)
               VALUES (?, 'assistant', ?, ?, ?, ?, ?, ?)""",
            (user_id, reply, json.dumps([p.model_dump() for p in products]) if products else None,
             page.path, page.product_id, intent, json.dumps([t.model_dump() for t in tools])),
        )


def clear_history(user_id: int) -> int:
    with connect() as conn:
        return conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount
