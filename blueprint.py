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
        self.default_temp = 0.7
        
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
            
        temperature = persona_conf.get('temperature', self.default_temp)
        if temperature is None: temperature = self.default_temp
        
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
        
        print(f"     Creating LLM: {model_name} (Temp: {temperature}) for role {role_name}")
        llm = ChatOllama(model=model_name, temperature=temperature)
        
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
        The Core Engine. Runs the LLM chains based on the workflow type.
        """
        print(f"\n⚙️ Station 3: Fabricate Content (Workflow: {workflow})")
        
        if not roles: roles = ["General"]
        if not kwargs: kwargs = {}
        if not model_overrides: model_overrides = {}

        try:
            if workflow == 'once':
                role = roles[0]
                model = model_overrides.get(role)
                history_messages, llm = self.configure_persona(role, model_override=model, **kwargs.get(role, {}))
                
                print(f"   ↳ Running Single Chain with Role: {role}")
                
                prompt = ChatPromptTemplate.from_messages(history_messages)
                chain = prompt | llm | StrOutputParser()
                self.final_content = await chain.ainvoke({})

            elif workflow == 'sequential':
                print(f"   ↳ Running Sequential Chain with {len(roles)} Steps: {roles}")
                
                chain_history = ""
                
                for i, role in enumerate(roles):
                    print(f"     ➜ Step {i+1}/{len(roles)}: {role}")
                    
                    model = model_overrides.get(role)
                    history_messages, llm = self.configure_persona(role, model_override=model, **kwargs.get(role, {}))
                    
                    if i > 0:
                        context_msg = f"Output from previous agent ({roles[i-1]}):\n{chain_history}\n\nTask: Continue, refine, or critique based on this."
                        history_messages.append(HumanMessage(content=context_msg))
                    
                    prompt = ChatPromptTemplate.from_messages(history_messages)
                    chain = prompt | llm | StrOutputParser()
                    
                    response = await chain.ainvoke({})
                    chain_history = response 
                
                self.final_content = chain_history

            elif workflow == 'parallel':
                if len(roles) < 2:
                    print("⚠️ Parallel workflow requires at least 2 roles.")
                    return

                judge_role = roles[-1]
                swarm_roles = roles[:-1]
                
                print(f"   ↳ Running Parallel Swarm with {len(swarm_roles)} Agents: {swarm_roles}")
                print(f"   ↳ Synthesizer/Judge: {judge_role}")
                
                chains = {}
                for role in swarm_roles:
                    model = model_overrides.get(role)
                    hist_msgs, llm = self.configure_persona(role, model_override=model, **kwargs.get(role, {}))
                    prompt = ChatPromptTemplate.from_messages(hist_msgs)
                    chains[role] = (prompt | llm | StrOutputParser())
                
                map_chain = RunnableParallel(**chains)
                swarm_results = await map_chain.ainvoke({})
                
                debate_transcript = "\n\n".join([f"--- {r.upper()} OUTPUT ---\n{content}" for r, content in swarm_results.items()])
                
                print(f"     ➜ Synthesizing with {judge_role}...")
                
                model_j = model_overrides.get(judge_role)
                judge_msgs, llm_judge = self.configure_persona(judge_role, model_override=model_j, **kwargs.get(judge_role, {}))
                
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

    # --- Station 5: Quality Assurance (Critique) ---
    async def critique_response(self, original_query: str) -> Tuple[bool, str]:
        """
        Assesses the quality of the generated response using the 'Critique' persona.
        Returns (is_passed, critique_feedback).
        """
        print(f"\n⚖️ Station 5: Quality Assurance (Critique)")
        
        # Configure the 'Critique' persona
        # We pass the required kwargs directly
        critique_kwargs = {
            "init_original_query": original_query,
            "source_context": self.raw_context,
            "init_response": self.final_content
        }
        
        try:
            # We don't use memory for the critique to keep it objective and focused only on the current turn
            # But the requirement was to use configure_persona which includes memory.
            # For a pure audit, we might want to temporarily clear session_id context, 
            # but let's stick to the standard flow first.
            messages, llm = self.configure_persona("Critique", **critique_kwargs)
            
            prompt = ChatPromptTemplate.from_messages(messages)
            chain = prompt | llm | StrOutputParser()
            
            critique_result = await chain.ainvoke({})
            print(f"   ↳ Critique Result: {critique_result[:50]}...")
            
            # Simple parsing: check for PASS or FAIL at the start
            is_passed = critique_result.strip().upper().startswith("PASS")
            
            # Log the critique turn
            self.memory.log_turn(
                self.session_id,
                sender="AI",
                content=critique_result,
                ai_assistant="Kyle (QA)",
                model_used=self.active_persona_config.get('model_preference')
            )
            
            return is_passed, critique_result
            
        except Exception as e:
            print(f"❌ Critique Failed: {e}")
            return True, "" # Fail open to avoid infinite loops if critique crashes

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
                               critique: bool = False,
                               **persona_kwargs):
        """
        Runs the full assembly line with optional Quality Assurance retry loop.
        """
        if not roles: roles = ["General"]
        if not outputs: outputs = []

        # 1. Ignition
        self.ignition(query, mode=session_mode)
        
        # 2. Ingest
        self.ingest_materials(query, source)
        
        # --- FABRICATION LOOP (with Critique) ---
        max_retries = 2
        attempt = 0
        current_query = query
        
        while attempt <= max_retries:
            attempt += 1
            if attempt > 1:
                print(f"\n🔄 RE-FABRICATION ATTEMPT {attempt}/{max_retries+1}")

            # 3. Fabricate
            await self.fabricate_content(current_query, workflow, roles, model_overrides=model_overrides, kwargs=persona_kwargs)
            
            # 4. Critique (if enabled)
            if critique:
                is_passed, feedback = await self.critique_response(query)
                if is_passed:
                    print("   ✨ Quality Check PASSED.")
                    break
                else:
                    print(f"   ⚠️ Quality Check FAILED. Retrying...")
                    # Update query for next attempt to include the feedback
                    current_query = f"{query}\n\nNOTE: Previous response failed quality check. Please address these issues:\n{feedback}"
            else:
                break # Exit loop if critique is disabled

        # 5. Forge
        await self.forge_artifacts(outputs)
        
        return self.final_content

# --- Verification Test Block ---
if __name__ == "__main__":
    async def run_test_mission():
        orchestrator = Assembly()
        
        print("\n🚀 STARTING MISSION WITH CRITIQUE")
        
        query = "Explain what is gravity in physics."
        
        # Run with Critique enabled
        result = await orchestrator.execute_assembly(
            query=query,
            workflow='once',
            roles=["General"],
            outputs=[],
            critique=True # Enable QA
        )
        
        print("\n🏁 MISSION COMPLETE")
        print(f"Final Output:\n{result}...")

    asyncio.run(run_test_mission())
