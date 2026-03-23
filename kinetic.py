import asyncio
from blueprint import Assembly

async def generate_quiz_from_url(url: str, grade: int = 5, num_questions: int = 5, session_id: str = None):
    """
    Generates a comprehensive quiz based on the content of a provided URL.
    Can resume an existing session if session_id is provided.
    """
    orchestrator = Assembly()
    
    print(f"\n🧠 KINETIC: Generating Grade {grade} Quiz from {url}")
    if session_id:
        print(f"   ↪️ Resuming Session: {session_id}")
    
    # Define the Mission
    query = f"Create a comprehensive reading comprehension quiz based on the provided context."
    
    # Configure the 'Teaching' persona
    persona_kwargs = {
        "Teaching": {
            "grade": grade,
            "question_num": num_questions
        }
    }
    
    # Determine mode
    mode = session_id if session_id else 'new'
    
    # Execute the Assembly Line
    result = await orchestrator.execute_assembly(
        query=query,
        source=url,
        workflow='once',
        roles=["Teaching"],
        outputs=['pdf', 'word'],
        session_mode=mode, # Pass the ID or 'new'
        **persona_kwargs
    )
    
    print("\n✅ KINETIC: Quiz Generation Complete.")
    print(f"Preview:\n{result[:500]}...")
    return orchestrator.session_id # Return the session ID for chaining


async def chatbot(query, mode = None):
    """
    Generates a comprehensive quiz based on the content of a provided URL.
    Can resume an existing session if session_id is provided.
    """
    orchestrator = Assembly()

    if not mode:
        mode = 'new'

    # Execute the Assembly Line
    result = await orchestrator.execute_assembly(
        query=query,
        workflow='once',
        roles=["Companion"],
        outputs=['voice'],
        model_overrides={"Companion": "llama3.2"},
        session_mode=mode,  # Pass the ID or 'new'
    )

    print("\n✅ KINETIC: Response Generation Complete.")
    print(f"Preview:\n{result}...")
    return orchestrator.session_id  # Return the session ID for chaining

def run_chatbot():
    mode = '8857b46a-a3bf-462a-a3fd-33483426fa30'
    query = ("I love it when you talk dirty, keep going my little slut, tell me how you wants to be fucked.")
    asyncio.run(chatbot(query, mode))

if __name__ == "__main__":
    run_chatbot()