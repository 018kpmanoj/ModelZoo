# 🦁 ModelZoo

**Multi-LLM Chat System with Intelligent Model Orchestration**

ModelZoo is a full-stack application that enables users to interact with multiple Azure OpenAI models through a unified, intelligent interface. The system features automatic model selection based on query complexity, chat history management, and comprehensive feedback mechanisms.

![ModelZoo Architecture](docs/modelzoo_architecture.png)

## ✨ Features

- **🧠 Intelligent Model Orchestration**: Auto-selects the optimal model (GPT-4 vs GPT-3.5 Turbo) based on query complexity
- **💬 Multi-Model Chat**: Switch between models manually or let the system decide
- **📚 Chat History**: Persistent chat sessions with full history
- **⭐ Feedback System**: Rate responses to help improve the system
- **🔄 Memory Context**: Chat maintains context across conversation
- **🚀 Streaming Responses**: Real-time response streaming
- **🎨 Modern UI**: Beautiful, responsive interface with dark theme

## 🏗️ Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Layer                                    │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  ┌─────────────┐ │
│  │  Chat UI    │  │Model Selector│  │Chat History│  │  Feedback   │ │
│  └──────┬──────┘  └──────┬───────┘  └─────┬─────┘  └──────┬──────┘ │
└─────────┼────────────────┼────────────────┼───────────────┼─────────┘
          │                │                │               │
          ▼                ▼                ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                                 │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Intelligent Orchestrator                      ││
│  │  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐   ││
│  │  │Query Analyzer│──│Model Router │──│Fallback Handler      │   ││
│  │  └──────────────┘  └─────────────┘  └──────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────┘│
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Azure OpenAI Service                            │
│  ┌─────────────┐  ┌─────────────────┐  ┌───────────────────────┐   │
│  │   GPT-4     │  │  GPT-3.5 Turbo  │  │  Embeddings (ada-002) │   │
│  └─────────────┘  └─────────────────┘  └───────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Layer                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │  Chat Sessions  │  │    Messages     │  │     Feedback        │ │
│  │  (SQLite/Cosmos)│  │                 │  │                     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Azure OpenAI Service (optional - works with mock responses for development)

### 1. Clone the Repository

```bash
git clone https://github.com/018kpmanoj/ModelZoo.git
cd ModelZoo
```

### 2. Start Both Servers

**Windows:**
```bash
START_ALL.bat
```

**Or start individually:**

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy env.template .env  # Edit with your Azure credentials
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
ModelZoo/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Configuration settings
│   │   ├── models.py        # Data models (SQLAlchemy + Pydantic)
│   │   ├── database.py      # Database connection
│   │   ├── orchestrator.py  # Model selection logic
│   │   ├── azure_client.py  # Azure OpenAI client
│   │   └── services.py      # Business logic
│   ├── requirements.txt
│   ├── env.template
│   └── run.bat
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js           # Main React component
│   │   ├── App.css          # Styles
│   │   ├── index.js
│   │   └── index.css
│   ├── package.json
│   └── run.bat
├── docs/
│   ├── system_design.md     # Detailed system design
│   └── modelzoo_architecture.png
├── README.md
├── START_ALL.bat
└── .gitignore
```

## 🔧 Configuration

### Azure OpenAI Setup

1. Create an Azure OpenAI resource in Azure Portal
2. Deploy models: `gpt-4`, `gpt-35-turbo`, `text-embedding-ada-002`
3. Copy `env.template` to `.env` and fill in your credentials:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_GPT4_DEPLOYMENT=gpt-4
AZURE_OPENAI_GPT35_DEPLOYMENT=gpt-35-turbo
```

### Development Mode (No Azure)

The application works without Azure credentials using mock responses - perfect for UI development and testing.

## 🎯 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send chat message |
| `/api/chat/stream` | POST | Stream chat response |
| `/api/sessions` | GET | List chat sessions |
| `/api/sessions` | POST | Create new session |
| `/api/sessions/{id}` | GET | Get session with messages |
| `/api/sessions/{id}` | DELETE | Delete session |
| `/api/models` | GET | List available models |
| `/api/feedback` | POST | Submit feedback |
| `/api/analyze` | POST | Analyze query complexity |

## 🧠 Model Orchestration Logic

The orchestrator analyzes queries based on:

1. **Query Length**: Longer queries suggest complex topics
2. **Keywords**: Detects complexity indicators ("analyze", "compare", "design", etc.)
3. **Structure**: Code blocks, multiple questions, numbered lists

**Scoring:**
- Score >= 4: Uses GPT-4 (complex reasoning)
- Score >= 2: Uses GPT-3.5 Turbo (balanced)
- Score < 2: Uses GPT-3.5 Turbo (simple queries)

## 📊 System Design Diagrams

Detailed Mermaid diagrams are available in `docs/system_design.md`:
- High-Level Architecture
- User Flow Sequence Diagram
- Orchestrator Logic Flowchart
- Data Model ER Diagram
- Error Handling Flow

## 🛠️ Technology Stack

**Backend:**
- FastAPI (Python)
- SQLAlchemy (ORM)
- Azure OpenAI SDK
- Pydantic (Validation)

**Frontend:**
- React 18
- Lucide React (Icons)
- CSS3 (Modern styling)

**Azure Services:**
- Azure OpenAI (GPT-4, GPT-3.5, Embeddings)
- Azure Cosmos DB (Production)
- Azure AI Search (Vector storage)

## 📝 License

MIT License - feel free to use this project for learning and development.

## 👤 Author

Created by Manoj Kumar P

---

**🦁 ModelZoo** - Intelligent Multi-Model AI Chat Platform

