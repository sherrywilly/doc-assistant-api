"""AI Document Assistant — Streamlit Frontend.

A conversational interface to upload PDFs and ask questions using RAG.
Includes JWT-based login/register and per-user document management.
"""

import uuid

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_API_URL = "http://localhost:8000/api/v1"
_DEFAULT_AUTH_URL = "http://localhost:8001/auth"

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
    .login-box {
        max-width: 420px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 12px;
        background: #f8f9fa;
        border: 1px solid #dee2e6;
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
        "logged_in": False,
        "access_token": None,
        "username": None,
        "doc_id": None,
        "uploaded_file_name": None,
        "messages": [],
        "api_base_url": _DEFAULT_API_URL,
        "auth_base_url": _DEFAULT_AUTH_URL,
        "user_docs": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_session_state()

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state.access_token}"}


def register_user(username: str, password: str, auth_url: str) -> tuple[bool, str]:
    """Register a new account.

    Returns:
        (True, "") on success.
        (False, error_message) on failure.
    """
    try:
        response = requests.post(
            f"{auth_url}/register",
            json={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code == 201:
            return True, ""
        detail = response.json().get("detail", response.text)
        return False, detail
    except requests.ConnectionError:
        return False, "Cannot connect to the auth service."
    except requests.RequestException as exc:
        return False, str(exc)


def login_user(
    username: str, password: str, auth_url: str
) -> tuple[bool, str]:
    """Log in and return a JWT token.

    Returns:
        (True, access_token) on success.
        (False, error_message) on failure.
    """
    try:
        response = requests.post(
            f"{auth_url}/login",
            data={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code == 200:
            return True, response.json()["access_token"]
        detail = response.json().get("detail", response.text)
        return False, detail
    except requests.ConnectionError:
        return False, "Cannot connect to the auth service."
    except requests.RequestException as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Document API helpers
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
            headers=_auth_headers(),
            timeout=60,
        )
        if response.status_code == 200:
            return True, doc_id
        if response.status_code == 401:
            return False, "Session expired. Please log in again."
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
            headers=_auth_headers(),
            timeout=30,
        )
        if response.status_code == 200:
            return True, response.json()["answer"]
        if response.status_code == 401:
            return False, "Session expired. Please log in again."
        detail = response.json().get("detail", response.text)
        return False, f"Error: {detail}"
    except requests.ConnectionError:
        return False, "Cannot connect to the API. Make sure the backend is running."
    except requests.Timeout:
        return False, "Request timed out."
    except requests.RequestException as exc:
        return False, f"Request error: {exc}"


def fetch_user_docs(api_url: str) -> list[str]:
    """Retrieve the list of document IDs for the current user."""
    try:
        response = requests.get(
            f"{api_url}/docs/list",
            headers=_auth_headers(),
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get("documents", [])
    except requests.RequestException:
        pass
    return []


# ---------------------------------------------------------------------------
# Login / Register page
# ---------------------------------------------------------------------------


def render_auth_page():
    st.markdown(
        '<p class="main-header">📄 AI Document Assistant</p>', unsafe_allow_html=True
    )
    st.markdown(
        '<p class="sub-caption">Sign in to upload PDFs and ask questions'
        " — powered by RAG + Google Gemini</p>",
        unsafe_allow_html=True,
    )

    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Login", type="primary", use_container_width=True
                )
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    with st.spinner("Logging in…"):
                        ok, result = login_user(
                            username,
                            password,
                            st.session_state.auth_base_url,
                        )
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.access_token = result
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error(f"Login failed: {result}")

        with tab_register:
            with st.form("register_form"):
                new_username = st.text_input("Choose a username", key="reg_user")
                new_password = st.text_input(
                    "Choose a password (min 8 chars)",
                    type="password",
                    key="reg_pass",
                )
                confirm_password = st.text_input(
                    "Confirm password", type="password", key="reg_confirm"
                )
                reg_submitted = st.form_submit_button(
                    "Create Account", type="primary", use_container_width=True
                )
            if reg_submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    with st.spinner("Creating account…"):
                        ok, err = register_user(
                            new_username,
                            new_password,
                            st.session_state.auth_base_url,
                        )
                    if ok:
                        st.success(
                            "✅ Account created! Switch to the Login tab to sign in."
                        )
                    else:
                        st.error(f"Registration failed: {err}")
        st.markdown("</div>", unsafe_allow_html=True)

    # Service URL config below the login box
    with st.expander("⚙️ Service configuration"):
        st.session_state.auth_base_url = st.text_input(
            "Auth Service URL", value=st.session_state.auth_base_url
        )
        st.session_state.api_base_url = st.text_input(
            "API Service URL", value=st.session_state.api_base_url
        )


# ---------------------------------------------------------------------------
# Main app (authenticated)
# ---------------------------------------------------------------------------


def render_main_app():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.button("🚪 Logout", use_container_width=True):
            for key in [
                "logged_in",
                "access_token",
                "username",
                "doc_id",
                "uploaded_file_name",
                "messages",
                "user_docs",
            ]:
                st.session_state[key] = (
                    [] if key in ("messages", "user_docs") else None
                )
            st.session_state.logged_in = False
            st.rerun()

        st.divider()
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
            if st.button(
                "🚀 Process Document", type="primary", use_container_width=True
            ):
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
                    if result not in st.session_state.user_docs:
                        st.session_state.user_docs.append(result)
                    st.success(f"✅ Document ready!\nID: `{result}`")
                else:
                    if "Session expired" in result:
                        st.session_state.logged_in = False
                        st.rerun()
                    st.error(result)

        # Active-document panel
        if st.session_state.doc_id:
            st.divider()
            st.markdown("### 📄 Active Document")
            st.info(
                f"**{st.session_state.uploaded_file_name}**\n"
                f"ID: `{st.session_state.doc_id}`"
            )

            if st.button("🗑️ Clear Document", use_container_width=True):
                st.session_state.doc_id = None
                st.session_state.uploaded_file_name = None
                st.session_state.messages = []
                st.rerun()

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

        # My documents list
        if st.session_state.user_docs:
            st.divider()
            st.markdown("### 🗂️ My Documents")
            for doc in st.session_state.user_docs:
                label = f"📄 `{doc}`"
                if st.button(label, key=f"load_{doc}", use_container_width=True):
                    st.session_state.doc_id = doc
                    st.session_state.uploaded_file_name = doc
                    st.session_state.messages = []
                    st.rerun()

    # ---- Main content ----
    st.markdown(
        '<p class="main-header">📄 AI Document Assistant</p>', unsafe_allow_html=True
    )
    st.markdown(
        '<p class="sub-caption">Upload a PDF and ask questions in plain English'
        f" — powered by RAG + Google Gemini | Logged in as <b>{st.session_state.username}</b></p>",
        unsafe_allow_html=True,
    )

    if st.session_state.doc_id is None:
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
        st.markdown(f"### 💬 Chat — *{st.session_state.uploaded_file_name}*")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

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
                    if "Session expired" in answer:
                        st.session_state.logged_in = False
                        st.rerun()
                    st.error(answer)
                    answer = f"⚠️ {answer}"
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

if not st.session_state.logged_in:
    render_auth_page()
else:
    render_main_app()
