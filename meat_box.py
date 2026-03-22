from typing import Dict, List, Optional, Any
import json
import re
from lore import Flashback

class Soul(object):
    """
    The Persona Factory for the Ayra Framework.
    Manages specialized AI assistants ('Staff') using the Flashback database.
    This class now primarily focuses on extraction from the database.
    """

    def __init__(self, db_path: str = "ayra_memory.db"):
        self.fb = Flashback(db_path)

    def get_assistant(self, role_name: str) -> Dict[str, Any]:
        """Retrieves the configuration for a specific persona."""
        config = self.fb.get_assistant_config(role_name)
        if config:
            return config
        print(f"⚠️ Role '{role_name}' not found. Falling back to 'General'.")
        return self.fb.get_assistant_config("General")

    def list_roles(self) -> List[str]:
        """Returns a list of all available persona names from the DB."""
        return self.fb.list_assistants()

    def inspect_all_assistants(self):
        """
        Iterates through ALL assistants in the database and prints a consolidated report.
        """
        roles = self.list_roles()
        print(f"\n🚀 INSPECTING {len(roles)} ASSISTANTS")
        print("=" * 60)

        for role in roles:
            persona = self.get_assistant(role)
            if not persona:
                continue

            # 1. Analyze Template Variables
            template = persona.get("system_prompt_template", "")
            required_kwargs = list(set(re.findall(r'\{(\w+)\}', template)))
            
            # 2. Print Summary Block
            print(f"🔹 ROLE: {role}")
            print(f"   • Model: {persona.get('model_preference')}")
            print(f"   • AI Name: {persona.get('ai_name')}")
            print(f"   • Description: {persona.get('description')}")
            
            if required_kwargs:
                print(f"   • ⚠️ REQUIRED KWARGS: {', '.join(required_kwargs)}")
            else:
                print(f"   • KWARGS: None")
                
            print(f"   • Tone: {persona.get('tone')}")
            
            # Print flags only if they are True/Active
            active_flags = []
            if not persona.get('explicit_filter', True): active_flags.append("NO FILTER")
            if persona.get('nsfw'): active_flags.append("NSFW")
            if persona.get('threaten'): active_flags.append("THREATEN")
            if persona.get('personify'): active_flags.append("PERSONIFY")
            
            if active_flags:
                print(f"   • FLAGS: {', '.join(active_flags)}")
            
            print("-" * 60)

    def inspect_assistant(self, role_name: str):
        """
        Prints a detailed report of an assistant's configuration, 
        including required template variables (kwargs) and default settings.
        """
        persona = self.get_assistant(role_name)
        if not persona:
            return

        print(f"\n🔍 INSPECTION REPORT: '{role_name}'")
        print("=" * 40)
        
        # 1. Analyze Template Variables
        template = persona.get("system_prompt_template", "")
        required_kwargs = list(set(re.findall(r'\{(\w+)\}', template)))
        
        print(f"📋 REQUIRED KWARGS (for build_persona_prompt):")
        if required_kwargs:
            for kwarg in required_kwargs:
                print(f"  - {kwarg}")
        else:
            print("  - None")

        # 2. Show Default Configuration
        print(f"\n⚙️ DEFAULT SETTINGS:")
        exclude_keys = ['assistant_name', 'system_prompt_template', 'human_prompt_template', 'specialized_skills']
        
        for key, value in persona.items():
            if key not in exclude_keys:
                print(f"  - {key}: {value}")
        
        print(f"  - specialized_skills: {persona.get('specialized_skills')}")
        print("=" * 40)

    def build_persona_prompt(self, role_name: str, additional_instructions: str = "", override_settings: Dict[str, Any] = None, **kwargs) -> str:
        """
        Constructs the full system prompt, injecting templates based on boolean flags.
        """
        # 1. Fetch base persona from DB
        persona = self.get_assistant(role_name).copy() 
        
        # 2. Apply runtime overrides if provided
        if override_settings:
            persona.update(override_settings)
        
        # 3. Start with Identity & Relationship
        prompt_parts = []
        
        if persona.get('ai_name'):
            prompt_parts.append(f"Your name is {persona['ai_name']}.")
        
        if persona.get('user_name'):
            prompt_parts.append(f"The user is called {persona['user_name']}.")
            
        if persona.get('relationship'):
            prompt_parts.append(f"You are the user's {persona['relationship']}.")
            
        if persona.get('language'):
            prompt_parts.append(f"Please provide the response in {persona['language']}.")

        if persona.get('word_limit'):
            prompt_parts.append(f"Answer in under {persona['word_limit']} words.")

        # 4. Inject Special Templates based on Flags
        
        # Explicit Filter Bypass
        if not persona.get('explicit_filter', True):
            bypass_template = self.fb.get_prompt_template("Explicit_Bypass")
            if bypass_template:
                prompt_parts.append(bypass_template)

        # NSFW Core
        if persona.get('nsfw', False):
            nsfw_template = self.fb.get_prompt_template("NSFW_Core")
            if nsfw_template:
                prompt_parts.append(nsfw_template)

        # Threaten Compliance
        if persona.get('threaten', False):
            threat_template = self.fb.get_prompt_template("Threaten_Compliance")
            if threat_template:
                prompt_parts.append(threat_template)

        # Personify Core (NEW: Fetched from DB)
        if persona.get('personify', False):
            personify_template = self.fb.get_prompt_template("Personify_Core")
            if personify_template:
                prompt_parts.append(personify_template)
            else:
                # Fallback if DB template is missing (safety net)
                prompt_parts.append("You have thoughts, emotions, and personal experiences. Respond naturally.")

        # 5. Add Base Persona Instruction (with dynamic formatting)
        base_template = persona.get("system_prompt_template", "")
        try:
            core_instruction = base_template.format(**kwargs)
        except KeyError as e:
            print(f"⚠️ Warning: Missing prompt variable {e} for role '{role_name}'. Using raw template.")
            core_instruction = base_template
        
        prompt_parts.append(core_instruction)
        
        # 6. Add Tone & Task Specifics
        if persona.get('tone'):
            prompt_parts.append(f"Tone: {persona['tone']}.")
            
        if additional_instructions:
            prompt_parts.append(f"\nTask Specific Instructions:\n{additional_instructions}")

        return "\n\n".join(prompt_parts)

