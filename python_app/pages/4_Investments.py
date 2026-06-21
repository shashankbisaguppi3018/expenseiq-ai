import streamlit as st
import pandas as pd
import plotly.express as px
import importlib
import services.finance as finance
from services.db import format_inr

finance = importlib.reload(finance)

st.set_page_config(page_title="Investments - ExpenseIQ", page_icon="📈", layout="wide")
if not st.session_state.get("user"):
    st.warning("Please sign in first.")
    st.stop()
u = st.session_state.user

st.markdown("<div class='overline'>Markets - live/delayed quotes</div>", unsafe_allow_html=True)
st.title("Investments")

left, right = st.columns([2, 1], gap="large")

with left:
    mode = st.radio("Market view", ["NSE Top 30", "BSE Sensex 30", "Search"], horizontal=True)
    results = []

    if mode in finance.MARKET_LISTS:
        st.caption("Quotes refresh when the page reruns. Exchange data can be delayed depending on Yahoo Finance.")
        if st.button("Refresh prices", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        results = finance.market_quotes(mode)
    else:
        q = st.text_input("Search by ticker", placeholder="RELIANCE, TCS, AAPL, TSLA...")
        if q:
            results = finance.search_stocks(q)

    if results:
        table_rows = []
        for r in results:
            table_rows.append({
                "Symbol": r["symbol"],
                "Name": r["name"],
                "Exchange": r["exchange"],
                "Price": r["price"],
                "Change %": r["change_pct"],
            })
        st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)

    if mode == "Search":
        no_result_message = "No quote found. Try the exact ticker, for example AAPL or RELIANCE.NS."
    else:
        no_result_message = "Could not load prices right now. Check internet access and refresh."

    if not results and (mode in finance.MARKET_LISTS or "q" in locals() and q):
        st.warning(no_result_message)

    if results:
        st.markdown("#### Add to watchlist")
    for r in results:
        ticker = r.get("ticker") or r["symbol"]
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        c1.write(f"**{r['symbol']}** - {r['exchange']}")
        c1.caption(r["name"])
        c2.markdown(f"<span class='tabular'>{r['price']}</span>", unsafe_allow_html=True)
        color = "#34C759" if r["change_pct"] >= 0 else "#FF3B30"
        c3.markdown(f"<span style='color:{color}'>{r['change_pct']:+.2f}%</span>", unsafe_allow_html=True)
        if c4.button("Add", key=f"add-{mode}-{ticker}"):
            finance.watchlist_add(u["user_id"], ticker)
            st.rerun()

    st.divider()
    st.subheader("Your watchlist")
    wl = finance.watchlist_get(u["user_id"])
    if not wl:
        st.info("Search or use a market list to add stocks above.")
    else:
        if "selected_symbol" not in st.session_state:
            st.session_state.selected_symbol = None
        for w in wl:
            ticker = w.get("ticker") or w["symbol"]
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            if c1.button(f"**{w['symbol']}** - {w['name']}",
                         key=f"sel-{ticker}", use_container_width=True):
                st.session_state.selected_symbol = ticker
            c2.markdown(f"<span class='tabular'>{w['price']}</span>", unsafe_allow_html=True)
            color = "#34C759" if w["change_pct"] >= 0 else "#FF3B30"
            c3.markdown(f"<span style='color:{color}'>{w['change_pct']:+.2f}%</span>", unsafe_allow_html=True)
            if c4.button("x", key=f"rm-{ticker}"):
                finance.watchlist_remove(u["user_id"], ticker)
                st.rerun()

        if st.session_state.selected_symbol:
            df = pd.DataFrame(finance.history(st.session_state.selected_symbol, 30))
            if not df.empty:
                fig = px.line(df, x="date", y="price")
                fig.update_traces(line_color="#0A84FF")
                fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  height=300, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("SIP Calculator")
    monthly = st.number_input("Monthly (Rs.)", min_value=500.0, value=5000.0, step=500.0)
    years = st.slider("Years", 1, 30, 10)
    rate = st.slider("Expected return %", 1.0, 25.0, 12.0, 0.5)
    n = years * 12
    r = rate / 12 / 100
    fv = monthly * (((1 + r) ** n - 1) / r) * (1 + r)
    invested = monthly * n
    st.markdown(
        f"<div class='card'><div class='overline'>Projected value</div>"
        f"<div class='metric-big'>{format_inr(fv)}</div>"
        f"<div style='color:#888;margin-top:0.3rem'>Invested: {format_inr(invested)}</div>"
        f"<div style='color:#34C759'>Gain: {format_inr(fv - invested)}</div></div>",
        unsafe_allow_html=True)
