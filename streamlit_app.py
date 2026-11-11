import streamlit as st
import uuid
import time
import html

from src.agent import ParcelPilotAgent

import pandas as pd
from pathlib import Path

DATA_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "ParcelPilot_Assessment_Data.xlsx"
)

@st.cache_data
def load_customer_data():

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Customer dataset not found: {DATA_FILE}"
        )

    accounts = pd.read_excel(DATA_FILE, sheet_name="accounts")
    orders = pd.read_excel(DATA_FILE, sheet_name="orders")
    tickets = pd.read_excel(DATA_FILE, sheet_name="tickets")

    required_columns = {
        "accounts": {"account_id", "account_name"},
        "orders": {"order_id", "account_id", "carrier", "status"},
        "tickets": {"ticket_id", "account_id", "subject"}
    }

    datasets = {
        "accounts": accounts,
        "orders": orders,
        "tickets": tickets
    }

    for name, df in datasets.items():
        missing = required_columns[name] - set(df.columns)

        if missing:
            raise ValueError(
                f"Missing columns in {name}: {sorted(missing)}"
            )

    if accounts.empty:
        raise ValueError("No customer accounts found.")

    return accounts, orders, tickets



def reset_customer_selections():
    st.session_state["order_selector"] = ""
    st.session_state["ticket_selector"] = ""


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agents" not in st.session_state:
    st.session_state.agents = {}

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

/* =========================================================
   1. THEME VARIABLES
========================================================= */

:root {
    --pp-bg: #080d19;
    --pp-surface: #111a2b;
    --pp-border: rgba(148, 163, 184, 0.17);
    --pp-text: #e8eef9;
    --pp-muted: #9aa9bf;
    --pp-accent: #8b7cff;
    --pp-orange: #f97316;
}

/* =========================================================
   2. MAIN APPLICATION BACKGROUND
========================================================= */

.stApp {
    background:
        radial-gradient(
            ellipse at 12% 0%,
            rgba(99,102,241,.16),
            transparent 34%
        ),
        radial-gradient(
            ellipse at 88% 12%,
            rgba(6,182,212,.10),
            transparent 30%
        ),
        linear-gradient(
            145deg,
            #080d19 0%,
            #0b1220 48%,
            #0c1424 100%
        );

    color: var(--pp-text);
}

[data-testid="stAppViewContainer"] {
    background-color: #080d19 !important;
}

[data-testid="stHeader"] {
    background: #080d19 !important;
}

.block-container {
    max-width: 1120px;
    padding-top: 2.2rem;
    padding-bottom: 7rem;
}

/* =========================================================
   3. SIDEBAR
========================================================= */

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #0c1424 0%,
        #101a2c 100%
    ) !important;

    border-right: 1px solid var(--pp-border);
}

[data-testid="stSidebar"] * {
    color: var(--pp-text);
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] .stCaption {
    color: var(--pp-muted);
}

[data-testid="stSidebar"] hr,
hr {
    border-color: var(--pp-border) !important;
}

/* Sidebar labels */

[data-testid="stSidebar"] label {
    color: #dce6f5 !important;
    font-weight: 600 !important;
}

/* Sidebar buttons */

[data-testid="stSidebar"] .stButton button {
    background: #172338;
    color: var(--pp-text);
    border: 1px solid #2b3a54;
    border-radius: 10px;
    min-height: 42px;
    transition: all .18s ease;
}

[data-testid="stSidebar"] .stButton button:hover {
    background: #202f49;
    border-color: var(--pp-accent);
    color: #fff;
    transform: translateY(-1px);
}



/* =========================================================
   5. TYPOGRAPHY
========================================================= */

html,
body,
[class*="css"] {
    color: var(--pp-text);
}

[data-testid="stMarkdownContainer"] {
    color: #dce6f5;
}

[data-testid="stMarkdownContainer"] strong {
    color: #f4f7ff;
}

[data-testid="stMarkdownContainer"] a {
    color: #75d8ec;
}

h1, h2, h3, h4, h5, h6 {
    color: #f3f6ff !important;
    letter-spacing: -.025em;
}

/* =========================================================
   6. ANIMATED RAINBOW BRAND HEADING
========================================================= */

.app-title {
    display: flex;
    align-items: center;
    gap: 14px;
    width: fit-content;

    font-size: clamp(34px, 4vw, 46px);
    font-weight: 850;
    letter-spacing: -1.5px;
    line-height: 1.12;

    margin: 8px 0 10px;
}

.app-title-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;

    font-size: 40px;

    filter: drop-shadow(
        0 5px 15px rgba(99,102,241,.32)
    );
}

