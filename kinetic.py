import asyncio
from blueprint import Assembly

async def generate_quiz_from_url(url: str, grade: int = 8, num_questions: int = 5):
    """
    Generates a comprehensive quiz based on the content of a provided URL.
    Uses the Ayra Assembly Line: Iris (Ingest) -> MeatBox (Teaching Persona) -> Aether (PDF).
    """
    orchestrator = Assembly()
    query = f"Create a comprehensive reading comprehension quiz based on the provided context."

    print(f"\n🧠 KINETIC: Generating Grade {grade} Quiz from {url}")
    
    # Define the Mission

    # Configure the 'Teaching' persona
    # The default Teaching prompt expects {grade} and {question_num}
    persona_kwargs = {
        "Teaching": {
            "grade": grade,
            "question_num": num_questions
        }
    }
    
    # Execute the Assembly Line
    result = await orchestrator.execute_assembly(
        query=query,
        source=url,  # Iris will scrape this
        workflow='once', # Single pass is enough for generation
        roles=["Teaching"],
        outputs=['word'], # Generate both for convenience
        session_mode='new',
        **persona_kwargs # Pass the persona specific settings
    )
    
    print("\n✅ KINETIC: Quiz Generation Complete.")
    print(f"Preview:\n{result}...")

def run_annika_comps():
    # Example: Generate a quiz about Quantum Computing
    target_url = "https://en.wikipedia.org/wiki/Quantum_computing"
    asyncio.run(generate_quiz_from_url(target_url, grade=8, num_questions=10))


if __name__ == "__main__":
    run_annika_comps()