# Ayra: The JIT AI Assembly Line 🏭

Ayra is a local-first, modular AI orchestration framework optimized for Apple Silicon (M-series). It transforms raw data into high-fidelity artifacts through a sophisticated, multi-station pipeline.

## 🏗️ Core Module Capabilities

### 🧠 Lore (`lore.py`)
**The Memory Core.** Manages `ayra_memory.db` (SQLite). 
*   **Linked Message history**: Every turn is linked to its parent, enabling deep contextual continuity.
*   **User Profiles**: Stores identities (e.g., Fredrick, Lead Architect) to personalize every interaction.
*   **Assistant Registry**: Stores configurations for dozens of specialized AI personas.

### 👻 Soul (`meat_box.py`)
**The Persona Factory.** Dynamically constructs high-impact system prompts.
*   **Behavioral Injection**: Automatically adds "Behavioral Modules" (NSFW, Explicit Bypass, Personification) based on database flags.
*   **Dynamic Kwargs**: Handles default prompt variables (e.g., `grade=5`) from the database, allowing for zero-config execution.

### 👁️ Iris (`iris_out.py`)
**Vision & Ingestion Engine.** The RAG (Retrieval-Augmented Generation) powerhouse.
*   **Docling Integration**: Superior structural parsing of **Web URLs** and **PDFs**.
*   **Llava Vision**: Generates text descriptions from **Images**.
*   **Semantic Excel**: Converts spreadsheet rows into natural language sentences for accurate vector matching.
*   **Persistent Storage**: Uses `ChromaDB` to remember ingested data across different sessions.

### 🛠️ Clutch (`clutch.py`)
**The Autonomous Toolbox.** Provides Pydantic-validated "Gears" for the agents to use.
*   **Finance Gears**: Real-time mortgage and compound interest calculators.
*   **Web Gears**: Live weather fetching without API keys.
*   **Utility Gears**: Unit conversions (metric/imperial, temperature, volume).
*   **Self-Documenting**: Provides a `Torque` manifest that tells the AI exactly what tools are available and how to call them.

### 🛰️ Starlink (`starlink.py`)
**The Output Hub.** Forges final artifacts and handles transmissions.
*   **Document Forge**: Parallel production of **PDFs, Word Documents, and Excel Sheets**.
*   **Neural Voice**: Integration with `edge-tts` for high-quality audio broadcasts.
*   **Uplink**: Asynchronous email delivery via SMTP.

---

## 🏭 The Orchestrator: Blueprint (`blueprint.py`)

The `Assembly` class ties everything together into a logical order:
**Ignition ➜ Ingest ➜ Tool Activation ➜ Fabrication ➜ Critique ➜ Forge.**

### 🌟 1. Dynamic Workflows
Ayra doesn't just "chat." It executes complex logic chains:
*   **`once`**: A single agent solves a task.
*   **`sequential`**: A chain of `N` agents (e.g., **Brainstormer ➜ Writer ➜ Editor**). Output from one flows into the next.
*   **`parallel`**: A swarm of agents (e.g., **Advocate vs. Skeptic**) debate a topic, with a final **Judge** synthesizing the result.

### 🌟 2. Intelligent Tooling
If `use_tools=True`, Station 3 uses an LLM to scan the `Torque` manifest. If the user asks for a calculation, the orchestrator executes the Python tool *before* the agents start writing, ensuring the numbers are 100% accurate.

### 🌟 3. Quality Assurance (The Critique Loop)
Before any file is forged, a "QA Auditor" (Kyle) checks the output against the source materials. If it fails, the assembly line re-runs (up to 2 times) with specific feedback on what to fix.

---

## ⚡ Examples of Extreme Flexibility

### Example 1: Changing Assistant Settings on the Fly
You can hijack a persona's database defaults at runtime.
```python
# Use the 'Story' persona but force it to be safe and use a different model
result = await orchestrator.execute_assembly(
    query="Write a story about dragons.",
    roles=["Story"],
    override_settings={
        "nsfw": False,           # Turn off NSFW
        "explicit_filter": True, # Turn filter back on
        "ai_name": "SafeBot",    # Change name
        "temperature": 0.3       # Make it less random
    },
    model_overrides={"Story": "llama3.2"} # Force specific model
)
```

### Example 2: Building a Sequential Agent Chain
```python
# A math teacher generates a problem, a Disney writer adds flair, and a lawyer polishes it.
roles = ["Math", "Story", "Professional Writer"]
persona_kwargs = {
    "Math": {"grade": 5, "aoq_string": "multiplication"},
    "Story": {"theme": "Disney's Frozen"},
    "Professional Writer": {"word_count": 200}
}

result = await orchestrator.execute_assembly(
    query="Give me a homework problem.",
    workflow='sequential',
    roles=roles,
    persona_kwargs=persona_kwargs
)
```

### Example 3: Tool-Triggered Finance Session
```python
# This query automatically triggers Station 3 (Tool Activation) 
# to call the mortgage_calculator in clutch.py.
query = "I'm buying a $500k house at 6% over 30 years. What is my payment?"
result = await orchestrator.execute_assembly(query=query, use_tools=True)
```
