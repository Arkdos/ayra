from lore import Flashback
import os
import sys

def launch_rocket(fb):
    """
    Standard Workflow: Reads 'ai_assistants.csv' and 'prompt_templates.csv' 
    and updates the database with any changes found in the files.
    """
    print("\n🚀 Launching Persona Rocket (CSV -> DB Sync)...")
    
    # 1. Sync Assistants
    assistants_csv = "ai_assistants.csv"
    if os.path.exists(assistants_csv):
        # This will dynamically read headers (including 'temperature' and 'default_kwargs')
        fb.import_csv_to_table("ai_assistants", assistants_csv, pk_column="assistant_name")
    else:
        print(f"   ⚠️ '{assistants_csv}' not found. Cannot sync assistants.")

    # 2. Sync Templates
    templates_csv = "prompt_templates.csv"
    if os.path.exists(templates_csv):
        fb.import_csv_to_table("prompt_templates", templates_csv, pk_column="template_name")
    else:
        print(f"   ⚠️ '{templates_csv}' not found. Cannot sync templates.")
        
    print("   ✅ Sync Complete.")

def export_rocket(fb):
    """
    Backup Workflow: Dumps the current state of the database tables 
    back into the CSV files. Useful for initializing or backing up data.
    """
    print("\n📦 Exporting DB -> CSV...")
    fb.export_table_to_csv("ai_assistants", "ai_assistants.csv")
    fb.export_table_to_csv("prompt_templates", "prompt_templates.csv")
    print("   ✅ Export Complete.")

if __name__ == "__main__":
    db_path = "ayra_memory.db"
    fb_instance = Flashback(db_path)
    
    # Simple CLI: 'export' to dump DB, otherwise default to Sync (Import)
    if len(sys.argv) > 1 and sys.argv[1].lower() == "export":
        export_rocket(fb_instance)
    else:
        # Check if CSVs exist before trying to sync
        if not os.path.exists("ai_assistants.csv"):
            print("❌ Error: 'ai_assistants.csv' not found. Please place your spreadsheet in this folder.")
        else:
            launch_rocket(fb_instance)
            # Optional: Export back to ensure formatting consistency?
            # export_rocket(fb_instance)
