import streamlit as st
import requests
import uuid


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="ParcelPilot AI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


API_URL = "http://127.0.0.1:8000/query"


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())

if "account_id" not in st.session_state:
    st.session_state.account_id = "ACCT-001"

if "order_id" not in st.session_state:
    st.session_state.order_id = "ORD-1001"

if "ticket_id" not in st.session_state:
    st.session_state.ticket_id = ""


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def save_current_chat():
    """Save the current conversation."""

    if st.session_state.messages:
        st.session_state.conversations[
            st.session_state.current_chat_id
        ] = st.session_state.messages.copy()


def new_chat():
    """Create a new conversation."""

    save_current_chat()

    st.session_state.current_chat_id = str(
        uuid.uuid4()
    )

    st.session_state.messages = []


def get_chat_title(messages):
    """Generate a title from the first user message."""

    for message in messages:

        if message["role"] == "user":

            text = message["content"]

            if len(text) > 35:
                return text[:35] + "..."

            return text

    return "New Conversation"


def load_chat(chat_id):
    """Load a previous conversation."""

    save_current_chat()

    st.session_state.current_chat_id = chat_id

    st.session_state.messages = (
        st.session_state.conversations[
            chat_id
        ].copy()
    )


# =========================================================
# PROFESSIONAL CSS
# =========================================================

