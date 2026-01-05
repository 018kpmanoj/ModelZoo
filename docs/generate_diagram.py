"""
Generate PNG diagram from Mermaid markdown.
Run this script to create the system architecture PNG.

Requirements:
    pip install requests pillow

Usage:
    python generate_diagram.py
"""

import requests
import base64
import os

# Mermaid diagram code for the architecture
MERMAID_DIAGRAM = """
flowchart TB
    subgraph UserLayer["🧑‍💻 User Layer"]
        UI["Simple Chat UI<br/>React Frontend"]
        UserInput["User Query Input"]
        ModelSelector["Manual Model Selector"]
        ChatHistory["Chat History View"]
        FeedbackUI["Feedback Interface"]
    end

    subgraph APIGateway["🌐 API Gateway Layer"]
        FastAPI["FastAPI Backend<br/>REST API"]
        Auth["Authentication<br/>Service"]
        RateLimit["Rate Limiter"]
    end

    subgraph Orchestrator["🧠 Intelligent Orchestrator"]
        QueryAnalyzer["Query Complexity<br/>Analyzer"]
        ModelRouter["Model Router<br/>& Selector"]
        LoadBalancer["Load Balancer"]
        FallbackHandler["Fallback<br/>Handler"]
    end

    subgraph AzureModels["☁️ Azure OpenAI Models"]
        GPT4["GPT-4<br/>Complex Tasks"]
        GPT35["GPT-3.5 Turbo<br/>Simple Tasks"]
        GPT4Vision["GPT-4 Vision<br/>Multimodal"]
        Embeddings["Azure Embeddings<br/>text-embedding-ada-002"]
    end

    subgraph DataLayer["💾 Data Layer"]
        subgraph VectorDB["Azure AI Search"]
            VectorStore["Vector Store<br/>Embeddings"]
            SemanticSearch["Semantic<br/>Search"]
        end
        
        subgraph RelationalDB["Azure Cosmos DB"]
            ChatStore["Chat Sessions"]
            MessageStore["Messages"]
            FeedbackStore["User Feedback"]
            SuggestionsStore["Suggestions"]
        end
    end

    subgraph RAGPipeline["📚 RAG Pipeline"]
        DocProcessor["Document<br/>Processor"]
        Chunker["Text Chunker"]
        EmbeddingGen["Embedding<br/>Generator"]
        ContextRetriever["Context<br/>Retriever"]
    end

    subgraph ResponseFlow["📤 Response Pipeline"]
        ResponseGen["Response<br/>Generator"]
        StreamHandler["Stream<br/>Handler"]
        ErrorHandler["Error &<br/>Retry Handler"]
        ResponseLogger["Response<br/>Logger"]
    end

    %% User Layer Connections
    UI --> UserInput
    UI --> ModelSelector
    UI --> ChatHistory
    UI --> FeedbackUI

    %% API Gateway Connections
    UserInput --> FastAPI
    ModelSelector --> FastAPI
    FastAPI --> Auth
    FastAPI --> RateLimit

    %% Orchestrator Connections
    FastAPI --> QueryAnalyzer
    QueryAnalyzer --> ModelRouter
    ModelRouter --> LoadBalancer
    LoadBalancer --> FallbackHandler

    %% Azure Model Connections
    ModelRouter -->|Auto Select| GPT4
    ModelRouter -->|Auto Select| GPT35
    ModelRouter -->|Vision Tasks| GPT4Vision
    LoadBalancer --> GPT4
    LoadBalancer --> GPT35
    FallbackHandler --> GPT35

    %% RAG Pipeline Connections
    FastAPI --> DocProcessor
    DocProcessor --> Chunker
    Chunker --> EmbeddingGen
    EmbeddingGen --> Embeddings
    Embeddings --> VectorStore
    
    %% Context Retrieval
    QueryAnalyzer --> ContextRetriever
    ContextRetriever --> SemanticSearch
    SemanticSearch --> VectorStore

    %% Response Pipeline Connections
    GPT4 --> ResponseGen
    GPT35 --> ResponseGen
    GPT4Vision --> ResponseGen
    ContextRetriever --> ResponseGen
    ResponseGen --> StreamHandler
    StreamHandler --> ErrorHandler
    ErrorHandler --> ResponseLogger

    %% Data Storage Connections
    ResponseLogger --> ChatStore
    ResponseLogger --> MessageStore
    FeedbackUI --> FeedbackStore
    FeedbackStore --> SuggestionsStore

    %% Response to UI
    StreamHandler --> UI
    ChatStore --> ChatHistory

    %% Styling
    classDef userLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#01579b
    classDef apiLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#4a148c
    classDef orchestrator fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#e65100
    classDef azureModels fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#1b5e20
    classDef dataLayer fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#880e4f
    classDef ragPipeline fill:#e0f2f1,stroke:#004d40,stroke-width:2px,color:#004d40
    classDef responseFlow fill:#fff8e1,stroke:#ff6f00,stroke-width:2px,color:#ff6f00

    class UI,UserInput,ModelSelector,ChatHistory,FeedbackUI userLayer
    class FastAPI,Auth,RateLimit apiLayer
    class QueryAnalyzer,ModelRouter,LoadBalancer,FallbackHandler orchestrator
    class GPT4,GPT35,GPT4Vision,Embeddings azureModels
    class VectorStore,SemanticSearch,ChatStore,MessageStore,FeedbackStore,SuggestionsStore dataLayer
    class DocProcessor,Chunker,EmbeddingGen,ContextRetriever ragPipeline
    class ResponseGen,StreamHandler,ErrorHandler,ResponseLogger responseFlow
"""

