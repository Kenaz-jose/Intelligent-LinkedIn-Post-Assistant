# 🚀 Intelligent LinkedIn Post Assistant — LinkedInForge

> A self-healing, multi-agent AI pipeline for creating fact-checked, highly engaging, and authentic LinkedIn content.

Traditional AI writing tools generate generic content and stop. Professional writing is inherently iterative — it requires drafting, strict fact-checking, external research, evaluation, and targeted stylistic revisions.

**LinkedInForge** is a multi-agent AI system built with **LangGraph**, **LangChain**, and **Streamlit** that transforms a user's raw perspective and first-hand experience into a polished LinkedIn post.

Instead of relying on a single LLM call, LinkedInForge orchestrates specialized agents — including a **Generator, Evaluator, Fact Checker, Hook Reviser, Style Reviser, and Researcher** — that collaborate through a stateful workflow.

The system also includes a **Factual Firewall**, **autonomous web research**, **dynamic routing**, and **Human-in-the-Loop (HITL)** checkpoints to reduce hallucinations and preserve the user's authentic voice.

---

## ✨ Key Features

### 🧠 Perspective Interviewing

Before generating a post, LinkedInForge interviews the user to extract:

* Personal opinions and perspectives
* First-hand experiences
* Technical details
* Metrics and evidence
* Contrarian viewpoints
* Lessons learned

This creates a structured **Perspective Brief** that becomes the foundation of the generated content.

### 🛡️ Factual Firewall

A dedicated `FactCheckerAgent` validates claims against the available source context.

It identifies and removes:

* Unsupported metrics
* Fabricated claims
* Contradictions
* Unverified technical statements
* Hallucinated information

The goal is to ensure that the final post remains **faithful to the user's actual knowledge and verified evidence**.

### 🌐 Autonomous Web Research

When the system identifies a claim that requires external validation, the `ResearcherAgent` can:

1. Identify the missing information.
2. Formulate a targeted search query.
3. Search authoritative sources through Tavily.
4. Extract relevant evidence.
5. Present the findings for human approval.
6. Inject approved information back into the workflow.

### ⏸️ Human-in-the-Loop

LinkedInForge does not blindly publish AI-generated content.

The workflow can pause at important decision points so the user can:

* Review external research
* Approve or reject facts
* Review the generated post
* Provide revision instructions
* Edit the final content

### 🔀 Dynamic Switchboard Routing

Instead of sending every failed draft through the same revision process, the evaluator determines **what needs to be fixed**.

The Router Agent can direct the draft to specialized repair agents such as:

* **Fact Checker** → factual problems
* **Hook Reviser** → weak opening
* **Style Reviser** → tone and writing style
* **Researcher** → missing external evidence

This creates targeted iterative refinement rather than repeatedly regenerating the entire post.

### 📊 Multi-Dimensional Evaluation

Every generated post is evaluated across multiple dimensions:

* Hook
* Clarity
* Engagement
* Authenticity
* Professionalism
* Structure
* Faithfulness

The evaluation results determine whether the post should be finalized or sent back through another repair cycle.

---

# 🏗️ System Architecture

LinkedInForge is implemented as a **stateful LangGraph workflow**.

The graph uses conditional routing, iterative repair loops, early stopping, and Human-in-the-Loop checkpoints.

```text
┌──────────────────────────────────────────────────────────────┐
│ 1. INTERVIEW STAGE                                           │
│                                                              │
│ Extract user experience, opinions, metrics and perspective   │
│                     ↓                                        │
│              Perspective Brief                               │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. GENERATION                                                │
│                                                              │
│ Generator Agent creates the initial LinkedIn post            │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. EVALUATION                                                │
│                                                              │
│ Evaluator Agent scores the draft and identifies weaknesses   │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. DYNAMIC SWITCHBOARD                                       │
│                                                              │
│ Router analyzes evaluator feedback and selects a repair path │
└───────────────┬──────────────┬──────────────┬────────────────┘
                │              │              │
                ▼              ▼              ▼
         ┌────────────┐ ┌────────────┐ ┌────────────┐
         │ FACT       │ │ HOOK       │ │ STYLE      │
         │ CHECKER    │ │ REVISER    │ │ REVISER    │
         └──────┬─────┘ └──────┬─────┘ └──────┬─────┘
                │              │              │
                └──────────────┼──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ EVALUATION   │
                        │ LOOP         │
                        └──────┬───────┘
                               │
                               │ Research Required
                               ▼
                        ┌──────────────┐
                        │  RESEARCHER  │
                        │    AGENT     │
                        └──────┬───────┘
                               │
                               ▼
                       ┌────────────────┐
                       │ HITL APPROVAL  │
                       │ Review Facts   │
                       └───────┬────────┘
                               │
                               ▼
                          EVALUATION
                               │
                               │ Pass
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. FINAL REVIEW                                              │
│                                                              │
│ Human reviews, edits, or provides final revision instructions│
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ FINAL LINKEDIN  │
                     │      POST       │
                     └─────────────────┘
```

---

# ⚙️ Tech Stack

| Component           | Technology | Purpose                                                  |
| ------------------- | ---------- | -------------------------------------------------------- |
| **Orchestration**   | LangGraph  | Stateful multi-agent workflows, routing, loops, and HITL |
| **LLM Integration** | LangChain  | LLM abstraction and structured agent interactions        |
| **LLM Provider**    | Groq       | High-speed LLM inference                                 |
| **Web Research**    | Tavily     | Autonomous web search and evidence retrieval             |
| **Data Validation** | Pydantic   | Structured outputs and schema validation                 |
| **Frontend**        | Streamlit  | Interactive application interface                        |
| **Visualization**   | Plotly     | Evaluation and scoring visualizations                    |
| **Backend**         | FastAPI    | API routes and service layer                             |

