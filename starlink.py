import asyncio
import os
import pandas as pd
from docx import Document as DocxDocument
from fpdf import FPDF
import edge_tts
from nicegui import ui


class Aether:
    """
    Aether: The Transmission & Archival Layer of Ayra.
    Forges Word, Excel, and PDF artifacts.
    Default Voice: en-US-AvaNeural (Bright, modern, and natural).
    """

    def __init__(self, base_dir="./ayra_output"):
        self.base_dir = os.path.abspath(base_dir)
        self.folders = {
            "docs": os.path.join(self.base_dir, "documents"),
            "reports": os.path.join(self.base_dir, "reports"),
            "audio": os.path.join(self.base_dir, "briefings")
        }

        for folder in self.folders.values():
            os.makedirs(folder, exist_ok=True)

        # Neural Voice Catalog
        self.voices = {
            "ava": "en-US-AvaNeural",  # Bright/Modern (DEFAULT)
            "clara": "en-CA-ClaraNeural",  # Toronto Professional
            "sonia": "en-GB-SoniaNeural",  # Authoritative Announcer
            "libby": "en-GB-LibbyNeural",  # Warm Storyteller
            "emma": "en-US-EmmaNeural",  # Gentle/Low-pitch
            "natasha": "en-AU-NatashaNeural"  # Sophisticated/Smooth
        }

        print(f"📡 Aether: Mission Control established at -> {self.base_dir}")

    # --- The Forge: Document Generation ---

    def forge_spreadsheet(self, data, filename="market_analysis"):
        path = os.path.join(self.folders["reports"], f"{filename}.xlsx")
        pd.DataFrame(data).to_excel(path, index=False)
        print(f"📊 Aether: Spreadsheet forged -> {path}")
        return path

    def forge_word_doc(self, title, content, filename="study_sheet"):
        doc = DocxDocument()
        doc.add_heading(title, 0)
        doc.add_paragraph(content)
        path = os.path.join(self.folders["docs"], f"{filename}.docx")
        doc.save(path)
        print(f"📝 Aether: Word Document (.docx) forged -> {path}")
        return path

    def forge_pdf(self, title, content, filename="ayra_report"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        pdf.set_font("helvetica", size=12)
        pdf.multi_cell(0, 10, content)
        path = os.path.join(self.folders["reports"], f"{filename}.pdf")
        pdf.output(path)
        print(f"📄 Aether: PDF forged -> {path}")
        return path

    # --- The Signal: Voice Briefing ---

    async def broadcast(self, text, voice="ava", filename="announcement"):
        """
        Broadcasts voice signal using the Neural Edge-TTS engine.
        :param text: The text to speak.
        :param voice: Key from self.voices (defaults to 'ava').
        :param filename: Name of the archived audio file.
        :return: Path to the generated audio file.
        """
        path = os.path.join(self.folders["audio"], f"{filename}.mp3")

        # Get selected voice or fall back to Ava
        voice_id = self.voices.get(voice.lower(), self.voices["ava"])
        print(f"🔊 Aether: Transmitting via {voice_id}...")

        try:
            communicate = edge_tts.Communicate(text, voice_id)
            await communicate.save(path)
            print(f"✅ Aether: Signal broadcasted to -> {path}")
            return path
        except Exception as e:
            print(f"❌ Aether: Transmission failed. Check your internet connection or library version. Error: {e}")
            return None

    def forge_gui(self, mission_name: str, content: str, paths: list):
        """Spins up a local web UI to review the assembly line output."""

        @ui.page('/mission_report')
        def report():
            with ui.column().classes('w-full items-center p-8'):
                ui.label(f'MISSION: {mission_name}').classes('text-h4 font-bold')
                ui.markdown(content).classes('border p-4 rounded bg-gray-100 w-full')

                ui.label('Generated Artifacts').classes('text-h6 mt-4')
                for path in paths:
                    ui.link(os.path.basename(path), f'file://{path}')

                ui.button('Close Dashboard', on_click=lambda: ui.run_javascript('window.close()'))

        # Run in a non-blocking way or as a final step
        ui.run(title="Ayra Mission Control", port=8080, reload=False, show=False)
        print(f"🖥️ Aether: Dashboard live at http://localhost:8080/mission_report")

# --- Verification ---
if __name__ == "__main__":
    hub = Aether()


    async def run_mission():
        # Test 1: Default Ava for a personal greeting
        await hub.broadcast("Hello Fredrick. This is Ayra, using your preferred neural voice.", voice="ava")

        # Test 2: Using Libby for educational content
        await hub.broadcast("Here are your reading comprehension questions for today.", voice="libby")


    asyncio.run(run_mission())