# 🚀 ProductPilot

> **An AI-powered Product Management Workspace that transforms product ideas into structured product documentation using a multi-agent architecture.**

ProductPilot streamlines the early stages of product development by converting natural language product ideas into production-ready planning artifacts. Using a coordinated pipeline of specialized AI agents, it generates Product Requirement Documents (PRDs), Business Analysis, User Stories, Roadmaps, Sprint Backlogs, and Jira-ready tasks while allowing users to iteratively refine and manage their workspace.

The platform combines **multi-agent orchestration**, **Retrieval-Augmented Generation (RAG)**, and **deterministic validation** to produce structured, consistent, and context-aware outputs.

---

## ✨ Key Features

- 🤖 **Multi-Agent Pipeline** for structured product planning.
- 📄 **Automated Documentation** including PRDs, Business Analysis, User Stories, Roadmaps, and Sprint Backlogs.
- 📚 **Project-Isolated Knowledge Grounding** with Retrieval-Augmented Generation (RAG).
- 💬 **AI Product Management Copilot** for explaining, refining, and reviewing generated documents.
- ⚡ **Deterministic Validation Engine** for fast structural verification and consistency checks.
- 🛡️ **Rate-Limit Resilience** through exponential backoff and graceful fallback handling.
- 📦 **Workspace Export & Import** for portable project workspaces.

---

# Architecture

The following diagram illustrates the end-to-end execution pipeline used by ProductPilot, from user input through multi-agent orchestration and document generation.

```mermaid
YOUR MAIN FLOWCHART HERE
```

---

# Knowledge Grounding Pipeline

ProductPilot combines project-specific knowledge with a shared knowledge base to ensure generated requirements remain context-aware while preventing cross-project contamination.

```mermaid
YOUR RAG FLOWCHART HERE
```

---

# Incremental Refinement

Rather than regenerating an entire workspace after every edit, ProductPilot selectively updates only the affected documents. This significantly reduces latency and improves consistency across generated artifacts.

```mermaid
YOUR INCREMENTAL REFINEMENT FLOWCHART HERE
```

---

# Technology Stack

| Layer | Technologies |
|--------|--------------|
| **Frontend** | Streamlit, Custom CSS |
| **Backend** | Python |
| **LLM Framework** | LangChain |
| **Model Provider** | Groq (`llama-3.1-8b-instant`) |
| **Knowledge Grounding** | FAISS, Sentence Transformers |
| **Architecture** | Multi-Agent AI Pipeline |
| **Validation** | Deterministic Python Validator |

---

# Getting Started

Clone the repository

```bash
git clone https://github.com/<username>/productpilot.git

cd productpilot
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate the environment

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file

```env
GROQ_API_KEY=your_api_key
```

Run the application

```bash
streamlit run app.py
```

---

# Usage

1. Create a new workspace by describing your product idea.
2. Generate the initial planning workspace.
3. Review and refine generated documents.
4. Ask ProductPilot for explanations, critiques, or modifications.
5. Upload project-specific documents to improve grounding.
6. Export the completed workspace.

---

# Project Structure

```
text
backend/
│
├── agents/
├── validation/
├── orchestrator.py
└── prompts.py
knowledge_base/
rag/
ui/
app.py
```
---

# License

This project is licensed under the MIT License.
