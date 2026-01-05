"""Intelligent Model Orchestrator - Analyzes queries and routes to optimal model."""
import re
from typing import Optional, Tuple, Dict, Any
from app.config import MODEL_CONFIGS, COMPLEXITY_KEYWORDS, settings


class QueryOrchestrator:
    """Orchestrator for analyzing queries and selecting optimal models."""
    
    def __init__(self):
        self.models = MODEL_CONFIGS
        self.complexity_keywords = COMPLEXITY_KEYWORDS
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query complexity and return analysis results.
        
        Returns:
            dict: Analysis results including complexity score and factors
        """
        analysis = {
            "length_score": 0,
            "keyword_score": 0,
            "structure_score": 0,
            "total_score": 0,
            "factors": [],
            "recommended_model": None
        }
        
        # 1. Length Analysis
        query_length = len(query)
        if query_length > 1000:
            analysis["length_score"] = 3
            analysis["factors"].append("Very long query (>1000 chars)")
        elif query_length > 500:
            analysis["length_score"] = 2
            analysis["factors"].append("Long query (>500 chars)")
        elif query_length > 200:
            analysis["length_score"] = 1
            analysis["factors"].append("Medium length query")
        
        # 2. Keyword Analysis
        query_lower = query.lower()
        
        # Check for high complexity keywords
        high_matches = [kw for kw in self.complexity_keywords["high"] if kw in query_lower]
        if high_matches:
            analysis["keyword_score"] += 2
            analysis["factors"].append(f"High complexity keywords: {', '.join(high_matches[:3])}")
        
        # Check for medium complexity keywords
        medium_matches = [kw for kw in self.complexity_keywords["medium"] if kw in query_lower]
        if medium_matches:
            analysis["keyword_score"] += 1
            analysis["factors"].append(f"Medium complexity keywords detected")
        
        # Check for low complexity (simple greetings)
        low_matches = [kw for kw in self.complexity_keywords["low"] if query_lower.strip() == kw]
        if low_matches:
            analysis["keyword_score"] = 0
            analysis["factors"].append("Simple greeting/response")
        
        # 3. Structure Analysis
        # Code detection
        code_patterns = [
            r'```', r'def\s+\w+', r'function\s+\w+', r'class\s+\w+',
            r'import\s+', r'from\s+\w+\s+import', r'=>', r'\bconst\b', r'\blet\b'
        ]
        if any(re.search(pattern, query) for pattern in code_patterns):
            analysis["structure_score"] += 2
            analysis["factors"].append("Contains code or technical content")
        
        # Question complexity
        question_words = query_lower.count("?")
        if question_words > 2:
            analysis["structure_score"] += 1
            analysis["factors"].append("Multiple questions detected")
        
        # Numbered lists or steps
        if re.search(r'\d+\.\s+', query):
            analysis["structure_score"] += 1
            analysis["factors"].append("Structured list/steps detected")
        
        # Calculate total score
        analysis["total_score"] = (
            analysis["length_score"] + 
            analysis["keyword_score"] + 
            analysis["structure_score"]
        )
        
        return analysis
    
    def select_model(self, query: str, preferred_model: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Select the optimal model for a query.
        
        Args:
            query: User's query text
            preferred_model: User's preferred model (if any)
            
        Returns:
            Tuple of (model_id, analysis_results)
        """
        # If user specified a model, use it
        if preferred_model and preferred_model in self.models:
            analysis = self.analyze_query(query)
            analysis["recommended_model"] = preferred_model
            analysis["selection_reason"] = "User specified model"
            analysis["was_auto_selected"] = False
            return preferred_model, analysis
        
        # Analyze query
        analysis = self.analyze_query(query)
        
        # Select model based on complexity score
        total_score = analysis["total_score"]
        
        if total_score >= 4:
            selected_model = "gpt-4"
            analysis["selection_reason"] = "High complexity query - using GPT-4 for best results"
        elif total_score >= 2:
            selected_model = "gpt-35-turbo"
            analysis["selection_reason"] = "Medium complexity - GPT-3.5 Turbo is efficient"
        else:
            selected_model = "gpt-35-turbo"
            analysis["selection_reason"] = "Simple query - using fast GPT-3.5 Turbo"
        
        analysis["recommended_model"] = selected_model
        analysis["was_auto_selected"] = True
        
        return selected_model, analysis
    
    def get_model_config(self, model_id: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        return self.models.get(model_id, self.models["gpt-35-turbo"])
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def get_available_models(self) -> list:
        """Get list of available models with their info."""
        return [
            {
                "id": model_id,
                "display_name": config["display_name"],
                "description": config["description"],
                "max_tokens": config["max_tokens"],
                "capabilities": config["capabilities"]
            }
            for model_id, config in self.models.items()
        ]


# Global orchestrator instance
orchestrator = QueryOrchestrator()

