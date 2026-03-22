import asyncio
import os
import warnings
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

# Suppress Warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="opentelemetry")
os.environ["USER_AGENT"] = "Ayra/1.0"

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
        """
        Sets up the session and logs the initial user turn.
        Mode can be: 'new', 'continue' (latest), or a specific Session UUID.
        """
        print(f"\n🔌 Station 1: Ignition (Mode: {mode})")
        self.active_user_id = user_id
        
        if mode == 'continue':
            self.session_id = self.memory.get_latest_session_id()
            if self.session_id:
                print(f"   ↪️ Resuming Latest Session: {self.session_id}")
            else:
                print("   ⚠️ No previous session found. Starting new.")
                self.session_id = self.memory.new_session()
                
        elif mode != 'new':
            self.session_id = mode
            print(f"   ↪️ Resuming Specific Session: {self.session_id}")
            
        else: # 'new'
            self.session_id = self.memory.new_session()
            print(f"   ✅ New Session Created: {self.session_id}")

        self.memory.log_turn(
            self.session_id, 
            sender=self.active_user_id, 
            content=user_query, 
            ai_assistant=None,  
            model_used=None
        )
        
        return self.session_id

    # --- Station 2: Ingest Materials ---
    def ingest_materials(self, query: str, source_path: str = None):
        """Uses Iris to fetch RAG context."""
        print(f"\n📥 Station 2: Ingest Materials")
        
        if source_path:
            self.iris.rag_ingest(source_path)

        context = self.iris.get_context(query, n_results=3)
        self.raw_context = context if context else "No external context found."
        print(f"   ✅ Context Loaded ({len(self.raw_context)} chars)")

    # --- Internal Factory: Persona Config ---
    def configure_persona(self, role_name: str, **kwargs) -> Tuple[str, ChatOllama]:
        """
        Fetches persona from Soul and prepares the system prompt.
        """
        persona_conf = self.soul.get_assistant(role_name)
        model_name = persona_conf.get('model_preference', self.default_model)
        
        context_instruction = f"\n\nCONTEXT FROM IRIS:\n{self.raw_context}"
        
        system_prompt = self.soul.build_persona_prompt(
            role_name, 
            additional_instructions=context_instruction,
            **kwargs 
        )
        
        llm = ChatOllama(model=model_name, temperature=0.7)
        
        self.active_persona_config = persona_conf
        return system_prompt, llm

    # --- Station 3: Fabricate Content ---
    async def fabricate_content(self, 
                                scenario: str, 
                                workflow: str = 'once', 
                                roles: List[str] = None, 
                                kwargs: Dict[str, Any] = None):
        """
        The Core Engine. Runs the LLM chains based on the workflow type.
        """
        print(f"\n⚙️ Station 3: Fabricate Content (Workflow: {workflow})")
        
        if not roles: roles = ["General"]
        if not kwargs: kwargs = {}

        try:
            if workflow == 'once':
                role = roles[0]
                sys_prompt, llm = self.configure_persona(role, **kwargs)
                print(f"   ↳ Running Single Chain with Role: {role}")
                
                prompt = ChatPromptTemplate.from_messages([("system", sys_prompt), ("human", "{input}")])
                chain = prompt | llm | StrOutputParser()
                self.final_content = await chain.ainvoke({"input": scenario})

            elif workflow == 'sequential':
                print(f"   ↳ Running Sequential Chain: {roles}")
                chain_history = ""
                for i, role in enumerate(roles):
                    print(f"     ➜ Step {i+1}: {role}")
                    sys_prompt, llm = self.configure_persona(role, **kwargs.get(role, {}))
                    
                    if i == 0:
                        step_input = scenario
                    else:
                        step_input = f"Original Request: {scenario}\n\nPrevious Output:\n{chain_history}\n\nTask: Build upon/refine this."
                    
                    prompt = ChatPromptTemplate.from_messages([("system", sys_prompt), ("human", "{input}")])
                    chain = prompt | llm | StrOutputParser()
                    response = await chain.ainvoke({"input": step_input})
                    chain_history = response 
                self.final_content = chain_history

            elif workflow == 'parallel':
                if len(roles) < 2:
                    print("⚠️ Parallel workflow requires at least 2 roles.")
                    return

                judge_role = roles[-1]
                debate_roles = roles[:-1]
                
                print(f"   ↳ Parallel Swarm: {debate_roles} -> Judge: {judge_role}")
                
                chains = {}
                for role in debate_roles:
                    sys_p, llm = self.configure_persona(role, **kwargs.get(role, {}))
                    prompt = ChatPromptTemplate.from_messages([("system", sys_p), ("human", "{input}")])
                    chains[role] = (prompt | llm | StrOutputParser())
                
                map_chain = RunnableParallel(**chains)
                debate_results = await map_chain.ainvoke({"input": scenario})
                
                debate_transcript = "\n\n".join([f"--- {r.upper()} --- \n{content}" for r, content in debate_results.items()])
                
                print(f"     ➜ Synthesizing with {judge_role}...")
                sys_prompt_judge, llm_judge = self.configure_persona(judge_role, **kwargs.get(judge_role, {}))
                judge_input = f"Scenario: {scenario}\n\nArguments:\n{debate_transcript}\n\nTask: Synthesize."
                
                prompt_judge = ChatPromptTemplate.from_messages([("system", sys_prompt_judge), ("human", "{input}")])
                chain_judge = prompt_judge | llm_judge | StrOutputParser()
                self.final_content = await chain_judge.ainvoke({"input": judge_input})

            # Log Final Turn
            assistant_name = self.active_persona_config.get('ai_name', 'Assembly')
            model = self.active_persona_config.get('model_preference', 'Unknown')
            
            self.memory.log_turn(
                self.session_id, 
                sender="AI", 
                content=self.final_content, 
                ai_assistant=assistant_name,
                model_used=model
            )
            print("   ✅ Fabrication Complete.")

        except Exception as e:
            print(f"❌ Fabrication Failed: {e}")
            self.final_content = f"Error: {e}"

    # --- Station 4: Forge Artifacts ---
    async def forge_artifacts(self, outputs: List[str]):
        """Parallel production of files and signals."""
        print(f"\n🔨 Station 4: Forge Artifacts {outputs}")
        tasks = []
        
        if 'word' in outputs:
            tasks.append(self.aether.forge_word(self.final_content, f"mission_{self.session_id[:8]}.docx"))
        if 'pdf' in outputs:
            tasks.append(self.aether.forge_pdf(self.final_content, f"mission_{self.session_id[:8]}.pdf"))
        if 'excel' in outputs:
            dummy_data = [{"Session": self.session_id, "Content": self.final_content[:100]}]
            tasks.append(self.aether.forge_excel(dummy_data, f"mission_{self.session_id[:8]}.xlsx"))
        if 'voice' in outputs:
            tasks.append(self.aether.broadcast(self.final_content[:500], save_file=f"brief_{self.session_id[:8]}.mp3")) 

        if tasks:
            results = await asyncio.gather(*tasks)
            print(f"   ✅ Artifacts Created.")
        else:
            print("   ⚠️ No artifacts requested.")

    # --- Extra: On-Demand Summary ---
    async def summarize_session(self):
        """
        Reads the full chat history of the current session and generates a concise summary.
        """
        print(f"\n📝 Generating Session Summary for {self.session_id}...")
        
        history = self.memory.get_session_history(self.session_id)
        if not history:
            print("   ⚠️ No history to summarize.")
            return

        transcript = "\n".join([f"{msg['sender']}: {msg['content']}" for msg in history])
        
        sys_prompt, llm = self.configure_persona("Summarizer") 
        prompt = ChatPromptTemplate.from_messages([
            ("system", sys_prompt),
            ("human", "Summarize this conversation context:\n\n{input}")
        ])
        chain = prompt | llm | StrOutputParser()
        
        summary_text = await chain.ainvoke({"input": transcript})
        
        self.memory.update_chat_summary(self.session_id, summary_text)
        print(f"   ✅ Summary Updated: {summary_text[:100]}...")

    # --- Master Controller ---
    async def execute_assembly(self, 
                               query: str, 
                               source: str = None, 
                               workflow: str = 'once', 
                               roles: List[str] = None, 
                               outputs: List[str] = None,
                               session_mode: str = 'new', # 'new', 'continue', or UUID string
                               **persona_kwargs):
        """
        Runs the full assembly line.
        """
        if not roles: roles = ["General"]
        if not outputs: outputs = []

        # 1. Ignition (with dynamic mode)
        self.ignition(query, mode=session_mode)
        
        # 2. Ingest
        self.ingest_materials(query, source)
        
        # 3. Fabricate
        await self.fabricate_content(query, workflow, roles, kwargs=persona_kwargs)
        
        # 4. Forge
        await self.forge_artifacts(outputs)
        
        return self.final_content

def sample_sequential_process():
    async def run_test_mission():
        orchestrator = Assembly()

        print("\n🚀 STARTING COMPLEX SEQUENTIAL MISSION")

        query = "Generate a simple multiplication problem for a 5th grader."

        # Define the 3-step sequential workflow
        roles = ["Math", "Story", "Professional Writer"]

        # Define the desired output
        outputs = ['word']

        result = await orchestrator.execute_assembly(
            query=query,
            workflow='sequential',
            roles=roles,
            outputs=outputs,
        )

        print("\n🏁 MISSION COMPLETE")
        print(f"Final Output (from Professional Writer):\n{result}")

    asyncio.run(run_test_mission())

# --- Verification Test Block ---
if __name__ == "__main__":
    sample_sequential_process()