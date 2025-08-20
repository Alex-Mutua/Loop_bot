
import streamlit as st
import pandas as pd

# === PAGE CONFIG ===
st.set_page_config(page_title="LOOP Budget Assistant", layout="wide")

# === SAMPLE DATA ===
def load_budget_data():
    return pd.DataFrame({
        "category": ["Groceries", "Transport", "Entertainment", "Utilities", "Loan Repayment", "Savings"],
        "budgeted": [15000, 8000, 5000, 7000, 12000, 5000],
        "actual_spent": [14500, 9200, 3000, 7100, 13500, 2000]
    })

def evaluate_budget_status(row):
    pct = row["actual_spent"] / row["budgeted"]
    if pct < 0.75:
        return "🟢 On Track"
    elif pct < 1.0:
        return "🟡 Near Limit"
    return "🔴 Over Budget"

def loop_tip(row):
    pct = row["actual_spent"] / row["budgeted"]
    category = row["category"]
    if category == "Loan Repayment" and pct < 1.0:
        return "You're close to completing your LOOP loan repayment — great job staying on track!"
    if category == "Savings" and pct < 0.5:
        return "Consider setting up a LOOP Goal to automate your savings this month."
    if pct > 1.0:
        return f"You've exceeded your {category} budget. Consider using LOOP FLEX to balance your spending."
    if pct >= 0.8:
        return f"You're nearing your limit in {category}. A LOOP loan could help smooth your finances."
    if pct < 0.5 and category not in ["Savings", "Loan Repayment"]:
        return f"You're under budget in {category}. Could this be an opportunity to grow your LOOP Goal?"
    return "You're on track. Keep it up."

def interpret_question(message, df):
    message = message.lower()
    for _, row in df.iterrows():
        if row["category"].lower() in message:
            response = f"You've spent KES {int(row['actual_spent']):,} out of your KES {int(row['budgeted']):,} budget for {row['category']}. "
            response += f"That's {int(row['spent_pct'] * 100)}% — {row['status']}. "
            response += f"💡 {row['loop_tip']}"
            return response
    return "I'm not sure which category you're referring to. Please ask about a specific budget category like Transport, Savings, or Loan Repayment."

# === BUDGET DATA PROCESSING ===
df = load_budget_data()
df["spent_pct"] = (df["actual_spent"] / df["budgeted"]).round(2)
df["status"] = df.apply(evaluate_budget_status, axis=1)
df["loop_tip"] = df.apply(loop_tip, axis=1)

# === NAVIGATION ===
tab = st.sidebar.radio("Navigate", ["📊 Budget Overview", "💬 Chat Assistant"])

# === BUDGET OVERVIEW TAB ===
if tab == "📊 Budget Overview":
    st.title("📊 Monthly Budget Tracker")

    for _, row in df.iterrows():
        st.markdown(f"**{row['category']}** — {row['status']}")
        st.progress(min(row["spent_pct"], 1.0))
        st.caption(f"Spent: {int(row['actual_spent'])} / {int(row['budgeted'])} KES")
        st.info(row["loop_tip"])

# === CHAT ASSISTANT TAB ===
elif tab == "💬 Chat Assistant":
    st.title("💬 LOOP Chat Assistant")

    if "chat" not in st.session_state:
        st.session_state.chat = []
        st.session_state.chat.append(("bot", "Hi! I'm your LOOP Budget Assistant. Ask me anything or choose a quick question below."))

    st.subheader("🧾 Budget Summary (Top 3)")
    for _, row in df.sort_values("spent_pct", ascending=False).head(3).iterrows():
        st.markdown(f"- **{row['category']}**: {row['status']} — {int(row['spent_pct'] * 100)}% used")

    st.markdown("---")
    for sender, msg in st.session_state.chat:
        role = "🤖 LOOP Assistant" if sender == "bot" else "🧍 You"
        st.markdown(f"**{role}:** {msg.replace(chr(10), ' ')}")  # Clean display

    # === PRESET RADIO PROMPTS ===
    st.markdown("**Quick Questions:**")
    options = [
        "How much have I spent on Transport?",
        "What’s my status on Savings?",
        "Have I exceeded my Loan Repayment budget?"
    ]
    selected_question = st.radio("Choose a question to ask:", options, index=0, key="radio_question")
    if st.button("Ask Selected Question"):
        st.session_state.chat.append(("user", selected_question))
        reply = interpret_question(selected_question, df)
        st.session_state.chat.append(("bot", reply))
        st.rerun()

    # === ADVANCED TEXT INPUT ===
    st.markdown("---")
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Or type your own question:")
        submitted = st.form_submit_button("Send")

    if submitted and user_input:
        st.session_state.chat.append(("user", user_input))
        reply = interpret_question(user_input, df)
        st.session_state.chat.append(("bot", reply))
        st.rerun()

