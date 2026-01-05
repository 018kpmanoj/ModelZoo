"""Azure OpenAI Client for model interactions."""
import asyncio
from typing import AsyncGenerator, Optional, List, Dict, Any
from openai import AsyncAzureOpenAI, AzureOpenAI
from app.config import settings, MODEL_CONFIGS
import time


class AzureOpenAIClient:
    """Client for Azure OpenAI API interactions."""
    
    def __init__(self):
        """Initialize Azure OpenAI clients."""
        self.async_client = None
        self.sync_client = None
        self._initialized = False
        
    def initialize(self):
        """Initialize the Azure OpenAI clients."""
        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            print("⚠️ Azure OpenAI credentials not configured - using mock responses")
            self._initialized = False
            return
            
        try:
            self.async_client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version
            )
            self.sync_client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version
            )
            self._initialized = True
            print("✅ Azure OpenAI client initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize Azure OpenAI client: {e}")
            self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if client is properly initialized."""
        return self._initialized
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_id: str = "gpt-35-turbo",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Get chat completion from Azure OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model_id: Model identifier
            max_tokens: Maximum tokens in response
            temperature: Response creativity (0-1)
            stream: Whether to stream response
            
        Returns:
            Dict with response content and metadata
        """
        model_config = MODEL_CONFIGS.get(model_id, MODEL_CONFIGS["gpt-35-turbo"])
        deployment_name = model_config["deployment_name"]
        
        if not self._initialized:
            # Return mock response for development
            return await self._mock_response(messages, model_id)
        
        start_time = time.time()
        
        try:
            response = await self.async_client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                max_tokens=min(max_tokens, model_config["max_tokens"]),
                temperature=temperature,
                stream=stream
            )
            
            if stream:
                return {"stream": response, "model": model_id}
            
            end_time = time.time()
            
            return {
                "content": response.choices[0].message.content,
                "model": model_id,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "response_time": end_time - start_time,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            print(f"❌ Azure OpenAI error: {e}")
            # Attempt fallback
            if model_id == "gpt-4":
                print("↪️ Falling back to GPT-3.5 Turbo...")
                return await self.chat_completion(
                    messages, "gpt-35-turbo", max_tokens, temperature, stream
                )
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model_id: str = "gpt-35-turbo",
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from Azure OpenAI.
        
        Yields:
            Chunks of response text
        """
        model_config = MODEL_CONFIGS.get(model_id, MODEL_CONFIGS["gpt-35-turbo"])
        deployment_name = model_config["deployment_name"]
        
        if not self._initialized:
            # Yield mock response chunks
            async for chunk in self._mock_stream_response(messages, model_id):
                yield chunk
            return
        
        try:
            response = await self.async_client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                max_tokens=min(max_tokens, model_config["max_tokens"]),
                temperature=temperature,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"❌ Azure OpenAI streaming error: {e}")
            yield f"Error: {str(e)}"
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using Azure OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding floats
        """
        if not self._initialized:
            # Return mock embedding
            import random
            return [random.random() for _ in range(1536)]
        
        try:
            response = await self.async_client.embeddings.create(
                model=settings.azure_openai_embedding_deployment,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            raise
    
    async def _mock_response(
        self,
        messages: List[Dict[str, str]],
        model_id: str
    ) -> Dict[str, Any]:
        """Generate mock response for development."""
        await asyncio.sleep(0.5)  # Simulate API latency
        
        user_message = messages[-1]["content"] if messages else "Hello"
        
        mock_responses = {
            "gpt-4": f"[GPT-4 Mock Response]\n\nI've analyzed your request: \"{user_message[:100]}...\"\n\nThis is a sophisticated mock response simulating GPT-4's capabilities. In production, this would be replaced with actual Azure OpenAI responses.\n\n**Key Points:**\n1. Your query has been processed\n2. Model orchestration is working\n3. The system is ready for Azure integration\n\nTo enable real responses, configure your Azure OpenAI credentials in the `.env` file.",
            "gpt-35-turbo": f"[GPT-3.5 Turbo Mock Response]\n\nHello! I received your message: \"{user_message[:50]}...\"\n\nThis is a mock response for development. Configure Azure OpenAI credentials to enable real AI responses.\n\n✅ Backend is running\n✅ Orchestrator is working\n✅ Database is connected"
        }
        
        content = mock_responses.get(model_id, mock_responses["gpt-35-turbo"])
        
        return {
            "content": content,
            "model": model_id,
            "tokens_used": len(content) // 4,
            "response_time": 0.5,
            "finish_reason": "stop",
            "is_mock": True
        }
    
    async def _mock_stream_response(
        self,
        messages: List[Dict[str, str]],
        model_id: str
    ) -> AsyncGenerator[str, None]:
        """Generate mock streaming response."""
        response = await self._mock_response(messages, model_id)
        content = response["content"]
        
        # Stream word by word
        words = content.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.03)  # Simulate streaming delay


# Global client instance
azure_client = AzureOpenAIClient()

