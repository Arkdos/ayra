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
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

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
                
        elif mode != 'new' and mode is not None:
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
    def configure_persona(self, role_name: str, model_override: str = None, **kwargs) -> Tuple[List[Any], ChatOllama]:
        """
        Fetches persona from Soul and prepares the full message history.
        """
        persona_conf = self.soul.get_assistant(role_name)
        
        if model_override:
            model_name = model_override
        else:
            model_name = persona_conf.get('model_preference', self.default_model)
        
        context_instruction = f"\n\nCONTEXT FROM IRIS:\n{self.raw_context}"
        
        system_text = self.soul.build_persona_prompt(
            role_name, 
            additional_instructions=context_instruction,
            **kwargs 
        )
        
        messages = [SystemMessage(content=system_text)]
        
        if self.session_id:
            history = self.memory.get_session_history(self.session_id)
            for msg in history:
                content = msg.get('content', '')
                sender = msg.get('sender')
                if sender == 'AI':
                    messages.append(AIMessage(content=content))
                else:
                    messages.append(HumanMessage(content=content))
        
        print(f"     Creating LLM: {model_name} for role {role_name}")
        llm = ChatOllama(model=model_name, temperature=0.7)
        
        persona_conf['model_preference'] = model_name
        self.active_persona_config = persona_conf
        
        return messages, llm

    # --- Station 3: Fabricate Content ---
    async def fabricate_content(self, 
                                scenario: str, 
                                workflow: str = 'once', 
                                roles: List[str] = None,
                                model_overrides: Dict[str, str] = None,
                                kwargs: Dict[str, Any] = None):
        """
        The Core Engine. Runs LLM chains based on the workflow type.
        Fully dynamic: supports any number of roles in sequential or parallel.
        """
        print(f"\n⚙️ Station 3: Fabricate Content (Workflow: {workflow})")
        
        if not roles: roles = ["General"]
        if not kwargs: kwargs = {}
        if not model_overrides: model_overrides = {}

        try:
            if workflow == 'once':
                # --- Workflow: Single Shot ---
                role = roles[0]
                model = model_overrides.get(role)
                history_messages, llm = self.configure_persona(role, model_override=model, **kwargs.get(role, {}))
                
                print(f"   ↳ Running Single Chain with Role: {role}")
                
                prompt = ChatPromptTemplate.from_messages(history_messages)
                chain = prompt | llm | StrOutputParser()
                self.final_content = await chain.ainvoke({})

            elif workflow == 'sequential':
                # --- Workflow: Dynamic Sequential Chain ---
                # A -> B -> C -> D ... -> N
                # Each step receives the output of the previous step as context.
                print(f"   ↳ Running Sequential Chain with {len(roles)} Steps: {roles}")
                
                chain_history = ""
                
                for i, role in enumerate(roles):
                    print(f"     ➜ Step {i+1}/{len(roles)}: {role}")
                    
                    model = model_overrides.get(role)
                    history_messages, llm = self.configure_persona(role, model_override=model, **kwargs.get(role, {}))
                    
                    if i > 0:
                        # Append the previous step's output as explicit context for the next agent
                        context_msg = f"Output from previous agent ({roles[i-1]}):\n{chain_history}\n\nTask: Continue, refine, or critique based on this."
                        history_messages.append(HumanMessage(content=context_msg))
                    
                    prompt = ChatPromptTemplate.from_messages(history_messages)
                    chain = prompt | llm | StrOutputParser()
                    
                    response = await chain.ainvoke({})
                    chain_history = response 
                
                self.final_content = chain_history

            elif workflow == 'parallel':
                # --- Workflow: Dynamic Parallel Swarm ---
                # Roles [A, B, C, D] -> [A, B, C] run in parallel -> D synthesizes.
                # Requires at least 2 roles.
                if len(roles) < 2:
                    print("⚠️ Parallel workflow requires at least 2 roles.")
                    return

                judge_role = roles[-1]        # The last role is always the synthesizer
                swarm_roles = roles[:-1]      # All previous roles are the swarm
                
                print(f"   ↳ Running Parallel Swarm with {len(swarm_roles)} Agents: {swarm_roles}")
                print(f"   ↳ Synthesizer/Judge: {judge_role}")
                
                # 1. Create Parallel Chains for the Swarm
                chains = {}
                for role in swarm_roles:
                    model = model_overrides.get(role)
                    hist_msgs, llm = self.configure_persona(role, model_override=model, **kwargs.get(role, {}))
                    prompt = ChatPromptTemplate.from_messages(hist_msgs)
                    chains[role] = (prompt | llm | StrOutputParser())
                
                # 2. Run Swarm
                map_chain = RunnableParallel(**chains)
                swarm_results = await map_chain.ainvoke({})
                
                # 3. Format Output
                debate_transcript = "\n\n".join([f"--- {r.upper()} OUTPUT ---\n{content}" for r, content in swarm_results.items()])
                
                # 4. Run Judge
                print(f"     ➜ Synthesizing with {judge_role}...")
                
                model_j = model_overrides.get(judge_role)
                judge_msgs, llm_judge = self.configure_persona(judge_role, model_override=model_j, **kwargs.get(judge_role, {}))
                
                # Judge sees the swarm's collective output
                judge_msgs.append(HumanMessage(content=f"Collective Output from Team:\n{debate_transcript}\n\nTask: Synthesize and conclude."))
                
                prompt_judge = ChatPromptTemplate.from_messages(judge_msgs)
                chain_judge = prompt_judge | llm_judge | StrOutputParser()
                self.final_content = await chain_judge.ainvoke({})

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
        """Reads the full chat history and generates a summary."""
        print(f"\n📝 Generating Session Summary for {self.session_id}...")
        
        history = self.memory.get_session_history(self.session_id)
        if not history:
            print("   ⚠️ No history to summarize.")
            return

        transcript = "\n".join([f"{msg['sender']}: {msg['content']}" for msg in history])
        
        llm = ChatOllama(model="mistral")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert summarizer."),
            ("human", "Summarize the following conversation log:\n\n{input}")
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
                               session_mode: str = 'new', 
                               model_overrides: Dict[str, str] = None, 
                               **persona_kwargs):
        """
        Runs the full assembly line.
        """
        if not roles: roles = ["General"]
        if not outputs: outputs = []

        # 1. Ignition
        self.ignition(query, mode=session_mode)
        
        # 2. Ingest
        self.ingest_materials(query, source)
        
        # 3. Fabricate
        await self.fabricate_content(query, workflow, roles, model_overrides=model_overrides, kwargs=persona_kwargs)
        
        # 4. Forge
        await self.forge_artifacts(outputs)
        
        return self.final_content

