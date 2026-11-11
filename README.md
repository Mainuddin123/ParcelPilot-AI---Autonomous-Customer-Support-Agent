# 📦 ParcelPilot AI

### AI-Powered Customer Support Decision Assistant

ParcelPilot AI is an AI-powered customer support decision assistant designed to help logistics and parcel operations teams handle customer queries using structured order data, policy documents, RAG-based retrieval, and workflow-driven decision logic.

---

## 🚀 Features

- 📦 Order status tracking
- ❌ Order cancellation decisions
- 💰 Service credit eligibility evaluation
- 🚨 Ticket escalation with confirmation
- 📄 RAG-based policy and agreement retrieval
- 🤖 AI-generated responses
- 🛡️ Structured fallback when the LLM is unavailable
- 💬 Interactive Streamlit chat interface
- 🌐 API support

---

## 🏗️ Project Architecture

```text
parcelpilot-ai-agent/
│
├── data/
│   ├── ParcelPilot_Assessment_Data.xlsx
│   └── documents/
│       ├── 01_Support_Policy_v3_CURRENT.pdf
│       ├── 02_Support_Policy_v2_DEPRECATED.pdf
│       ├── 03_Cancellation_and_Service_Credit_SOP_v4.pdf
│       ├── 04_Product_Operations_Guide_and_Known_Issues.pdf
│       ├── 05_Northstar_Logistics_Enterprise_Agreement.pdf
│       └── 06_LumenWorks_Service_Agreement.pdf
│
├── src/
│   ├── agent.py
│   ├── api.py
│   ├── config.py
│   ├── data_loader.py
│   ├── escalation_action.py
│   ├── llm.py
│   ├── response_generator.py
│   ├── session_manager.py
│   ├── workflow.py
│   │
│   ├── rag/
│   │   ├── chunking.py
│   │   ├── document_loader.py
│   │   ├── retriever.py
│   │   └── vector_store.py
│   │
│   └── tools/
│       ├── cancellation_tools.py
│       ├── order_tools.py
│       ├── service_credit_tools.py
│       └── ticket_tools.py
│
├── storage/
│   ├── chunks.pkl
│   └── faiss_index.bin
│
├── main.py
├── streamlit_app.py
├── requirements.txt
└── README.md
```

---

## 🧠 How It Works

```text
Customer Query
      │
      ▼
Input Guardrails + Workflow Detection
      │
      ├── Structured workflows
      │      ├── Order / account lookup
      │      ├── Cancellation / service-credit rules
      │      └── Ticket validation + confirmed escalation
      │
      └── Policy / knowledge questions
             ├── FAISS dense retrieval + BM25
             ├── RRF fusion + Cross-Encoder reranking
             └── Gemini response with source references
                              │
                              ▼
                 Output Validation + Fallback
```

---

## 📦 Supported Workflows

### 1. Order Status

Retrieves available order information including:

- Order ID
- Carrier
- Current status
- Scheduled pickup window
- Actual pickup time
- Relevant order notices

Example query:

```text
What is the status of my order?
```

---

### 2. Cancellation Decision

Evaluates cancellation eligibility using:

- Order status
- Pickup status
- Customer-specific agreements
- Applicable support policies
- Cancellation and service credit SOPs

Example query:

```text
Can I cancel this order?
```

---

### 3. Service Credit Decision

Checks whether a customer may be eligible for a service credit based on available order information and applicable conditions.

Example query:

```text
Am I eligible for a service credit?
```

---

### 4. Escalation Workflow

The escalation process uses confirmation before creating an escalation.

```text
Customer requests escalation
            ↓
System identifies ticket
            ↓
Confirmation requested
            ↓
Customer replies Yes or No
            ↓
Escalation created or cancelled
```

Example query:

```text
I want to escalate this issue.
```

---

## 🔎 Advanced RAG Pipeline

The upgraded retrieval branch implements:
- Dense semantic retrieval using FAISS
- Sparse lexical retrieval using BM25
- Reciprocal Rank Fusion (RRF)
- Cross-Encoder reranking
- Account-scoped customer-agreement filtering and inactive-document exclusion

## 🛡️ Guardrails and Observability

- Basic input validation and prompt-injection pattern checks
- Output checks for empty, oversized, and obvious secret-bearing responses
- LangSmith tracing for agent execution, retrieval, response generation, and Gemini calls
- Retrieval evaluation script reporting Precision@K, Recall@K, MRR, and nDCG@K

These checks are defense-in-depth measures, not a guarantee against all prompt injection or data leakage. Evaluation scores must be measured using reviewed relevance labels.

Set these environment variables in your local environment or deployment secrets:

```env
GEMINI_API_KEY=your_gemini_api_key
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=parcelpilot-ai
```

Run retrieval evaluation after reviewing the relevant document IDs in `evaluation_dataset.json`:

```bash
python evaluate_rag.py
```

## 🤖 RAG-Based Document Retrieval

ParcelPilot AI uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from support policies, SOPs, product documentation, and customer agreements.

The workflow includes:

1. Loading PDF documents
2. Splitting documents into chunks
3. Generating vector embeddings
4. Storing embeddings in FAISS
5. Retrieving relevant document chunks
6. Using retrieved context to support decisions and responses

---

## 🛡️ Reliability and Fallback

ParcelPilot AI supports a structured fallback mechanism.

### AI Response

When the LLM is available:

```text
Customer Query
      ↓
Structured Data + Retrieved Documents
      ↓
LLM
      ↓
AI-Generated Response
```

### Structured Fallback

If the LLM is unavailable or reaches an API quota limit:

```text
Customer Query
      ↓
Structured Data
      ↓
Workflow Decision Logic
      ↓
Fallback Response
```

This allows core workflows such as order lookup, cancellation evaluation, service credit decisions, and escalation handling to continue using available structured data and decision logic.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| Streamlit | Interactive chat interface |
| FastAPI | API layer |
| Pandas | Structured data processing |
| FAISS | Dense vector retrieval |\n| BM25 | Sparse keyword retrieval |\n| Reciprocal Rank Fusion | Hybrid ranking fusion |\n| Cross-Encoder | Retrieved-document reranking |\n| LangSmith | LLM and retrieval tracing |
| Sentence Transformers | Text embeddings |
| Google Gemini | AI response generation |
| PyPDF | PDF document processing |
| SQLite | Local escalation persistence and duplicate protection |
| Python Dotenv | Environment variable management |

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Mainuddin123/parcelpilot-ai-agent.git
```

```bash
cd parcelpilot-ai-agent
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### macOS/Linux

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key\n\nLANGSMITH_TRACING=true\nLANGSMITH_TRACING_V2=true\nLANGSMITH_API_KEY=your_langsmith_api_key\nLANGSMITH_PROJECT=parcelpilot-ai\nLANGSMITH_HIDE_INPUTS=true\nLANGSMITH_HIDE_OUTPUTS=true
```

> ⚠️ Do not commit your API keys or `.env` file to GitHub.

---

## ▶️ Running the Application

### Run the Streamlit Application

```bash
streamlit run streamlit_app.py
```

### Optional API Layer\n\nThe FastAPI module remains available for separate API experiments, but the Streamlit application does not depend on it.\n\n### Run the Terminal Application

```bash
python main.py
```

---

## 🌐 API Usage

The project includes an API layer for programmatic access.

Example request:

```json
{
  "query": "What is the status of my order?",
  "account_id": "ACCT-001",
  "order_id": "ORD-1001",
  "ticket_id": null
}
```

---

## 💬 Example Queries

```text
What is the status of my order?

Can I cancel this order?

Am I eligible for a service credit?

I want to escalate this issue.

What is the cancellation policy for my order?
```

---

## 📊 Data Sources

The system uses:

- Structured account data
- Order and shipment information
- Ticket information
- Support policies
- Cancellation and service credit SOPs
- Product operations documentation
- Customer-specific service agreements

These sources are used to provide context-aware and policy-informed responses.

---

## 🔮 Future Improvements

- User authentication
- Persistent chat history
- Database integration
- Real-time order tracking
- Automated testing
- Docker containerization
- Cloud deployment
- Multi-user support
- Improved LLM fallback strategies
- Admin dashboard

---

## 👨‍💻 Author

**Mainuddin**

Engineering Graduate | Aspiring AI Engineer & Data Scientist

GitHub: https://github.com/Mainuddin123

---

## 📄 License

This project is developed for educational and assessment purposes.

---

## ⭐ Key Highlights

- AI-powered customer support assistant
- Structured order data processing
- Policy-aware decision making
- RAG-based document retrieval
- Cancellation workflow
- Service credit evaluation
- Confirmation-based escalation
- Streamlit chat interface
- API integration
- LLM fallback using structured decision logic

---

## ⚡ Reliability, Performance and Safety

The upgrade branch includes the following implementation details:

- **Lazy RAG initialization:** embedding/vector retrieval is not initialized for structured order, cancellation, service-credit, or account workflows.
- **Process-level model reuse:** the embedding model, Cross-Encoder, and read-only retriever are reused across Streamlit chat sessions in one Python process. The first RAG request can still be slower because it performs cold initialization.
- **Hybrid retrieval fallback:** dense FAISS + BM25 + RRF results remain available if Cross-Encoder loading or inference fails.
- **Bounded Gemini calls:** requests use a configurable timeout (GEMINI_TIMEOUT_MS, default 20,000 ms) and at most one retry for recognized transient failures. LLM failures fall back to structured information where available.
- **Retrieval fallback:** if document retrieval fails, the app returns a clearly labelled response based only on available structured records; it does not invent policy details.
- **Account isolation:** order and ticket lookups require an Account ID and verify ownership. Customer-specific agreement chunks are filtered by account.
- **Escalation confirmation:** a ticket is revalidated immediately before the action is recorded. A negative confirmation cancels the action.
- **Idempotent escalation store:** SQLite persists local demo escalations and prevents more than one escalation record per ticket. The SQLite file is stored under storage/escalations.sqlite3.

### Deployment limitation

The SQLite escalation store is intended for a **single-instance local/demo deployment**. It is not a shared database for multiple app replicas and may not persist on ephemeral hosting platforms. A production multi-instance deployment should use a shared transactional database and authenticated user identity. The demo does not connect to a real carrier or ticketing platform.

### LangSmith monitoring

Set LANGSMITH_TRACING=true, LANGSMITH_API_KEY, and LANGSMITH_PROJECT=parcelpilot-ai in .env. Traced operations include agent processing, hybrid retrieval, response generation, and Gemini generation. Keep input/output hiding enabled when tracing customer-like data.

### Run tests and retrieval evaluation

```bash
python -m pytest test_upgrade.py -q
python evaluate_rag.py
```

The retrieval evaluation uses reviewed document/page labels in evaluation_dataset.json and reports Precision@K, Recall@K, MRR, and nDCG@K. These metrics are only meaningful after the relevance labels have been manually checked. Record the output as the measured result; do not claim a score before running the script.

The Streamlit interface displays measured request latency. Compare the first RAG request (cold start) with later requests (warm start); structured workflows should avoid initializing the RAG models.
