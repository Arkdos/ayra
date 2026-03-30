# Ayra: High-Performance AI Orchestration Framework

Ayra is a modular, local-first AI framework designed for high-precision mission execution. Optimized for Apple Silicon (M-series), it transforms raw data and user intent into sophisticated deliverables—ranging from Word reports and PDF quizzes to financial spreadsheets and neural voice broadcasts.

## 🏗️ Core Architecture (Station-by-Station)

Ayra's power lies in its **"JIT Assembly Line"** structure, where every task passes through specialized stations managed by the `Assembly` orchestrator (`blueprint.py`).

### 1. 🧠 Lore (`lore.py`)
**Role:** The Memory Core.
- **SQLite Integration:** Manages `ayra_memory.db` to store message history, user profiles, and AI assistant metadata.
- **Continuity:** Restores conversation context by loading previous turns as a structured message list (`System`, `Human`, `AI`).
- **Data Bridge:** Enables CSV-based management of assistants, making it the source of truth for the entire framework.

### 2. 👻 Soul (`meat_box.py`)
**Role:** The Persona Factory.
- **Dynamic Prompts:** Constructs complex system instructions on-the-fly.
- **Behavioral Injection:** Injects specific modular templates based on DB flags (e.g., `Explicit Bypass`, `NSFW Core`, `Personify`).
- **Kwarg Defaults:** Merges user input with database-stored `default_kwargs`, ensuring templates (like `Math` or `Teaching`) never fail due to missing variables.

### 3. 👁️ Iris (`iris_out.py`)
**Role:** The Vision & Knowledge Intake.
- **Docling Integration:** Scrapes URLs and parses PDFs while preserving structure (tables/headers).
- **Vision (LLaVA):** Analyzes images and generates descriptive text context.
- **Semantic RAG:** Persists knowledge in `ChromaDB` using `nomic-embed-text` for lightning-fast similarity search.

### 4. 🛠️ Clutch (`clutch.py`)
**Role:** The Precision Toolbox (Torque).
- **Modular Gears:** Contains specialized classes for **Finance** (advanced compounding), **Web** (real-time weather), **Text**, and **Utilities** (universal unit conversion).
- **Ollama Tool Calling:** The orchestrator can "activate" these tools by scanning a self-documenting manifest.
- **Confidence Validation:** Uses **Pydantic** to enforce strict bounds on all numerical and string inputs.

### 5. 🏭 Assembly (`blueprint.py`)
**Role:** The Central Orchestrator.
- **Station Management:** Manages the logical flow: `Ignition` → `Ingest` → `Activate Tools` → `Fabricate` → `Critique` → `Forge`.
- **Workflows:**
    - **Sequential:** Chains agents (e.g., `Math` → `Story` → `Professional Writer`) where each output feeds the next.
    - **Parallel:** Runs a swarm of agents (e.g., `Advocate` + `Skeptic`) and synthesizes their debate using a `Judge`.
- **Quality Assurance:** Triggers a **Critique Agent** (Kyle) to audit the response, initiating an automatic re-fabrication loop if quality checks fail.

### 6. 🛰️ Starlink (`starlink.py`)
**Role:** The Forge & Communication Hub.
- **Artifact Forging:** Parallel generation of Word docs, PDFs, and Excel spreadsheets.
- **Signals:** Provides Neural TTS voice (`edge-tts`) and asynchronous email delivery.

---

## 🚀 Easy Configuration

### Change Assistant Settings without Code
To change an assistant's behavior (e.g., make the Math tutor use a higher temperature or a different default grade), simply edit **`ai_assistants.csv`** and run:
```bash
python3 persona_rocket.py
```
This syncs your spreadsheet changes directly to the framework's database.

### Simple Workflow Execution
```python
from blueprint import Assembly
import asyncio

orchestrator = Assembly()

# 3-Agent Sequential Chain: Generate Math -> Disney Spin -> Professional Memo
roles = ["Math", "Story", "Professional Writer"]
persona_kwargs = {
    "Math": {"grade": 5, "aoq_string": "a single multiplication equation"},
    "Story": {"theme": "Disney"},
    "Professional Writer": {"word_count": 200}
}

asyncio.run(orchestrator.execute_assembly(
    query="Create a test for me.",
    workflow='sequential',
    roles=roles,
    persona_kwargs=persona_kwargs
))
```

## 📊 Performance Reporting
Ayra automatically tracks and reports **Estimated TPS (Tokens Per Second)** and execution duration, giving you immediate feedback on model performance on your local hardware.
