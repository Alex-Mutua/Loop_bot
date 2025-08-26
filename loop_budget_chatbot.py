import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="LOOP Budget Assistant", layout="wide")

# === DATA LOADING ===
@st.cache_data
def load_data():
    categories = {
        "Housing": ["Rent", "Internet", "Water", "Electricity"],
        "Transport": ["Fuel", "Car Repairs", "Public Transport", "Uber"],
        "Utilities": ["Garbage", "Cleaning", "Phone Bill"],
        "Food": ["Groceries", "Dining Out", "Takeout"],
        "Goals (Savings)": ["LOOP Goal", "Emergency Fund"],
        "Debts (Loan)": ["LOOP FLEX", "Term Loan"],
        "Miscellaneous": ["Gifts", "Unexpected", "Other"]
    }

    data = []
    np.random.seed(42)
    for period in ["current", "last_month", "peers"]:
        for cat, subs in categories.items():
            for sub in subs:
                budget = np.random.randint(4000, 18000)
                multiplier = np.random.uniform(0.8, 1.2) if period == "last_month" else \
                             np.random.uniform(0.85, 1.15) if period == "peers" else 1
                actual = int(np.random.randint(int(budget * 0.5), int(budget * 1.5)) * multiplier)
                data.append({
                    "period": period,
                    "category": cat,
                    "subcategory": sub,
                    "budgeted": budget,
                    "actual_spent": actual
                })
    df = pd.DataFrame(data)
    df["spent_pct"] = (df["actual_spent"] / df["budgeted"]).round(2)
    df["status"] = df.apply(lambda r: "🟢 On Track" if r["spent_pct"] < 0.75 else "🟡 Near Limit"
                            if r["spent_pct"] < 1.0 else "🔴 Over Budget" if r["period"] == "current" else "", axis=1)
    return df

df = load_data()

# === RESPONSE FUNCTION ===
def respond_to_question(q):
    q = q.lower()
    curr = df[df["period"] == "current"]
    last = df[df["period"] == "last_month"]
    peer = df[df["period"] == "peers"]

    if "last month" in q:
        diffs = []
        for cat in curr["category"].unique():
            c = curr[curr["category"] == cat]["actual_spent"].sum()
            l = last[last["category"] == cat]["actual_spent"].sum()
            if c > l:
                diffs.append(f"{cat} ↑ (+{c - l:,} KES)")
            elif l > c:
                diffs.append(f"{cat} ↓ ({l - c:,} KES)")
        return "📊 **Spending vs Last Month:**\\n" + ", ".join(diffs)

    if "peer" in q or "compare" in q:
        diffs = []
        for cat in curr["category"].unique():
            c = curr[curr["category"] == cat]["actual_spent"].sum()
            p = peer[peer["category"] == cat]["actual_spent"].sum()
            if abs(c - p) > 2000:
                label = "higher" if c > p else "lower"
                diffs.append(f"{cat} ({label} by {abs(c - p):,} KES)")
        return "👥 **Compared to Peers:**\\n" + ", ".join(diffs) if diffs else "You're spending is similar to peers."

    if "most" in q or "highest" in q or "subcategory" in q:
        top = curr.sort_values("actual_spent", ascending=False).iloc[0]
        return f"💸 Top subcategory: **{top['subcategory']}** under **{top['category']}** ({top['actual_spent']:,} KES)"

    if "surplus" in q or "left" in q:
        total_budget = curr["budgeted"].sum()
        total_spent = curr["actual_spent"].sum()
        surplus = total_budget - total_spent
        if surplus > 0:
            return f"💰 You have a surplus of {surplus:,} KES. Consider boosting your LOOP Goal or repaying a loan."
        else:
            return "⚠️ You are over budget. Consider using LOOP FLEX to manage cashflow."

    return "❓ Try asking about last month, peers, subcategories, or surplus."

