"""AI Document Assistant — Streamlit Frontend.

A conversational interface to upload PDFs and ask questions using RAG.
"""

import uuid

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_API_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0;
    }
    .sub-caption {
        font-size: 1rem;
        color: #666;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .feature-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.2rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------


def _init_session_state() -> None:
    defaults: dict = {
        "doc_id": None,
        "uploaded_file_name": None,
        "messages": [],
        "api_base_url": _DEFAULT_API_URL,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_session_state()

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def upload_document(
    file_bytes: bytes, file_name: str, api_url: str
) -> tuple[bool, str]:
    """Upload a PDF to the API.

    Returns:
        (True, doc_id) on success.
        (False, error_message) on failure.
    """
    doc_id = str(uuid.uuid4())[:8]
    try:
        response = requests.post(
            f"{api_url}/upload/{doc_id}",
            files={"file": (file_name, file_bytes, "application/pdf")},
            timeout=60,
        )
        if response.status_code == 200:
            return True, doc_id
        detail = response.json().get("detail", response.text)
        return False, f"Upload failed: {detail}"
    except requests.ConnectionError:
        return False, "Cannot connect to the API. Make sure the backend is running."
    except requests.Timeout:
        return False, "Request timed out. The document may be too large."
    except requests.RequestException as exc:
        return False, f"Request error: {exc}"


def ask_question(question: str, doc_id: str, api_url: str) -> tuple[bool, str]:
    """Send a question to the API.

    Returns:
        (True, answer) on success.
        (False, error_message) on failure.
    """
    try:
        response = requests.post(
            f"{api_url}/ask/{doc_id}",
            params={"question": question},
            timeout=30,
        )
        if response.status_code == 200:
            return True, response.json()["answer"]
        detail = response.json().get("detail", response.text)
        return False, f"Error: {detail}"
    except requests.ConnectionError:
        return False, "Cannot connect to the API. Make sure the backend is running."
    except requests.Timeout:
        return False, "Request timed out."
    except requests.RequestException as exc:
        return False, f"Request error: {exc}"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    api_url_input = st.text_input(
        "API Base URL",
        value=st.session_state.api_base_url,
        help="Base URL of the FastAPI backend (without trailing slash)",
    )
    st.session_state.api_base_url = api_url_input

    st.divider()

    st.markdown("## 📂 Document Upload")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF to start asking questions about it",
    )

    if uploaded_file is not None:
        if st.button("🚀 Process Document", type="primary", use_container_width=True):
            with st.spinner("Processing document… this may take a moment."):
                success, result = upload_document(
                    uploaded_file.getvalue(),
                    uploaded_file.name,
                    st.session_state.api_base_url,
                )
            if success:
                st.session_state.doc_id = result
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.messages = []
                st.success(f"✅ Document ready!\nID: `{result}`")
            else:
                st.error(result)

    # Active-document panel
    if st.session_state.doc_id:
        st.divider()
        st.markdown("### 📄 Active Document")
        st.info(
            f"**{st.session_state.uploaded_file_name}**\nID: `{st.session_state.doc_id}`"
        )

        if st.button("🗑️ Clear Document", use_container_width=True):
            st.session_state.doc_id = None
            st.session_state.uploaded_file_name = None
            st.session_state.messages = []
            st.rerun()

        # Chat export
        if st.session_state.messages:
            st.divider()
            chat_text = "\n\n".join(
                f"{'You' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
                for m in st.session_state.messages
            )
            st.download_button(
                "💾 Export Chat",
                data=chat_text,
                file_name="chat_history.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.markdown(
    '<p class="main-header">📄 AI Document Assistant</p>', unsafe_allow_html=True
)
st.markdown(
    '<p class="sub-caption">Upload a PDF and ask questions in plain English'
    " — powered by RAG + Google Gemini</p>",
    unsafe_allow_html=True,
)

if st.session_state.doc_id is None:
    # ---- Welcome / empty state ----
    st.info("👈 **Upload a PDF** from the sidebar to get started.", icon="💡")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="feature-card"><h3>📤 Upload</h3>'
            "<p>Select any PDF and click <b>Process Document</b>.</p></div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="feature-card"><h3>🤖 Analyze</h3>'
            "<p>The AI splits, embeds and indexes your document automatically.</p></div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="feature-card"><h3>💬 Ask</h3>'
            "<p>Type any question and get precise, source-grounded answers.</p></div>",
            unsafe_allow_html=True,
        )
else:
    # ---- Chat interface ----
    st.markdown(f"### 💬 Chat — *{st.session_state.uploaded_file_name}*")

    # Replay conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # New question input
    if prompt := st.chat_input("Ask a question about your document…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                success, answer = ask_question(
                    prompt,
                    st.session_state.doc_id,
                    st.session_state.api_base_url,
                )
            if success:
                st.markdown(answer)
            else:
                st.error(answer)
                answer = f"⚠️ {answer}"
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
