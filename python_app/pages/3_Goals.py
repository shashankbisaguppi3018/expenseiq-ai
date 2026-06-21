import streamlit as st
from datetime import date
from services.finance import list_goals, add_goal, update_goal, delete_goal
from services.db import format_inr

st.set_page_config(page_title="Goals · ExpenseIQ", page_icon="🏆", layout="wide")
if not st.session_state.get("user"):
    st.warning("Please sign in first."); st.stop()
u = st.session_state.user

st.markdown("<div class='overline'>Savings</div>", unsafe_allow_html=True)
st.title("Goals")

with st.expander("➕ New goal"):
    with st.form("goal", clear_on_submit=True):
        name = st.text_input("Name", placeholder="Emergency fund")
        target = st.number_input("Target amount (₹)", min_value=0.0, step=1000.0)
        saved = st.number_input("Already saved (₹)", min_value=0.0, step=500.0)
        td = st.date_input("Target date", value=date.today())
        if st.form_submit_button("Create", type="primary"):
            if name and target > 0:
                add_goal(u["user_id"], name, target, td.isoformat(), saved)
                st.success("Created"); st.rerun()
            else:
                st.error("Fill name and target")

goals = list_goals(u["user_id"])
if not goals:
    st.info("No goals yet.")
else:
    for g in goals:
        pct = min(100, (g["saved_amount"] / g["target_amount"] * 100)) if g["target_amount"] else 0
        days_left = (date.fromisoformat(g["target_date"]) - date.today()).days
        c1, c2 = st.columns([3, 1])
        with c1:
            color = "#34C759" if pct >= 100 else "#fff"
            st.markdown(
                f"<div class='card'><h4 style='margin:0'>{g['name']}</h4>"
                f"<div style='color:#888;font-size:0.85rem'>Target by {g['target_date']} · {days_left} days left</div>"
                f"<div style='margin-top:0.8rem' class='tabular'>{format_inr(g['saved_amount'])} of {format_inr(g['target_amount'])}</div>"
                f"<div style='margin-top:0.5rem;height:6px;background:#222;border-radius:99px;overflow:hidden'>"
                f"<div style='height:100%;width:{pct}%;background:{color}'></div></div>"
                f"<div style='color:#888;font-size:0.75rem;margin-top:0.3rem'>{pct:.0f}% complete</div></div>",
                unsafe_allow_html=True)
        with c2:
            new_saved = st.number_input("Update saved", min_value=0.0,
                                         value=float(g["saved_amount"]), step=500.0, key=f"sv-{g['id']}")
            cc1, cc2 = st.columns(2)
            if cc1.button("Update", key=f"up-{g['id']}", use_container_width=True):
                update_goal(u["user_id"], g["id"], saved_amount=new_saved); st.rerun()
            if cc2.button("🗑", key=f"d-{g['id']}", use_container_width=True):
                delete_goal(u["user_id"], g["id"]); st.rerun()