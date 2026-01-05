# ModelZoo - System Design Documentation

## Overview
ModelZoo is a multi-LLM chat system that enables users to interact with multiple Azure OpenAI models through a unified interface. The system features intelligent model orchestration, chat history management, and comprehensive feedback mechanisms.

## High-Level Design (HLD)

```mermaid
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
    classDef userLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef apiLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef orchestrator fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef azureModels fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef dataLayer fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef ragPipeline fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    classDef responseFlow fill:#fff8e1,stroke:#ff6f00,stroke-width:2px

    class UI,UserInput,ModelSelector,ChatHistory,FeedbackUI userLayer
    class FastAPI,Auth,RateLimit apiLayer
    class QueryAnalyzer,ModelRouter,LoadBalancer,FallbackHandler orchestrator
    class GPT4,GPT35,GPT4Vision,Embeddings azureModels
    class VectorStore,SemanticSearch,ChatStore,MessageStore,FeedbackStore,SuggestionsStore dataLayer
    class DocProcessor,Chunker,EmbeddingGen,ContextRetriever ragPipeline
    class ResponseGen,StreamHandler,ErrorHandler,ResponseLogger responseFlow
```

## Low-Level Design (LLD)

### 1. User Flow Diagram

```mermaid
sequenceDiagram
    actor User
    participant UI as React Frontend
    participant API as FastAPI Backend
    participant Orch as Orchestrator
    participant Model as Azure OpenAI
    participant DB as Cosmos DB
    participant Vector as Azure AI Search

    User->>UI: Enter Query
    UI->>API: POST /api/chat
    API->>DB: Get Chat Session
    API->>Orch: Analyze Query
    
    alt Auto Model Selection
        Orch->>Orch: Calculate Complexity Score
        Orch->>Orch: Select Optimal Model
    else Manual Selection
        Orch->>Orch: Use User Selected Model
    end

    opt RAG Enabled
        API->>Vector: Search Similar Context
        Vector-->>API: Return Context Chunks
    end

    API->>Model: Send Request + Context
    Model-->>API: Stream Response
    API-->>UI: Stream Response
    API->>DB: Save Message & Response
    UI->>User: Display Response

    User->>UI: Submit Feedback
    UI->>API: POST /api/feedback
    API->>DB: Store Feedback
```

### 2. Orchestrator Logic

```mermaid
flowchart TD
    Start["Receive User Query"] --> Analyze["Analyze Query"]
    
    Analyze --> CheckLength{"Query Length<br/>> 500 chars?"}
    CheckLength -->|Yes| HighComplexity["High Complexity +2"]
    CheckLength -->|No| CheckKeywords
    
    HighComplexity --> CheckKeywords{"Contains Complex<br/>Keywords?"}
    CheckKeywords -->|Yes| AddComplexity["Complexity +2"]
    CheckKeywords -->|No| CheckContext
    
    AddComplexity --> CheckContext{"Requires<br/>Context?"}
    CheckContext -->|Yes| RAGPath["Add RAG Context +1"]
    CheckContext -->|No| CalculateScore
    
    RAGPath --> CalculateScore["Calculate Total Score"]
    CalculateScore --> ScoreCheck{"Score >= 4?"}
    
    ScoreCheck -->|Yes| SelectGPT4["Select GPT-4"]
    ScoreCheck -->|No| ScoreCheck2{"Score >= 2?"}
    
    ScoreCheck2 -->|Yes| SelectGPT35["Select GPT-3.5 Turbo"]
    ScoreCheck2 -->|No| SelectFast["Select Fastest Available"]
    
    SelectGPT4 --> SendRequest["Send to Selected Model"]
    SelectGPT35 --> SendRequest
    SelectFast --> SendRequest
    
    SendRequest --> CheckResponse{"Response OK?"}
    CheckResponse -->|Yes| ReturnResponse["Return Response"]
    CheckResponse -->|No| Fallback["Fallback to GPT-3.5"]
    Fallback --> ReturnResponse
```

### 3. Data Models

```mermaid
erDiagram
    CHAT_SESSION ||--o{ MESSAGE : contains
    CHAT_SESSION ||--o{ FEEDBACK : has
    MESSAGE ||--o{ SUGGESTION : generates
    
    CHAT_SESSION {
        string id PK
        string user_id
        string title
        datetime created_at
        datetime updated_at
        boolean is_active
    }
    
    MESSAGE {
        string id PK
        string session_id FK
        string role
        text content
        string model_used
        float complexity_score
        int tokens_used
        float response_time
        datetime timestamp
    }
    
    FEEDBACK {
        string id PK
        string session_id FK
        string message_id FK
        int rating
        text comment
        boolean was_helpful
        datetime created_at
    }
    
    SUGGESTION {
        string id PK
        string message_id FK
        text suggestion_text
        string category
        boolean is_applied
        datetime created_at
    }
    
    MODEL_CONFIG {
        string id PK
        string model_name
        string deployment_name
        int max_tokens
        float temperature
        boolean is_active
        json capabilities
    }
    
    VECTOR_DOCUMENT {
        string id PK
        text content
        vector embedding
        json metadata
        datetime indexed_at
    }
```

### 4. Error Handling & Retry Flow

```mermaid
flowchart TD
    Request["API Request"] --> TryPrimary["Try Primary Model"]
    TryPrimary --> CheckSuccess1{"Success?"}
    
    CheckSuccess1 -->|Yes| Return["Return Response"]
    CheckSuccess1 -->|No| CheckError{"Error Type?"}
    
    CheckError -->|Rate Limit| Wait["Wait & Retry<br/>Exponential Backoff"]
    CheckError -->|Model Unavailable| TryFallback["Try Fallback Model"]
    CheckError -->|Invalid Request| ReturnError["Return Error<br/>with Details"]
    CheckError -->|Timeout| Retry["Retry Same Model<br/>Max 3 times"]
    
    Wait --> TryPrimary
    Retry --> CheckRetryCount{"Retry Count<br/>< 3?"}
    CheckRetryCount -->|Yes| TryPrimary
    CheckRetryCount -->|No| TryFallback
    
    TryFallback --> CheckSuccess2{"Success?"}
    CheckSuccess2 -->|Yes| Return
    CheckSuccess2 -->|No| ReturnError
```

## Component Details

### Frontend (React)
- **Chat Interface**: Real-time message display with streaming support
- **Model Selector**: Dropdown for manual model selection
- **History Panel**: Sidebar showing all chat sessions
- **Feedback Widget**: Star rating and comment input

### Backend (FastAPI)
- **REST API Endpoints**: Chat, History, Feedback, Models
- **WebSocket**: Real-time streaming responses
- **Orchestrator**: Query complexity analysis and model routing
- **Rate Limiter**: Request throttling per user

### Azure Services
- **Azure OpenAI**: GPT-4, GPT-3.5 Turbo, Embeddings
- **Azure AI Search**: Vector storage and semantic search
- **Azure Cosmos DB**: Chat history and metadata storage

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send chat message |
| `/api/chat/stream` | WS | Stream chat response |
| `/api/sessions` | GET | List chat sessions |
| `/api/sessions/{id}` | GET | Get session details |
| `/api/sessions` | POST | Create new session |
| `/api/sessions/{id}` | DELETE | Delete session |
| `/api/models` | GET | List available models |
| `/api/feedback` | POST | Submit feedback |
| `/api/suggestions` | GET | Get suggestions |