.app-title-text {
    background: linear-gradient(
        90deg,
        #A78BFA,
        #60A5FA,
        #22D3EE,
        #34D399,
        #F472B6,
        #A78BFA
    );

    background-size: 300% 100%;
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    animation: parcelpilot-rainbow 7s linear infinite;
}

@keyframes parcelpilot-rainbow {
    0% {
        background-position: 0% 50%;
    }

    100% {
        background-position: 300% 50%;
    }
}

.app-subtitle {
    color: #AAB7CA !important;
    font-size: 14px;
    font-weight: 500;
    margin: 0 0 25px 3px;
}

@media (prefers-reduced-motion: reduce) {
    .app-title-text {
        animation: none !important;
    }
}

/* =========================================================
   7. WELCOME CARD
========================================================= */

.welcome-box {
    max-width: 760px;
    margin: 18px auto 20px !important;
    padding: 42px 24px !important;
    min-height: 0 !important;

    text-align: center;

    border-radius: 20px !important;
    border: 1px solid rgba(116,132,169,.22) !important;

    background:
        radial-gradient(
            circle at 50% 0%,
            rgba(80,92,150,.13),
            transparent 58%
        ),
        linear-gradient(
            145deg,
            #101a2c 0%,
            #0c1525 100%
        ) !important;

    box-shadow:
        0 16px 42px rgba(0,0,0,.20),
        inset 0 1px 0 rgba(255,255,255,.025) !important;
}

.welcome-icon {
    font-size: 42px !important;
    margin-bottom: 10px !important;

    filter: drop-shadow(
        0 8px 20px rgba(99,102,241,.25)
    );
}

.welcome-title {
    font-size: 25px !important;
    font-weight: 750;
    color: #f3f6ff;
    margin-bottom: 8px !important;
}

.welcome-text {
    font-size: 14px !important;
    line-height: 1.6 !important;
    max-width: 570px !important;
    margin: auto;
    color: #a5b2c7 !important;
}

/* =========================================================
   8. CHAT MESSAGES
========================================================= */

.user-box {
    background: linear-gradient(
        135deg,
        rgba(70,83,145,.28),
        rgba(34,52,82,.48)
    );

    border: 1px solid rgba(129,140,248,.25);
    border-left: 3px solid #8b7cff;

    padding: 17px 20px;
    border-radius: 6px 16px 16px 16px;
    margin: 18px 0;

    color: #edf2ff;
    box-shadow: 0 8px 24px rgba(0,0,0,.12);

    line-height: 1.65;
    overflow-wrap: anywhere;
}

.assistant-name {
    font-weight: 750;
    color: #a99cff;
    margin: 24px 0 9px;
    letter-spacing: .01em;
}

/* =========================================================
   9. STATUS PILLS
========================================================= */

.status-success,
.status-fallback,
.status-error {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;

    font-size: 12px;
    font-weight: 700;
    margin: 6px 0 12px;
}

.status-success {
    color: #86efac;
    background: rgba(34,197,94,.10);
    border: 1px solid rgba(34,197,94,.22);
}

.status-fallback {
    color: #fcd34d;
    background: rgba(245,158,11,.10);
    border: 1px solid rgba(245,158,11,.22);
}

.status-error {
    color: #fda4af;
    background: rgba(244,63,94,.10);
    border: 1px solid rgba(244,63,94,.22);
}

/* =========================================================
   10. EXPANDERS AND SOURCES
========================================================= */

[data-testid="stExpander"] {
    background: rgba(17,26,43,.78);
    border: 1px solid var(--pp-border);
    border-radius: 14px;
    overflow: hidden;
}

[data-testid="stExpander"] summary {
    color: #dce6f5;
}

[data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
    color: #cbd7e8;
}

/* =========================================================
   11. CHAT COMPOSER - ORANGE ACCENT
========================================================= */

[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"] {
    background: #080d19 !important;
    background-color: #080d19 !important;
}

[data-testid="stChatInput"] {
    background: #101827 !important;
    background-color: #101827 !important;

    border: 1.5px solid #F97316 !important;
    border-radius: 15px !important;

    box-shadow: 0 5px 25px rgba(0,0,0,.3) !important;

    transition:
        border-color .18s ease,
        box-shadow .18s ease !important;
}

[data-testid="stChatInput"] > div {
    background: #101827 !important;
    background-color: #101827 !important;
}

/* Typed text */

