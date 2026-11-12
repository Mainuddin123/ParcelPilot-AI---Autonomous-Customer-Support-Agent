# 📦 ParcelPilot AI – Autonomous Customer Support Agent

An AI-powered customer support decision assistant designed for parcel delivery and logistics operations. ParcelPilot AI combines structured workflow automation, Retrieval-Augmented Generation (RAG), hybrid document retrieval, and LLM-powered responses to assist customers with shipment tracking, cancellations, ticket escalation, and policy-related queries.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" alt="Python 3.11"/>
  <img src="https://img.shields.io/badge/Framework-Streamlit-FF4B4B?logo=streamlit" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/LLM-Google%20Gemini-4285F4?logo=google" alt="Google Gemini"/>
  <img src="https://img.shields.io/badge/Vector%20Database-ChromaDB-orange" alt="ChromaDB"/>
  <img src="https://img.shields.io/badge/Status-Development%20Validated-success" alt="Development Validated"/>
</p>

---

## 🚀 Project Overview

Traditional logistics customer support often requires agents to search through multiple systems, including order records, customer agreements, service policies, and standard operating procedures.

ParcelPilot AI addresses this challenge through an intelligent support assistant that combines structured operational data with contextual document retrieval.

The application identifies customer requests, routes them to appropriate workflows, retrieves relevant policy information, and generates contextual responses.

### Key Objectives

- Automate common logistics customer-support workflows.
- Provide accurate shipment tracking information.
- Support confirmation-based cancellation workflows.
- Facilitate ticket escalation with customer approval.
- Retrieve relevant policies from business documents.
- Maintain account-aware retrieval for customer-specific agreements.
- Improve response consistency through structured logic and RAG.

---

## ✨ Key Features

### 1. 📍 Intelligent Order Tracking
- Retrieve shipment information using order IDs.
- Display carrier and shipment status.
- Show scheduled pickup windows.
- Identify missing pickup information.

### 2. ❌ Confirmation-Based Cancellation
- Evaluate cancellation eligibility.
- Check applicable cancellation conditions.
- Request explicit customer confirmation.
- Revalidate eligibility before execution.
- Record local cancellation state using SQLite.
- Handle cancellation approval and rejection.

### 3. 🎫 Ticket Escalation
- Identify relevant support tickets.
- Request customer confirmation before escalation.
- Revalidate ticket ownership.
- Create escalation records.
- Apply idempotency safeguards to reduce duplicate actions.

### 4. 💰 Service Credit Assessment
- Evaluate service-credit eligibility.
- Consider applicable operational conditions.
- Retrieve customer-specific agreement rules.
- Present relevant eligibility information.

*Eligibility assessment does not automatically issue a financial credit.*

### 5. 🧠 Retrieval-Augmented Generation (RAG)
- Retrieve information from PDF policies and customer agreements.
- Combine dense and keyword-based retrieval.
- Apply Reciprocal Rank Fusion (RRF).
- Rerank retrieved passages using a Cross-Encoder.
- Generate contextual responses using Google Gemini.
- Display supporting document sources and page references.

### 6. 🔐 Security and Guardrails
- Account-aware document retrieval.
- Cross-account access checks.
- Prompt-injection pattern detection.
- Output validation.
- Confirmation before sensitive actions.
- Revalidation before action execution.

---

## 🏗️ System Architecture

```text
                 CUSTOMER
                    |
                    v
             STREAMLIT UI
                    |
                    v
          PARCELPILOT AI AGENT
                    |
                    v
           WORKFLOW DETECTION
                    |
          +---------+----------+
          |                    |
          v                    v
   STRUCTURED WORKFLOWS      RAG PIPELINE
          |                    |
   +------+------+       PDF DOCUMENTS
   |      |      |             |
 Orders Cancel Escalation      v
   |      |      |       DOCUMENT CHUNKING
   |      |      |             |
   |      v      |       EMBEDDINGS
   |   SQLite    |             |
   |             |       +-----+------+
   |             |       |            |
   |             |    ChromaDB       BM25
   |             |    Dense Search   Search
   |             |       |            |
   |             |       +-----+------+
   |             |             |
   |             |           RRF
   |             |             |
   |             |      CROSS-ENCODER
   |             |        RERANKING
   |             |             |
   |             |       GOOGLE GEMINI
   |             |             |
   +-------------+-------------+
                    |
                    v
             RESPONSE LAYER
                    |
                    v
          CUSTOMER SUPPORT RESPONSE
```

---

## 🧠 RAG Architecture

ParcelPilot AI uses a hybrid retrieval approach to improve document search relevance.

### Retrieval Pipeline

| Component | Purpose |
|---|---|
| PDF Loader | Loads policy and agreement documents |
| Text Chunking | Splits documents into manageable passages |
| Sentence Transformers | Generates document embeddings |
| ChromaDB | Performs dense vector retrieval |
| BM25 | Performs keyword-based retrieval |
| Reciprocal Rank Fusion | Combines retrieval rankings |
| Cross-Encoder | Reranks retrieved passages |
| Google Gemini | Generates contextual responses |

### Hybrid Retrieval Flow

