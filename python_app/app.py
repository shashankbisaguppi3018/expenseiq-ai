"""ExpenseIQ AI - Streamlit entry point.  Run:  streamlit run app.py"""
import streamlit as st
from services.auth import login, signup

st.set_page_config(page_title="ExpenseIQ AI", page_icon="💰",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');
html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; }
h1, h2, h3, h4 { font-family: 'Outfit', sans-serif !important; letter-spacing: -0.02em; font-weight: 600; }
.tabular { font-family: 'JetBrains Mono', monospace; font-variant-numeric: tabular-nums; }
.overline { text-transform: uppercase; letter-spacing: 0.18em; font-size: 0.7rem; color: #888; font-weight: 600; }
.card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 1.25rem 1.5rem; }
.metric-big { font-family: 'Outfit', sans-serif; font-size: 2rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.insight-danger { border-left: 3px solid #FF3B30; padding-left: 0.75rem; }
.insight-warning { border-left: 3px solid #FF9500; padding-left: 0.75rem; }
.insight-success { border-left: 3px solid #34C759; padding-left: 0.75rem; }
.insight-info { border-left: 3px solid #0A84FF; padding-left: 0.75rem; }
section[data-testid="stSidebar"] {
    background: #f4f7fb;
    border-right: 1px solid #d8e0ea;
}
section[data-testid="stSidebar"] * {
    color: #1f2937 !important;
}
section[data-testid="stSidebar"] a {
    color: #1f2937 !important;
}
section[data-testid="stSidebar"] a[aria-current="page"],
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:has(a[aria-current="page"]) {
    background: #dbe7f6;
    border-radius: 8px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None


def auth_screen():
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("<div style='padding-top: 4rem'></div>", unsafe_allow_html=True)
        st.markdown("<div class='overline'>Premium Fintech · Reimagined</div>", unsafe_allow_html=True)
        st.markdown("# Your money,<br/>understood by AI.", unsafe_allow_html=True)
        st.write("Track expenses, set smart budgets, predict overspending, and get personalised insights — all in one calm Python dashboard.")
        st.caption("✨ Powered by GPT-5.2 · ExpenseIQ AI (Streamlit edition)")
    with col2:
        st.markdown("<div style='padding-top: 3rem'></div>", unsafe_allow_html=True)
        tabs = st.tabs(["Sign in", "Create account"])
        with tabs[0]:
            with st.form("login"):
                email = st.text_input("Email", placeholder="you@example.com")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Sign in", use_container_width=True, type="primary"):
                    user, err = login(email, pwd)
                    if err: st.error(err)
                    else:
                        st.session_state.user = user
                        st.rerun()
        with tabs[1]:
            with st.form("signup"):
                name = st.text_input("Full name")
                email = st.text_input("Email", key="su_email")
                pwd = st.text_input("Password (min 6)", type="password", key="su_pwd")
                if st.form_submit_button("Create account", use_container_width=True, type="primary"):
                    if len(pwd) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        user, err = signup(email, pwd, name)
                        if err: st.error(err)
                        else:
                            st.session_state.user = user
                            st.rerun()


if not st.session_state.user:
    auth_screen()
    st.stop()

u = st.session_state.user
with st.sidebar:
    st.markdown("### 💰 ExpenseIQ")
    st.caption("AI Finance Dashboard")
    st.divider()
    st.write(f"**{u['name']}**")
    st.caption(u['email'])
    st.divider()
    if st.button("Sign out", use_container_width=True):
        st.session_state.user = None
        st.rerun()

from services.finance import summary, insights, list_expenses
from services.db import format_inr
import plotly.express as px
import pandas as pd
from datetime import datetime, timezone, timedelta

s = summary(u["user_id"])

st.markdown("<div class='overline'>Overview · Welcome back</div>", unsafe_allow_html=True)
st.title(f"Hello, {u['name'].split()[0]} 👋")

c1, c2, c3, c4, c5 = st.columns(5)
for col, (label, val, suffix) in zip(
    [c1, c2, c3, c4, c5],
    [("Total Balance", format_inr(s["balance"]), ""),
     ("Total Income", format_inr(s["income"]), ""),
     ("Total Expenses", format_inr(s["expenses"]), ""),
     ("Savings", format_inr(s["savings"]), ""),
     ("Health Score", f"{s['health']}", "/100")],
):
    with col:
        st.markdown(
            f"<div class='card'><div class='overline'>{label}</div>"
            f"<div class='metric-big'>{val}<span style='font-size:0.9rem;color:#888'>{suffix}</span></div></div>",
            unsafe_allow_html=True)

st.write("")
q1, q2, q3, q4 = st.columns(4)
for col, label, val in [(q1, "Today", s["today"]), (q2, "This Week", s["week"]),
                        (q3, "This Month", s["month"]), (q4, "Budget Remaining", s["budget_remaining"])]:
    with col:
        st.markdown(
            f"<div class='card'><div class='overline'>{label}</div>"
            f"<div class='metric-big'>{format_inr(val)}</div></div>",
            unsafe_allow_html=True)

st.write("")
left, right = st.columns([2, 1], gap="large")
with left:
    st.markdown("<div class='overline'>Spending · last 14 days</div>", unsafe_allow_html=True)
    exps = list_expenses(u["user_id"])
    if exps:
        df = pd.DataFrame(exps)
        df = df[df["type"] != "income"].copy()
        df["day"] = df["date"].str[:10]
        days = [(datetime.now(timezone.utc) - timedelta(days=13 - i)).strftime("%Y-%m-%d") for i in range(14)]
        agg = df.groupby("day")["amount"].sum().reindex(days, fill_value=0).reset_index()
        agg.columns = ["day", "amount"]
        fig = px.area(agg, x="day", y="amount", labels={"day": "", "amount": "₹"})
        fig.update_traces(line_color="#FFFFFF", fillcolor="rgba(255,255,255,0.08)")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          height=280, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses yet — head to the **Expenses** page to start tracking.")

with right:
    st.markdown("<div class='overline'>✨ AI Insight Center</div>", unsafe_allow_html=True)
    for level, title, msg in insights(u["user_id"])[:5]:
        st.markdown(
            f"<div class='card insight-{level}' style='margin-bottom:0.6rem'>"
            f"<strong>{title}</strong><br/>"
            f"<span style='color:#aaa;font-size:0.85rem'>{msg}</span></div>",
            unsafe_allow_html=True)

st.write("")
st.markdown("<div class='overline'>Recent Transactions</div>", unsafe_allow_html=True)
exps = list_expenses(u["user_id"], limit=8)
if exps:
    df = pd.DataFrame(exps)[["date", "category", "note", "type", "amount"]]
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d %b %Y")
    df["amount"] = df.apply(lambda r: ("+ " if r["type"] == "income" else "− ") + format_inr(r["amount"]), axis=1)
    df.columns = ["Date", "Category", "Note", "Type", "Amount"]
    st.dataframe(df, hide_index=True, use_container_width=True)
else:
    st.caption("No recent transactions.")
