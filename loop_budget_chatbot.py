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
                multiplier = (
                    np.random.uniform(0.8, 1.2) if period == "last_month"
                    else np.random.uniform(0.85, 1.15) if period == "peers"
                    else 1
                )
                actual = int(np.random.randint(int(budget * 0.5), int(budget * 1.5)) * multiplier)
                data.append({
                    "period": period,
                    "category": cat,
                    "subcategory": sub,
                    "budgeted": budget,
                    "actual_spent": actual
                })
    df = pd.DataFrame(data)
    df["spent_pct"] = df["actual_spent"] / df["budgeted"]
    df["status"] = df["spent_pct"].apply(
        lambda x: "⚪ Well Below" if x < 0.5 else
                  "🟢 On Track" if x < 0.75 else
                  "🟡 Near Limit" if x <= 1.0 else
                  "🔴 Over Budget"
    )
    return df

df = load_data()
current_df = df[df["period"] == "current"]

# === CATEGORY INSIGHTS ===
def get_category_advice(pct, cat):
    if pct > 1.0:
        return f"🔴 You’ve exceeded your {cat} budget. Consider trimming or applying for a Term Loan."
    elif 0.9 <= pct <= 1.0:
        return f"🟡 You're nearing your {cat} budget limit. Consider LOOP FLEX or readjusting."
    elif 0.5 <= pct < 0.9:
        return f"🟢 You're on track for {cat}. You could allocate surplus to your LOOP Goal."
    else:
        return f"⚪ You're well below your {cat} budget. Did you miss a bill or delay something?"

summary = current_df.groupby("category").agg({
    "budgeted": "sum",
    "actual_spent": "sum"
}).reset_index()
summary["spent_pct"] = summary["actual_spent"] / summary["budgeted"]
summary["advice"] = summary.apply(lambda r: get_category_advice(r["spent_pct"], r["category"]), axis=1)

# === CHATBOT RESPONSE LOGIC ===
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
        return "📊 This Month vs Last Month: " + ", ".join(diffs)

    if "peer" in q or "compare" in q:
        diffs = []
        for cat in curr["category"].unique():
            c = curr[curr["category"] == cat]["actual_spent"].sum()
            p = peer[peer["category"] == cat]["actual_spent"].sum()
            if abs(c - p) > 2000:
                label = "higher" if c > p else "lower"
                diffs.append(f"{cat} ({label} by {abs(c - p):,} KES)")
        return "👥 Compared to Peers: " + ", ".join(diffs) if diffs else "You're spending is similar to peers."

    if "most" in q or "subcategory" in q:
        top = curr.sort_values("actual_spent", ascending=False).iloc[0]
        return f"💸 Top subcategory: {top['subcategory']} under {top['category']} ({top['actual_spent']:,} KES)"

    if "surplus" in q or "left" in q:
        total_budget = curr["budgeted"].sum()
        total_spent = curr["actual_spent"].sum()
        surplus = total_budget - total_spent
        if surplus > 0:
            return f"💰 You have a surplus of {surplus:,} KES. Consider boosting LOOP Goal or early loan repayment."
        else:
            return "⚠️ You're over budget. Consider using LOOP FLEX for relief."

    if "loan" in q:
        loans = curr[curr["subcategory"].str.contains("loan", case=False)]
        if loans.empty:
            return "🔍 I couldn't find active loan repayment data. Check back next month."
        total = loans["actual_spent"].sum()
        budget = loans["budgeted"].sum()
        pct = total / budget
        if pct > 1.0:
            return f"💳 You've spent {int(pct*100)}% of your loan repayment budget. Consider early repayment or rebalancing."
        elif pct > 0.75:
            return f"🕒 You're nearing your loan repayment limit ({int(pct*100)}%). Stay steady or top up gradually."
        else:
            return f"✅ You're on track with loan repayment ({int(pct*100)}%). Great work!"

    if "headroom" in q:
        curr["remaining"] = curr["budgeted"] - curr["actual_spent"]
        remaining = curr.groupby("category")["remaining"].sum()
        headroom = remaining.idxmax()
        amt = remaining.max()
        return f"📌 You have the most headroom in **{headroom}** (approx {int(amt):,} KES remaining)."

    return "❓ Try asking about last month comparison, peers, subcategories, surplus, loan repayment, or headroom."

# === NAVIGATION ===
tab = st.sidebar.radio("Navigate", ["📊 Tracker", "💬 Chat Assistant"])

# === TRACKER TAB ===
if tab == "📊 Tracker":
    st.title("📊 Monthly Budget Tracker")

    selected_cat = st.selectbox("Choose a category to view breakdown:", sorted(current_df["category"].unique()))

    # Trend chart
    st.markdown("### 📈 Trend Chart")
    compare_df = df[df["category"] == selected_cat].groupby("period")["actual_spent"].sum().reindex(["last_month", "current", "peers"])
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(compare_df.index, compare_df.values, color=["#1f77b4", "#2ca02c", "#ff7f0e"])
    ax.set_ylabel("KES")
    ax.set_title(f"{selected_cat} — Spending Trend")
    st.pyplot(fig)

    # Category insight
    st.markdown("###  Category Insight")
    advice = summary[summary["category"] == selected_cat]["advice"].values[0]
    st.info(advice)

    # Subcategory progress
    st.subheader(f"📂 Subcategories in {selected_cat}")
    filtered = current_df[current_df["category"] == selected_cat]
    for _, row in filtered.iterrows():
        st.markdown(f"**{row['subcategory']}** — {row['status']}")
        st.progress(min(row["spent_pct"], 1.0))
        st.caption(f"Spent: {int(row['actual_spent'])} / {int(row['budgeted'])} KES")

# === CHAT ASSISTANT TAB ===
elif tab == "💬 Chat Assistant":
    st.title("💬 LOOP Chat Assistant")

    if "chat" not in st.session_state:
        st.session_state.chat = [("bot", "Hi! Ask me about your trends, surplus, peer comparisons, or categories.")]

    for sender, msg in st.session_state.chat:
        role = "🤖 LOOP Assistant" if sender == "bot" else "🧍 You"
        st.markdown(f"**{role}:** {msg.replace(chr(10), ' ')}")

    # Quick questions
    st.markdown("#### 🔘 Quick Questions:")
    prompts = [
        "How does this month compare to last month?",
        "How do I compare to peers?",
        "Which subcategory used the most money?",
        "How is my loan repayment progress?",
        "Which category has the most headroom?"
    ]
    cols = st.columns(len(prompts))
    for i, q in enumerate(prompts):
        if cols[i].button(q):
            st.session_state.chat.append(("user", q))
            reply = respond_to_question(q)
            st.session_state.chat.append(("bot", reply))
            st.rerun()

    # Free-form input
    st.markdown("---")
    with st.form("chat_form", clear_on_submit=True):
        user_q = st.text_input("Ask a trend question:")
        send = st.form_submit_button("Send")
    if send and user_q:
        st.session_state.chat.append(("user", user_q))
        reply = respond_to_question(user_q)
        st.session_state.chat.append(("bot", reply))
        st.rerun()
