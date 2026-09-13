# Intelligent LinkedIn Post Assistant | LinkForge

> A self-healing, deterministic multi-agent AI pipeline for creating fact-checked, high-craft, and authentic LinkedIn content.

Traditional AI writing tools generate generic prose in a single pass and stop. Production-grade content engineering requires an iterative editorial pipeline: extraction of first-hand experience, parallel hook exploration, adversarial evaluation, surgical fact-checking, and targeted stylistic refinement.

**LinkedInForge** is an agentic content generation pipeline built with **LangGraph**, **FastAPI** and a modern **React/Vite/Tailwind** frontend. It transforms an engineer's raw perspectives and debugging anecdotes into an executive-ready LinkedIn post while enforcing guardrails designed to reduce unsupported claims and preserve the author's authentic voice.

---

## System Architecture

LinkedInForge coordinates specialized agents through a stateful LangGraph workflow governed by an asynchronous FastAPI backend. The state and UI events are streamed to a React frontend via Server-Sent Events (SSE).

```text
[React/Tailwind Frontend]  <--- (SSE Streaming / REST) --->  [FastAPI Service Layer]
                                                                  |
                                                          [LangGraph State Engine]
                                                                  |
                  +-----------------------------------------------+-----------------------------------------------+
                  |                                               |                                               |
         [Pre-Flight / Tavily]                        [Database & Vector Stores]                          [LLM Integrations]
         (Live External Data)                   (PostgreSQL/pgvector, ChromaDB, HF)                  (Groq, Google, NVIDIA)
                  |                                               |                                               |
          [Generator Agent] -------> [Evaluator Agent] <==========================================================+
                                            |
                                    /       |         \
                              (Fail)       |       (Low Craft)
                                /       (Pass)          \
                       [FactChecker]      |           [Stylist] ---------------+
                            \             v                /
                             +-----> [HITL Breakpoint] <---+
                                      (User Inspection)
                                             |
                                        [Final Post]
```

---

## Product Workflow

The application guides the user through a structured, calm editorial process:

1. **Topic** - Define the core subject matter.
2. **Interview** - Answer targeted questions to extract first-hand experience.
3. **Probe** - Deep-dive follow-up questions to fill in missing context.
4. **Brief** - Review the compiled `PerspectiveBrief` before generation begins.
5. **Review** - A Human-in-the-Loop (HITL) interface to inspect the AI's drafts, swap hooks, and provide explicit feedback.
6. **Result** - The finalized, polished, and factual LinkedIn post.

---

## Core Engineering Innovations

### Provenance-Based Factual Firewall

Most LLM guardrails verify claims against general web truth. LinkedInForge enforces **Provenance Over Factuality**.

* If a statement is technically true in the real world but was never mentioned in the author's brief or approved external references, the `EvaluatorAgent` flags it as **Unfaithful**.
* The prompt architecture uses an **Observation-First Rubric**, forcing the model to cite verbatim evidence before generating numerical score tokens.
* If unsupported claims occur, the pipeline routes to the `FactCheckerAgent` to surgically excise them without rewriting the entire post.

### Deterministic Hierarchical Switchboard

Agent routing is decoupled from LLM non-determinism. The `dynamic_switchboard` conditional edge governs workflow routing using a four-tier hierarchy:

1. **Tier 1: Explicit Overrides** — Direct human revisions bypass AI scoring and route straight to the `StylistAgent`.
2. **Tier 2: System Guardrails** — Enforces hard iteration limits (`MAX_ITERATIONS`) and early stopping buffers to halt score degradation before attempting repairs.
3. **Tier 3: Repair Routing** — Prioritizes factual fidelity (`fix_facts`) over stylistic refinement (`fix_flow`).
4. **Tier 4: Default Success** — Drafts meeting quality (`>= 8.0`) and faithfulness bars terminate safely at `finalize`.

### Incumbent Pattern — Score Degradation Protection

Iterative AI rewriting frequently introduces awkward phrasing that degrades a post's craft score. LinkedInForge maintains an incumbent record of the `best_post`, `best_verdict`, and `best_evaluation`.

* After each evaluation cycle, the state engine assesses `is_better(verdict, incumbent)`.
* If a stylistic revision lowers the craft score, the engine logs: `Draft not an improvement - keeping iteration X`
* When the workflow concludes, the system serves the highest-scoring historical incumbent rather than the degraded terminal draft.

### Human-in-the-Loop (HITL) Brief Injection

When human revisions are submitted during an interrupt (`interrupt_before=["finalize"]`), traditional systems risk having the Evaluator flag the user's new input as a hallucination.