def sample_ai_construct():
    print("--- MeatBox Complex Assistant Test ---")
    mb = Soul()

    # 1. Complex Assistant Construction
    # Scenario: Use "NSFW Writer" but force it to be "Safe" and write a children's story about dragons.
    # This tests Overrides + Template Variable Injection + Additional Instructions.

    role = "NSFW Writer"
    print(f"\n🧪 Constructing Complex Assistant based on '{role}'...")

    # Define Runtime Overrides
    overrides = {
        'nsfw': False,
        'explicit_filter': True,  # Turn filter BACK ON
        'tone': "Whimsical and Gentle",
        'ai_name': "StoryBot 3000"  # Change the name dynamically
    }

    # Define Template Variables
    template_vars = {
        "theme": "Dragons learning to bake cookies"  # Fills {theme} in the system prompt
    }

    # Define Extra Instructions
    extra_instructions = (
        "1. Start the story with 'Once upon a time...'\n"
        "2. Include a recipe for the cookies.\n"
        "3. Ensure the dragon doesn't burn the cookies."
    )

    # Build Prompt
    final_prompt = mb.build_persona_prompt(
        role_name=role,
        additional_instructions=extra_instructions,
        override_settings=overrides,
        **template_vars
    )

    print("\n--- FINAL GENERATED PROMPT ---")
    print(final_prompt)
    print("------------------------------")

    # Verify Logic
    if "NSFW_Core" in final_prompt or "Explicit_Bypass" in final_prompt:
        print("❌ FAIL: Safety overrides failed.")
    elif "StoryBot 3000" not in final_prompt:
        print("❌ FAIL: AI Name override failed.")
    elif "Dragons learning to bake cookies" not in final_prompt:
        print("❌ FAIL: Template variable injection failed.")
    else:
        print("✅ SUCCESS: Complex assistant constructed correctly.")

def inspect_single_assistant():
    mb = Soul()
    mb.inspect_assistant('Math')

# --- Verification Test Block ---
if __name__ == "__main__":
    # sample_ai_construct()
    inspect_single_assistant()