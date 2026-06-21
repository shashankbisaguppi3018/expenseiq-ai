import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone, timedelta
from services.finance import list_expenses

st.set_page_config(page_title="Analytics · ExpenseIQ", page_icon="📊", layout="wide")
if not st.session_state.get("user"):
    st.warning("Please sign in first."); st.stop()
u = st.session_state.user

st.markdown("<div class='overline'>Reports</div>", unsafe_allow_html=True)
st.title("Analytics")

exps = list_expenses(u["user_id"], 5000)
if not exps:
    st.info("No data yet — add expenses to see analytics.")
    st.stop()

df = pd.DataFrame(exps)
df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.tz_convert(None)
df = df.dropna(subset=["date"])
df_exp = df[df["type"] != "income"].copy()
now = datetime.now(timezone.utc).replace(tzinfo=None)
this_month = df_exp[df_exp["date"].dt.strftime("%Y-%m") == now.strftime("%Y-%m")]

col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown("<div class='overline'>Expense distribution · this month</div>", unsafe_allow_html=True)
    if not this_month.empty:
        cat = this_month.groupby("category")["amount"].sum().reset_index()
        fig = px.pie(cat, names="category", values="amount", hole=0.5,
                     color_discrete_sequence=px.colors.sequential.Greys_r)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          height=360, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("No expenses this month.")

with col2:
    st.markdown("<div class='overline'>Income vs Expenses · last 6 months</div>", unsafe_allow_html=True)
    df["month"] = df["date"].dt.strftime("%Y-%m")
    monthly = df.groupby(["month", "type"])["amount"].sum().reset_index()
    monthly = monthly[monthly["month"] >= (now - timedelta(days=180)).strftime("%Y-%m")]
    fig = px.bar(monthly, x="month", y="amount", color="type", barmode="group",
                 color_discrete_map={"income": "#34C759", "expense": "#888"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      height=360, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.markdown("<div class='overline'>Daily spending · last 30 days</div>", unsafe_allow_html=True)
days = [(now - timedelta(days=29 - i)).strftime("%Y-%m-%d") for i in range(30)]
df_exp["day"] = df_exp["date"].dt.strftime("%Y-%m-%d")
trend = df_exp.groupby("day")["amount"].sum().reindex(days, fill_value=0).reset_index()
trend.columns = ["day", "amount"]
fig = px.line(trend, x="day", y="amount")
fig.update_traces(line_color="#FFF")
fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                  height=300, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

st.divider()
csv = df[["date", "category", "note", "type", "amount"]].to_csv(index=False).encode()
st.download_button("Export CSV", csv, "expenses.csv", "text/csv")