[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea:focus {
    background: transparent !important;
    background-color: transparent !important;

    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;

    caret-color: #F97316 !important;
    font-size: 15px !important;
    opacity: 1 !important;
}

/* Placeholder */

[data-testid="stChatInput"] textarea::placeholder {
    color: #AAB7CA !important;
    -webkit-text-fill-color: #AAB7CA !important;
    opacity: 1 !important;
}

/* Send button */

[data-testid="stChatInput"] button {
    background: #F97316 !important;
    border: none !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
}

/* White send arrow */

[data-testid="stChatInput"] button svg {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}

[data-testid="stChatInput"] button:hover {
    background: #EA580C !important;
}

/* Composer focus */

[data-testid="stChatInput"]:focus-within {
    border-color: #FB923C !important;

    box-shadow:
        0 0 0 2px rgba(249,115,22,.2),
        0 5px 25px rgba(0,0,0,.3) !important;
}

/* =========================================================
   12. OTHER INPUTS AND BUTTONS
========================================================= */

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="input"] > div,
.stTextInput input,
.stTextArea textarea {
    background: #111d30 !important;
    color: #edf2ff !important;

    border: 1px solid #34445f !important;
    border-radius: 10px !important;
}

.stButton button {
    border-radius: 10px;
    transition: all .18s ease;
}

.stButton button[kind="primary"] {
    background: linear-gradient(
        100deg,
        #6d5dfc,
        #3978df
    );

    border: 0;
    color: #fff;
}

.stButton button:hover {
    border-color: #8b7cff;
}

/* Alerts */

[data-testid="stAlert"] {
    background: #142238;
    border: 1px solid var(--pp-border);
    color: #e8eef9;
}

[data-testid="stSpinner"] p {
    color: #c5d2e5;
}

[data-testid="stCaptionContainer"] {
    color: #8fa0b8;
}

/* =========================================================
   13. FOOTER
========================================================= */

.app-footer {
    width: 100%;
    margin-top: 42px;
    padding: 18px 12px 10px;

    text-align: center;
    color: #8795aa;

    font-size: 12px;
    letter-spacing: .04em;

    border-top: 1px solid rgba(148,163,184,.14);
}

.app-footer strong {
    color: #f0a064;
    font-weight: 700;
}

/* =========================================
   DROPDOWN - BURGUNDY INDICATOR
========================================= */

