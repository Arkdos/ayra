import asyncio
import os
import warnings
import json
import re
from typing import List, Dict, Any, Optional, Tuple

# --- Core Dependencies ---
from lore import Flashback 
from meat_box import Soul
from iris_out import Iris
from starlink import Aether
from clutch import Torque 

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
    The JIT Assembly Line: Orchestrates Memory, Personas, Ingestion, Tools, and Output.
    Optimized for Apple Silicon (M-series) via async execution.

    Logical Station Re-mapping:
    •Station 1: Ignition (Session Setup)
    •Station 2: Ingest Materials (RAG)
    •Station 3: Tool Activation (Ollama Tool Selection)
    •Station 4: Fabricate Content (LLM Generation)
    •Station 5: Quality Assurance (Critique)
    •Station 6: Forge Artifacts (File/TTS Generation)

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
        self.tool_result: str = "" 
        self.final_content: str = ""
        self.active_persona_config: Dict = {}

    # --- Station 1: Ignition ---
    def ignition(self, user_query: str, user_id: str = "default_user", mode: str = 'new') -> str:
        """Sets up the session and logs the user turn."""
        print(f"\n🔌 Station 1: Ignition (Mode: {mode})")
        self.active_user_id = user_id
        
        if mode == 'continue':
            self.session_id = self.memory.get_latest_session_id() or self.memory.new_session()
        elif mode != 'new' and mode is not None:
            self.session_id = mode
        else:
            self.session_id = self.memory.new_session()

        self.memory.log_turn(self.session_id, self.active_user_id, user_query, ai_assistant=None)
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

    # --- Station 3: Tool Activation ---
    async def activate_tools(self, query: str) -> Optional[str]:
        """
        Determines if a tool from Torque is required and executes it.
        """
        print(f"\n🛠️ Station 3: Tool Activation")
        manifest = Torque.get_tool_manifest()
        
        selector_prompt = f"""
        You are a Tool Dispatcher. Analyze the user query and the available tools below.
        
        TOOLS:
        {json.dumps(manifest, indent=2)}
        
        CRITICAL: Respond ONLY with a JSON object.
        Format: {{"tool_name": "name", "parameters": {{...}}}}
        If no tool is relevant, respond with {{"tool_name": "NONE"}}.
        
        USER QUERY: {query}
        """
        
        llm = ChatOllama(model="llama3.2", temperature=0)
        response = await llm.ainvoke(selector_prompt)
        content = response.content.strip()
        
        if "NONE" in content.upper():
            print("   ↳ No relevant tool found.")
            return None
            
        try:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if not match:
                print("   ↳ Tool content does not match expected format.")
                print('      ↳' + content)
                return None
                
            call_info = json.loads(match.group(0))
            
            if "tool_name" in call_info and isinstance(call_info["tool_name"], str):
                tool_name = call_info['tool_name']
                params = call_info.get('parameters', {})
            else:
                tool_name = list(call_info.keys())[0]
                params = call_info[tool_name]
            
            print(f"   ↳ Triggering Tool: {tool_name}")
            result = Torque.execute(tool_name, **params)
            self.tool_result = result
            return result
        except Exception as e:
            print(f"   ❌ Tool Activation Error: {e}")
            return None

    # --- Internal Factory: Persona Config ---
    def configure_persona(self, role_name: str, model_override: str = None, **kwargs) -> Tuple[List[Any], ChatOllama]:
        """Fetches persona and prepares the full message history."""
        persona_conf = self.soul.get_assistant(role_name)
        model_name = model_override or persona_conf.get('model_preference', self.default_model)
        temperature = persona_conf.get('temperature', self.default_temp) or self.default_temp
        
        context_instruction = f"\n\n--- SOURCE CONTEXT (RAG) ---\n{self.raw_context}"
        if self.tool_result:
            context_instruction += f"\n\n--- TOOL CALCULATION OUTPUT ---\n{self.tool_result}"
        
        system_text = self.soul.build_persona_prompt(role_name, additional_instructions=context_instruction, **kwargs)
        messages = [SystemMessage(content=system_text)]
        
        if self.session_id:
            history = self.memory.get_session_history(self.session_id)
            for msg in history:
                if msg['content']: 
                    messages.append(AIMessage(content=msg['content']) if msg['sender'] == 'AI' else HumanMessage(content=msg['content']))
        
        llm = ChatOllama(model=model_name, temperature=temperature)
        self.active_persona_config = persona_conf
        return messages, llm

    # --- Station 4: Fabricate Content ---
    async def fabricate_content(self, 
                                scenario: str, 
                                workflow: str = 'once', 
                                roles: List[str] = None,
                                model_overrides: Dict[str, str] = None,
                                kwargs: Dict[str, Any] = None):
        """Dynamic workflows: supports any number of roles."""
        print(f"\n⚙️ Station 4: Fabricate Content (Workflow: {workflow})")
        if not roles: roles = ["General"]
        if not kwargs: kwargs = {}
        if not model_overrides: model_overrides = {}

        try:
            if workflow == 'once':
                role = roles[0]
                history_messages, llm = self.configure_persona(role, model_override=model_overrides.get(role), **kwargs.get(role, {}))
                chain = ChatPromptTemplate.from_messages(history_messages) | llm | StrOutputParser()
                self.final_content = await chain.ainvoke({})

            elif workflow == 'sequential':
                print(f"   ↳ Sequential Chain with {len(roles)} Steps: {roles}")
                chain_history = ""
                for i, role in enumerate(roles):
                    print(f"     ➜ Step {i+1}: {role}")
                    history_messages, llm = self.configure_persona(role, model_override=model_overrides.get(role), **kwargs.get(role, {}))
                    if i > 0:
                        history_messages.append(HumanMessage(content=f"Previous Result:\n{chain_history}"))
                    chain = ChatPromptTemplate.from_messages(history_messages) | llm | StrOutputParser()
                    chain_history = await chain.ainvoke({})
                self.final_content = chain_history

            elif workflow == 'parallel':
                if len(roles) < 2: return
                judge_role = roles[-1]
                swarm_roles = roles[:-1]
                print(f"   ↳ Parallel Swarm: {swarm_roles} -> Judge: {judge_role}")
                
                chains = {}
                for role in swarm_roles:
                    hist_msgs, llm = self.configure_persona(role, model_override=model_overrides.get(role), **kwargs.get(role, {}))
                    chains[role] = (ChatPromptTemplate.from_messages(hist_msgs) | llm | StrOutputParser())
                
                swarm_results = await RunnableParallel(**chains).ainvoke({})
                debate_transcript = "\n\n".join([f"--- {r.upper()} --- \n{content}" for r, content in swarm_results.items()])
                
                judge_msgs, llm_judge = self.configure_persona(judge_role, model_override=model_overrides.get(judge_role), **kwargs.get(judge_role, {}))
                judge_msgs.append(HumanMessage(content=f"Arguments from Team:\n{debate_transcript}\n\nTask: Synthesize."))
                self.final_content = await (ChatPromptTemplate.from_messages(judge_msgs) | llm_judge | StrOutputParser()).ainvoke({})

            if self.final_content:
                print(f"   ✅ Fabrication Complete ({len(self.final_content)} chars).")
                self.memory.log_turn(self.session_id, "AI", self.final_content, 
                                    ai_assistant=self.active_persona_config.get('ai_name'), 
                                    model_used=self.active_persona_config.get('model_preference'))
        except Exception as e:
            print(f"❌ Fabrication Failed: {e}")

    # --- Station 5: Quality Assurance (Critique) ---
    async def critique_response(self, original_query: str) -> Tuple[bool, str]:
        """Assesses the quality of the generated response."""
        print(f"\n⚖️ Station 5: Quality Assurance (Critique)")
        critique_kwargs = {
            "init_original_query": original_query,
            "source_context": self.raw_context + "\n" + self.tool_result,
            "init_response": self.final_content,
        }
        print(critique_kwargs)
        try:
            messages, llm = self.configure_persona("Critique", **critique_kwargs)
            result = await (ChatPromptTemplate.from_messages(messages) | llm | StrOutputParser()).ainvoke({})
            print(f"   ↳ Critique Result: {result}...")
            self.memory.log_turn(self.session_id, "AI", result, ai_assistant="Kyle (QA)")
            return result.strip().upper().startswith("PASS"), result
        except Exception as e:
            print(f"❌ Critique Failed: {e}")
            return True, ""

    # --- Station 6: Forge Artifacts ---
    async def forge_artifacts(self, outputs: List[str]):
        """Parallel production of files."""
        if not self.final_content: return
        print(f"\n🔨 Station 6: Forge Artifacts {outputs}")
        tasks = []
        if 'word' in outputs: tasks.append(self.aether.forge_word(self.final_content, f"mission_{self.session_id[:8]}.docx"))
        if 'pdf' in outputs: tasks.append(self.aether.forge_pdf(self.final_content, f"mission_{self.session_id[:8]}.pdf"))
        if tasks: await asyncio.gather(*tasks)

    # --- Master Controller ---
    async def execute_assembly(self, query: str, source: str = None, workflow: str = 'once', 
                               roles: List[str] = None, outputs: List[str] = None, session_mode: str = 'new', 
                               model_overrides: Dict[str, str] = None, use_tools: bool = True, 
                               critique: bool = False, **persona_kwargs):
        """The Master Controller executing the assembly line order."""
        self.ignition(query, mode=session_mode)
        self.ingest_materials(query, source)
        
        self.tool_result = "" 
        if use_tools: await self.activate_tools(query)
        
        max_retries = 2
        attempt = 0
        current_query = query
        while attempt <= max_retries:
            attempt += 1
            if attempt > 1: print(f"\n🔄 RE-FABRICATION ATTEMPT {attempt}/{max_retries+1}")
            await self.fabricate_content(current_query, workflow, roles, model_overrides, persona_kwargs)
            if critique and self.final_content:
                is_passed, feedback = await self.critique_response(query)
                if is_passed: break
                current_query = f"{query}\n\nNOTE: Your previous attempt failed Quality Assurance. Fix these:\n{feedback}"
            else: break

        await self.forge_artifacts(outputs or [])
        return self.final_content