def generate_diagram_mermaid_ink(diagram_code: str, output_path: str):
    """Generate PNG using mermaid.ink service."""
    
    # Base64 encode the diagram
    diagram_bytes = diagram_code.encode('utf-8')
    diagram_b64 = base64.urlsafe_b64encode(diagram_bytes).decode('utf-8')
    
    # Use mermaid.ink API
    url = f"https://mermaid.ink/img/{diagram_b64}?type=png&bgColor=0f172a&theme=dark"
    
    print(f"Generating diagram...")
    print(f"URL length: {len(url)}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Diagram saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error generating diagram: {e}")
        return False


def generate_simple_diagram():
    """Generate a simpler diagram for better rendering."""
    
    simple_diagram = """
flowchart TB
    subgraph UI["🧑‍💻 User Interface"]
        Chat["Chat UI"]
        History["History"]
        Feedback["Feedback"]
    end
    
    subgraph Backend["🔧 FastAPI Backend"]
        API["REST API"]
        Orch["Orchestrator"]
    end
    
    subgraph Azure["☁️ Azure OpenAI"]
        GPT4["GPT-4"]
        GPT35["GPT-3.5"]
        Embed["Embeddings"]
    end
    
    subgraph Data["💾 Data Storage"]
        DB["Cosmos DB"]
        Vector["AI Search"]
    end
    
    Chat --> API
    API --> Orch
    Orch --> GPT4
    Orch --> GPT35
    Orch --> Embed
    Embed --> Vector
    API --> DB
    DB --> History
    Feedback --> DB
    
    style UI fill:#e1f5fe,stroke:#01579b
    style Backend fill:#f3e5f5,stroke:#4a148c
    style Azure fill:#e8f5e9,stroke:#1b5e20
    style Data fill:#fce4ec,stroke:#880e4f
"""
    return simple_diagram


if __name__ == "__main__":
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "modelzoo_architecture.png")
    
    # Try simple diagram first (more likely to render correctly)
    simple = generate_simple_diagram()
    
    if not generate_diagram_mermaid_ink(simple, output_path):
        print("\nTrying full diagram...")
        generate_diagram_mermaid_ink(MERMAID_DIAGRAM, output_path)
    
    print("\n📋 Alternative: Copy the Mermaid code from system_design.md")
    print("   and paste into https://mermaid.live to generate PNG manually.")

