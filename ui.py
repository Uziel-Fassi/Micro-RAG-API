import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000/api/v1/document"

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Micro RAG",
    page_icon="🧠",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Main background */
        .stApp { background-color: #0f1117; }

        /* Sidebar */
        [data-testid="stSidebar"] { background-color: #161b27; }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 { color: #e2e8f0; }

        /* Upload area */
        [data-testid="stFileUploader"] {
            background: #1e2535;
            border: 1.5px dashed #3b4a6b;
            border-radius: 12px;
            padding: 8px;
        }

        /* Success / error banners */
        .stAlert { border-radius: 10px; }

        /* Expander */
        [data-testid="stExpander"] {
            background: #1a2235;
            border: 1px solid #2d3a55;
            border-radius: 10px;
        }

        /* Chat messages */
        [data-testid="stChatMessage"] {
            background: #1a2235;
            border-radius: 12px;
            margin-bottom: 6px;
        }

        /* Source chips */
        .source-chip {
            background: #1e2d45;
            border-left: 3px solid #4a90d9;
            border-radius: 4px;
            padding: 8px 12px;
            margin-bottom: 8px;
            font-size: 0.82rem;
            color: #94a3b8;
            white-space: pre-wrap;
            font-family: monospace;
        }

        /* Title gradient */
        .hero-title {
            background: linear-gradient(135deg, #4a90d9 0%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.4rem;
            font-weight: 800;
            margin-bottom: 0;
        }
        .hero-sub {
            color: #64748b;
            font-size: 1rem;
            margin-top: 2px;
            margin-bottom: 28px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── State ──────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_info" not in st.session_state:
    st.session_state.doc_info = None


# ── Sidebar — Upload ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📄 Document")
    st.markdown("Upload a PDF to index it into the knowledge base.")

    uploaded = st.file_uploader(
        label="",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded:
        upload_btn = st.button("⬆️  Index document", use_container_width=True, type="primary")
        if upload_btn:
            with st.spinner("Uploading and indexing…"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/upload",
                        files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                        timeout=120,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.doc_info = data
                        st.success(
                            f"✅ **{data['filename']}**\n\n"
                            f"Chunks indexed: **{data['chunks_processed']}**\n\n"
                            f"ID: `{data['document_id'][:12]}…`"
                        )
                        # Reset chat when a new doc is loaded
                        st.session_state.messages = []
                    else:
                        detail = resp.json().get("detail", resp.text)
                        st.error(f"Upload failed ({resp.status_code}): {detail}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot reach the API.\nMake sure Uvicorn is running on http://127.0.0.1:8000")
                except requests.exceptions.Timeout:
                    st.error("⏱️ The upload timed out. Try a smaller PDF.")

    if st.session_state.doc_info:
        st.divider()
        info = st.session_state.doc_info
        st.markdown(f"**Active document**")
        st.caption(f"📁 {info['filename']}")
        st.caption(f"🗂️ {info['chunks_processed']} chunks")
        if st.button("🗑️ Clear session", use_container_width=True):
            st.session_state.messages = []
            st.session_state.doc_info = None
            st.rerun()

    st.divider()
    st.caption("Micro RAG · FastAPI + ChromaDB + Gemini")


# ── Main — Chat ────────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">🧠 Micro RAG</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Upload a PDF in the sidebar, then ask anything about it.</p>',
    unsafe_allow_html=True,
)

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📎 Sources", expanded=False):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(
                        f'<div class="source-chip"><b>#{i}</b>  {src}</div>',
                        unsafe_allow_html=True,
                    )

# Input
if prompt := st.chat_input("Ask something about your document…"):
    # Guard: require a document
    if not st.session_state.doc_info:
        st.warning("⚠️ Please upload and index a PDF first using the sidebar.")
        st.stop()

    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Query API
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                resp = requests.post(
                    f"{API_BASE}/query",
                    json={
                        "query": prompt,
                        "document_id": st.session_state.doc_info.get("document_id"),
                    },
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    answer = data["answer"]
                    sources = data.get("sources", [])

                    st.markdown(answer)
                    if sources:
                        with st.expander("📎 Sources", expanded=False):
                            for i, src in enumerate(sources, 1):
                                st.markdown(
                                    f'<div class="source-chip"><b>#{i}</b>  {src}</div>',
                                    unsafe_allow_html=True,
                                )

                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer, "sources": sources}
                    )

                elif resp.status_code == 429:
                    detail = resp.json().get("detail", "Rate limit exceeded.")
                    st.warning(f"⏱️ {detail}")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": f"⏱️ {detail}"}
                    )
                elif resp.status_code == 404:
                    msg = "No relevant information found for that query in the indexed document."
                    st.info(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                else:
                    detail = resp.json().get("detail", resp.text)
                    st.error(f"API error ({resp.status_code}): {detail}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot reach the API. Is Uvicorn running on http://127.0.0.1:8000?")
            except requests.exceptions.Timeout:
                st.error("⏱️ The request timed out. Please try again.")