# --- Verification Test Block ---
if __name__ == "__main__":
    async def run_test_mission():
        orchestrator = Assembly()
        
        print("\n🚀 STARTING MASSIVE PARALLEL MISSION")
        
        query = "Discuss the pros and cons of Space Colonization."
        
        # Scenario: 4-Way Debate + 1 Judge (5 Roles Total)
        # We can reuse roles or define new ones in DB.
        # Here we reuse available roles to simulate different perspectives.
        roles = [
            "Propaganda",   # The Advocate (Pro)
            "Critique",     # The Skeptic (Con)
            "Financial Advisor", # The Economist (Cost)
            "Story",        # The Visionary (Dream)
            "General"       # The Judge (Synthesis) - LAST ROLE is ALWAYS JUDGE
        ]
        
        # Override models to speed up the swarm (using smaller models for swarm, big for judge)
        overrides = {
            "Propaganda": "mistral",
            "Critique": "mistral",
            "Financial Advisor": "mistral",
            "Story": "mistral",
            "General": "llama3.2" # Judge
        }
        
        result = await orchestrator.execute_assembly(
            query=query,
            workflow='parallel',
            roles=roles,
            outputs=['word'],
            model_overrides=overrides
        )
        
        print("\n🏁 MISSION COMPLETE")
        print(f"Final Output:\n{result[:300]}...")

    asyncio.run(run_test_mission())
