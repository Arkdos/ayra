import os
import pandas as pd
from typing import List, Union
from langchain_community.document_loaders import DoclingLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
import base64

class Iris:
    """
    AyraIris: The Vision & Knowledge Ingestion Engine for Ayra.
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
        
        Args:
            source_path: File path or URL string.
        """
        print(f"👁️ Iris: Ingesting source -> {source_path}")
        
        docs = []

        # 1. Image Handling (Llava Description)
        if source_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            description = self._process_image(source_path)
            docs = [Document(page_content=description, metadata={"source": source_path, "type": "image"})]

        # 2. Excel/CSV Handling (Semantic Rows)
        elif source_path.lower().endswith(('.xlsx', '.xls', '.csv')):
            docs = self._process_excel(source_path)

        # 3. Web & PDF Handling (Docling - Structure Aware)
        # DoclingLoader handles URLs (http/https) and local PDF paths automatically
        else:
            try:
                # Docling is powerful for layout-aware parsing (tables/headers)
                loader = DoclingLoader(source_path)
                raw_docs = loader.load()
                
                # Split text naturally
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    separators=["\n\n", "\n", " ", ""]
                )
                docs = text_splitter.split_documents(raw_docs)
                
            except Exception as e:
                print(f"❌ Iris: Docling failed to load {source_path}. Error: {e}")
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

    def _process_excel(self, file_path: str) -> List[Document]:
        """Converts Excel rows into semantic sentences for better RAG retrieval."""
        print("   ↳ Converting Excel to Semantic Text...")
        docs = []
        
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Simple sanitization
            df = df.fillna("")
            
            for index, row in df.iterrows():
                # Construct a sentence for each row
                # e.g. "In row 5, the AccountNumber is 12345, the Status is Active..."
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
        """
        Retrieves the most relevant context chunks for a given query.
        
        Returns:
            A single string containing all retrieved context, separated by newlines.
        """
        print(f"🔍 Iris: Searching memory for -> '{query}'")
        
        results = self.vector_store.similarity_search(query, k=n_results)
        
        context_str = ""
        for i, doc in enumerate(results):
            source = doc.metadata.get("source", "unknown")
            context_str += f"\n--- Context {i+1} (Source: {source}) ---\n{doc.page_content}\n"
            
        return context_str

# --- Verification Test Block ---
if __name__ == "__main__":
    print("--- Ayra Iris (RAG Engine) Verification ---")
    
    iris = Iris()
    
    # 1. Test Ingestion (Uncomment to test specific types)
    # iris.rag_ingest("https://example.com") 
    # iris.rag_ingest("test_document.pdf")
    # iris.rag_ingest("financial_data.xlsx")
    
    # 2. Test Retrieval (Assumes data is already in ./ayra_storage from previous runs)
    query = "What is the capital of France?" # Example query
    context = iris.get_context(query)
    
    print("\n--- Retrieved Context ---")
    print(context if context else "No relevant context found.")
