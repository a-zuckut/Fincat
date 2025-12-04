from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class Stock(BaseModel):
    symbol: str
    name: str
    price: float
    notes: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    stocks: List[Stock]


app = FastAPI(title="Fincat Demo API")


# In-memory store for demo purposes only
_STOCKS: dict[str, Stock] = {}


@app.get("/stocks", response_model=List[Stock])
async def list_stocks() -> List[Stock]:
    """Return the current list of stocks."""
    return list(_STOCKS.values())


@app.post("/stocks", response_model=Stock)
async def add_stock(stock: Stock) -> Stock:
    """Add a stock to the in-memory list."""
    key = stock.symbol.upper()
    if key in _STOCKS:
        raise HTTPException(status_code=400, detail="Stock already exists")
    _STOCKS[key] = stock
    return stock


@app.put("/stocks/{symbol}", response_model=Stock)
async def update_stock(symbol: str, stock: Stock) -> Stock:
    """Update an existing stock by symbol."""
    key = symbol.upper()
    if key not in _STOCKS:
        raise HTTPException(status_code=404, detail="Stock not found")
    # Keep symbol from the path canonical
    updated = stock.copy(update={"symbol": key})
    _STOCKS[key] = updated
    return updated


@app.delete("/stocks/{symbol}")
async def delete_stock(symbol: str) -> dict:
    """Remove a stock by symbol."""
    key = symbol.upper()
    if key not in _STOCKS:
        raise HTTPException(status_code=404, detail="Stock not found")
    del _STOCKS[key]
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Very simple rule-based chatbot to manipulate the stock list.

    This is intentionally minimal; you can later wire this up to a real LLM.
    Supported commands (case-insensitive):
      - "add SYMBOL NAME PRICE" e.g. "add AAPL Apple 195.3"
      - "remove SYMBOL" e.g. "remove AAPL"
      - "update SYMBOL PRICE" e.g. "update AAPL 200.0"
      - "list" to list all stocks
    """

    text = request.message.strip()
    lower = text.lower()

    if lower == "list":
        reply = f"You currently have {len(_STOCKS)} stock(s)."
        return ChatResponse(reply=reply, stocks=list(_STOCKS.values()))

    parts = text.split()
    if not parts:
        return ChatResponse(reply="Please type a command like 'add AAPL Apple 195.3' or 'list'.", stocks=list(_STOCKS.values()))

    cmd = parts[0].lower()

    if cmd == "add" and len(parts) >= 4:
        symbol = parts[1].upper()
        try:
            price = float(parts[-1])
        except ValueError:
            return ChatResponse(reply="Could not parse price. Use something like 'add AAPL Apple 195.3'", stocks=list(_STOCKS.values()))

        name = " ".join(parts[2:-1])
        stock = Stock(symbol=symbol, name=name, price=price)
        _STOCKS[symbol] = stock
        return ChatResponse(reply=f"Added {symbol} ({name}) at {price}.", stocks=list(_STOCKS.values()))

    if cmd == "remove" and len(parts) == 2:
        symbol = parts[1].upper()
        if symbol not in _STOCKS:
            return ChatResponse(reply=f"{symbol} is not in your list.", stocks=list(_STOCKS.values()))
        del _STOCKS[symbol]
        return ChatResponse(reply=f"Removed {symbol}.", stocks=list(_STOCKS.values()))

    if cmd == "update" and len(parts) == 3:
        symbol = parts[1].upper()
        if symbol not in _STOCKS:
            return ChatResponse(reply=f"{symbol} is not in your list.", stocks=list(_STOCKS.values()))
        try:
            price = float(parts[2])
        except ValueError:
            return ChatResponse(reply="Could not parse price. Use something like 'update AAPL 200.0'", stocks=list(_STOCKS.values()))

        existing = _STOCKS[symbol]
        updated = existing.copy(update={"price": price})
        _STOCKS[symbol] = updated
        return ChatResponse(reply=f"Updated {symbol} to {price}.", stocks=list(_STOCKS.values()))

    help_text = (
        "I support: 'list', 'add SYMBOL NAME PRICE', 'remove SYMBOL', "
        "and 'update SYMBOL PRICE'."
    )
    return ChatResponse(reply=help_text, stocks=list(_STOCKS.values()))
