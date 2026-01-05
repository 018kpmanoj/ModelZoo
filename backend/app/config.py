"""Application configuration settings."""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"
    
    # Model Deployments
    azure_openai_gpt4_deployment: str = "gpt-4"
    azure_openai_gpt35_deployment: str = "gpt-35-turbo"
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"
    
    # Azure Cosmos DB
    azure_cosmos_endpoint: Optional[str] = None
    azure_cosmos_key: Optional[str] = None
    azure_cosmos_database: str = "modelzoo"
    azure_cosmos_container: str = "chats"
    
    # Azure AI Search
    azure_search_endpoint: Optional[str] = None
    azure_search_key: Optional[str] = None
    azure_search_index: str = "modelzoo-vectors"
    
    # Application Settings
    app_secret_key: str = "dev-secret-key-change-in-production"
    app_debug: bool = True
    use_local_db: bool = True
    database_url: str = "sqlite+aiosqlite:///./modelzoo.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


# Model configurations with capabilities
MODEL_CONFIGS = {
    "gpt-4": {
        "deployment_name": settings.azure_openai_gpt4_deployment,
        "display_name": "GPT-4",
        "description": "Most capable model for complex reasoning and analysis",
        "max_tokens": 8192,
        "capabilities": ["complex_reasoning", "code_generation", "analysis", "creative_writing"],
        "complexity_threshold": 4,
        "cost_per_1k_tokens": 0.03
    },
    "gpt-35-turbo": {
        "deployment_name": settings.azure_openai_gpt35_deployment,
        "display_name": "GPT-3.5 Turbo",
        "description": "Fast and efficient for straightforward tasks",
        "max_tokens": 4096,
        "capabilities": ["general_chat", "simple_code", "summarization", "translation"],
        "complexity_threshold": 2,
        "cost_per_1k_tokens": 0.002
    }
}

# Complexity keywords for query analysis
COMPLEXITY_KEYWORDS = {
    "high": [
        "analyze", "explain in detail", "compare", "contrast", "evaluate",
        "synthesize", "create a plan", "design", "architect", "optimize",
        "debug complex", "refactor", "implement algorithm"
    ],
    "medium": [
        "summarize", "describe", "list", "what is", "how does", "example",
        "convert", "translate", "format", "write code"
    ],
    "low": [
        "hi", "hello", "thanks", "yes", "no", "ok", "bye"
    ]
}

