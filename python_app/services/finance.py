"""Finance domain logic: expenses, budgets, goals, watchlist, analytics, insights."""
import uuid
from datetime import datetime, timezone, timedelta
from calendar import monthrange
from services.db import db
import yfinance as yf


def _now():
    return datetime.now(timezone.utc)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ---------- Expenses ----------
def add_expense(user_id, amount, category, note, etype="expense", date=None, receipt_url=None):
    if isinstance(date, datetime):
        date_iso = date.isoformat()
    else:
        date_iso = date or _now().isoformat()
    doc = {
        "id": _id("exp"), "user_id": user_id, "amount": float(amount),
        "category": category, "note": note or "",
        "date": date_iso, "type": etype, "receipt_url": receipt_url,
        "created_at": _now().isoformat(),
    }
    db.expenses.insert_one(doc)
    doc.pop("_id", None)
    return doc


def list_expenses(user_id, limit=500):
    return list(db.expenses.find({"user_id": user_id}, {"_id": 0}).sort("date", -1).limit(limit))


def update_expense(user_id, exp_id, **fields):
    db.expenses.update_one({"id": exp_id, "user_id": user_id}, {"$set": fields})


def delete_expense(user_id, exp_id):
    db.expenses.delete_one({"id": exp_id, "user_id": user_id})


# ---------- Budgets ----------
def get_budget(user_id):
    b = db.budgets.find_one({"user_id": user_id}, {"_id": 0})
    if not b:
        b = {"user_id": user_id, "global_limit": 20000.0, "categories": {}}
        db.budgets.insert_one(b)
    return b


def update_budget(user_id, global_limit, categories):
    db.budgets.update_one(
        {"user_id": user_id},
        {"$set": {"global_limit": float(global_limit),
                  "categories": {k: float(v) for k, v in categories.items()}}},
        upsert=True,
    )


# ---------- Goals ----------
def add_goal(user_id, name, target_amount, target_date, saved_amount=0):
    doc = {
        "id": _id("goal"), "user_id": user_id, "name": name,
        "target_amount": float(target_amount), "target_date": target_date,
        "saved_amount": float(saved_amount or 0),
        "created_at": _now().isoformat(),
    }
    db.goals.insert_one(doc); doc.pop("_id", None)
    return doc


def list_goals(user_id):
    return list(db.goals.find({"user_id": user_id}, {"_id": 0}))


def update_goal(user_id, goal_id, **fields):
    db.goals.update_one({"id": goal_id, "user_id": user_id}, {"$set": fields})


def delete_goal(user_id, goal_id):
    db.goals.delete_one({"id": goal_id, "user_id": user_id})


# ---------- Stocks ----------
INDIAN_TICKER_ALIASES = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "SBIN": "SBIN.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "ITC": "ITC.NS",
    "LT": "LT.NS",
}

NSE_TOP_30 = [
    "RELIANCE.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS", "INFY.NS",
    "TCS.NS", "LT.NS", "ITC.NS", "AXISBANK.NS", "SBIN.NS",
    "M&M.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "HINDUNILVR.NS", "HCLTECH.NS",
    "SUNPHARMA.NS", "MARUTI.NS", "NTPC.NS", "BEL.NS", "TMPV.NS",
    "ULTRACEMCO.NS", "TITAN.NS", "POWERGRID.NS", "TRENT.NS", "ASIANPAINT.NS",
    "BAJAJFINSV.NS", "ADANIPORTS.NS", "ADANIENT.NS", "ONGC.NS", "COALINDIA.NS",
]

BSE_SENSEX_30 = [
    "ADANIPORTS.BO", "ASIANPAINT.BO", "AXISBANK.BO", "BAJFINANCE.BO", "BAJAJFINSV.BO",
    "BEL.BO", "BHARTIARTL.BO", "ETERNAL.BO", "HCLTECH.BO", "HDFCBANK.BO",
    "HINDUNILVR.BO", "ICICIBANK.BO", "INFY.BO", "ITC.BO", "KOTAKBANK.BO",
    "LT.BO", "M&M.BO", "MARUTI.BO", "NTPC.BO", "POWERGRID.BO",
    "RELIANCE.BO", "SBIN.BO", "SUNPHARMA.BO", "TMPV.BO", "TATASTEEL.BO",
    "TCS.BO", "TECHM.BO", "TITAN.BO", "TRENT.BO", "ULTRACEMCO.BO",
]

MARKET_LISTS = {
    "NSE Top 30": NSE_TOP_30,
    "BSE Sensex 30": BSE_SENSEX_30,
}