st.markdown(
    """
<style>

/* ---------------------------------------------------------
   MAIN APPLICATION
--------------------------------------------------------- */

.stApp {
    background-color: #FFFFFF;
}


/* ---------------------------------------------------------
   MAIN CONTENT
--------------------------------------------------------- */

.block-container {
    max-width: 1050px;
    padding-top: 2.5rem;
    padding-bottom: 7rem;
}


/* ---------------------------------------------------------
   SIDEBAR
--------------------------------------------------------- */

[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #1F2937;
}

[data-testid="stSidebar"] * {
    color: #F9FAFB;
}


/* ---------------------------------------------------------
   SIDEBAR INPUTS
--------------------------------------------------------- */

[data-testid="stSidebar"] input {
    background-color: #1F2937 !important;
    color: #F9FAFB !important;
    border: 1px solid #374151 !important;
    border-radius: 8px !important;
}

[data-testid="stSidebar"] input:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 1px #6366F1 !important;
}


/* ---------------------------------------------------------
   SIDEBAR BUTTONS
--------------------------------------------------------- */

[data-testid="stSidebar"] .stButton button {
    background-color: #1F2937;
    color: #F9FAFB;
    border: 1px solid #374151;
    border-radius: 8px;
    min-height: 40px;
}

[data-testid="stSidebar"] .stButton button:hover {
    border-color: #6366F1;
    color: #FFFFFF;
}


/* ---------------------------------------------------------
   APPLICATION HEADER
--------------------------------------------------------- */

.app-title {
    font-size: 38px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 4px;
}

.app-subtitle {
    color: #6B7280;
    font-size: 16px;
    margin-bottom: 30px;
}


/* ---------------------------------------------------------
   WELCOME SCREEN
--------------------------------------------------------- */

.welcome-box {
    text-align: center;
    padding: 110px 20px;
}

.welcome-icon {
    font-size: 48px;
    margin-bottom: 15px;
}

.welcome-title {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 10px;
}

.welcome-text {
    color: #6B7280;
    font-size: 16px;
    max-width: 600px;
    margin: auto;
    line-height: 1.6;
}


/* ---------------------------------------------------------
   USER MESSAGE
--------------------------------------------------------- */

.user-box {
    background-color: #F3F4F6;
    border-left: 3px solid #6366F1;
    padding: 15px 18px;
    border-radius: 8px;
    margin-top: 15px;
    margin-bottom: 18px;
    color: #111827;
}


/* ---------------------------------------------------------
   ASSISTANT
--------------------------------------------------------- */

.assistant-name {
    font-weight: 700;
    color: #4F46E5;
    margin-top: 20px;
    margin-bottom: 8px;
}


/* ---------------------------------------------------------
   STATUS
--------------------------------------------------------- */

.status-success {
    color: #16A34A;
    font-size: 13px;
    font-weight: 600;
}

.status-fallback {
    color: #D97706;
    font-size: 13px;
    font-weight: 600;
}

.status-error {
    color: #DC2626;
    font-size: 13px;
    font-weight: 600;
}


/* ---------------------------------------------------------
   SOURCES
--------------------------------------------------------- */

[data-testid="stExpander"] {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
}


/* ---------------------------------------------------------
   CHAT INPUT
--------------------------------------------------------- */

[data-testid="stChatInput"] {
    border: 1px solid #D1D5DB;
    border-radius: 10px;
}


/* ---------------------------------------------------------
   HIDE STREAMLIT DEFAULT ELEMENTS
--------------------------------------------------------- */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("📦 ParcelPilot AI")

    st.caption(
        "Customer Support Decision Assistant"
    )

    st.divider()

    st.subheader("Customer Details")

    account_id = st.text_input(
        "Account ID",
        value=st.session_state.account_id
    )

    order_id = st.text_input(
        "Order ID (optional)",
        value=st.session_state.order_id
    )

    ticket_id = st.text_input(
        "Ticket ID (optional)",
        value=st.session_state.ticket_id
    )

    st.session_state.account_id = account_id
    st.session_state.order_id = order_id
    st.session_state.ticket_id = ticket_id

    st.divider()

    st.subheader("💬 Chat History")

    previous_chats = [
        (chat_id, conversation)
        for chat_id, conversation
        in st.session_state.conversations.items()
        if chat_id != st.session_state.current_chat_id
    ]

    if previous_chats:

        for chat_id, conversation in reversed(
            previous_chats
        ):

            title = get_chat_title(
                conversation
            )

            if st.button(
                title,
                key=f"chat_{chat_id}",
                use_container_width=True
            ):

                load_chat(chat_id)
                st.rerun()

    else:

        st.caption(
            "No previous conversations"
        )

    st.divider()

    if st.button(
        "＋ New Chat",
        use_container_width=True
    ):

        new_chat()
        st.rerun()


# =========================================================
# MAIN HEADER
# =========================================================

st.markdown(
    """
    <div class="app-title">
        📦 ParcelPilot AI
    </div>

    <div class="app-subtitle">
        AI-powered customer support decision assistant
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# WELCOME SCREEN
# =========================================================

# =========================================================
# WELCOME SCREEN
# =========================================================

if not st.session_state.messages:

    st.markdown(
        """
<div class="welcome-box">

<div class="welcome-icon">📦</div>

<div class="welcome-title">
How can I help you today?
</div>

<div class="welcome-text">
Ask about your parcel, cancellation, escalation,
service credit, or any customer support query.
</div>

</div>
""",
        unsafe_allow_html=True
    )

# =========================================================
# DISPLAY MESSAGES
# =========================================================

for message in st.session_state.messages:

    role = message.get(
        "role"
    )

    content = message.get(
        "content",
        ""
    )

    # -----------------------------------------------------
    # USER MESSAGE
    # -----------------------------------------------------

    if role == "user":

        st.markdown(
            f"""
<div class="user-box">
<b>You</b><br><br>
{content}
</div>
""",
            unsafe_allow_html=True
        )

    # -----------------------------------------------------
    # ASSISTANT MESSAGE
    # -----------------------------------------------------

    elif role == "assistant":

        st.markdown(
            """
<div class="assistant-name">
🤖 ParcelPilot AI
</div>
""",
            unsafe_allow_html=True
        )

        st.markdown(
            content
        )

        workflow = message.get(
            "workflow"
        )

        if workflow:

            st.caption(
                f"Workflow used: `{workflow}`"
            )

        status = message.get(
            "status"
        )

        if status == "success":

            st.markdown(
                """
<div class="status-success">
● AI response generated
</div>
""",
                unsafe_allow_html=True
            )

        elif status == "fallback_response":

            st.markdown(
                """
<div class="status-fallback">
● Response generated from structured data
</div>
""",
                unsafe_allow_html=True
            )

        elif status == "error":

            st.markdown(
                """
<div class="status-error">
● Request could not be completed
</div>
""",
                unsafe_allow_html=True
            )

        citations = message.get(
            "citations",
            []
        )

        if citations:

            with st.expander(
                "📚 Sources Used"
            ):

                for citation in citations:

                    source = citation.get(
                        "source",
                        "Unknown source"
                    )

                    page = citation.get(
                        "page",
                        "N/A"
                    )

                    source_type = citation.get(
                        "source_type",
                        ""
                    )

                    st.markdown(
                        f"**{source}**  \n"
                        f"Page: {page}  \n"
                        f"Type: `{source_type}`"
                    )

                    st.divider()


# =========================================================
# CHAT INPUT
# =========================================================

query = st.chat_input(
    "Ask about your parcel, cancellation, escalation, or service credit..."
)


# =========================================================
# PROCESS QUERY
# =========================================================

if query:

    query = query.strip()

    if query:

        # -------------------------------------------------
        # ADD USER MESSAGE
        # -------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": query
            }
        )

        save_current_chat()

        # -------------------------------------------------
        # BUILD API PAYLOAD
        # -------------------------------------------------

        payload = {
            "query": query,

            # IMPORTANT:
            # Send the current chat ID to the backend
            "session_id": (
                st.session_state.current_chat_id
            )
        }

        if account_id.strip():

            payload["account_id"] = (
                account_id.strip()
            )

        if order_id.strip():

            payload["order_id"] = (
                order_id.strip()
            )

        if ticket_id.strip():

            payload["ticket_id"] = (
                ticket_id.strip()
            )

        # -------------------------------------------------
        # API REQUEST
        # -------------------------------------------------

        try:

            with st.spinner(
                "ParcelPilot AI is analyzing your request..."
            ):

                response = requests.post(
                    API_URL,
                    json=payload,
                    timeout=90
                )

                response.raise_for_status()

                data = response.json()

            # -------------------------------------------------
            # EXTRACT API RESPONSE
            # -------------------------------------------------

            answer = data.get(
                "answer",
                "No response was generated."
            )

            structured_data = data.get(
                "structured_data",
                {}
            )

            workflow = structured_data.get(
                "workflow",
                "general"
            )

            citations = data.get(
                "citations",
                []
            )

            status = data.get(
                "status",
                "success"
            )

            # -------------------------------------------------
            # ADD ASSISTANT RESPONSE
            # -------------------------------------------------

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "workflow": workflow,
                    "citations": citations,
                    "status": status
                }
            )

        # -------------------------------------------------
        # CONNECTION ERROR
        # -------------------------------------------------

        except requests.exceptions.ConnectionError:

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "⚠️ Unable to connect to the "
                        "ParcelPilot API.\n\n"
                        "Make sure the FastAPI server "
                        "is running."
                    ),
                    "workflow": "system",
                    "citations": [],
                    "status": "error"
                }
            )

        # -------------------------------------------------
        # TIMEOUT ERROR
        # -------------------------------------------------

        except requests.exceptions.Timeout:

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "⚠️ The request took too long "
                        "to complete.\n\n"
                        "Please try again."
                    ),
                    "workflow": "system",
                    "citations": [],
                    "status": "error"
                }
            )

        # -------------------------------------------------
        # HTTP ERROR
        # -------------------------------------------------

        except requests.exceptions.HTTPError:

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        f"⚠️ API error: "
                        f"{response.status_code}"
                    ),
                    "workflow": "system",
                    "citations": [],
                    "status": "error"
                }
            )

        # -------------------------------------------------
        # UNEXPECTED ERROR
        # -------------------------------------------------

        except Exception:

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "⚠️ An unexpected error occurred. "
                        "Please try again."
                    ),
                    "workflow": "system",
                    "citations": [],
                    "status": "error"
                }
            )

        # -------------------------------------------------
        # SAVE CONVERSATION
        # -------------------------------------------------

        save_current_chat()

        st.rerun()