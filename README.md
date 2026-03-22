# Ayra: Modular AI Orchestration Framework

Ayra is a local-first, modular AI framework designed to orchestrate specialized LLM personas, RAG (Retrieval-Augmented Generation), and multi-modal outputs. It leverages **Ollama** for local inference and **LangChain** for complex workflows, optimized for Apple Silicon (M-series) performance.

## 🌟 Core Architecture

The framework is built as an assembly line (`blueprint.py`) with distinct, specialized modules:

### 1. 🧠 Flashback (`lore.py`) - Memory
- **Persistent Storage**: Uses SQLite (`ayra_memory.db`) to store session history, user profiles, and assistant configurations.
- **Context Awareness**: Retrieves relevant history and user details to inject into prompts.
- **CSV Sync**: Use `persona_rocket.py` to manage your AI assistants and templates via CSV files instead of code.

### 2. 👻 Soul (`meat_box.py`) - Personas
- **Persona Factory**: Dynamically constructs system prompts based on roles (e.g., "Math Tutor", "Financial Analyst", "NSFW Writer").
- **Template Injection**: Automatically injects behavior modules (e.g., "Explicit Bypass", "Threaten Compliance") based on database flags.
- **Runtime Overrides**: Allows on-the-fly adjustment of tone, strictness, and directives.

### 3. 👁️ Iris (`iris_out.py`) - Vision & Ingestion (RAG)
- **Multi-Source Ingestion**:
  - **Web**: Scrapes and parses URLs using `Docling`.
  - **PDF**: Intelligent structural parsing of documents.
  - **Excel**: Converts rows into semantic sentences for better retrieval.
  - **Images**: Uses **LLaVA** to generate text descriptions of visual content.
- **Vector Memory**: Persists embeddings using `ChromaDB` and `nomic-embed-text`.

### 4. 🛰️ Aether (`starlink.py`) - Output & Communication
- **Artifact Forging**: Asynchronously generates high-quality **PDF**, **Word**, and **Excel** files.
- **Signals**:
  - **Voice**: Generates neural TTS audio via `edge-tts`.
  - **Uplink**: Sends emails via SMTP.

### 5. 🏭 Assembly (`blueprint.py`) - Orchestration
- **The Engine**: Ties all modules together into a cohesive pipeline: **Ignition -> Ingest -> Fabricate -> Forge**.
- **Complex Workflows**:
  - **Sequential**: Chain agents (e.g., Brainstorm -> Draft -> Edit).
  - **Parallel**: Run agents simultaneously (e.g., Debate) and synthesize results (Judge).

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) installed and running.
- Required Models: `mistral`, `llama3.2`, `gemma3`, `qwen2.5`, `llava`, `nomic-embed-text`.

### Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/yourusername/ayra.git
    cd ayra
    ```

2.  **Install Dependencies**:
    ```bash
    pip install langchain langchain-community langchain-ollama langchain-chroma langchain-docling 
    pip install pandas openpyxl python-docx fpdf2 aiosmtplib edge-tts pillow reportlab
    ```

3.  **Initialize Database**:
    Run the rocket to populate your local database with default personas and templates.
    ```bash
    python3 persona_rocket.py bootstrap
    ```

### Usage Examples

#### 1. Generate a Quiz from a URL (`kinetic.py`)
```python
from kinetic import generate_quiz_from_url
import asyncio

# Generates a PDF quiz about Quantum Computing
asyncio.run(generate_quiz_from_url("https://en.wikipedia.org/wiki/Quantum_computing", grade=8))
```

#### 2. Run a Complex Debate (`blueprint.py`)
```python
from blueprint import Assembly
import asyncio

async def run_debate():
    orchestrator = Assembly()
    await orchestrator.execute_assembly(
        query="Is AI sentience possible?",
        workflow='parallel',
        roles=["Propaganda", "Critique", "General"], # Advocate, Skeptic, Judge
        outputs=['word']
    )

asyncio.run(run_debate())
```

## 📂 File Structure

- `ayra_memory.db`: SQLite database storing all state.
- `ai_assistants.csv`: Editable source of truth for AI personas.
- `prompt_templates.csv`: Editable source for reusable prompt blocks.
- `mission_artifacts/`: Directory where generated PDFs, Docs, and Audio are saved.

## 🛠️ Customization

To add a new AI persona, simply edit **`ai_assistants.csv`** and add a new row. Then run:
```bash
python3 persona_rocket.py
```
This will sync your CSV changes to the database, making the new persona immediately available to the Assembly line.