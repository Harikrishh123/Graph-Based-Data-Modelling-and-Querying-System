# Nexus Context - Order-to-Cash Graph Explorer

An intelligent, interactive context graph system for visualizing and exploring SAP Order-to-Cash (O2C) data flows. Powered by **Google Gemini 2.5 Flash** and **FastAPI**, it allows users to query complex relationships using natural language and see them represented as a dynamic, connected graph.

##  Architecture Decisions

The project follows a modern decoupled architecture designed for speed, flexibility, and high-quality user experience.

### 1. **Backend: FastAPI & Python**
- **Choice**: chosen for its high performance, asynchronous support, and native Pydantic integration for data validation.
- **Role**: acts as the bridge between the LLM and the local SQLite database. It handles the orchestration of tool-calling and graph extraction logic.

### 2. **Frontend: Vanilla Web Stack (HTML5/CSS3/JS)**
- **Choice**: Vanilla JavaScript with [Vis-Network](https://visjs.github.io/vis-network/docs/network/) for graph rendering.
- **Rationale**: Minimal overhead while providing extreme control over the "Glassmorphism" UI design and complex graph interactions.

### 3. **AI Engine: Google Gemini 2.5 Flash**
- **Choice**: chosen via the latest `google-genai` SDK.
- **Rationale**: Offers an exceptional balance of speed, cost-effectiveness, and advanced reasoning for complex SQL generation and entity extraction.

##  Database Choice: SQLite

For this application, **SQLite** was selected as the primary data store.

- **Portability**: The entire dataset resides in a single `o2c.db` file, eliminating the need for a separate database server (like PostgreSQL or SAP HANA) for initial exploration and portability.
- **Integration**: Python's `sqlite3` and `pandas` make it seamless to transform relational table results into graph-compatible JSON formats.
- **Relational Integrity**: Maintains the structured nature of SAP tables (`sales_order_headers`, `outbound_delivery_items`, etc.) while the application layer projects them into a graph visualization.

##  LLM Prompting Strategy

The LLM is configured with a specialized system instruction that transforms it into a **Context Graph Exploration AI**.

1. **System Instruction**: Explicitly defines the AI's persona as an SAP Order-to-Cash expert.
2. **Schema Injection**: The full database schema is read from `schema.txt` and injected into the prompt, giving the model precise knowledge of table names and join keys.
3. **Multi-Turn Tool Use (Function Calling)**:
    - `execute_sql`: Used by the model to generate and run deterministic queries against the database.
    - `final_response`: Forces the model to structure its output into a natural language `answer` and a structured list of `graph_entities`.
4. **Deterministic Reasoning**: By setting `temperature=0.0`, we ensure the model remains grounded in the data fetched from the SQL engine.

##  Guardrails

To ensure reliability and security, several guardrail layers are implemented:

- **Domain Restriction**: The system prompt explicitly instructs the LLM to only answer questions related to the O2C dataset and provides a fallback message for out-of-scope queries.
- **Hallucination Mitigation**: The LLM is prohibited from "guessing" data. It *must* use `execute_sql` to retrieve facts before answering.
- **Data Capping**: The `execute_sql` function automatically limits results to 50 rows, preventing context window fatigue and maintaining system performance.
- **CORS & Authentication**: The FastAPI backend supports Bearer token authentication (Gemini API Key) and restricted CORS origins for secure web deployment.

---

##  Project Structure

```text
o2c-graph-app/
├── app.py              # FastAPI Backend & LLM Orchestration
├── ingest.py           # Data Ingestion Script (JSONL -> SQLite)
├── get_schema.py       # Utility to extract DB schema for LLM context
├── schema.txt          # Exported DB schema used in System Prompts
├── o2c.db              # SQLite Database (Auto-generated/Ingested)
├── requirements.txt    # Python Dependencies
├── .env                # Environment Variables (API Keys)
└── frontend/           # Web Interface
    ├── index.html      # UI Structure
    ├── styles.css      # Glassmorphism Design System
    └── script.js       # Graph Interaction & API Integration
```

##  Getting Started

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_google_gemini_api_key
```

### 3. Data Ingestion (Optional)
If you need to rebuild the database from source JSONL files:
1. Ensure your source data is in the directory specified in `ingest.py`.
2. Run `python ingest.py`.
3. Update `schema.txt` by running `python get_schema.py`.

### 4. Running the Application
Start the backend server:
```bash
python app.py
```
Then, open `frontend/index.html` in your browser.

---

##  Built With

- **FastAPI**: Backend framework
- **Google GenAI SDK**: Gemini 2.5 Flash interface
- **Vis-Network**: High-performance graph visualization
- **SQLite**: Local relational storage
- **Pandas**: Efficient data transformation
