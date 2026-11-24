"""
Adaptadores de Provedores de Modelos de Linguagem - Battle IA (TCC II)
Utiliza apenas a biblioteca padrao do Python (urllib/json/time) para portabilidade maxima.
"""

import os
import json
import time
import random
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ProviderResponse:
    success: bool
    model_id: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    output_text: str
    error_message: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    def __init__(self, model_id: str):
        self.model_id = model_id

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.2) -> ProviderResponse:
        pass


class MockProvider(BaseProvider):
    """
    Provedor simulado para testes offline, validacao de pipeline e dry-runs.
    Gera contagem deterministica de tokens e latencia realista.
    """
    def __init__(self, model_id: str = "mock-model", simulated_latency_range=(120.0, 450.0)):
        super().__init__(model_id)
        self.simulated_latency_range = simulated_latency_range

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.2) -> ProviderResponse:
        start_time = time.perf_counter()
        
        # Simula latencia de rede/inferencia
        sim_latency = random.uniform(*self.simulated_latency_range) / 1000.0
        time.sleep(sim_latency)
        
        # Estimativa de tokens: ~4 caracteres por token
        prompt_tokens = max(1, len(prompt) // 4)
        if system_prompt:
            prompt_tokens += max(1, len(system_prompt) // 4)
            
        mock_output = f"[MOCK_RESPONSE: {self.model_id}] Resposta sintetica gerada para prompt de {len(prompt)} caracteres. Conformidade semantica mantida."
        completion_tokens = max(1, len(mock_output) // 4)
        total_tokens = prompt_tokens + completion_tokens
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        return ProviderResponse(
            success=True,
            model_id=self.model_id,
            provider="mock",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=round(elapsed_ms, 2),
            output_text=mock_output,
            raw_payload={"mock": True}
        )


class OpenAIProvider(BaseProvider):
    """Provedor REST compativel com OpenAI / Chat Completions API."""
    def __init__(self, model_id: str = "gpt-4o-mini", api_key: Optional[str] = None):
        super().__init__(model_id)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.2) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="openai",
                prompt_tokens=0, completion_tokens=0, total_tokens=0, latency_ms=0.0,
                output_text="", error_message="Variavel OPENAI_API_KEY ausente."
            )
            
        url = "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        start = time.perf_counter()
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency_ms = (time.perf_counter() - start) * 1000.0
                usage = data.get("usage", {})
                content = data["choices"][0]["message"]["content"]
                
                return ProviderResponse(
                    success=True,
                    model_id=self.model_id,
                    provider="openai",
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    latency_ms=round(latency_ms, 2),
                    output_text=content,
                    raw_payload=data
                )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="openai",
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                latency_ms=round(latency_ms, 2), output_text="",
                error_message=str(e)
            )


class AnthropicProvider(BaseProvider):
    """Provedor REST para Anthropic Messages API."""
    def __init__(self, model_id: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None):
        super().__init__(model_id)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.2) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="anthropic",
                prompt_tokens=0, completion_tokens=0, total_tokens=0, latency_ms=0.0,
                output_text="", error_message="Variavel ANTHROPIC_API_KEY ausente."
            )
            
        url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        start = time.perf_counter()
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency_ms = (time.perf_counter() - start) * 1000.0
                usage = data.get("usage", {})
                content = "".join([b.get("text", "") for b in data.get("content", [])])
                
                return ProviderResponse(
                    success=True,
                    model_id=self.model_id,
                    provider="anthropic",
                    prompt_tokens=usage.get("input_tokens", 0),
                    completion_tokens=usage.get("output_tokens", 0),
                    total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                    latency_ms=round(latency_ms, 2),
                    output_text=content,
                    raw_payload=data
                )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="anthropic",
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                latency_ms=round(latency_ms, 2), output_text="",
                error_message=str(e)
            )


class GeminiProvider(BaseProvider):
    """Provedor REST para Google Gemini API."""
    def __init__(self, model_id: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        super().__init__(model_id)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.2) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="google",
                prompt_tokens=0, completion_tokens=0, total_tokens=0, latency_ms=0.0,
                output_text="", error_message="Variavel GEMINI_API_KEY ausente."
            )
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Directive: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Entendido."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature
            }
        }
        
        headers = {"Content-Type": "application/json"}
        start = time.perf_counter()
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency_ms = (time.perf_counter() - start) * 1000.0
                usage = data.get("usageMetadata", {})
                candidates = data.get("candidates", [])
                text = ""
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join([p.get("text", "") for p in parts])
                
                return ProviderResponse(
                    success=True,
                    model_id=self.model_id,
                    provider="google",
                    prompt_tokens=usage.get("promptTokenCount", 0),
                    completion_tokens=usage.get("candidatesTokenCount", 0),
                    total_tokens=usage.get("totalTokenCount", 0),
                    latency_ms=round(latency_ms, 2),
                    output_text=text,
                    raw_payload=data
                )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="google",
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                latency_ms=round(latency_ms, 2), output_text="",
                error_message=str(e)
            )


class GroqProvider(BaseProvider):
    """Provedor REST para Groq (Llama, etc.). Compativel com interface OpenAI."""
    def __init__(self, model_id: str = "llama-3.1-8b-instant", api_key: Optional[str] = None):
        super().__init__(model_id)
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.2) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="groq",
                prompt_tokens=0, completion_tokens=0, total_tokens=0, latency_ms=0.0,
                output_text="", error_message="Variavel GROQ_API_KEY ausente."
            )
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        start = time.perf_counter()
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency_ms = (time.perf_counter() - start) * 1000.0
                usage = data.get("usage", {})
                content = data["choices"][0]["message"]["content"]
                
                return ProviderResponse(
                    success=True,
                    model_id=self.model_id,
                    provider="groq",
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    latency_ms=round(latency_ms, 2),
                    output_text=content,
                    raw_payload=data
                )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="groq",
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                latency_ms=round(latency_ms, 2), output_text="",
                error_message=str(e)
            )