1. Customer submits a policy-related question.
2. The retriever searches using dense vector retrieval.
3. BM25 retrieves keyword-relevant passages.
4. RRF combines candidate rankings.
5. Cross-Encoder reranks the retrieved passages.
6. Relevant context is provided to Gemini.
7. The response is generated with supporting source references.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| LLM | Google Gemini |
| Embeddings | Sentence Transformers |
| Vector Database | ChromaDB |
| Keyword Retrieval | BM25 |
| Rank Fusion | Reciprocal Rank Fusion |
| Reranking | Cross-Encoder |
| Database | SQLite |
| Data Processing | Pandas |
| Document Processing | PyPDF |
| Testing | Pytest |
| Observability | LangSmith |
| Version Control | Git and GitHub |

---

## 📂 Project Structure

```text
ParcelPilot-AI/
│
├── src/
│   ├── agent.py
│   ├── config.py
│   ├── data_loader.py
│   ├── database.py
│   ├── llm.py
│   ├── response_generator.py
│   ├── workflow.py
│   ├── escalation_action.py
│   ├── session_manager.py
│   │
│   ├── tools/
│   │   └── cancellation_tools.py
│   │
│   └── rag/
│       ├── vector_store.py
│       ├── retriever.py
│       └── test_hybrid_retrieval.py
│
├── tests/
│   └── test_workflow_routing.py
│
├── streamlit_app.py
├── test_upgrade.py
├── test_workflow.py
├── requirements.txt
├── .gitignore
└── README.md
```

*The structure above highlights the main application modules. Additional data, configuration, and test files may be present in the repository.*

---

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.11 or compatible version
- Git
- Google Gemini API key
- VS Code or another Python development environment

### Step 1: Clone the Repository

```bash
git clone https://github.com/Mainuddin123/ParcelPilot-AI---Autonomous-Customer-Support-Agent.git
```

### Step 2: Navigate to the Project

```bash
cd ParcelPilot-AI---Autonomous-Customer-Support-Agent
```

### Step 3: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure API Credentials

Configure your Google Gemini API key using the environment variable expected by the application's configuration.

For example, if the application reads `GEMINI_API_KEY`:

```powershell
$env:GEMINI_API_KEY="your_api_key"
```

For persistent deployment, configure credentials through the hosting platform's secrets management.

**Security:** Never commit API keys, `.env` files, or Streamlit secrets to GitHub.

### Step 6: Run the Application

```bash
streamlit run streamlit_app.py
```

The application will be available at:

```text
http://localhost:8501
```

---

## 🧪 Testing and Validation

The project was tested using automated pytest tests and manual application demonstrations.

### Automated Testing

| Metric | Result |
|---|---:|
| Tests collected | 47 |
| Tests passed | 47 |
| Tests failed | 0 |
| Execution time | 43.05 seconds |
| Python version | 3.11.9 |

Run the automated test suite:

```bash
python -m pytest -v
```

### Manual End-to-End Testing

The following five scenarios were demonstrated successfully in the Streamlit application.

| Test Case | Scenario | Result |
|---|---|---|
| TC-01 | Order tracking | Passed |
| TC-02 | Cancellation declined | Passed |
| TC-03 | Cancellation confirmed | Passed |
| TC-04 | Ticket escalation | Passed |
| TC-05 | RAG policy retrieval | Passed |

### Demonstrated Results

- Successfully retrieved order information for `ORD-1001`.
- Confirmed that declining cancellation leaves the order unchanged.
- Demonstrated a local cancellation status update to `CANCELLED`.
- Successfully created escalation `ESC-TKT-501`.
- Retrieved cancellation and service-credit policies with supporting document references.

*Testing results reflect the development environment and demonstrations performed. They do not establish production-scale reliability.*

---

## 🔒 Limitations and Considerations

- SQLite cancellation updates represent local application state; they do not independently cancel shipments through external carrier systems.
- Carrier API integration is required for real shipment cancellation and synchronization.
- Service-credit assessment does not automatically issue financial credits.
- Local database and vector-store persistence must be verified in the deployment environment.
- Production deployment requires authentication, authorization, persistent storage, monitoring, and additional security validation.
- Prompt-injection detection and output validation are safeguards, not guarantees against every attack.

---

## 🔮 Future Enhancements

- Integrate real-time carrier APIs.
- Implement shipment status synchronization.
- Introduce managed database infrastructure.
- Add authentication and role-based access control.
- Improve audit logging and action traceability.
- Add comprehensive RAG evaluation metrics.
- Implement advanced observability and monitoring.
- Expand automated integration and deployment tests.
- Improve workflow classification and response metadata.

---

## 📊 Project Validation Summary

| Area | Status |
|---|---|
| Order Tracking | Demonstrated |
| Cancellation Workflow | Demonstrated |
| Ticket Escalation | Demonstrated |
| Service Credit Assessment | Implemented workflow |
| Hybrid RAG Retrieval | Demonstrated |
| Account-Aware Retrieval | Automated tests passed |
| Automated Test Suite | 47/47 passed |
| Manual Demonstrations | 5/5 completed |

---

## 👨‍💻 Developer

**Mainuddin**

AI & Data Science Graduate | Aspiring AI Engineer

- GitHub: [Mainuddin123](https://github.com/Mainuddin123)
- LinkedIn: [Khaja Mainuddin SK](https://www.linkedin.com/in/khaja-mainuddin-sk-958436348)

---

## 📌 Project Repository

[ParcelPilot AI – Autonomous Customer Support Agent](https://github.com/Mainuddin123/ParcelPilot-AI---Autonomous-Customer-Support-Agent)

**Latest development commit:** `4db1e76`

---

<p align="center">
  <b>ParcelPilot AI</b><br/>
  Intelligent Support. Contextual Answers. Safer Workflows.
</p>
