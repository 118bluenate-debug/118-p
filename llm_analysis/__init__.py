"""
118 팔배개 - Ollama 로컬 LLM 분석 패키지
"""

from llm_analysis.schemas import RealtimeAnalysisResult, FinalConsultationSummary
from llm_analysis.ollama_client import OllamaClient

__all__ = ["RealtimeAnalysisResult", "FinalConsultationSummary", "OllamaClient"]
