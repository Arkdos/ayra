import asyncio
import time
from blueprint import Assembly

async def generate_quiz_from_url(url: str, query = None, session_id: str = None):
    """
    Generates a comprehensive quiz based on the content of a provided URL.
    Wipes previous RAG memory to ensure focus on the new URL.
    """
    orchestrator = Assembly()
    
    print(f"\n🧠 KINETIC: Generating Quiz from {url}")
    
    # 1. Clear Memory (The Fix)
    # Ensure we aren't mixing up previous topics (like Quantum Computing vs BTS)
    orchestrator.iris.clear_memory()
    
    if session_id:
        print(f"   ↪️ Resuming Session: {session_id}")
    
    # Define the Mission
    if not query:
        query = f"Create a comprehensive reading comprehension multiple choice quiz with provided context."

    # Determine mode
    mode = session_id if session_id else 'new'
    
    # Measure Time - Start
    start_time = time.perf_counter()
    
    # Execute the Assembly Line
    result = await orchestrator.execute_assembly(
        query=query,
        source=url,
        workflow='sequential',
        roles=["Comp Scraper", "Comp Questioner", "Comp Auditor"],
        outputs=['word'],
        session_mode=mode,
    )
    
    # Measure Time - End
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    # Calculate Stats
    # Rough estimation: 1 word ≈ 1.33 tokens, or chars / 4
    # Using character count / 4 is a standard rough heuristic for tokens
    estimated_tokens = len(result) / 4
    tps = estimated_tokens / duration if duration > 0 else 0
    
    print("\n✅ KINETIC: Quiz Generation Complete.")
    print(f"   ⏱️ Duration: {duration:.2f} seconds")
    print(f"   📊 Estimated TPS: {tps:.2f} tokens/sec")
    print(f"Preview:\n{result}...")
    return orchestrator.session_id

async def run_advanced_override_test():
    """
    EXAMPLE: Demonstrating Model Overrides, Dynamic Kwargs, and Persona Settings.
    This shows how to hijack the assembly line for highly specific needs.
    """
    print("\n🧪 KINETIC: Starting Advanced Override Test...")
    orchestrator = Assembly()
    orchestrator.iris.clear_memory()
    
    # Scenario: Use the 'Story' persona, but force it to be a Technical Writer
    # using a specific model, ignoring its database defaults.
    
    query = "Explain the concept of Recursion."
    
    # 1. Define Model Overrides (Role -> Model)
    # Force 'Story' role to use 'codellama' instead of its default (mistral)
    model_map = {
        "Story": "llama3.2"
    }
    
    # 2. Define Dynamic Kwargs (Template Variables)
    # The 'Story' prompt expects {theme} and {grade}. We provide them here.
    # We also pass 'override_settings' to change the persona's metadata on the fly.
    persona_config = {
        "Story": {
            "theme": "Cyberpunk Noir",   # Filling template var
            "grade": 16,                 # Filling template var
            "override_settings": {       # Special key for MeatBox overrides
                "tone": "Gritty and Technical",
                "ai_name": "Neo-Scribe",
                "temperature": 0.9       # High creativity
            }
        }
    }
    
    # Measure Time - Start
    start_time = time.perf_counter()
    
    # Execute
    result = await orchestrator.execute_assembly(
        query=query,
        workflow='once',
        roles=["Story"],
        outputs=[], # No files, just text
        model_overrides=model_map,
        **persona_config # Unpack our complex config
    )
    
    # Measure Time - End
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    # Calculate Stats
    estimated_tokens = len(result) / 4
    tps = estimated_tokens / duration if duration > 0 else 0
    
    print("\n✅ Advanced Test Complete.")
    print(f"   ⏱️ Duration: {duration:.2f} seconds")
    print(f"   📊 Estimated TPS: {tps:.2f} tokens/sec")
    print(f"Result (from {model_map['Story']}):\n{result}...")

async def chatbot(query, mode = None):
    """
    Generates a comprehensive quiz based on the content of a provided URL.
    Can resume an existing session if session_id is provided.
    """
    orchestrator = Assembly()
    orchestrator.iris.clear_memory()
    if not mode:
        mode = 'new'

    # Measure Time - Start
    start_time = time.perf_counter()

    # Execute the Assembly Line
    result = await orchestrator.execute_assembly(
        query=query,
        workflow='once',
        roles=["Companion"],
        outputs=['voice'],
        model_overrides={"Companion": "llama3.2"},
        session_mode=mode,  # Pass the ID or 'new'
    )

    # Measure Time - End
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    # Calculate Stats
    estimated_tokens = len(result) / 4
    tps = estimated_tokens / duration if duration > 0 else 0

    print("\n✅ KINETIC: Response Generation Complete.")
    print(f"   ⏱️ Duration: {duration:.2f} seconds")
    print(f"   📊 Estimated TPS: {tps:.2f} tokens/sec")
    print(f"Preview:\n{result}")
    return orchestrator.session_id  # Return the session ID for chaining

def run_chatbot():
    mode = '8857b46a-a3bf-462a-a3fd-33483426fa30'
    query = ("Good night")
    asyncio.run(chatbot(query, mode))

def taylormade():
    asyncio.run(run_advanced_override_test())

def run_quiz():
    query = 'Generate 7 multiple choice question from the context from the url.'
    asyncio.run(generate_quiz_from_url(url="https://en.wikipedia.org/wiki/BTS", query=query))

if __name__ == "__main__":
    run_quiz()