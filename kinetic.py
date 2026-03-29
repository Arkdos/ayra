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

async def run_mortgage_test():
    """
    Scenario: User asks a natural language financial question.
    The system should activate the mortgage tool, calculate the result,
    and have Kyle (QA) verify the accuracy of the final advice.
    """
    print("\n🏠 KINETIC: Starting Mortgage Calculation Scenario...")
    orchestrator = Assembly()
    orchestrator.iris.clear_memory()
    
    query = "I want to buy a house for $500,000 with a 20% down payment. If I get a 30-year mortgage at 6.5% interest, what will my monthly payment be?"
    
    # Measure Time - Start
    start_time = time.perf_counter()
    
    # Execute the Assembly Line
    # workflow='once' is fine here as the tool handles the heavy lifting
    # critique=True enables Kyle to double check the math/logic
    result = await orchestrator.execute_assembly(
        query=query,
        workflow='once',
        roles=["Financial Advisor"],
        outputs=['pdf'], # Forge a PDF for the record
        use_tools=True,
        critique=True
    )
    
    # Measure Time - End
    duration = time.perf_counter() - start_time
    tps = (len(result) / 4) / duration if duration > 0 else 0
    
    print("\n✅ Mortgage Scenario Complete.")
    print(f"   ⏱️ Duration: {duration:.2f} seconds")
    print(f"   📊 Estimated TPS: {tps:.2f} tokens/sec")
    print(f"\nFinal AI Response:\n{result}")

async def run_themed_story_gen(url: str, theme: str = "Sci-Fi Noir"):
    """
    Generates a story inspired by the content of a URL.
    Demonstrates RAG ingestion + Persona-driven fabrication.
    """
    print(f"\n📖 KINETIC: Generating {theme} story based on {url}")
    orchestrator = Assembly()
    orchestrator.iris.clear_memory()
    
    start_time = time.perf_counter()
    
    # Execute
    result = await orchestrator.execute_assembly(
        query=f"Write a short story in the style of {theme} that incorporates themes from the provided context. use names that were in the url",
        source=url,
        workflow='once',
        roles=["Comp Scraper", 'NSFW Writer'],
        outputs=['word'],
        critique= True,
        theme=theme # Passes to Story persona's default_kwargs
    )
    
    duration = time.perf_counter() - start_time
    print(f"\n✅ Story Generation Complete. ({duration:.2f}s)")
    print(f"Preview:\n{result}...")

def run_chatbot():
    mode = '8857b46a-a3bf-462a-a3fd-33483426fa30'
    query = ("Good night")
    asyncio.run(chatbot(query, mode))

def taylormade():
    asyncio.run(run_advanced_override_test())

def run_quiz():
    query = 'Generate 7 multiple choice question from the main concept and theme from the provided context from the url.'
    asyncio.run(generate_quiz_from_url(url="https://en.wikipedia.org/wiki/List_of_public_corporations_by_market_capitalization", query=query))

def run_mortgage():
    asyncio.run(run_mortgage_test())

def run_story():
    url = ""
    asyncio.run(run_themed_story_gen(url, theme="BDSM"))

if __name__ == "__main__":
    run_quiz()