[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #111d30 !important;
    border: 1px solid #C04459 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* Target the complete arrow compartment */
[data-testid="stSidebar"] [data-baseweb="select"]
> div > div:last-child,
[data-testid="stSidebar"] [data-baseweb="select"]
> div > div:last-child * {
    background: #3B1018 !important;
    background-color: #3B1018 !important;
    background-image: none !important;
}

/* Selected value */
[data-testid="stSidebar"] [data-baseweb="select"] span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Arrow icon */
[data-testid="stSidebar"] [data-baseweb="select"] svg {
    color: #FF9AAA !important;
    fill: #FF9AAA !important;
    stroke: #FF9AAA !important;
}

/* =========================================================
   14. HIDE STREAMLIT CHROME
========================================================= */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* =========================================
   FINAL DROPDOWN ARROW DESIGN
========================================= */

/* Arrow button */
[data-testid="stSidebar"] [data-testid="stSelectbox"]
button[aria-label="Open"] {
    background: #3B1018 !important;
    background-color: #3B1018 !important;

    border: none !important;
    outline: none !important;
    box-shadow: none !important;

    border-radius: 0 9px 9px 0 !important;
    min-width: 30px !important;
    width: 30px !important;
    padding: 0 !important;
}

/* Hover and focus */
[data-testid="stSidebar"] [data-testid="stSelectbox"]
button[aria-label="Open"]:hover,
[data-testid="stSidebar"] [data-testid="stSelectbox"]
button[aria-label="Open"]:focus,
[data-testid="stSidebar"] [data-testid="stSelectbox"]
button[aria-label="Open"]:focus-visible {
    background: #3B1018 !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

/* Arrow icon */
[data-testid="stSidebar"] [data-testid="stSelectbox"]
button[aria-label="Open"] svg {
    background: transparent !important;
    border: none !important;
    color: #FF9AAA !important;
    stroke: #FF9AAA !important;
    fill: none !important;
}

</style>
""",
    unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("📦 ParcelPilot AI")
    st.caption("Customer Support Decision Assistant")

    st.divider()
    st.subheader("Customer Details")

    # Load customer records from Excel
    accounts_df, orders_df, tickets_df = load_customer_data()

    # -----------------------------------------------------
    # ACCOUNT DROPDOWN
    # -----------------------------------------------------

    account_ids = (
        accounts_df["account_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    account_names = dict(
        zip(
            accounts_df["account_id"].astype(str),
            accounts_df["account_name"].astype(str)
        )
    )

    if st.session_state.get("account_selector") not in account_ids:
        st.session_state["account_selector"] = (
            st.session_state.account_id
            if st.session_state.account_id in account_ids
            else account_ids[0]
        )

    account_id = st.selectbox(
        "Account ID",
        options=account_ids,
        format_func=lambda x: (
            f"{x} — {account_names.get(x, '')}"
        ),
        key="account_selector",
        on_change=reset_customer_selections
    )

    # -----------------------------------------------------
    # ORDER DROPDOWN (ACCOUNT FILTERED)
    # -----------------------------------------------------

    account_orders = orders_df[
        orders_df["account_id"].astype(str) == account_id
    ]

    order_ids = (
        account_orders["order_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    order_options = [""] + order_ids

    if st.session_state.get("order_selector") not in order_options:
        st.session_state["order_selector"] = ""

    order_labels = {
        str(row["order_id"]):
        f'{row["order_id"]} — {row["carrier"]} ({row["status"]})'
        for _, row in account_orders.iterrows()
    }

    order_id = st.selectbox(
        "Order ID (optional)",
        options=order_options,
        format_func=lambda x: (
            "Select an order"
            if x == ""
            else order_labels.get(x, x)
        ),
        key="order_selector"
    )

    # -----------------------------------------------------
    # TICKET DROPDOWN (ACCOUNT FILTERED)
    # -----------------------------------------------------

    account_tickets = tickets_df[
        tickets_df["account_id"].astype(str) == account_id
    ]

    ticket_ids = (
        account_tickets["ticket_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    ticket_options = [""] + ticket_ids

    if st.session_state.get("ticket_selector") not in ticket_options:
        st.session_state["ticket_selector"] = ""

    ticket_labels = {
        str(row["ticket_id"]):
        f'{row["ticket_id"]} — {row["subject"]}'
        for _, row in account_tickets.iterrows()
    }

    ticket_id = st.selectbox(
        "Ticket ID (optional)",
        options=ticket_options,
        format_func=lambda x: (
            "No ticket"
            if x == ""
            else ticket_labels.get(x, x)
        ),
        key="ticket_selector"
    )

    # -----------------------------------------------------
    # UPDATE SESSION STATE
    # -----------------------------------------------------

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

        for chat_id, conversation in reversed(previous_chats):

            title = get_chat_title(conversation)

            if st.button(
                title,
                key=f"chat_{chat_id}",
                use_container_width=True
            ):
                load_chat(chat_id)
                st.rerun()

    else:
        st.caption("No previous conversations")

    st.divider()

    if st.button("＋ New Chat", use_container_width=True):
        new_chat()
        st.rerun()



# =========================================================
# MAIN HEADER
# =========================================================
st.markdown("""
<div class="app-title">
    <span class="app-title-icon">📦</span>
    <span class="app-title-text">ParcelPilot AI</span>
</div>
<div class="app-subtitle">
    AI-powered customer support decision assistant
</div>
""", unsafe_allow_html=True)


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
{html.escape(str(content))}
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

        latency_ms = message.get("latency_ms")
        if latency_ms is not None:
            st.caption(f"Response time: {latency_ms} ms")

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
        # DIRECT LOCAL AGENT EXECUTION (NO FASTAPI SERVER)
        # -------------------------------------------------

        try:
            started_at = time.perf_counter()
            with st.spinner(
                "ParcelPilot AI is analyzing your request..."
            ):
                chat_id = st.session_state.current_chat_id
                if chat_id not in st.session_state.agents:
                    st.session_state.agents[chat_id] = ParcelPilotAgent()

                agent = st.session_state.agents[chat_id]
                data = agent.process(
                    query=query,
                    account_id=st.session_state.account_id or None,
                    order_id=st.session_state.order_id or None,
                    ticket_id=st.session_state.ticket_id or None
)

            latency_ms = round((time.perf_counter() - started_at) * 1000, 1)

            answer = data.get("answer", "No response was generated.")
            structured_data = data.get("structured_data", {})
            workflow = structured_data.get("workflow", "general")
            citations = data.get("citations", [])
            status = data.get("status", "success")

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "workflow": workflow,
                    "citations": citations,
                    "status": status,
                    "latency_ms": latency_ms
                }
            )

        except Exception as error:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "⚠️ ParcelPilot encountered an internal error. "
                        "Please check the terminal logs and try again."
                    ),
                    "workflow": "system",
                    "citations": [],
                    "status": "error"
                }
            )
            print(f"ParcelPilot execution error: {error}")

        # -------------------------------------------------
        # SAVE CONVERSATION
        # -------------------------------------------------

        save_current_chat()

        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="app-footer">
        Developed by <strong>Khaja Mainuddin</strong>
    </div>
    """,
    unsafe_allow_html=True
)
