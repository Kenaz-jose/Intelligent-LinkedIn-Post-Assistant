# 🚀 Intelligent LinkedIn Post Assistant — LinkedInForge

> A self-healing, deterministic multi-agent AI pipeline for creating fact-checked, high-craft, and authentic LinkedIn content.

Traditional AI writing tools generate generic prose in a single pass and stop. Production-grade content engineering requires an iterative editorial pipeline: extraction of first-hand experience, parallel hook exploration, adversarial evaluation, surgical fact-checking, and targeted stylistic refinement.

**LinkedInForge** is an agentic content generation pipeline built with **LangGraph**, **FastAPI** and **Streamlit**. It transforms an engineer's raw perspectives and debugging anecdotes into an executive-ready LinkedIn post while enforcing zero-hallucination guardrails and preserving the author's authentic voice.

---

## 🏗️ System Architecture

LinkedInForge coordinates specialized agents through a stateful LangGraph workflow governed by an asynchronous FastAPI backend and streamed to a Streamlit frontend via Server-Sent Events (SSE).

```text
[Streamlit Frontend]  <--- (SSE Streaming / REST) --->  [FastAPI Service Layer]
                                                                |
                                                        [LangGraph State Engine]
                                                                |
                  +---------------------------------------------+---------------------------------------------+
                  |                                                                                           |
         [Pre-Flight / Tavily]                                                                  [State Checkpoints]
                  |                                                                                           |
          (Live External Data)                                                                        (Thread UUID)
                  |
          [Generator Agent] -------> [Evaluator Agent] <========================+
                  |                         |                                  |
         [Hook Agent] (Parallel)   [dynamic_switchboard]                       |
                                    /       |         \                         |
                              (Fail)       |       (Low Craft)                 |
                                /       (Pass)          \                      |
                       [FactChecker]      |           [Stylist] ---------------+
                            \             v                /
                             +-----> [HITL Breakpoint] <---+
                                      (User Inspection)
                                             |
                                          [Publish]
```

---

## ✨ Core Engineering Innovations

### 🛡️ Provenance-Based Factual Firewall

Most LLM guardrails verify claims against general web truth. LinkedInForge enforces **Provenance Over Factuality**.

* If a statement is technically true in the real world but was never mentioned in the author's brief or approved external references, the `EvaluatorAgent` flags it as **Unfaithful**.
* The prompt architecture uses an **Observation-First Rubric**, forcing the model to cite verbatim evidence before generating numerical score tokens.
* If hallucinations occur, the pipeline routes to the `FactCheckerAgent` to surgically excise unsupported metrics without rewriting the entire post.

### 🔀 Deterministic Hierarchical Switchboard

Agent routing is decoupled from LLM non-determinism. The `dynamic_switchboard` conditional edge governs workflow routing using a four-tier hierarchy:

1. **Tier 1: Explicit Overrides** — Direct human revisions bypass AI scoring and route straight to the `StylistAgent`.
2. **Tier 2: System Guardrails** — Enforces hard iteration limits (`MAX_ITERATIONS`) and early stopping buffers to halt score degradation before attempting repairs.
3. **Tier 3: Repair Routing** — Prioritizes factual fidelity (`fix_facts`) over stylistic refinement (`fix_flow`).
4. **Tier 4: Default Success** — Drafts meeting quality (`≥ 8.0`) and faithfulness bars terminate safely at `finalize`.

### 🏆 Incumbent Pattern — Score Degradation Protection

Iterative AI rewriting frequently introduces awkward phrasing that degrades a post's craft score. LinkedInForge maintains an immutable record of the `best_post`, `best_verdict`, and `best_evaluation`.

* After each evaluation cycle, the state engine assesses `is_better(verdict, incumbent)`.

* If a stylistic revision lowers the craft score, the engine logs:

  `Draft not an improvement - keeping iteration X`

* When the workflow concludes, the system serves the highest-scoring historical incumbent rather than the degraded terminal draft.

### ⏸️ Human-in-the-Loop (HITL) Brief Injection

When human revisions are submitted during an interrupt (`interrupt_before=["finalize"]`), traditional systems risk having the Evaluator flag the user's new input as a hallucination.

LinkedInForge addresses this by:

* Dynamically appending human revision instructions directly to `brief["details"]` as an immutable `HUMAN VERIFIED FACT`.
* Updating the core ground truth within the checkpoint state, allowing the `StylistAgent` to integrate new claims without triggering false-positive hallucination flags on subsequent passes.

