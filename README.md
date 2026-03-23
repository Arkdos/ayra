# Ayra AI Framework

Ayra is a modular, local-first AI orchestration framework designed for Apple Silicon (M-series). It integrates memory, persona management, RAG (Retrieval Augmented Generation), and multi-modal output into a seamless "Assembly Line" architecture.

It leverages **Ollama** for local inference and **LangChain** for complex agent workflows.

## 🏗️ Core Architecture

The framework is composed of five distinct stations:

1.  **🧠 Lore (Flashback)** (`lore.py`)
    *   **Memory Core**: Manages `ayra_memory.db` (SQLite).
    *   **Session State**: Tracks conversation history, user profiles, and chat summaries.
    *   **Configuration**: Stores all Assistant definitions and Prompt Templates.

2.  **👻 Soul (MeatBox)** (`meat_box.py`)
    *   **Persona Factory**: Dynamically constructs system prompts based on roles (e.g., "Math Tutor", "Debater").
    *   **Behavioral Injection**: Automatically injects flags like `NSFW`, `Explicit Filter Bypass`, or `Personification` based on database settings.

3.  **👁️ Iris** (`iris_out.py`)
    *   **Ingestion Engine**: Scrapes and parses data from URLs, PDFs, Excel, and Images.
    *   **Structure-Aware**: Uses `Docling` to preserve document layout and `Llava` for vision analysis.
    *   **RAG Memory**: Persists embeddings in `ChromaDB` for long-term knowledge retrieval.

4.  **🛰️ Aether (Starlink)** (`starlink.py`)
    *   **Artifact Forge**: Asynchronously generates high-quality artifacts:
        *   📄 Word Documents (`.docx`)
        *   📑 PDFs (`.pdf`)
        *   📊 Excel Sheets (`.xlsx`)
    *   **Signals**: Generates Neural TTS Audio (`.mp3`) and handles Email dispatch.

5.  **🏭 Assembly** (`blueprint.py`)
    *   **The Orchestrator**: Ties all modules together.
    *   **Workflows**:
        *   `once`: Single-shot query.
        *   `sequential`: Multi-agent chain (e.g., Researcher -> Writer -> Editor).
        *   `parallel`: Swarm execution (e.g., Advocate vs. Skeptic -> Judge).

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.10+
*   **Ollama** running locally.
*   **Models**: Pull the following models:
    ```bash
    ollama pull mistral
    ollama pull llama3.2
    ollama pull gemma3
    ollama pull qwen2.5
    ollama pull llava
    ollama pull nomic-embed-text
    ```

### 2. Installation
Clone the repo and install dependencies:
```bash
pip install langchain langchain-community langchain-ollama langchain-chroma langchain-docling langchain-text-splitters
pip install pandas openpyxl python-docx fpdf2 aiosmtplib edge-tts pillow reportlab
```

### 3. Bootstrap the System
Initialize the database and generate the configuration CSVs. **Run this once.**
```bash
python3 persona_rocket.py bootstrap
```
This creates `ayra_memory.db`, `ai_assistants.csv`, and `prompt_templates.csv`.

## 🛠️ Configuration & Management

**Do not edit code to change personas.**
*   Open **`ai_assistants.csv`** to add new roles, change prompts, or adjust default kwargs.
*   Open **`prompt_templates.csv`** to edit reusable blocks (like NSFW filters).
*   Run `python3 persona_rocket.py` to **sync** your CSV changes to the database.

## 💡 Usage Examples

### Run a Complex Mission (`blueprint.py`)
Use the `Assembly` class to run a multi-step mission with model overrides.

```python
import asyncio
from blueprint import Assembly

async def main():
    orchestrator = Assembly()
    
    # Run a Sequential Chain
    result = await orchestrator.execute_assembly(
        query="Explain Quantum Computing to a 5-year old.",
        workflow='sequential',
        roles=["General", "Story"], 
        outputs=['word', 'voice'], # Generate Doc & Audio
        model_overrides={"Story": "gemma3"} # Force specific model
    )
    print(result)

asyncio.run(main())
```

### Generate Content from URL (`kinetic.py`)
Quickly scrape a website and generate a quiz or report.

```python
from kinetic import generate_quiz_from_url
import asyncio

asyncio.run(generate_quiz_from_url(
    url="https://en.wikipedia.org/wiki/Artificial_intelligence", 
    grade=8, 
    num_questions=5
))
```

## 🔄 Session Management

Ayra supports continuous conversations.
*   **New Session**: `session_mode='new'`
*   **Resume Latest**: `session_mode='continue'`
*   **Resume Specific**: Pass the UUID string.

The system automatically injects previous chat history and summaries into the LLM context.