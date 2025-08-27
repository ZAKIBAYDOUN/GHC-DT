"""
GHC Digital Twin LangGraph App
Main graph for processing queries and generating responses
"""

import os
from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END
import chromadb


class TwinState(TypedDict):
    """State for the Digital Twin conversation"""
    question: str
    context_docs: Optional[list]
    final_answer: str
    error: Optional[str]


class GHCDigitalTwin:
    """Digital Twin for Green Hill Canarias"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.vector_store_dir = os.getenv("VECTOR_STORE_DIR", "vector_store")
        self._setup_vector_store()
    
    def _setup_vector_store(self):
        """Initialize or connect to ChromaDB vector store"""
        try:
            # Ensure directory exists
            os.makedirs(self.vector_store_dir, exist_ok=True)
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(path=self.vector_store_dir)
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="ghc_documents",
                embedding_function=None  # We'll handle embeddings manually
            )
            
            # Initialize Langchain ChromaDB wrapper
            self.vector_store = Chroma(
                client=self.chroma_client,
                collection_name="ghc_documents",
                embedding_function=self.embeddings,
                persist_directory=self.vector_store_dir
            )
        except Exception as e:
            print(f"Error setting up vector store: {e}")
            self.vector_store = None
    
    def search_context(self, state: TwinState) -> TwinState:
        """Search for relevant context in vector store"""
        try:
            if not self.vector_store:
                state["context_docs"] = []
                state["error"] = "Vector store not available"
                return state
            
            # Search for relevant documents
            docs = self.vector_store.similarity_search(
                state["question"], 
                k=5
            )
            
            state["context_docs"] = [doc.page_content for doc in docs]
            return state
            
        except Exception as e:
            state["context_docs"] = []
            state["error"] = f"Search error: {str(e)}"
            return state
    
    def generate_answer(self, state: TwinState) -> TwinState:
        """Generate answer using LLM with context"""
        try:
            context = "\n".join(state.get("context_docs", []))
            
            if not context:
                # Provide basic information if no context available
                context = """
                Green Hill Canarias is a sustainable development project focused on environmental 
                conservation and renewable energy solutions in the Canary Islands.
                """
            
            prompt = f"""
            You are a digital twin assistant for Green Hill Canarias (GHC), a sustainable development 
            project in the Canary Islands. Based on the following context, answer the user's question 
            accurately and helpfully.
            
            Context:
            {context}
            
            Question: {state["question"]}
            
            Please provide a clear, informative answer based on the available information. If the 
            context doesn't contain enough information to fully answer the question, acknowledge 
            this and provide what relevant information you can.
            """
            
            response = self.llm.invoke(prompt)
            state["final_answer"] = response.content
            
        except Exception as e:
            state["final_answer"] = f"I apologize, but I encountered an error while processing your question: {str(e)}"
            state["error"] = str(e)
        
        return state
    
    def ingest_documents(self, texts: list[str]) -> dict:
        """Ingest text documents into the vector store"""
        try:
            if not self.vector_store:
                return {"status": "error", "message": "Vector store not available"}
            
            # Create documents
            documents = [Document(page_content=text) for text in texts]
            
            # Add to vector store
            self.vector_store.add_documents(documents)
            
            return {
                "status": "success", 
                "message": f"Successfully ingested {len(texts)} documents"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Ingestion error: {str(e)}"}


# Initialize the Digital Twin
digital_twin = GHCDigitalTwin()

# Create the LangGraph
def create_graph():
    """Create the LangGraph StateGraph"""
    graph = StateGraph(TwinState)
    
    # Add nodes
    graph.add_node("search", digital_twin.search_context)
    graph.add_node("generate", digital_twin.generate_answer)
    
    # Add edges
    graph.add_edge(START, "search")
    graph.add_edge("search", "generate")
    graph.add_edge("generate", END)
    
    return graph.compile()

# Create the app
app = create_graph()