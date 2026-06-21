import streamlit as st
import pandas as pd
from datetime import date, datetime
from services.finance import add_expense, list_expenses, delete_expense
from services.ai import parse_voice_expense, ocr_receipt
from services.db import CATEGORIES, format_inr

st.set_page_config(page_title="Expenses · ExpenseIQ", page_icon="💳", layout="wide")
if not st.session_state.get("user"):
    st.warning("Please sign in first."); st.stop()
u = st.session_state.user

st.markdown("<div class='overline'>Wallet</div>", unsafe_allow_html=True)
st.title("Expenses")

c1, c2, c3 = st.columns(3)
with c1:
    with st.expander("➕ Add expense"):
        with st.form("add_exp", clear_on_submit=True):
            etype = st.radio("Type", ["expense", "income"], horizontal=True)
            amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
            cat = st.selectbox("Category", CATEGORIES)
            note = st.text_input("Note")
            d = st.date_input("Date", value=date.today())
            if st.form_submit_button("Save", type="primary"):
                add_expense(u["user_id"], amount, cat, note, etype,
                            datetime.combine(d, datetime.min.time()))
                st.success("Added"); st.rerun()

with c2:
    with st.expander("🎙 Voice add (AI parsed)"):
        text = st.text_input("Speak / type", placeholder="e.g. Spent 250 on lunch")
        if st.button("Parse & save", type="primary", use_container_width=True):
            if not text:
                st.warning("Type a sentence first")
            else:
                data, err = parse_voice_expense(text)
                if err: st.error(err)
                else:
                    add_expense(u["user_id"], data["amount"],
                                data.get("category", "Miscellaneous"),
                                data.get("note", text), data.get("type", "expense"))
                    st.success(f"Added {data.get('category')}: ₹{data['amount']}"); st.rerun()

with c3:
    with st.expander("🧾 Scan receipt (AI OCR)"):
        up = st.file_uploader("Upload receipt image", type=["png", "jpg", "jpeg", "webp"])
        if up and st.button("Scan & extract", type="primary", use_container_width=True):
            data, err = ocr_receipt(up.read())
            if err: st.error(err)
            else:
                add_expense(u["user_id"], float(data.get("amount", 0)),
                            data.get("category", "Miscellaneous"),
                            data.get("merchant", ""), "expense")
                st.success("Saved from receipt"); st.rerun()

st.divider()
fil = st.selectbox("Filter by category", ["All"] + CATEGORIES, label_visibility="collapsed")
exps = list_expenses(u["user_id"])
if fil != "All":
    exps = [e for e in exps if e["category"] == fil]

if not exps:
    st.info("No expenses yet.")
else:
    for e in exps:
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        sign = "+" if e["type"] == "income" else "−"
        c1.markdown(
            f"**{e.get('note') or e['category']}**  \n<span style='color:#888;font-size:0.8rem'>{e['category']}</span>",
            unsafe_allow_html=True)
        c2.write(pd.to_datetime(e["date"]).strftime("%d %b %Y"))
        c3.write(e["type"].title())
        color = "#34C759" if e["type"] == "income" else "#fff"
        c4.markdown(f"<span class='tabular' style='color:{color}'>{sign} {format_inr(e['amount'])}</span>",
                    unsafe_allow_html=True)
        if c5.button("🗑", key=f"del-{e['id']}", help="Delete"):
            delete_expense(u["user_id"], e["id"]); st.rerun()