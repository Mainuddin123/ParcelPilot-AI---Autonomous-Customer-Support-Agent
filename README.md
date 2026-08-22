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
Intent / Workflow Detection
      │
      ├───────────────┬────────────────┬─────────────────┐
      ▼               ▼                ▼                 ▼
Order Status     Cancellation    Service Credit     Escalation
      │               │                │                 │
      └───────────────┴────────────────┴─────────────────┘
                              │
                              ▼
                 Structured Data Retrieval
                              │
                              ▼
                  RAG Document Retrieval
                              │
                              ▼
                    Decision Workflow
                              │
                              ▼
                     AI / Fallback Response
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
| LangChain | LLM and RAG integration |
| LangGraph | Workflow orchestration |
| FAISS | Vector similarity search |
| Sentence Transformers | Text embeddings |
| Google Gemini | AI response generation |
| PyPDF | PDF document processing |
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
GOOGLE_API_KEY=your_google_api_key
```

> ⚠️ Do not commit your API keys or `.env` file to GitHub.

---

## ▶️ Running the Application

### Run the Streamlit Application

```bash
streamlit run streamlit_app.py
```

### Run the Terminal Application

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
