import sqlite3
import uuid
import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

class Flashback(object):
    """
    Manages session-based chat history, user identity, and AI assistant configurations.
    """
    
    DB_PATH = "ayra_memory.db"

    def __init__(self, db_path: str = None):
        if db_path:
            self.DB_PATH = db_path
        self._initialize_db()

    def _get_connection(self):
        return sqlite3.connect(self.DB_PATH)

    def _initialize_db(self):
        """Creates the necessary tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. User Profile Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    role TEXT,
                    company TEXT,
                    location TEXT,
                    interests TEXT
                )
            """)
            
            # 2. Chat History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    msg_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    parent_msg_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sender TEXT, 
                    ai_assistant TEXT,
                    model_used TEXT,
                    content TEXT
                )
            """)
            
            # 3. Chat Summary Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_summary (
                    session_id TEXT PRIMARY KEY,
                    chat_summary TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. AI Assistants Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_assistants (
                    assistant_name TEXT PRIMARY KEY,
                    ai_name TEXT,
                    model_preference TEXT,
                    system_prompt_template TEXT,
                    human_prompt_template TEXT,
                    description TEXT,
                    tone TEXT,
                    specialized_skills TEXT,
                    language TEXT,
                    explicit_filter BOOLEAN,
                    nsfw BOOLEAN,
                    personify BOOLEAN,
                    user_name TEXT,
                    relationship TEXT,
                    word_limit INTEGER,
                    threaten BOOLEAN
                )
            """)
            
            # 5. Prompt Templates Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    template_name TEXT PRIMARY KEY,
                    template_content TEXT,
                    description TEXT
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON chat_history(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parent_msg_id ON chat_history(parent_msg_id)")
            
            conn.commit()

    # --- Session Management ---

    def new_session(self) -> str:
        """Generates and returns a new session ID."""
        return str(uuid.uuid4())

    def get_latest_session_id(self) -> Optional[str]:
        """Retrieves the ID of the most recently active session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id FROM chat_history ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else None

    def get_latest_msg_id(self, session_id: str) -> Optional[str]:
        """Retrieves the msg_id of the most recent message in a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT msg_id FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1", (session_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    # --- Message Logging ---

    def log_turn(self, session_id: str, sender: str, content: str, ai_assistant: str = None, model_used: str = None) -> str:
        """Logs a new message turn."""
        parent_msg_id = self.get_latest_msg_id(session_id)
        new_msg_id = str(uuid.uuid4())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history (msg_id, session_id, parent_msg_id, sender, ai_assistant, model_used, content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (new_msg_id, session_id, parent_msg_id, sender, ai_assistant, model_used, content))
            conn.commit()
            
        return new_msg_id

    # --- Summary Management ---

    def update_chat_summary(self, session_id: str, summary_text: str):
        """Updates the chat_summary table for a given session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_summary (session_id, chat_summary, timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(session_id) DO UPDATE SET
                    chat_summary=excluded.chat_summary,
                    timestamp=CURRENT_TIMESTAMP
            """, (session_id, summary_text))
            conn.commit()

    def get_chat_summary(self, session_id: str) -> Optional[Dict]:
        """Retrieves the latest summary for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chat_summary WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "session_id": row[0], 
                    "chat_summary": row[1], 
                    "timestamp": row[2]
                }
            return None

    # --- Retrieval ---

    def get_session_history(self, session_id: str) -> List[Dict]:
        """Returns all messages for a session, ordered chronologically."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT msg_id, parent_msg_id, timestamp, sender, ai_assistant, model_used, content FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
            rows = cursor.fetchall()
            history = []
            for row in rows:
                history.append({
                    "msg_id": row[0], "parent_msg_id": row[1], "timestamp": row[2],
                    "sender": row[3], "ai_assistant": row[4], "model_used": row[5], "content": row[6]
                })
            return history

    def assemble_prompt_context(self, session_id: str, user_id: str, limit: int = 10) -> str:
        """Constructs a context string for the LLM."""
        identity = self.get_identity_context(user_id=user_id)
        profile_str = "User Profile: Not Found\n---\n"
        if identity:
            profile_str = (
                f"User Profile:\n"
                f"Name: {identity.get('name', 'Unknown')}\n"
                f"Role: {identity.get('role', 'N/A')}\n"
                f"Interests: {identity.get('interests', 'N/A')}\n"
                f"---\n"
            )

        summary_data = self.get_chat_summary(session_id)
        summary_str = ""
        if summary_data:
            summary_str = f"Previous Conversation Summary: {summary_data['chat_summary']}\n---\n"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sender, content, ai_assistant FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?", (session_id, limit))
            rows = cursor.fetchall()
            
            chronological_msgs = reversed(rows)
            history_str = "Recent Conversation History:\n"
            for sender, content, assistant in chronological_msgs:
                display_sender = "AI"
                if sender != 'AI':
                    display_sender = identity.get('name', f"User({sender[:8]})") if identity else f"User({sender[:8]})"
                
                if sender == 'AI' and assistant:
                     display_sender = f"AI ({assistant})"

                history_str += f"{display_sender}: {content}\n"

        return f"{profile_str}{summary_str}{history_str}"

    # --- User Profile Management ---

    def set_user_profile(self, user_id: str, name: str, role: str, company: str, location: str, interests: str):
        """Creates or updates a user profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_profile (user_id, name, role, company, location, interests)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name=excluded.name, role=excluded.role, company=excluded.company,
                    location=excluded.location, interests=excluded.interests
            """, (user_id, name, role, company, location, interests))
            conn.commit()

    def get_identity_context(self, user_id: str) -> Optional[Dict]:
        """Retrieves a user profile by user_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {"user_id": row[0], "name": row[1], "role": row[2], "company": row[3], "location": row[4], "interests": row[5]}
            return None

    # --- AI Assistant Management ---

    def upsert_assistant(self, **kwargs):
        """
        Inserts or updates an AI assistant configuration using a dictionary of arguments.
        Dynamic kwargs allow flexibility for CSV importing.
        """
        # Ensure mandatory PK exists
        if 'assistant_name' not in kwargs:
            print("❌ upsert_assistant failed: 'assistant_name' is required.")
            return

        # Prepare specialized_skills (convert list to JSON string if needed)
        if 'specialized_skills' in kwargs and isinstance(kwargs['specialized_skills'], list):
            kwargs['specialized_skills'] = json.dumps(kwargs['specialized_skills'])
        
        # Define all columns and their default values (None)
        columns = [
            'assistant_name', 'ai_name', 'model_preference', 'system_prompt_template', 
            'human_prompt_template', 'description', 'tone', 'specialized_skills',
            'language', 'explicit_filter', 'nsfw', 'personify', 'user_name', 
            'relationship', 'word_limit', 'threaten'
        ]
        
        # Construct the query dynamically based on provided keys (upserting all supported cols)
        values = [kwargs.get(col) for col in columns]
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join(["?"] * len(columns))
            # Construct the UPDATE SET clause
            update_clause = ",".join([f"{col}=excluded.{col}" for col in columns if col != 'assistant_name'])
            
            query = f"""
                INSERT INTO ai_assistants ({",".join(columns)})
                VALUES ({placeholders})
                ON CONFLICT(assistant_name) DO UPDATE SET
                    {update_clause}
            """
            cursor.execute(query, values)
            conn.commit()

    def get_assistant_config(self, assistant_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves assistant config as a dictionary."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_assistants WHERE assistant_name = ?", (assistant_name,))
            row = cursor.fetchone()
            
            if row:
                # Get column names from cursor description
                col_names = [description[0] for description in cursor.description]
                result = dict(zip(col_names, row))
                
                # Parse JSON fields and Booleans
                if result.get('specialized_skills'):
                    try:
                        result['specialized_skills'] = json.loads(result['specialized_skills'])
                    except json.JSONDecodeError:
                        result['specialized_skills'] = []
                
                # Convert 1/0 integers to Booleans for flag columns
                bool_cols = ['explicit_filter', 'nsfw', 'personify', 'threaten']
                for col in bool_cols:
                    if col in result:
                        result[col] = bool(result[col])
                        
                return result
            return None

    def list_assistants(self) -> List[str]:
        """Returns a list of all available assistant names."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT assistant_name FROM ai_assistants")
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    # --- Prompt Template Management ---

    def upsert_prompt_template(self, template_name: str, template_content: str, description: str = ""):
        """Inserts or updates a reusable prompt template."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prompt_templates (template_name, template_content, description)
                VALUES (?, ?, ?)
                ON CONFLICT(template_name) DO UPDATE SET
                    template_content=excluded.template_content,
                    description=excluded.description
            """, (template_name, template_content, description))
            conn.commit()

    def get_prompt_template(self, template_name: str) -> Optional[str]:
        """Retrieves the content of a prompt template by name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT template_content FROM prompt_templates WHERE template_name = ?", (template_name,))
            row = cursor.fetchone()
            return row[0] if row else None

    # --- CSV Import / Export Utilities ---

    def export_table_to_csv(self, table_name: str, filepath: str):
        """
        Exports the entire contents of a table to a CSV file.
        """
        print(f"📦 Exporting table '{table_name}' to {filepath}...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                if not rows:
                    print(f"   ⚠️ Table '{table_name}' is empty. Creating empty CSV with headers.")
                    # Get headers anyway
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    headers = [info[1] for info in cursor.fetchall()]
                else:
                    headers = [description[0] for description in cursor.description]

                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
                    writer.writerows(rows)
            print(f"   ✅ Export successful.")
        except Exception as e:
            print(f"   ❌ Export failed: {e}")

    def import_csv_to_table(self, table_name: str, filepath: str, pk_column: str):
        """
        Reads a CSV file and upserts its data into the specified table.
        Assumes the CSV headers match the table column names.
        
        Args:
            table_name: The target table (e.g., 'ai_assistants').
            filepath: Path to the source CSV file.
            pk_column: The Primary Key column name used for conflict resolution (e.g., 'assistant_name').
        """
        print(f"📥 Importing from {filepath} into table '{table_name}'...")
        if not os.path.exists(filepath):
            print(f"   ❌ File not found: {filepath}")
            return

        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows_to_insert = list(reader)
                
                if not rows_to_insert:
                    print("   ⚠️ CSV file is empty.")
                    return

                headers = reader.fieldnames
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Prepare the upsert query dynamically
                    columns = ",".join(headers)
                    placeholders = ",".join(["?"] * len(headers))
                    update_clause = ",".join([f"{col}=excluded.{col}" for col in headers if col != pk_column])
                    
                    query = f"""
                        INSERT INTO {table_name} ({columns})
                        VALUES ({placeholders})
                        ON CONFLICT({pk_column}) DO UPDATE SET
                            {update_clause}
                    """
                    
                    count = 0
                    for row in rows_to_insert:
                        # Ensure values match the order of headers
                        values = [row[col] for col in headers]
                        cursor.execute(query, values)
                        count += 1
                    
                    conn.commit()
            print(f"   ✅ Import successful. {count} rows processed.")
        except Exception as e:
            print(f"   ❌ Import failed: {e}")

# --- Verification Test Block ---
if __name__ == "__main__":
    print("--- Flashback CSV Utilities Verification ---")
    fb = Flashback("ayra_memory.db")
    
    # Test Export
    fb.export_table_to_csv("ai_assistants", "ai_assistants.csv")
    fb.export_table_to_csv("prompt_templates", "prompt_templates.csv")
