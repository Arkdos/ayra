import asyncio
import os
from typing import List, Dict, Any, Optional, Tuple

# --- Core Dependencies ---
from lore import Flashback
from meat_box import Soul
from iris_out import Iris
from starlink import Aether

# --- LangChain & Ollama ---
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_ollama import ChatOllama

class Assembly:
    """
    The JIT Assembly Line: Orchestrates Memory, Personas, Ingestion, and Output.
    Optimized for Apple Silicon (M-series) via async execution.
    """

    def __init__(self):
        print("🏭 Initializing Ayra Assembly Line...")
        self.memory = Flashback()
        self.soul = Soul()
        self.iris = Iris()
        self.aether = Aether()
        
        self.default_model = "mistral" 
        
        # State (The Conveyor Belt)
        self.session_id: str = None
        self.active_user_id: str = "default_user"
        self.raw_context: str = ""
        self.final_content: str = ""
        self.active_persona_config: Dict = {}

    # --- Station 1: Ignition ---
    def ignition(self, user_query: str, user_id: str = "default_user", mode: str = 'new') -> str:
        """Sets up the session and logs the initial user turn."""
        print(f"\n🔌 Station 1: Ignition (Mode: {mode})")
        self.active_user_id = user_id
        
        if mode == 'new':
            self.session_id = self.memory.new_session()
        else:
            self.session_id = self.memory.get_latest_session_id()
            if not self.session_id:
                print("   ⚠️ No previous session found. Starting new.")
                self.session_id = self.memory.new_session()

        # Log User Input
        self.memory.log_turn(self.session_id, self.active_user_id, user_query, ai_assistant="Orchestrator")
        print(f"   ✅ Session Active: {self.session_id}")
        return self.session_id

    # --- Station 2: Ingest Materials ---
    def ingest_materials(self, query: str, source_path: str = None):
        """Uses Iris to fetch RAG context."""
        print(f"\n📥 Station 2: Ingest Materials")
        
        if source_path:
            # 1. Ingest (if path provided)
            # We run this in a thread to avoid blocking the event loop
            # self.iris.rag_ingest(source_path) # This is synchronous in Iris currently
            # For async wrapper:
            pass # Iris ingestion is synchronous, usually fast enough or should be threaded if huge
            self.iris.rag_ingest(source_path)

        # 2. Retrieve Context
        context = self.iris.get_context(query, n_results=3)
        self.raw_context = context if context else "No external context found."
        print(f"   ✅ Context Loaded ({len(self.raw_context)} chars)")

    # --- Internal Factory: Persona Config ---
    def configure_persona(self, role_name: str, **kwargs) -> Tuple[str, ChatOllama]:
        """
        Fetches persona from MeatBox and prepares the system prompt.
        Returns (system_prompt_str, chat_model_object)
        """
        # 1. Fetch Config
        persona_conf = self.soul.get_assistant(role_name)
        model_name = persona_conf.get('model_preference', self.default_model)
        
        # 2. Build Prompt
        # We inject the RAG context into the prompt construction as 'additional_instructions'
        context_instruction = f"\n\nCONTEXT FROM IRIS:\n{self.raw_context}"
        
        system_prompt = self.soul.build_persona_prompt(
            role_name, 
            additional_instructions=context_instruction,
            **kwargs # Pass dynamic vars like grade=5
        )
        
        # 3. Init Model
        llm = ChatOllama(model=model_name, temperature=0.7)
        
        self.active_persona_config = persona_conf # Store for logging
        return system_prompt, llm

    # --- Station 3: Fabricate Content ---
    async def fabricate_content(self, 
                                scenario: str, 
                                workflow: str = 'once', 
                                roles: List[str] = None, 
                                kwargs: Dict[str, Any] = None):
        """
        The Core Engine. Runs the LLM chains based on the workflow type.
        
        Workflows:
        - 'once': Single Agent.
        - 'sequential': Chain of Agents (A -> B -> C). Output of A is input to B.
        - 'parallel': Debate/Synthesis (A & B parallel -> C Judge).
        """
        print(f"\n⚙️ Station 3: Fabricate Content (Workflow: {workflow})")
        
        if not roles: roles = ["General"]
        if not kwargs: kwargs = {}

        try:
            if workflow == 'once':
                # --- Workflow: Single Shot ---
                role = roles[0]
                sys_prompt, llm = self.configure_persona(role, **kwargs)
                
                print(f"   ↳ Running Single Chain with Role: {role}")
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", sys_prompt),
                    ("human", "{input}")
                ])
                chain = prompt | llm | StrOutputParser()
                self.final_content = await chain.ainvoke({"input": scenario})

            elif workflow == 'sequential':
                # --- Workflow: Sequential (Chain of Command) ---
                # Example: Brainstormer -> Writer -> Editor
                print(f"   ↳ Running Sequential Chain: {roles}")
                
                chain_history = ""
                current_input = scenario
                
                for i, role in enumerate(roles):
                    print(f"     ➜ Step {i+1}: {role}")
                    sys_prompt, llm = self.configure_persona(role, **kwargs)
                    
                    # Update prompt to include previous output/context
                    if i == 0:
                        step_input = scenario
                    else:
                        step_input = f"Original Request: {scenario}\n\nPrevious Output to Refine/Use:\n{chain_history}\n\nYour Task: Build upon or edit the above."
                    
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", sys_prompt),
                        ("human", "{input}")
                    ])
                    chain = prompt | llm | StrOutputParser()
                    
                    response = await chain.ainvoke({"input": step_input})
                    
                    # For sequential, the "final" content is the output of the LAST step,
                    # but we keep history for context if needed.
                    chain_history = response 
                
                self.final_content = chain_history

            elif workflow == 'parallel':
                # --- Workflow: Parallel Debate & Judge ---
                # Logic: Run first N-1 roles in parallel. Run the LAST role as the Judge/Synthesizer.
                if len(roles) < 2:
                    print("⚠️ Parallel workflow requires at least 2 roles.")
                    return

                # The Judge is the last role in the list
                judge_role = roles[-1]
                debate_roles = roles[:-1]
                
                print(f"   ↳ Running Parallel Swarm: {debate_roles}")
                print(f"   ↳ Judge/Synthesizer: {judge_role}")
                
                # 1. Create Parallel Chains
                chains = {}
                for role in debate_roles:
                    sys_p, llm = self.configure_persona(role, **kwargs)
                    prompt = ChatPromptTemplate.from_messages([("system", sys_p), ("human", "{input}")])
                    chains[role] = (prompt | llm | StrOutputParser())
                
                # 2. Run Parallel
                map_chain = RunnableParallel(**chains)
                debate_results = await map_chain.ainvoke({"input": scenario})
                
                # 3. Format Debate Output for Judge
                debate_transcript = "\n\n".join([f"--- {r.upper()} ARGUMENT ---\n{content}" for r, content in debate_results.items()])
                
                # 4. Run Judge
                print(f"     ➜ Synthesizing with {judge_role}...")
                sys_prompt_judge, llm_judge = self.configure_persona(judge_role, **kwargs)
                judge_input = f"Scenario: {scenario}\n\nArguments from Team:\n{debate_transcript}\n\nTask: Synthesize, judge, or merge these into a final answer."
                
                prompt_judge = ChatPromptTemplate.from_messages([
                    ("system", sys_prompt_judge),
                    ("human", "{input}")
                ])
                chain_judge = prompt_judge | llm_judge | StrOutputParser()
                
                self.final_content = await chain_judge.ainvoke({"input": judge_input})

            # Log the AI's final turn
            assistant_name = self.active_persona_config.get('ai_name', 'Assembly')
            model = self.active_persona_config.get('model_preference', 'Unknown')
            
            self.memory.log_turn(
                self.session_id, 
                sender="AI", 
                content=self.final_content, 
                ai_assistant=assistant_name,
                model_used=model
            )
            
            # Update summary
            summary = f"Workflow '{workflow}' completed with roles {roles}."
            self.memory.update_chat_summary(self.session_id, summary)
            
            print("   ✅ Fabrication Complete.")

        except Exception as e:
            print(f"❌ Fabrication Failed: {e}")
            self.final_content = f"Error during fabrication: {e}"

    # --- Station 4: Forge Artifacts ---
    async def forge_artifacts(self, outputs: List[str]):
        """
        Parallel production of files (PDF, Word, Excel) and Signals.
        """
        print(f"\n🔨 Station 4: Forge Artifacts {outputs}")
        
        tasks = []
        
        # 1. Document Forging
        if 'word' in outputs:
            tasks.append(self.aether.forge_word(self.final_content, f"mission_{self.session_id[:8]}.docx"))
        
        if 'pdf' in outputs:
            tasks.append(self.aether.forge_pdf(self.final_content, f"mission_{self.session_id[:8]}.pdf"))
            
        if 'excel' in outputs:
            dummy_data = [{"Session": self.session_id, "Content": self.final_content[:100]}]
            tasks.append(self.aether.forge_excel(dummy_data, f"mission_{self.session_id[:8]}.xlsx"))

        # 2. Signals
        if 'voice' in outputs:
            tasks.append(self.aether.broadcast(self.final_content[:500], save_file=f"brief_{self.session_id[:8]}.mp3")) 

        # Execute all forge tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks)
            print(f"   ✅ Artifacts Created: {results}")
        else:
            print("   ⚠️ No artifacts requested.")

    # --- Master Controller ---
    async def execute_assembly(self, 
                               query: str, 
                               source: str = None, 
                               workflow: str = 'once', 
                               roles: List[str] = None, 
                               outputs: List[str] = None,
                               **persona_kwargs):
        """
        Runs the full assembly line: Ignition -> Ingest -> Fabricate -> Forge.
        """
        if not roles: roles = ["General"]
        if not outputs: outputs = []

        # 1. Ignition
        self.ignition(query)
        
        # 2. Ingest
        self.ingest_materials(query, source)
        
        # 3. Fabricate (Async)
        await self.fabricate_content(query, workflow, roles, kwargs=persona_kwargs)
        
        # 4. Forge (Async)
        await self.forge_artifacts(outputs)
        
        return self.final_content

# --- Verification Test Block ---
if __name__ == "__main__":
    async def run_test_mission():
        orchestrator = Assembly()
        
        # Test Scenario: Parallel Debate
        query = "Discuss the ethics of AI sentience."
        # Roles: 2 Debaters + 1 Judge
        # Assuming we have "Propaganda" (Advocate) and "Critique" (Judge) roles in DB. 
        # Using "General" as the skeptic if needed or just re-using roles.
        roles = ["General", "General", "General"]
        
        outputs = ['word']
        
        print("🚀 STARTING PARALLEL MISSION")
        result = await orchestrator.execute_assembly(
            query=query, 
            workflow='parallel',
            roles=roles,
            outputs=outputs
        )
        
        print("\n🏁 MISSION COMPLETE")
        print(f"Final Output Preview:\n{result}...")

    asyncio.run(run_test_mission())
