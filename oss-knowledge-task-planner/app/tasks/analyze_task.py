"""
ANALYZE task implementation
Analyzes information from previous tasks using Azure OpenAI
"""

import logging
import os
from typing import Dict, Any
from app.utils.azure_client import create_azure_openai_client
from app.tasks.base_task import BaseTask

logger = logging.getLogger(__name__)

class AnalyzeTask(BaseTask):
    """Task for analyzing information"""
    
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
            logger.info("Azure OpenAI client initialized for AnalyzeTask")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise
    
    def _build_analysis_prompt(self, dependency_results: Dict[str, Dict[str, Any]], plan_context: Dict[str, Any]) -> str:
        """Build prompt for analysis"""
        params = self.task.parameters
        analysis_type = params.analysis_type or "general_analysis"
        
        prompt = f"""You are an analysis assistant. Analyze the following information according to the task description.

Task Description: {self.task.description}
Analysis Type: {analysis_type}

Information from previous tasks:
"""
        
        # Format dependency results
        for task_id, result in dependency_results.items():
            if isinstance(result, dict):
                # Prioritize search_results over response (search_results contain actual documents)
                if "search_results" in result and result.get("search_results"):
                    prompt += f"\n--- Search Results from {task_id} ---\n"
                    search_results = result.get("search_results", [])
                    for i, sr in enumerate(search_results[:5], 1):  # Show top 5 results
                        content = sr.get('content', '') if isinstance(sr, dict) else getattr(sr, 'content', '')
                        source = sr.get('source_file', 'unknown') if isinstance(sr, dict) else getattr(sr, 'source_file', 'unknown')
                        score = sr.get('score', 0) if isinstance(sr, dict) else getattr(sr, 'score', 0)
                        prompt += f"{i}. [Score: {score:.3f}] {source}\n{content[:300]}\n\n"
                elif "response" in result:
                    # Fallback to response if no search_results
                    prompt += f"\n--- Results from {task_id} ---\n{result.get('response', '')}\n"
                else:
                    prompt += f"\n--- Results from {task_id} ---\n{str(result)}\n"
        
        prompt += f"\n\nOriginal Query: {plan_context.get('query', '')}\n\n"
        prompt += "Provide a detailed analysis based on the information above. Focus on the analysis type specified."
        
        return prompt
    
    async def execute(self, plan_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ANALYZE task using Azure OpenAI"""
        self.mark_started()
        
        try:
            # Get dependency results
            dependency_results = self.get_dependency_results(plan_context)
            
            if not dependency_results:
                raise ValueError(f"ANALYZE task {self.task.task_id} has no dependency results")
            
            # Build analysis prompt
            prompt = self._build_analysis_prompt(dependency_results, plan_context)
            
            # Call Azure OpenAI
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
            response = self.client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": "You are an expert analyst. Provide detailed, accurate analysis based on the provided information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            analysis_result = response.choices[0].message.content
            
            # Sanitize response to remove control characters
            from app.utils.sanitize import sanitize_json_string
            sanitized_analysis = sanitize_json_string(analysis_result) if isinstance(analysis_result, str) else analysis_result
            
            result = {
                "analysis_type": self.task.parameters.analysis_type,
                "analysis": sanitized_analysis,
                "input_tasks": list(dependency_results.keys())
            }
            
            self.mark_completed(result)
            return result
            
        except Exception as e:
            error_msg = f"ANALYZE task failed: {str(e)}"
            logger.error(error_msg)
            self.mark_failed(error_msg)
            raise

