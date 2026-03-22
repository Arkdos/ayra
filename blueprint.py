import asyncio
import uuid
from typing import List, Dict, Optional, Any

# Framework Imports
from iris_out import Iris
from meatbox import MeatBox
from flashback import Flashback
from starlink import Aether
from langchain_ollama import ChatOllama


class AyraOrchestrator:
    def __init__(self, db_path: str = "ayra_memory.db"):
        self.memory = Flashback(db_path=db_path)
        self.meatbox = MeatBox(db_path=db_path)
        self.iris = Iris()
        self.aether = Aether()
        self.llm = ChatOllama(model="llama3")

        # Internal Assembly State
        self.session_id = None
        self.raw_context = ""
        self.final_content = ""
        self.active_persona = {}

    # --- STATION 1: INITIAL IGNITION ---
    def ignition(self, user_query: str, mode: str = "new"):
        """Establishes the session ID and logs the user's initial intent."""
        if mode == "new":
            self.session_id = self.memory.new_session()
        elif mode == "previous":
            self.session_id = self.memory.get_latest_session_id() or self.memory.new_session()
        else:
            self.session_id = mode

        print(f"🔥 Ignition: Session {self.session_id} established.")
        self.memory.log_turn(self.session_id, "User", user_query)
        return user_query

    # --- STATION 2: KNOWLEDGE INGESTION ---
    def ingest_materials(self, query: str, source_path: Optional[str] = None):
        """Feeds external data (URL/PDF/Image) into Iris for RAG processing."""
        if source_path:
            print(f"📥 Ingesting Materials: {source_path}")
            self.iris.rag_ingest(source_path)
            self.raw_context = self.iris.get_context(query, n_results=5)
        else:
            print("⚠️ No external materials provided. Using internal memory.")
        return self.raw_context

    # --- STATION 3: PERSONA CONFIGURATION ---
    def configure_persona(self, role_name: str, **kwargs):
        """Pulls the specific 'Staff' from MeatBox and builds the system prompt."""
        print(f"🎭 Configuring Persona: {role_name}")
        self.active_persona = self.meatbox.get_assistant(role_name)

        # Merging raw context with the persona's base template
        blueprint_prompt = self.meatbox.build_persona_prompt(
            role_name=role_name,
            additional_instructions=f"Context from materials:\n{self.raw_context}",
            **kwargs
        )
        return blueprint_prompt

    # --- STATION 4: LOGIC FABRICATION ---
    async def fabricate_content(self, system_prompt: str, workflow: str = "parallel"):
        """Triggers the LLM to process the data and build the core response."""
        print(f"🛠️ Fabricating Content (Workflow: {workflow.upper()})...")

        # Threaded execution to leverage the M4's efficiency
        response = await asyncio.to_thread(self.llm.invoke, system_prompt)
        self.final_content = response.content
        return self.final_content

    # --- STATION 5: ARTIFACT FORGING & ARCHIVAL ---
    async def forge_artifacts(self, query: str, outputs: List[str], voice: str = "ava"):
        """Generates files, speaks the results, and logs the turn into Flashback."""
        print(f"⚒️ Forging Artifacts: {outputs}")

        # 1. Log the AI output to the permanent chat history
        self.memory.log_turn(
            session_id=self.session_id,
            sender="AI",
            content=self.final_content,
            ai_assistant=self.active_persona.get('ai_name', 'Ayra'),
            model_used=self.active_persona.get('model_preference', 'llama3')
        )

        # 2. Forge files in parallel
        filename = f"mission_{self.session_id[:8]}"
        tasks = []
        if "word" in outputs:
            tasks.append(asyncio.to_thread(self.aether.forge_word_doc, query, self.final_content, filename))
        if "pdf" in outputs:
            tasks.append(asyncio.to_thread(self.aether.forge_pdf, query, self.final_content, filename))

        # Capture generated paths
        paths = await asyncio.gather(*tasks)

        # 3. Final Broadcaster Signal
        if "voice" in outputs:
            await self.aether.broadcast(f"Mission complete. Artifacts forged.", voice=voice)

        # 4. Update memory with artifacts
        self.memory.update_chat_summary(self.session_id, f"Artifacts Forged: {paths}")

        # PyCharm Console Output for immediate review
        print(f"\n{'-' * 20}\n{self.final_content}\n{'-' * 20}")
        return paths

    # --- THE MASTER CONVEYOR BELT ---
    async def execute_assembly(self, query: str, source: str, role: str, outputs: list):
        """Runs the entire factory line from start to finish."""
        q = self.ignition(query)
        self.ingest_materials(q, source)
        prompt = self.configure_persona(role)
        await self.fabricate_content(prompt)
        await self.forge_artifacts(q, outputs)