# === TREND VISUALS ===
def show_chart():
    df_viz = df[df["period"].isin(["current", "last_month", "peers"])].copy()
    agg = df_viz.groupby(["category", "period"])["actual_spent"].sum().reset_index()
    pivot_df = agg.pivot(index="category", columns="period", values="actual_spent").fillna(0)
    pivot_df = pivot_df[["last_month", "current", "peers"]]

    st.subheader("📈 Trend Chart: Category Spending")
    st.caption("Compare current month spending to last month and peer average.")
    fig, ax = plt.subplots(figsize=(10, 5))
    pivot_df.plot(kind="bar", ax=ax)
    ax.set_ylabel("KES")
    ax.set_title("Spending Trends: Current vs Last Month vs Peers")
    ax.legend(title="Period")
    st.pyplot(fig)

# === PAGE NAVIGATION ===
tab = st.sidebar.radio("Navigate", ["📊 Tracker", "💬 Chat Assistant"])

# === TRACKER TAB ===
if tab == "📊 Tracker":
    st.title("📊 Budget Tracker")
    show_chart()

    cat = st.selectbox("Choose a Category", sorted(df[df["period"] == "current"]["category"].unique()))
    view = df[(df["category"] == cat) & (df["period"] == "current")]

    for _, row in view.iterrows():
        st.markdown(f"### {row['subcategory']}")
        st.markdown(f"**Status:** {row['status']}")
        st.progress(min(row["spent_pct"], 1.0))
        st.caption(f"Spent: {int(row['actual_spent'])} / {int(row['budgeted'])} KES")
        if row["subcategory"].lower() in ["loop goal", "emergency fund"]:
            st.info("💡 Boost your LOOP Goal to grow savings." if row["spent_pct"] < 0.5 else "🚀 Great savings progress!")
        elif row["subcategory"].lower() in ["loop flex", "term loan"]:
            st.info("💡 Consider early repayment to access new LOOP loan." if row["spent_pct"] >= 1.0 else "🕒 Stay on track with your loan.")
        elif row["spent_pct"] > 1.0:
            st.info(f"⚠️ Over budget on {row['subcategory']}. Consider LOOP FLEX to cover this area.")
        else:
            st.info("👍 Well managed. Consider redirecting extra to LOOP Goals.")

# === CHATBOT TAB ===
elif tab == "💬 Chat Assistant":
    st.title("💬 LOOP Trend Chat Assistant")

    if "chat" not in st.session_state:
        st.session_state.chat = [("bot", "Hi! Ask me about your spending trends, surplus, peer comparisons, or top categories.")]

    for sender, msg in st.session_state.chat:
        label = "🤖 LOOP Assistant" if sender == "bot" else "🧍 You"
        cleaned_msg = msg.replace("\n", " ").replace("\\n", " ")
        st.markdown(f"**{label}:** {cleaned_msg}")


    st.markdown("#### 🔘 Quick Questions:")
    cols = st.columns(3)
    q1 = "How does this month compare to last month?"
    q2 = "How do I compare to peers?"
    q3 = "Which subcategory used the most money?"

    if cols[0].button(q1):
        st.session_state.chat.append(("user", q1))
        reply = respond_to_question(q1)
        st.session_state.chat.append(("bot", reply))
        st.rerun()

    if cols[1].button(q2):
        st.session_state.chat.append(("user", q2))
        reply = respond_to_question(q2)
        st.session_state.chat.append(("bot", reply))
        st.rerun()

    if cols[2].button(q3):
        st.session_state.chat.append(("user", q3))
        reply = respond_to_question(q3)
        st.session_state.chat.append(("bot", reply))
        st.rerun()

    st.markdown("---")
    with st.form("ask_trend", clear_on_submit=True):
        user_q = st.text_input("Ask a trend question:")
        send = st.form_submit_button("Send")

    if send and user_q:
        st.session_state.chat.append(("user", user_q))
        reply = respond_to_question(user_q)
        st.session_state.chat.append(("bot", reply))
        st.rerun()