STOCK_NAMES = {
    "ADANIENT": "Adani Enterprises",
    "ADANIPORTS": "Adani Ports & SEZ",
    "ASIANPAINT": "Asian Paints",
    "AXISBANK": "Axis Bank",
    "BAJAJFINSV": "Bajaj Finserv",
    "BAJFINANCE": "Bajaj Finance",
    "BEL": "Bharat Electronics",
    "BHARTIARTL": "Bharti Airtel",
    "COALINDIA": "Coal India",
    "ETERNAL": "Eternal",
    "HCLTECH": "HCLTech",
    "HDFCBANK": "HDFC Bank",
    "HINDUNILVR": "Hindustan Unilever",
    "ICICIBANK": "ICICI Bank",
    "INFY": "Infosys",
    "ITC": "ITC",
    "KOTAKBANK": "Kotak Mahindra Bank",
    "LT": "Larsen & Toubro",
    "M&M": "Mahindra & Mahindra",
    "MARUTI": "Maruti Suzuki",
    "NTPC": "NTPC",
    "ONGC": "ONGC",
    "POWERGRID": "Power Grid Corporation",
    "RELIANCE": "Reliance Industries",
    "SBIN": "State Bank of India",
    "SUNPHARMA": "Sun Pharma",
    "TMPV": "Tata Motors Passenger Vehicles",
    "TATASTEEL": "Tata Steel",
    "TCS": "Tata Consultancy Services",
    "TECHM": "Tech Mahindra",
    "TITAN": "Titan Company",
    "TRENT": "Trent",
    "ULTRACEMCO": "UltraTech Cement",
}


def _normalize_symbol(symbol):
    s = (symbol or "").strip().upper()
    return INDIAN_TICKER_ALIASES.get(s, s)


def _display_symbol(symbol):
    s = (symbol or "").strip().upper()
    if s.endswith(".NS") or s.endswith(".BO"):
        return s[:-3]
    return s


def _exchange(symbol):
    if symbol.endswith(".NS"):
        return "NSE"
    if symbol.endswith(".BO"):
        return "BSE"
    return "US"


def _fallback_name(symbol):
    return STOCK_NAMES.get(_display_symbol(symbol), symbol)


def quote(symbol):
    ticker_symbol = _normalize_symbol(symbol)
    if not ticker_symbol:
        return None

    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="2d", interval="1m")
        if hist.empty:
            hist = ticker.history(period="5d")
        if hist.empty:
            return None

        price = float(hist["Close"].dropna().iloc[-1])
        previous = float(hist["Close"].dropna().iloc[0])
        change_pct = ((price - previous) / previous * 100) if previous else 0

        info = {}
        try:
            info = ticker.get_info()
        except Exception:
            info = {}

        return {
            "symbol": _display_symbol(ticker_symbol),
            "ticker": ticker_symbol,
            "name": info.get("shortName") or info.get("longName") or ticker_symbol,
            "exchange": info.get("exchange") or ("NSE" if ticker_symbol.endswith(".NS") else "US"),
            "price": round(price, 2),
            "change_pct": round(change_pct, 2),
        }
    except Exception:
        return None


def history(symbol, days=30):
    ticker_symbol = _normalize_symbol(symbol)
    try:
        hist = yf.Ticker(ticker_symbol).history(period=f"{int(days)}d")
        if hist.empty:
            return []
        return [
            {"date": idx.strftime("%Y-%m-%d"), "price": round(float(row["Close"]), 2)}
            for idx, row in hist.iterrows()
            if not pd_is_nan(row["Close"])
        ]
    except Exception:
        return []


def pd_is_nan(value):
    return value != value


def search_stocks(q):
    q = (q or "").strip().upper()
    if not q:
        return []

    symbols = [q]
    normalized = _normalize_symbol(q)
    if normalized != q:
        symbols.append(normalized)

    result = []
    seen = set()
    for symbol in symbols:
        if symbol in seen:
            continue
        seen.add(symbol)
        qu = quote(symbol)
        if qu:
            result.append(qu)
    return result


def market_quotes(list_name):
    symbols = MARKET_LISTS.get(list_name, [])
    rows = []
    if not symbols:
        return rows

    try:
        data = yf.download(
            " ".join(symbols),
            period="5d",
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )
    except Exception:
        data = None

    for symbol in symbols:
        try:
            if data is None or data.empty:
                qu = quote(symbol)
                if qu:
                    rows.append(qu)
                continue

            if len(symbols) == 1:
                close = data["Close"].dropna()
            else:
                close = data[symbol]["Close"].dropna()

            if close.empty:
                continue

            price = float(close.iloc[-1])
            previous = float(close.iloc[0])
            change_pct = ((price - previous) / previous * 100) if previous else 0
            rows.append({
                "symbol": _display_symbol(symbol),
                "ticker": symbol,
                "name": _fallback_name(symbol),
                "exchange": _exchange(symbol),
                "price": round(price, 2),
                "change_pct": round(change_pct, 2),
            })
        except Exception:
            continue
    return rows


def watchlist_get(user_id):
    items = list(db.watchlists.find({"user_id": user_id}, {"_id": 0}))
    result = []
    for it in items:
        q = quote(it.get("ticker") or it["symbol"])
        if q: result.append(q)
    return result