---

## 🤖 The Agent Suite

| Agent                | Responsibility                                                                         | Input Context                         |
| -------------------- | -------------------------------------------------------------------------------------- | ------------------------------------- |
| **GeneratorAgent**   | Drafts initial post based on technical anecdotes and tone.                             | Structured Brief + Permitted Web Data |
| **HookAgent**        | Generates 3 diverse opening hooks in parallel with initial generation.                 | Topic + Brief + Target Angle          |
| **EvaluatorAgent**   | Evaluates 7 dimensions including Hook, Clarity, Authenticity, Craft, and Faithfulness. | Draft + Brief + Approved Sources      |
| **FactCheckerAgent** | Surgically strips unsupported claims, metrics, or timeline fabrications.               | Draft + Brief + Evaluator Critique    |
| **StylistAgent**     | Polishes pacing, structural layout, and implements explicit user feedback.             | Draft + Weaknesses + Human Revision   |
| **ResearcherAgent**  | Retrieves real-time benchmarks and industry definitions using Tavily.                  | Topic + Evidence Gaps                 |

---

## ⚙️ Tech Stack

* **Orchestration:** LangGraph — StateGraph, checkpointing, interrupts
* **Backend Framework:** FastAPI, Uvicorn, Server-Sent Events (SSE)
* **LLM Engine:** Groq Cloud API — Llama 3.3 70B Versatile
* **External Retrieval:** Tavily Search API
* **State Validation:** Pydantic v2
* **Frontend:** Streamlit

---

## 📂 Project Structure

```text
Intelligent-LinkedIn-Post-Assistant/
├── src/
│   ├── agents/
│   │   ├── generator.py          # Initial post generation
│   │   ├── evaluator.py          # 7-dimension scoring & faithfulness check
│   │   ├── fact_checker.py       # Surgical hallucination removal
│   │   ├── stylist.py             # Prose polishing & HITL integration
│   │   ├── hook.py                # Parallel hook variants
│   │   ├── researcher.py          # Tavily web search integration
│   │   └── workflow.py            # LangGraph StateGraph & dynamic switchboard
│   │
│   ├── api/
│   │   ├── routes.py              # FastAPI endpoints (/optimize/stream, /resume)
│   │   └── service.py             # SSE streaming engine & state translators
│   │
│   ├── evaluation/
│   │   └── policy.py              # Verdict models, craft heuristics, and ranking
│   │
│   ├── schemas/
│   │   └── perspective.py         # Pydantic schemas for briefs and evaluations
│   │
│   └── UI/
│       └── streamlit.py           # Interactive review console & timeline
│
├── tests/                         # Agent integration & unit tests
├── main.py                        # FastAPI server entry point
├── requirements.txt               # Production dependencies
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.10+
* Groq API Key
* Tavily API Key

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/Kenaz-jose/Intelligent-LinkedIn-Post-Assistant.git
cd Intelligent-LinkedIn-Post-Assistant

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=gsk_your_groq_key_here
TAVILY_API_KEY=tvly_your_tavily_key_here
```

### 4. Running the Application

Start the FastAPI backend server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

In a separate terminal, launch the Streamlit interface:

```bash
streamlit run src/UI/streamlit.py
```

---

## 🔄 Execution Lifecycle

### 1. Perspective Extraction

The user answers structured technical questions. The system compiles responses into a validated `PerspectiveBrief`.

### 2. Pre-Flight Research

If selected, the `ResearcherAgent` queries Tavily for current benchmarks and injects verified external snippets into the state.

### 3. Parallel Generation

The `GeneratorAgent` writes the body draft while the `HookAgent` generates alternative opening hooks. Both synchronize before the evaluation step.

### 4. Adversarial Evaluation

The `EvaluatorAgent` scores the draft against the provenance-bounded brief.

### 5. Self-Correction Loops

Depending on the evaluation:

* **Unverified metrics detected** → `FactCheckerAgent` strips them.
* **Craft score < 8.0** → `StylistAgent` refines readability and pacing.

### 6. HITL Review

The graph halts at `finalize`.

The user can:

* Swap hooks
* Accept the draft
* Provide custom instructions

Human revisions update the core brief as `HUMAN VERIFIED FACT` entities to guarantee downstream evaluation safety.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
