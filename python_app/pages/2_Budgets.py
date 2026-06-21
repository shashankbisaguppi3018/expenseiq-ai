import streamlit as st
from datetime import datetime, timezone
from services.finance import get_budget, update_budget, list_expenses
from services.db import CATEGORIES, format_inr

st.set_page_config(page_title="Budgets · ExpenseIQ", page_icon="🎯", layout="wide")
if not st.session_state.get("user"):
    st.warning("Please sign in first."); st.stop()
u = st.session_state.user

st.markdown("<div class='overline'>Limits</div>", unsafe_allow_html=True)
st.title("Monthly budgets")

budget = get_budget(u["user_id"])
exps = list_expenses(u["user_id"], 2000)
month_key = datetime.now(timezone.utc).strftime("%Y-%m")
cur, total = {}, 0
for e in exps:
    if e.get("type") == "income": continue
    if e["date"][:7] != month_key: continue
    cur[e["category"]] = cur.get(e["category"], 0) + e["amount"]
    total += e["amount"]


def pct_color(p):
    if p >= 100: return "#FF3B30"
    if p >= 90:  return "#FF9500"
    if p >= 70:  return "#FFCC00"
    return "#34C759"


gp = (total / budget["global_limit"] * 100) if budget["global_limit"] > 0 else 0
st.markdown(
    f"<div class='card'><div class='overline'>Global monthly limit</div>"
    f"<div class='metric-big'>{format_inr(budget['global_limit'])}</div>"
    f"<div style='margin-top:0.5rem;color:#aaa'>Used {format_inr(total)} · {gp:.0f}%</div>"
    f"<div style='margin-top:0.7rem;height:8px;background:#222;border-radius:99px;overflow:hidden'>"
    f"<div style='height:100%;width:{min(100, gp)}%;background:{pct_color(gp)}'></div></div></div>",
    unsafe_allow_html=True)

st.divider()
st.markdown("<div class='overline'>Edit category limits</div>", unsafe_allow_html=True)

with st.form("budget_form"):
    new_global = st.number_input("Global monthly limit (₹)", min_value=0.0,
                                 value=float(budget["global_limit"]), step=500.0)
    new_cats = {}
    cols = st.columns(2)
    for i, cat in enumerate(CATEGORIES):
        with cols[i % 2]:
            new_cats[cat] = st.number_input(cat, min_value=0.0,
                                             value=float(budget["categories"].get(cat, 0)), step=100.0)
    if st.form_submit_button("Save budget", type="primary"):
        update_budget(u["user_id"], new_global, new_cats)
        st.success("Saved"); st.rerun()

st.divider()
st.markdown("<div class='overline'>Per category</div>", unsafe_allow_html=True)
for cat in CATEGORIES:
    lim = budget["categories"].get(cat, 0)
    if lim <= 0: continue
    used = cur.get(cat, 0)
    p = (used / lim * 100) if lim else 0
    st.markdown(
        f"<div class='card' style='margin-bottom:0.5rem'>"
        f"<div style='display:flex;justify-content:space-between'><strong>{cat}</strong>"
        f"<span class='tabular'>{format_inr(used)} / {format_inr(lim)}</span></div>"
        f"<div style='margin-top:0.5rem;height:6px;background:#222;border-radius:99px;overflow:hidden'>"
        f"<div style='height:100%;width:{min(100, p)}%;background:{pct_color(p)}'></div></div></div>",
        unsafe_allow_html=True)