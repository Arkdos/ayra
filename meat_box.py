from typing import Dict, List, Optional, Any
import json
import re
from lore import Flashback

class Soul:
    """
    The Persona Factory for the Ayra Framework.
    Manages specialized AI assistants ('Staff') using the Flashback database (via Lore).
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
        """Iterates through ALL assistants in the database and prints a consolidated report."""
        roles = self.list_roles()
        print(f"\n🚀 INSPECTING {len(roles)} ASSISTANTS")
        print("=" * 60)

        for role in roles:
            persona = self.get_assistant(role)
            if not persona: continue

            template = persona.get("system_prompt_template", "")
            required_kwargs = list(set(re.findall(r'\{(\w+)\}', template)))
            
            print(f"🔹 ROLE: {role}")
            print(f"   • Model: {persona.get('model_preference')}")
            print(f"   • AI Name: {persona.get('ai_name')}")
            
            if required_kwargs:
                print(f"   • ⚠️ REQUIRED KWARGS: {', '.join(required_kwargs)}")
            else:
                print(f"   • KWARGS: None")
            
            # Show stored defaults if they exist
            defaults = persona.get('default_kwargs')
            if defaults:
                print(f"   • DEFAULTS: {defaults}")
                
            print("-" * 60)

    def inspect_assistant(self, role_name: str):
        """Prints a detailed report of an assistant's configuration."""
        persona = self.get_assistant(role_name)
        if not persona: return

        print(f"\n🔍 INSPECTION REPORT: '{role_name}'")
        print("=" * 40)
        
        template = persona.get("system_prompt_template", "")
        required_kwargs = list(set(re.findall(r'\{(\w+)\}', template)))
        
        print(f"📋 REQUIRED KWARGS (for build_persona_prompt):")
        if required_kwargs:
            for kwarg in required_kwargs:
                print(f"  - {kwarg}")
        else:
            print("  - None")

        print(f"\n⚙️ DEFAULT SETTINGS:")
        exclude_keys = ['assistant_name', 'system_prompt_template', 'human_prompt_template', 'specialized_skills']
        for key, value in persona.items():
            if key not in exclude_keys:
                print(f"  - {key}: {value}")
        print("=" * 40)

    def build_persona_prompt(self, role_name: str, additional_instructions: str = "", override_settings: Dict[str, Any] = None, **kwargs) -> str:
        """
        Constructs the full system prompt.
        Merges dynamic kwargs with stored default_kwargs to prevent formatting errors.
        """
        # 1. Fetch base persona from DB
        persona = self.get_assistant(role_name).copy() 
        
        # 2. Apply runtime overrides if provided
        if override_settings:
            persona.update(override_settings)
        
        # 3. Merge Defaults for Template Variables
        # Start with stored defaults (if any)
        template_vars = persona.get('default_kwargs', {}).copy()
        if not isinstance(template_vars, dict):
            template_vars = {} # Safety check
            
        # Update with runtime kwargs (passed arguments override defaults)
        template_vars.update(kwargs)

        # 4. Start with Identity & Relationship
        prompt_parts = []
        
        if persona.get('ai_name'):
            prompt_parts.append(f"Your name is {persona['ai_name']}.")
        if persona.get('user_name'):
            prompt_parts.append(f"The user is called {persona['user_name']}.")
        if persona.get('relationship'):
            prompt_parts.append(f"You are the user's {persona['relationship']}.")
        if persona.get('personify'):
            prompt_parts.append("You have thoughts, emotions, and personal experiences. Respond naturally, as a person would.")
        if persona.get('language'):
            prompt_parts.append(f"Please provide the response in {persona['language']}.")
        if persona.get('word_limit'):
            prompt_parts.append(f"Answer in under {persona['word_limit']} words.")

        # 5. Inject Special Templates based on Flags
        if not persona.get('explicit_filter', True):
            bypass = self.fb.get_prompt_template("Explicit_Bypass")
            if bypass: prompt_parts.append(bypass)

        if persona.get('nsfw', False):
            nsfw_core = self.fb.get_prompt_template("NSFW_Core")
            if nsfw_core: prompt_parts.append(nsfw_core)

        if persona.get('threaten', False):
            threat = self.fb.get_prompt_template("Threaten_Compliance")
            if threat: prompt_parts.append(threat)

        if persona.get('personify', False):
            personify_core = self.fb.get_prompt_template("Personify_Core")
            if personify_core: 
                prompt_parts.append(personify_core)

        # 6. Add Base Persona Instruction (with safe formatting)
        base_template = persona.get("system_prompt_template", "")
        try:
            # We use the merged template_vars dictionary here
            core_instruction = base_template.format(**template_vars)
        except KeyError as e:
            # This should happen less often now thanks to default_kwargs
            print(f"⚠️ Warning: Missing prompt variable {e} for role '{role_name}'. Using raw template.")
            core_instruction = base_template
        
        prompt_parts.append(core_instruction)
        
        # 7. Add Tone & Task Specifics
        if persona.get('tone'):
            prompt_parts.append(f"Tone: {persona['tone']}.")
            
        if additional_instructions:
            prompt_parts.append(f"\nTask Specific Instructions:\n{additional_instructions}")

        return "\n\n".join(prompt_parts)

# --- Verification Test Block ---
if __name__ == "__main__":
    soul = Soul()
    
    # Test: Translator with NO kwargs passed, relying on DB defaults
    print("\n--- Testing Defaults Merge ---")
    prompt = soul.build_persona_prompt("Translator")
    print(f"Generated Prompt Preview:\n{prompt[:200]}...")
