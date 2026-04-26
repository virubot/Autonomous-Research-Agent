import streamlit as st
import requests
import time

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="AI Research Assistant", layout="wide")

# ----------------------------
# 🔥 PREMIUM CSS
# ----------------------------
st.markdown("""
<style>

/* Background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: white;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(16px);
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    color: white;
    border-radius: 10px;
    padding: 10px 18px;
    border: none;
    font-weight: 600;
    transition: 0.3s;
}
.stButton>button:hover {
    transform: scale(1.05);
}

/* Chat bubbles */
.stChatMessage {
    background: rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 10px;
    backdrop-filter: blur(10px);
}

/* Cards */
.card {
    background: rgba(255,255,255,0.05);
    padding: 16px;
    border-radius: 16px;
    margin-bottom: 12px;
    backdrop-filter: blur(10px);
}

/* Inputs */
textarea, input {
    border-radius: 12px !important;
    background-color: #020617 !important;
    color: white !important;
}

/* Titles */
h1, h2, h3 {
    font-weight: 700;
}

/* Smooth spacing */
.block-container {
    padding-top: 2rem;
}

</style>
""", unsafe_allow_html=True)

# ----------------------------
# 🧠 SESSION STATE
# ----------------------------
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"
    st.session_state.chat_sessions["Chat 1"] = []

messages = st.session_state.chat_sessions[st.session_state.current_chat]

# ----------------------------
# 💬 SIDEBAR
# ----------------------------
st.sidebar.markdown("## 💬 Chats")

if st.sidebar.button("➕ New Chat"):
    new_chat = f"Chat {len(st.session_state.chat_sessions)+1}"
    st.session_state.chat_sessions[new_chat] = []
    st.session_state.current_chat = new_chat

for chat in st.session_state.chat_sessions:
    if st.sidebar.button(f"💭 {chat}"):
        st.session_state.current_chat = chat

# ----------------------------
# 🔬 HEADER
# ----------------------------
st.markdown("""
# 🔬 AI Research Assistant  
### 🚀 Search • Analyze • Generate Research Papers  
""")

# ----------------------------
# 📝 PAPER GENERATOR
# ----------------------------
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown("### 📝 Generate Research Paper")

    paper_topic = st.text_input("Enter topic")

    if st.button("🚀 Generate Paper"):
        if paper_topic:
            with st.spinner("Generating research paper..."):
                try:
                    res = requests.post(
                        "http://127.0.0.1:8000/generate",
                        json={"topic": paper_topic}
                    )

                    st.success("✅ Paper Generated!")

                    try:
                        with open("research_paper.pdf", "rb") as f:
                            st.download_button("📄 Download PDF", f)
                    except:
                        st.warning("PDF not found")

                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Enter topic")

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# 💬 CHAT INPUT
# ----------------------------
query = st.chat_input("💬 Ask anything about research...")

if query:
    messages.append({"role": "user", "content": query})

    with st.spinner("🤖 Thinking..."):
        try:
            res = requests.post(
                "http://127.0.0.1:8000/assistant",
                json={"query": query}
            )
            data = res.json()

            answer = data.get("answer", "No response")
            sources = data.get("sources", [])

        except Exception as e:
            answer = f"Error: {e}"
            sources = []

    messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })

# ----------------------------
# 💬 DISPLAY CHAT
# ----------------------------
for msg in messages:

    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f"""
            <div class="card">{msg["content"]}</div>
            """, unsafe_allow_html=True)

    else:
        with st.chat_message("assistant"):

            # ✨ Typing animation
            placeholder = st.empty()
            full_text = msg["content"]

            typed = ""
            for char in full_text:
                typed += char
                placeholder.markdown(f"""
                <div class="card">{typed}</div>
                """, unsafe_allow_html=True)
                time.sleep(0.002)

            # 📚 Sources
            if msg.get("sources"):
                st.markdown("### 📚 Sources")

                for p in msg["sources"]:
                    st.markdown(f"""
                    <div class="card">
                    📄 <b>{p.get('title','No title')}</b>
                    </div>
                    """, unsafe_allow_html=True)

# Save session
st.session_state.chat_sessions[st.session_state.current_chat] = messages