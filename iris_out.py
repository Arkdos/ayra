import os
import pandas as pd
import base64
import sys
from typing import List, Union


# --- LangChain Imports (Defensive Loading) ---
try:
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings, ChatOllama
    from langchain_core.documents import Document
    from langchain_core.messages import HumanMessage
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
except ImportError as e:
    print(f"❌ CRITICAL ERROR: Missing or incompatible LangChain packages.\n   Error: {e}")
    print("   Please run: pip install -U langchain-core langchain-ollama langchain-community langchain-chroma langchain-text-splitters")
    sys.exit(1)

# Try importing Docling, fall back if missing/broken
try:
    from langchain_docling import DoclingLoader
    HAS_DOCLING = True
except ImportError:
    print("⚠️ DoclingLoader not found or incompatible. Will fall back to standard loaders.")
    HAS_DOCLING = False

class Iris:
    """
    Iris: The Vision & Knowledge Ingestion Engine for Ayra.
    Handles RAG (Retrieval-Augmented Generation) from Web, PDF, Excel, and Images.
    Uses 'nomic-embed-text' for embeddings and persists data to './ayra_storage'.
    """

    def __init__(self, persist_directory: str = "./ayra_storage"):
        self.persist_directory = persist_directory
        self.embedding_model = OllamaEmbeddings(model="nomic-embed-text")
        
        # Initialize Vector Store (Persistent)
        self.vector_store = Chroma(
            collection_name="ayra_knowledge",
            embedding_function=self.embedding_model,
            persist_directory=self.persist_directory
        )

    def rag_ingest(self, source_path: str):
        """
        Intelligently ingests data from a source (URL, PDF, Excel, Image).
        """
        print(f"👁️ Iris: Ingesting source -> {source_path}")
        
        docs = []

        # 1. Image Handling
        if source_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            description = self._process_image(source_path)
            docs = [Document(page_content=description, metadata={"source": source_path, "type": "image"})]

        # 2. Excel/CSV Handling
        elif source_path.lower().endswith(('.xlsx', '.xls', '.csv')):
            docs = self._process_excel(source_path)

        # 3. URL & PDF Handling
        else:
            try:
                # Use Docling if available, otherwise standard loaders
                if HAS_DOCLING:
                    print("   ↳ Loading with Docling (Structure Aware)...")
                    loader = DoclingLoader(source_path)
                else:
                    if source_path.startswith(('http://', 'https://')):
                        print("   ↳ Loading with WebBaseLoader (Fallback)...")
                        loader = WebBaseLoader(source_path)
                    else:
                        print("   ↳ Loading with PyPDFLoader (Fallback)...")
                        loader = PyPDFLoader(source_path)

                raw_docs = loader.load()
                
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    separators=["\n\n", "\n", " ", ""]
                )
                docs = text_splitter.split_documents(raw_docs)
                
            except Exception as e:
                print(f"❌ Iris: Loader failed for {source_path}. Error: {e}")
                return

        if docs:
            print(f"   ↳ Storing {len(docs)} chunks into Ayra Memory...")
            self.vector_store.add_documents(docs)
            print("✅ Iris: Ingestion Complete.")
        else:
            print("⚠️ Iris: No content extracted.")

    def _process_image(self, image_path: str) -> str:
        """Uses Llava to generate a text description of an image."""
        print("   ↳ Analyzing Image with Llava...")
        
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")

            llava = ChatOllama(model="llava")
            message = HumanMessage(
                content=[
                    {"type": "text", "text": "Describe this image in detail. Extract any text visible."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                ]
            )
            response = llava.invoke([message])
            return f"Image Description for {os.path.basename(image_path)}:\n{response.content}"
        except Exception as e:
            print(f"❌ Iris: Vision analysis failed. {e}")
            return "Image analysis failed."

    def _process_excel(self, file_path: str) -> List[Document]:
        """Converts Excel rows into semantic sentences for better RAG retrieval."""
        print("   ↳ Converting Excel to Semantic Text...")
        docs = []
        
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            df = df.fillna("")
            
            for index, row in df.iterrows():
                row_text = f"Record {index}: "
                row_parts = []
                for col in df.columns:
                    if row[col] != "":
                        row_parts.append(f"{col} is '{row[col]}'")
                
                row_text += ", ".join(row_parts) + "."
                
                docs.append(Document(
                    page_content=row_text, 
                    metadata={"source": file_path, "row": index}
                ))
                
        except Exception as e:
            print(f"❌ Iris: Excel processing error: {e}")
            
        return docs

    def get_context(self, query: str, n_results: int = 5) -> str:
        """Retrieves the most relevant context chunks for a given query."""
        print(f"🔍 Iris: Searching memory for -> '{query}'")
        
        try:
            results = self.vector_store.similarity_search(query, k=n_results)
            context_str = ""
            for i, doc in enumerate(results):
                source = doc.metadata.get("source", "unknown")
                context_str += f"\n--- Context {i+1} (Source: {source}) ---\n{doc.page_content}\n"
            return context_str
        except Exception as e:
            print(f"❌ Iris: Retrieval failed. {e}")
            return ""

# --- Verification Test Block ---
if __name__ == "__main__":

    # Check imports first
    print(f"ℹ️ Docling Enabled: {HAS_DOCLING}")

    iris = Iris(persist_directory="./test_ayra_storage")

    # --- Test 1: URL ---
    print("\n[TEST 1] Ingesting Web URL...")
    iris.rag_ingest("https://en.wikipedia.org/wiki/Artificial_intelligence")

    # --- Test 2: CSV ---
    print("\n[TEST 2] Ingesting CSV...")
    iris.rag_ingest("prompt_templates.csv")

    # --- Test 3: PDF (Real) ---
    print("\n[TEST 3] Ingesting Real PDF...")
    pdf_path = "/Users/arkdos/Downloads/_OceanofPDF.com_The_Book_of_Money_How_to_feel_good_or_better_about_your_finances_-_Monzo.pdf"
    if os.path.exists(pdf_path):
        iris.rag_ingest(pdf_path)
    else:
        print(f"❌ PDF not found at: {pdf_path}")

    # --- Test 4: Image ---
    print("\n[TEST 4] Ingesting Image...")
    iris.rag_ingest("wallpaperflare.com_wallpaper.jpg")

    # --- Test 5: Retrieval ---
    print("\n[TEST 5] Verifying Retrieval...")
    context = iris.get_context("How can I feel better about my finances?", n_results=1)
    if context:
        print(f"   ✅ Context Found:\n{context.strip()[:200]}...")
    else:
        print("   ❌ No Context Found.")

    print("\n✅ IRIS SYSTEM TEST COMPLETE.")
