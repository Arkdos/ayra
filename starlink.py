import os
import asyncio
import pandas as pd
import openpyxl
from docx import Document
from fpdf import FPDF
from email.message import EmailMessage
from dotenv import load_dotenv
import edge_tts

# Load environment variables for email credentials
load_dotenv()

class Aether:
    """
    Aether (Starlink): The Output & Communication Hub for the Ayra Framework.
    Forges documents (Excel, Word, PDF) and handles transmissions (Email, Voice).
    """

    def __init__(self, output_dir: str = "mission_artifacts"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Email Config
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")

    def _get_path(self, filename: str) -> str:
        return os.path.join(self.output_dir, filename)

    # --- Forge: Document Generation ---

    async def forge_excel(self, data: list[dict], filename: str = "report.xlsx") -> str:
        """Creates an Excel spreadsheet from a list of dictionaries."""
        path = self._get_path(filename)
        print(f"🔨 Aether: Forging Excel -> {path}")
        
        try:
            # Running synchronous pandas code in a separate thread to stay non-blocking
            await asyncio.to_thread(self._forge_excel_sync, data, path)
            return path
        except Exception as e:
            print(f"❌ Aether Excel Error: {e}")
            return ""

    def _forge_excel_sync(self, data, path):
        df = pd.DataFrame(data)
        df.to_excel(path, index=False, engine='openpyxl')

    async def forge_word(self, content: str, filename: str = "brief.docx") -> str:
        """Creates a Word document."""
        path = self._get_path(filename)
        print(f"🔨 Aether: Forging Word Doc -> {path}")
        
        try:
            await asyncio.to_thread(self._forge_word_sync, content, path)
            return path
        except Exception as e:
            print(f"❌ Aether Word Error: {e}")
            return ""

    def _forge_word_sync(self, content, path):
        doc = Document()
        doc.add_heading('Ayra Mission Report', 0)
        doc.add_paragraph(content)
        doc.save(path)

    async def forge_pdf(self, content: str, filename: str = "dossier.pdf") -> str:
        """Creates a PDF document."""
        path = self._get_path(filename)
        print(f"🔨 Aether: Forging PDF -> {path}")
        
        try:
            await asyncio.to_thread(self._forge_pdf_sync, content, path)
            return path
        except Exception as e:
            print(f"❌ Aether PDF Error: {e}")
            return ""

    def _forge_pdf_sync(self, content, path):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        # FPDF doesn't handle utf-8 characters well by default, sanitizing lightly
        safe_content = content.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=safe_content)
        pdf.output(path)

    # --- Signals: Communication ---

    async def broadcast(self, text: str, voice: str = "en-US-AriaNeural", save_file: str = None):
        """Uses Edge-TTS to speak the text or save to file."""
        print(f"📡 Aether: Broadcasting Voice Signal...")
        try:
            communicate = edge_tts.Communicate(text, voice)
            if save_file:
                path = self._get_path(save_file)
                await communicate.save(path)
                print(f"   ✅ Audio saved to {path}")
            else:
                # To play audio directly requires a player like mpv or mpg123 installed
                # For this backend class, saving is the safest default, but we can try to stream/play
                # logic if needed. Here we just generate.
                pass 
        except Exception as e:
            print(f"❌ Aether Voice Error: {e}")

    async def send_uplink(self, recipient: str, subject: str, body: str, attachment_path: str = None):
        """Sends an email via SMTP."""
        if not self.smtp_user or not self.smtp_pass:
            print("⚠️ Aether: SMTP credentials missing. Uplink aborted.")
            return

        print(f"📡 Aether: Sending Uplink to {recipient}...")
        message = EmailMessage()
        message["From"] = self.smtp_user
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        if attachment_path and os.path.exists(attachment_path):
            # Guess MIME type or just use application/octet-stream
            import mimetypes
            ctype, encoding = mimetypes.guess_type(attachment_path)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)

            with open(attachment_path, 'rb') as f:
                file_data = f.read()
                message.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=os.path.basename(attachment_path))

        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_pass,
                use_tls=False,
                start_tls=True
            )
            print("   ✅ Uplink Successful.")
        except Exception as e:
            print(f"❌ Aether Uplink Failed: {e}")

# --- Verification ---
if __name__ == "__main__":
    async def test_aether():
        aether = Aether()
        
        # Test Doc Forge
        await aether.forge_word("This is a confidential mission report.", "test_doc.docx")
        await aether.forge_pdf("Subject: Project Omega\nStatus: Classified", "test_doc.pdf")
        
        data = [{"ID": 1, "Status": "Active"}, {"ID": 2, "Status": "Dormant"}]
        await aether.forge_excel(data, "test_sheet.xlsx")
        
        # Test Voice
        await aether.broadcast("System Online. Aether is listening.", save_file="test_voice.mp3")

    asyncio.run(test_aether())
