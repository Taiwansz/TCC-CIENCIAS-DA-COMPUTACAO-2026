"""
TokLang Compiler Engine
Compila documentos AST em prompts otimizados preservando a hierarquia estrutural
e orcamentos estritos de tokens com protecao de restricoes e instrucoes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .ast_nodes import PromptDocument

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False


@dataclass(frozen=True)
class CompiledPrompt:
    text: str
    token_count: int
    max_tokens: int
    truncated: bool
    constraints: tuple[str, ...]


class TokLangCompiler:
    """Compila AST do TokLang respeitando orcamentos e preservando formatacao estruturada."""

    def __init__(self, tokenizer_model: str = "cl100k_base"):
        self.tokenizer_model = tokenizer_model
        if _TIKTOKEN_AVAILABLE:
            try:
                self._encoding = tiktoken.get_encoding(tokenizer_model)
            except Exception:
                self._encoding = None
        else:
            self._encoding = None

    def _count_tokens(self, text: str) -> int:
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        return len(re.findall(r"\S+", text))

    def _truncate_text(self, text: str, max_tokens: int) -> tuple[str, bool]:
        if self._count_tokens(text) <= max_tokens:
            return text, False

        if self._encoding is not None:
            token_ids = self._encoding.encode(text)
            truncated_ids = token_ids[:max_tokens]
            return self._encoding.decode(truncated_ids), True

        words = re.findall(r"\S+", text)
        truncated_words = words[:max_tokens]
        return " ".join(truncated_words), True

    def compile(self, document: PromptDocument) -> CompiledPrompt:
        budget = document.budget.max_tokens if document.budget else 1000
        if budget <= 0:
            raise ValueError("TokLang budget must be positive.")

        # Constraints (Alta Prioridade de Seguranca)
        constraints = tuple(
            f"{constraint.name}: {', '.join(constraint.focus_terms)}"
            for constraint in document.constraints
        )
        constraint_section = ""
        if constraints:
            constraint_section = "[constraints]\n" + "\n".join(f"- {item}" for item in constraints)

        # Instructions (Alta Prioridade da Tarefa)
        instruction_section = ""
        if document.instruction and document.instruction.instructions:
            instruction_section = (
                "[instructions]\n"
                + "\n".join(f"- {instruction}" for instruction in document.instruction.instructions)
            )

        # Overhead de alta prioridade
        high_priority_sections = [s for s in [constraint_section, instruction_section] if s]
        high_priority_raw = "\n\n".join(high_priority_sections)
        high_priority_tokens = self._count_tokens(high_priority_raw)

        # Orcamento restante alocado estritamente aos blocos de contexto
        context_budget = max(0, budget - high_priority_tokens)

        context_sections: list[str] = []
        accumulated_context_tokens = 0
        truncated = False

        for context in sorted(document.contexts, key=lambda item: item.priority, reverse=True):
            ctx_text = f"[context:{context.name}]\n{context.content.strip()}"
            ctx_tokens = self._count_tokens(ctx_text)

            if accumulated_context_tokens + ctx_tokens <= context_budget:
                context_sections.append(ctx_text)
                accumulated_context_tokens += ctx_tokens
            else:
                remaining_tokens = max(0, context_budget - accumulated_context_tokens)
                if remaining_tokens > 0:
                    trimmed_ctx, _ = self._truncate_text(ctx_text, remaining_tokens)
                    context_sections.append(trimmed_ctx)
                truncated = True
                break

        if high_priority_tokens > budget:
            truncated = True

        all_sections = context_sections + high_priority_sections
        compiled_text = "\n\n".join(section for section in all_sections if section)
        final_token_count = self._count_tokens(compiled_text)

        return CompiledPrompt(
            text=compiled_text,
            token_count=final_token_count,
            max_tokens=budget,
            truncated=truncated,
            constraints=constraints,
        )