LinkedInForge addresses this by:

* Dynamically appending human revision instructions directly to `brief["details"]` as a clearly marked `HUMAN VERIFIED FACT` entry.
* Updating the core ground truth within the checkpoint state, allowing the `StylistAgent` to integrate new claims without triggering false-positive hallucination flags on subsequent passes.

---

## The Agent Suite

| Agent                | Responsibility                                                                         | Input Context                         |
| -------------------- | -------------------------------------------------------------------------------------- | ------------------------------------- |
| **GeneratorAgent**   | Drafts initial post based on technical anecdotes and tone.                             | Structured Brief + Permitted Web Data |
| **HookAgent**        | Generates 3 diverse opening hooks in parallel with initial generation.                 | Topic + Brief + Target Angle          |
| **EvaluatorAgent**   | Evaluates 7 dimensions including Hook, Clarity, Authenticity, Craft, and Faithfulness. | Draft + Brief + Approved Sources      |
| **FactCheckerAgent** | Surgically strips unsupported claims, metrics, or timeline fabrications.               | Draft + Brief + Evaluator Critique    |
| **StylistAgent**     | Polishes pacing, structural layout, and implements explicit user feedback.             | Draft + Weaknesses + Human Revision   |
| **ResearcherAgent**  | Retrieves real-time benchmarks and industry definitions using Tavily.                  | Topic + Evidence Gaps                 |

---

## Tech Stack

* **Frontend:** React, Vite, Tailwind CSS
* **Backend Framework:** FastAPI, Uvicorn, Server-Sent Events (SSE)
* **Orchestration:** LangGraph (StateGraph, checkpointing, interrupts)
* **LLM Integrations:** Groq, Google GenAI, NVIDIA AI Endpoints
* **Database & Memory:** PostgreSQL, pgvector
* **Vector Store & Embeddings:** ChromaDB, HuggingFace (`all-MiniLM-L6-v2`)
* **External Retrieval:** Tavily Search API
* **State Validation:** Pydantic v2

---

## Project Structure

```text
Intelligent-LinkedIn-Post-Assistant/
├── frontend/                      # React / Vite / Tailwind UI application
│
├── src/
│   ├── agents/
│   │   ├── generator.py           # Initial post generation
│   │   ├── evaluator.py           # 7-dimension scoring & faithfulness check
│   │   ├── fact_checker.py        # Surgical hallucination removal
│   │   ├── stylist.py             # Prose polishing & HITL integration
│   │   ├── hook.py                # Parallel hook variants
│   │   ├── researcher.py          # Tavily web search integration
│   │   └── workflow.py            # LangGraph StateGraph & dynamic switchboard
│   │
│   ├── api/
│   │   ├── main.py                # FastAPI server application entry point
│   │   ├── routes.py              # FastAPI endpoints (/optimize/stream, /resume, etc.)
│   │   └── service.py             # SSE streaming engine & state translators
│   │
│   ├── db/                        # PostgreSQL models & engine initialization
│   ├── store/                     # LangGraph checkpointer & ChromaDB VectorStore
│   ├── evaluation/                # Verdict models, craft heuristics, and ranking
│   ├── schemas/                   # Pydantic schemas for briefs and evaluations
│   └── UI/
│       └── streamlit.py           # Legacy/prototype UI (Deprecated)
│
├── init_db.py                     # Database schema creation script
├── requirements.txt               # Production backend dependencies
└── README.md
```

---

## Getting Started

### 1. Prerequisites

* Node.js (for the frontend)
* Python 3.10+
* PostgreSQL (Running locally or hosted)
* API Keys (e.g., Groq, Tavily, Google, NVIDIA depending on your configured agents)

### 2. Installation

Clone the repository:

```bash
git clone https://github.com/pranavppramod/Intelligent-LinkedIn-Post-Assistant.git
cd Intelligent-LinkedIn-Post-Assistant
```

### 3. Backend Setup

Set up a virtual environment and install the dependencies:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the root directory based on the APIs you intend to use. For example:

```env
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/linkedinforge
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly_...
```

Initialize the PostgreSQL database (creates the required tables and `pgvector` extensions):

```bash
python init_db.py
```

### 4. Frontend Setup

In a new terminal window, install and start the React frontend:

```bash
cd frontend
npm install
npm run dev
```

### 5. Running the Application

*Note: The frontend and backend must run in separate terminals.*

Start the FastAPI backend server:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The React frontend will be available at `http://localhost:5173` (or the port Vite provides) and the FastAPI backend will serve requests and SSE streams at `http://localhost:8000`.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
