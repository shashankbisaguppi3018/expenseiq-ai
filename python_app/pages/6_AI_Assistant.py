from datetime import datetime
import importlib

import streamlit as st

import services.ai as ai
import services.db as db_config
from services.finance import insights, list_expenses, list_goals, summary

db_config = importlib.reload(db_config)
ai = importlib.reload(ai)
chat_reply = ai.chat_reply
format_inr = db_config.format_inr

st.set_page_config(page_title="AI Assistant - ExpenseIQ", page_icon="✨", layout="wide")
if not st.session_state.get("user"):
    st.warning("Please sign in first.")
    st.stop()
u = st.session_state.user

st.markdown("<div class='overline'>AI Finance Assistant</div>", unsafe_allow_html=True)
st.title("✨ Ask anything")


def local_reply(user_id, question):
    q = question.lower()
    s = summary(user_id)
    exps = [e for e in list_expenses(user_id, 2000) if e.get("type") != "income"]
    month_key = datetime.now().strftime("%Y-%m")
    this_month = [e for e in exps if e.get("date", "")[:7] == month_key]

    if "spend" in q or "spent" in q or "this month" in q:
        return f"You spent {format_inr(s['month'])} this month. Your budget remaining is {format_inr(s['budget_remaining'])}."

    if "highest" in q or "top" in q or "category" in q:
        totals = {}
        for e in this_month:
            cat = e.get("category", "Miscellaneous")
            totals[cat] = totals.get(cat, 0) + float(e.get("amount", 0))
        if not totals:
            return "I do not see expenses for this month yet."
        cat, amount = max(totals.items(), key=lambda item: item[1])
        return f"Your highest expense category this month is {cat}, with {format_inr(amount)} spent."

    if "goal" in q or "savings" in q:
        goals = list_goals(user_id)
        if not goals:
            return "You do not have a savings goal yet. Add one in the Goals page and I can track it."
        g = max(goals, key=lambda item: item.get("target_amount", 0))
        saved = float(g.get("saved_amount", 0))
        target = float(g.get("target_amount", 0))
        remaining = max(0, target - saved)
        pct = (saved / target * 100) if target else 0
        return f"Your goal '{g['name']}' is {pct:.0f}% complete. You still need {format_inr(remaining)}."

    if "save" in q:
        tips = insights(user_id)[:3]
        lines = [f"- {title}: {msg}" for _, title, msg in tips]
        return "Here are 3 ways to improve this month:\n" + "\n".join(lines)

    return (
        f"Here is your current snapshot: balance {format_inr(s['balance'])}, "
        f"expenses {format_inr(s['expenses'])}, this month {format_inr(s['month'])}, "
        f"and budget remaining {format_inr(s['budget_remaining'])}."
    )


if "chat" not in st.session_state:
    st.session_state.chat = [{"role": "assistant",
                              "text": "Hi! I'm ExpenseIQ. Ask me anything about your money."}]

sugg = [
    "How much did I spend this month?",
    "Can I still reach my savings goal?",
    "What is my highest expense category?",
    "Give me 3 ways to save Rs. 2000 this month.",
]
cols = st.columns(len(sugg))
prompt = None
for i, s in enumerate(sugg):
    if cols[i].button(s, use_container_width=True):
        prompt = s

if not (db_config.EMERGENT_LLM_KEY or db_config.GEMINI_API_KEY):
    st.caption("Basic assistant mode: add GEMINI_API_KEY or EMERGENT_LLM_KEY to .env for full AI answers.")

for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.write(msg["text"])

user_input = st.chat_input("Ask about spending, budgets, savings...")
if user_input or prompt:
    q = user_input or prompt
    st.session_state.chat.append({"role": "user", "text": q})
    with st.chat_message("user"):
        st.write(q)
    s = summary(u["user_id"])
    system = (
        "You are ExpenseIQ AI, a friendly personal-finance assistant. Use Indian Rupees. "
        "Keep replies short, warm, and actionable. "
        f"User snapshot: Balance {format_inr(s['balance'])}, Income {format_inr(s['income'])}, "
        f"Expenses {format_inr(s['expenses'])}, Savings {format_inr(s['savings'])}, "
        f"This month {format_inr(s['month'])}, Budget remaining {format_inr(s['budget_remaining'])}."
    )
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if db_config.EMERGENT_LLM_KEY or db_config.GEMINI_API_KEY:
                reply = chat_reply(system, q, session_id=f"chat_{u['user_id']}")
            else:
                reply = local_reply(u["user_id"], q)
        st.write(reply)
    st.session_state.chat.append({"role": "assistant", "text": reply})
