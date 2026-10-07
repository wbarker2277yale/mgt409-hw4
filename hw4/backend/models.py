"""Structured types shared by the API routes, the agent, and its tools."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# ---------- products ----------

class ProductCard(BaseModel):
    """What the website needs to draw one product card."""
    product_id: str
    name: str
    garment_type: str
    price: float
    image_url: str
    description: str


class StockLine(BaseModel):
    size: str
    quantity: int
    in_stock: bool


class ProductInfo(BaseModel):
    """Result of the product info tool: the facts a customer asks about, straight from the catalogue."""
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float
    image_url: str


class StockReport(BaseModel):
    """Result of the stock tool. Counts come from the inventory table, never estimated."""
    product_id: str
    name: str
    sizes: list[StockLine]
    total_in_stock: int
    sold_out_sizes: list[str]
    requested_size: str | None = None
    requested_size_quantity: int | None = Field(
        default=None, description="Units of the requested size; 0 means sold out."
    )
    note: str | None = None


class ProductMatch(BaseModel):
    """One hit from find_products: enough to pick the right product_id."""
    product_id: str
    name: str
    garment_type: str
    price: float


class SearchResult(BaseModel):
    """Result of find_products."""
    exact: bool = Field(description="False when nothing matched every word; matches are the closest ones.")
    total_matches: int
    showing: int
    understood_as: list[str] = Field(description="How each search word was read, with its alternatives.")
    matches: list[ProductMatch]


# ---------- chat ----------

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)
    page: str | None = Field(default=None, max_length=200, description="Website path the customer is on.")
    viewing: list[str] = Field(default_factory=list, max_length=40,
                               description="product_ids of the cards on screen, if any.")


class AgentAnswer(BaseModel):
    """What the agent must return each turn: its message, the products to show, and why the shopper asked."""
    reply: str = Field(description="The message to the customer, in the shop's voice.")
    intent: str = Field(
        default="", max_length=120,
        description="The shopper's goal this turn in a few words, e.g. 'find a navy hoodie in M under $70'.",
    )
    product_ids: list[str] = Field(
        default_factory=list, max_length=40,
        description="product_ids (from tool results) to show as cards on the website, best first. "
                    "Empty when no products should be shown.",
    )


class ChatReply(BaseModel):
    """What /api/chat sends the website. Cards are rebuilt from the database, never from the model's text."""
    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    blocked: bool = Field(default=False, description="The message was refused by the content filter; "
                                                      "the website leaves it out of later history.")
    removed: list[str] = Field(default_factory=list, description="Sensitive data scrubbed from the message.")


# ---------- accounts ----------

class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class CategorySummary(BaseModel):
    """One garment type we carry, from list_categories."""
    garment_type: str
    product_count: int
    min_price: float
    max_price: float


# ---------- customer memory ----------

class CustomerProfile(BaseModel):
    """What the agent knows about a logged-in shopper. No password hash, ever."""
    id: int
    first_name: str
    last_name: str
    email: str
    member_since: str
    past_messages: int
    first_chat: str | None = None


class PageContext(BaseModel):
    """Where the shopper is when they send a message."""
    path: str
    kind: str
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None
    cards_on_screen: list[str] = Field(default_factory=list)


class ToolUse(BaseModel):
    tool: str
    args: dict


class SavedTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: str
    page: str | None = None
    products: list[ProductCard] = Field(default_factory=list)


class HistoryOut(BaseModel):
    turns: list[SavedTurn]
