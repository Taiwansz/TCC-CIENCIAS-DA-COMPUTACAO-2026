"""
Tabela de Precificacao de Modelos de Linguagem - Battle IA (TCC II)
Calcula custos estimados por chamada com base nos precos oficiais por milhao de tokens.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ModelPrice:
    provider: str
    model_id: str
    input_cost_per_million: float   # USD por 1M tokens de entrada
    output_cost_per_million: float  # USD por 1M tokens de saida


# Catalogo oficial de precos (atualizado para as APIs em 2026)
PRICING_CATALOG: Dict[str, ModelPrice] = {
    # OpenAI
    "gpt-4o": ModelPrice("openai", "gpt-4o", 2.50, 10.00),
    "gpt-4o-mini": ModelPrice("openai", "gpt-4o-mini", 0.15, 0.60),
    
    # Anthropic
    "claude-3-5-sonnet-20241022": ModelPrice("anthropic", "claude-3-5-sonnet-20241022", 3.00, 15.00),
    "claude-3-haiku-20240307": ModelPrice("anthropic", "claude-3-haiku-20240307", 0.25, 1.25),
    
    # Google Gemini
    "gemini-1.5-flash": ModelPrice("google", "gemini-1.5-flash", 0.075, 0.30),
    "gemini-1.5-pro": ModelPrice("google", "gemini-1.5-pro", 1.25, 5.00),
    "gemini-2.0-flash": ModelPrice("google", "gemini-2.0-flash", 0.10, 0.40),

    # Groq / Open-Weights
    "llama-3.1-8b-instant": ModelPrice("groq", "llama-3.1-8b-instant", 0.05, 0.08),
    "llama-3.3-70b-versatile": ModelPrice("groq", "llama-3.3-70b-versatile", 0.59, 0.79),

    # NVIDIA NIM (Modelos de Producao com API Keys ativas)
    "z-ai/glm-5.3": ModelPrice("nvidia", "z-ai/glm-5.3", 0.50, 1.50),
    "moonshotai/kimi-k3": ModelPrice("nvidia", "moonshotai/kimi-k3", 0.60, 2.00),
    "deepseek-ai/deepseek-v4-flash-0731": ModelPrice("nvidia", "deepseek-ai/deepseek-v4-flash-0731", 0.20, 0.80),
    "meta/llama-3.1-8b-instruct": ModelPrice("nvidia", "meta/llama-3.1-8b-instruct", 0.05, 0.08),
    "meta/llama-3.1-70b-instruct": ModelPrice("nvidia", "meta/llama-3.1-70b-instruct", 0.50, 0.70),
    "nvidia/nemotron-4-340b-instruct": ModelPrice("nvidia", "nvidia/nemotron-4-340b-instruct", 1.00, 2.00),

    # OpenRouter Free Tier (:free)
    "meta-llama/llama-3.1-8b-instruct:free": ModelPrice("openrouter", "meta-llama/llama-3.1-8b-instruct:free", 0.00, 0.00),
    "google/gemma-2-9b-it:free": ModelPrice("openrouter", "google/gemma-2-9b-it:free", 0.00, 0.00),

    # Mock / Local
    "mock-model": ModelPrice("mock", "mock-model", 0.10, 0.30),
    "ollama-local": ModelPrice("ollama", "ollama-local", 0.00, 0.00),
}


def calculate_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calcula o custo total em USD para a chamada."""
    price = PRICING_CATALOG.get(model_id)
    if not price:
        # Fallback conservador se modelo nao mapeado
        return 0.0
    input_cost = (prompt_tokens / 1_000_000.0) * price.input_cost_per_million
    output_cost = (completion_tokens / 1_000_000.0) * price.output_cost_per_million
    return round(input_cost + output_cost, 8)