def watchlist_add(user_id, symbol):
    ticker_symbol = _normalize_symbol(symbol)
    q = quote(ticker_symbol)
    if not q:
        return False

    db.watchlists.update_one(
        {"user_id": user_id, "ticker": q["ticker"]},
        {"$set": {
            "user_id": user_id,
            "symbol": q["symbol"],
            "ticker": q["ticker"],
            "name": q["name"],
            "added_at": _now().isoformat(),
        }},
        upsert=True,
    )
    return True


def watchlist_remove(user_id, symbol):
    ticker_symbol = _normalize_symbol(symbol)
    db.watchlists.delete_one({
        "user_id": user_id,
        "$or": [{"symbol": symbol.upper()}, {"ticker": ticker_symbol}],
    })


# ---------- Analytics ----------
def summary(user_id):
    exps = list_expenses(user_id, limit=2000)
    goals = list_goals(user_id)
    budget = get_budget(user_id)

    income = sum(e["amount"] for e in exps if e.get("type") == "income")
    expenses = sum(e["amount"] for e in exps if e.get("type") != "income")
    savings = sum(g.get("saved_amount", 0) for g in goals)
    balance = income - expenses
    savings_rate = (income - expenses) / income if income > 0 else 0
    health = max(0, min(100, int(40 + savings_rate * 60)))

    today = _now().strftime("%Y-%m-%d")
    week_start = (_now() - timedelta(days=7)).strftime("%Y-%m-%d")
    month_key = _now().strftime("%Y-%m")
    today_spend = sum(e["amount"] for e in exps if e.get("type") != "income" and e["date"][:10] == today)
    week_spend = sum(e["amount"] for e in exps if e.get("type") != "income" and e["date"][:10] >= week_start)
    month_spend = sum(e["amount"] for e in exps if e.get("type") != "income" and e["date"][:7] == month_key)
    return {
        "balance": balance, "income": income, "expenses": expenses, "savings": savings,
        "health": health, "today": today_spend, "week": week_spend, "month": month_spend,
        "budget_limit": budget.get("global_limit", 0),
        "budget_remaining": max(0, (budget.get("global_limit") or 0) - month_spend),
    }


def insights(user_id):
    exps = list_expenses(user_id, limit=2000)
    goals = list_goals(user_id)
    budget = get_budget(user_id)
    items = []
    month_key = _now().strftime("%Y-%m")
    prev_month = (_now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    cur_by_cat, prev_by_cat, cur_total = {}, {}, 0
    for e in exps:
        if e.get("type") == "income": continue
        m = e["date"][:7]
        if m == month_key:
            cur_by_cat[e["category"]] = cur_by_cat.get(e["category"], 0) + e["amount"]
            cur_total += e["amount"]
        elif m == prev_month:
            prev_by_cat[e["category"]] = prev_by_cat.get(e["category"], 0) + e["amount"]

    g_lim = budget.get("global_limit") or 0
    if g_lim > 0:
        used = cur_total / g_lim * 100
        if used >= 90:
            items.append(("danger", "Critical: Budget nearly exhausted",
                          f"You've used {used:.0f}% of your ₹{g_lim:.0f} monthly budget."))
        elif used >= 70:
            items.append(("warning", "Heads up: budget usage high",
                          f"You've used {used:.0f}% of your monthly budget."))

    for cat, lim in (budget.get("categories") or {}).items():
        sp = cur_by_cat.get(cat, 0)
        if lim > 0 and sp / lim >= 0.7:
            level = "danger" if sp / lim >= 0.9 else "warning"
            items.append((level, f"{cat} at {sp/lim*100:.0f}% of budget",
                          f"You're approaching your {cat} limit."))

    for cat, amt in cur_by_cat.items():
        prev = prev_by_cat.get(cat, 0)
        if prev > 0:
            change = (amt - prev) / prev * 100
            if change >= 15:
                items.append(("info", f"{cat} spending up {change:.0f}%",
                              f"{cat} expenses are up vs last month."))

    if cur_by_cat:
        top = max(cur_by_cat.items(), key=lambda x: x[1])
        items.append(("info", f"Top category: {top[0]}",
                      f"You've spent ₹{top[1]:.0f} on {top[0]} this month."))

    dom = _now().day
    if dom >= 5 and g_lim > 0 and cur_total > 0:
        daily = cur_total / dom
        dim = monthrange(_now().year, _now().month)[1]
        projected = daily * dim
        if projected > g_lim:
            days_left = max(0, int((g_lim - cur_total) / daily))
            items.append(("danger", "Overspending predicted",
                          f"At this pace you may exceed your budget in {days_left} days. Projected: ₹{projected:.0f}"))

    for g in goals:
        pct = (g.get("saved_amount", 0) / g["target_amount"] * 100) if g["target_amount"] else 0
        if pct >= 100:
            items.append(("success", f"Goal achieved: {g['name']}", "You reached 100% of this goal."))
        elif pct >= 50:
            items.append(("success", f"On track: {g['name']}", f"You're {pct:.0f}% toward your goal."))

    if not items:
        items.append(("info", "Start tracking", "Add a few expenses to unlock personalised insights."))
    return items