KNOWN_NVIDIA_ENV_MAP: Dict[str, str] = {
    "z-ai/glm-5.3": "NVIDIA_API_KEY_GLM",
    "moonshotai/kimi-k3": "NVIDIA_API_KEY_KIMI",
    "deepseek-ai/deepseek-v4-flash-0731": "NVIDIA_API_KEY_DEEPSEEK",
}
KNOWN_NVIDIA_MODELS = set(KNOWN_NVIDIA_ENV_MAP.keys())


class NvidiaNimProvider(BaseProvider):
    """Provedor REST para NVIDIA NIM API (integrate.api.nvidia.com). Gratuito com 1000 creditos na criacao de conta."""
    def __init__(self, model_id: str = "meta/llama-3.1-8b-instruct", api_key: Optional[str] = None):
        super().__init__(model_id)
        env_var = KNOWN_NVIDIA_ENV_MAP.get(model_id)
        self.api_key = (
            api_key
            or (os.getenv(env_var) if env_var else None)
            or os.getenv("NVIDIA_API_KEY")
            or os.getenv("NV_API_KEY")
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1536, temperature: float = 0.2) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="nvidia",
                prompt_tokens=0, completion_tokens=0, total_tokens=0, latency_ms=0.0,
                output_text="", error_message="Variavel NVIDIA_API_KEY ausente."
            )
            
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True}
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream"
        }
        
        start = time.perf_counter()
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                content_chunks = []
                usage = {}
                for line in resp:
                    line_str = line.decode("utf-8").strip()
                    if not line_str or line_str.startswith(":"):
                        continue
                    if line_str.startswith("data: "):
                        data_str = line_str[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            if "usage" in chunk and chunk["usage"]:
                                usage = chunk["usage"]
                            choices = chunk.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                text = delta.get("content") or delta.get("reasoning_content") or delta.get("reasoning") or ""
                                if text:
                                    content_chunks.append(text)
                        except Exception:
                            pass
                
                latency_ms = (time.perf_counter() - start) * 1000.0
                full_content = "".join(content_chunks)
                
                p_toks = usage.get("prompt_tokens", max(1, len(prompt) // 4))
                c_toks = usage.get("completion_tokens", max(1, len(full_content) // 4))
                t_toks = usage.get("total_tokens", p_toks + c_toks)
                
                return ProviderResponse(
                    success=True,
                    model_id=self.model_id,
                    provider="nvidia",
                    prompt_tokens=p_toks,
                    completion_tokens=c_toks,
                    total_tokens=t_toks,
                    latency_ms=round(latency_ms, 2),
                    output_text=full_content,
                    raw_payload={"usage": usage, "chunks_count": len(content_chunks)}
                )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="nvidia",
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                latency_ms=round(latency_ms, 2), output_text="",
                error_message=str(e)
            )


class OpenRouterProvider(BaseProvider):
    """Provedor REST para OpenRouter, com suporte nativo a modelos :free."""
    def __init__(self, model_id: str = "meta-llama/llama-3.1-8b-instruct:free", api_key: Optional[str] = None):
        super().__init__(model_id)
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.2) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="openrouter",
                prompt_tokens=0, completion_tokens=0, total_tokens=0, latency_ms=0.0,
                output_text="", error_message="Variavel OPENROUTER_API_KEY ausente."
            )
            
        url = "https://openrouter.ai/api/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/Taiwansz/TokLang",
            "X-Title": "Battle IA TCC"
        }
        
        start = time.perf_counter()
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency_ms = (time.perf_counter() - start) * 1000.0
                usage = data.get("usage", {})
                content = data["choices"][0]["message"]["content"]
                
                return ProviderResponse(
                    success=True,
                    model_id=self.model_id,
                    provider="openrouter",
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    latency_ms=round(latency_ms, 2),
                    output_text=content,
                    raw_payload=data
                )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return ProviderResponse(
                success=False, model_id=self.model_id, provider="openrouter",
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                latency_ms=round(latency_ms, 2), output_text="",
                error_message=str(e)
            )


def get_provider(model_id: str, is_mock: bool = False) -> BaseProvider:
    """Instancia o provedor apropriado com base no identificador do modelo."""
    if is_mock or model_id.startswith("mock"):
        return MockProvider(model_id=model_id)
        
    if (
        model_id in KNOWN_NVIDIA_MODELS
        or model_id.startswith("meta/")
        or model_id.startswith("nvidia/")
        or model_id.startswith("z-ai/")
        or model_id.startswith("moonshotai/")
        or model_id.startswith("deepseek-ai/")
        or "nemotron" in model_id.lower()
    ):
        return NvidiaNimProvider(model_id=model_id)
    elif ":free" in model_id or ("/" in model_id and not model_id.startswith("meta/")):
        return OpenRouterProvider(model_id=model_id)
    elif model_id.startswith("gemini-"):
        return GeminiProvider(model_id=model_id)
    elif "llama" in model_id.lower() or "mixtral" in model_id.lower():
        return GroqProvider(model_id=model_id)
    elif model_id.startswith("claude-"):
        return AnthropicProvider(model_id=model_id)
    elif model_id.startswith("gpt-") or model_id.startswith("o1") or model_id.startswith("o3"):
        return OpenAIProvider(model_id=model_id)
    else:
        # Fallback para OpenAI compat
        return OpenAIProvider(model_id=model_id)
