"""
GENERATE task implementation
Generates final response based on analysis results using Azure OpenAI
"""

import logging
import os
from typing import Dict, Any, List
from app.utils.azure_client import create_azure_openai_client
from app.tasks.base_task import BaseTask

logger = logging.getLogger(__name__)

class GenerateTask(BaseTask):
    """Task for generating final response"""
    
    def __init__(self, task):
        super().__init__(task)
        self.client = None
        self.initialized = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client using shared factory"""
        try:
            self.client = create_azure_openai_client()
            self.initialized = True
            logger.info("Azure OpenAI client initialized for GenerateTask")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise
    
    def _build_generation_prompt(self, dependency_results: Dict[str, Dict[str, Any]], plan_context: Dict[str, Any]) -> str:
        """Build prompt for response generation"""
        params = self.task.parameters
        response_type = params.response_type or "comprehensive_response"
        response_format = params.response_format or "natural_language"
        
        prompt = f"""You are a helpful assistant. Generate a {response_type} based on the following analysis and information.

Task Description: {self.task.description}
Response Type: {response_type}
Response Format: {response_format}

Original User Query: {plan_context.get('query', '')}

Analysis and Information from previous tasks:
"""
        
        # Format dependency results
        for task_id, result in dependency_results.items():
            if isinstance(result, dict):
                if "analysis" in result:
                    prompt += f"\n--- Analysis from {task_id} ---\n{result.get('analysis', '')}\n"
                elif "search_results" in result and result.get("search_results"):
                    # Include search results if available (for direct RETRIEVE -> GENERATE flow)
                    prompt += f"\n--- Search Results from {task_id} ---\n"
                    for i, sr in enumerate(result.get("search_results", [])[:3], 1):
                        content = sr.get('content', '') if isinstance(sr, dict) else getattr(sr, 'content', '')
                        prompt += f"{i}. {content[:200]}\n"
                elif "response" in result:
                    prompt += f"\n--- Information from {task_id} ---\n{result.get('response', '')}\n"
                else:
                    prompt += f"\n--- Results from {task_id} ---\n{str(result)}\n"
        
        prompt += f"\n\nGenerate a comprehensive, helpful response to the user's query. "
        prompt += f"Use the analysis and information provided above. "
        prompt += f"Respond in Korean if the query is in Korean, otherwise in English."
        
        return prompt
    
    async def execute(self, plan_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GENERATE task using Azure OpenAI"""
        self.mark_started()
        
        try:
            # Get dependency results
            dependency_results = self.get_dependency_results(plan_context)
            
            if not dependency_results:
                raise ValueError(f"GENERATE task {self.task.task_id} has no dependency results")
            
            # Build generation prompt
            prompt = self._build_generation_prompt(dependency_results, plan_context)
            
            # Call Azure OpenAI
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
            response = self.client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Provide clear, comprehensive responses based on the provided information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            generated_response = response.choices[0].message.content
            
            # Sanitize response to remove control characters
            from app.utils.sanitize import sanitize_json_string
            sanitized_response = sanitize_json_string(generated_response) if isinstance(generated_response, str) else generated_response
            
            result = {
                "response": sanitized_response,
                "response_type": self.task.parameters.response_type,
                "sources": self._extract_sources(dependency_results)
            }
            
            self.mark_completed(result)
            return result
            
        except Exception as e:
            error_msg = f"GENERATE task failed: {str(e)}"
            logger.error(error_msg)
            self.mark_failed(error_msg)
            raise
    
    def _extract_sources(self, dependency_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract sources from dependency results"""
        sources = []
        for result in dependency_results.values():
            if isinstance(result, dict):
                if "sources" in result and isinstance(result["sources"], list):
                    sources.extend(result["sources"])
        return sources