---

# 📂 Project Structure

```text
LinkedInForge/
│
├── data/
│   └── user_memory.json       # Local user data / memory
│
├── docs/                      # Documentation and screenshots
│
├── src/
│   │
│   ├── agents/                # Specialized LangGraph agents
│   │   ├── generator.py
│   │   ├── evaluator.py
│   │   ├── fact_checker.py
│   │   ├── researcher.py
│   │   └── revisers/
│   │
│   ├── api/                   # FastAPI backend
│   │
│   ├── config/                # Configuration and environment settings
│   │
│   ├── db/                    # Database configuration and models
│   │
│   ├── evaluation/            # Evaluation logic and routing policies
│   │
│   ├── prompts/               # Agent prompt templates
│   │
│   ├── schemas/               # Pydantic models and graph state
│   │
│   ├── services/              # External service integrations
│   │
│   ├── store/                 # State and run persistence
│   │
│   ├── UI/                    # Streamlit interface
│   │
│   └── utils/                 # Utilities, parsing and logging
│
├── tests/                     # Unit and integration tests
│
├── main.py                    # Application entry point
├── test_hitl.py               # HITL workflow testing
├── visualize_interview.py     # Interview flow visualization
├── requirements.txt           # Python dependencies
└── README.md
```

---

# 🚀 Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/Kenaz-jose/Intelligent-LinkedIn-Post-Assistant.git

cd Intelligent-LinkedIn-Post-Assistant
```

To work with the development branch:

```bash
git checkout develop
```

---

## 2. Create a Virtual Environment

### Linux / macOS

```bash
python3 -m venv linkedin
source linkedin/bin/activate
```

### Windows

```bash
python -m venv linkedin
linkedin\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

> **Important:** Never commit your `.env` file or expose API keys publicly.

---

# ▶️ Usage

Start the Streamlit application:

```bash
streamlit run src/UI/streamlit.py
```

The application will launch the interactive LinkedInForge dashboard.

---

# 🔄 Workflow

### 1. Perspective Interview

Select a topic or trending news item and answer a series of targeted questions.

The system extracts your:

* Perspective
* Experience
* Technical knowledge
* Evidence
* Opinions
* Metrics

These responses are converted into a structured **Perspective Brief**.

---

### 2. Autonomous Drafting

The Generator Agent creates the initial LinkedIn post using the Perspective Brief.

The draft then enters the evaluation pipeline.

---

### 3. Evaluation

The Evaluator Agent analyzes the draft across multiple dimensions and identifies problems such as:

* Weak hook
* Poor structure
* Unsupported claims
* Missing evidence
* Generic writing
* Low authenticity
* Poor engagement potential

---

### 4. Dynamic Repair

The Router Agent determines which specialized agent should handle the problem.

For example:

```text
Weak Hook
    ↓
Hook Reviser
    ↓
Evaluation

Unsupported Claim
    ↓
Fact Checker
    ↓
Evaluation

Missing Evidence
    ↓
Researcher
    ↓
HITL Approval
    ↓
Evaluation
```

---

### 5. HITL Research Review

If external information is required, the workflow pauses.

The user reviews the retrieved evidence and decides which information can be trusted.

Only approved information becomes part of the workflow's trusted context.

---

### 6. Iterative Refinement

The workflow continues through the evaluation → routing → repair cycle until the post satisfies the required quality and faithfulness thresholds.

---

### 7. Final Review

Before completion, the user gets a final opportunity to:

* Edit the post
* Approve the content
* Provide revision instructions
* Reject the draft

The final result is a polished LinkedIn post grounded in the user's perspective and verified evidence.

---

# 🧪 Testing

The repository includes utilities for testing important workflow components.

### Test HITL workflow

```bash
python test_hitl.py
```

### Visualize the interview workflow

```bash
python visualize_interview.py
```

Additional unit and integration tests are located inside:

```text
tests/
```

---

# 🗺️ Future Improvements

The project is actively evolving. Planned improvements include:

* [ ] Semantic memory for long-term user voice adaptation
* [ ] Persistent user profiles and preferences
* [ ] A/B post generation for different platforms
* [ ] Support for X, Threads, and other social platforms
* [ ] Ollama-based local LLM fallback
* [ ] Post scheduling and publishing
* [ ] Analytics tracking
* [ ] Database-backed post history
* [ ] Long-term content performance feedback loops
* [ ] Improved source credibility ranking
* [ ] Multi-model routing based on task complexity

---

# 🤝 Contributing

Contributions, suggestions, bug reports, and feedback are welcome.

To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Add or update tests where appropriate.
5. Submit a pull request.

For larger changes, consider opening an issue first to discuss the proposed approach.

---

# 📜 License

This project is licensed under the **MIT License**.

---

# 👨‍💻 Author

**Kenaz Jose**

Built with ❤️ using **Python, LangGraph, LangChain, Groq, Tavily, and Streamlit**.

If you find LinkedInForge useful, consider giving the repository a ⭐ on GitHub!

---

## ⭐ Project Philosophy

LinkedInForge is built around a simple principle:

> **AI should not replace your perspective — it should amplify it.**

The goal is not to generate more AI-written content.

The goal is to build an agentic system that understands **what you think, what you have experienced, what can be verified, and how your ideas should be communicated** — while keeping the human in control of the final voice.
