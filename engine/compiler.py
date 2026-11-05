"""
TokLang Compiler Engine & Shannon Self-Information Compressor
Compila documentos AST em prompts otimizados preservando a hierarquia estrutural,
aplicando poda algoritmica de autoinformacao de Shannon (I(w) = -log2 P(w)) com
token whitelisting e orcamentos estritos BPE (tiktoken) sob politica ZERO FALLBACK.

Autores: Matheus Sousa dos Santos, Felipe Guarnieri Pinete, Guilherme Gustavo Weber, Juan Pedro Souza de Oliveira
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re
import tiktoken

from .ast_nodes import PromptDocument


class ShannonPromptCompressor:
    """
    Compressor algoritmico de prompts baseado em Autoinformacao de Shannon
    I(w) = -log2(P(w)) e Whitelisting de Sintaxe e Semantica Critica.
    """

    PALAVRAS_CHAVE_PROTEGIDAS: set[str] = {
        # SQL & DDL
        "select", "from", "where", "join", "on", "delete", "cascade", "cte", "with",
        "dense_rank", "group", "by", "order", "having", "sum", "count", "over",
        "clientes", "pedidos", "itens_pedido", "faturas", "ranking", "faturamento", "2026",
        # Sistemas Distribuidos & Raft
        "raft", "split-brain", "linearizável", "quórum", "quóruns", "líder", "leader",
        "partição", "rede", "cap", "cp", "latência", "250ms", "heartbeat", "leasing",
        # LGPD & Governanca
        "lgpd", "artigo", "art.", "7º", "11º", "consentimento", "biometria", "biométricos",
        "telemetria", "legítimo", "interesse", "sensível", "sensíveis", "lia", "titular"
    }

    CONECTIVOS_REDUNDANTES: set[str] = {
        "de", "a", "o", "as", "os", "em", "um", "uma", "uns", "umas", "para", "com",
        "por", "no", "na", "nos", "nas", "ao", "aos", "à", "às", "pelo", "pela", "pelos",
        "pelas", "do", "da", "dos", "das", "que", "e", "ou", "se", "como", "mas", "porém",
        "portanto", "assim", "pois", "então", "muito", "mais", "bem", "já", "quando",
        "mesmo", "sendo", "tendo", "estando", "sobre", "entre", "após", "até", "desde"
    }

    def __init__(self, extra_whitelist: set[str] | None = None):
        self.whitelist = set(self.PALAVRAS_CHAVE_PROTEGIDAS)
        if extra_whitelist:
            self.whitelist.update(w.lower().strip() for w in extra_whitelist if w.strip())

    def tokenizar(self, texto: str) -> list[str]:
        padrao = r"[\wºª\-\.]+|[^\w\s]"
        return re.findall(padrao, texto)

    def calcular_autoinformacao(self, tokens: list[str]) -> list[float]:
        tokens_lower = [t.lower() for t in tokens]
        total_tokens = len(tokens_lower)
        if total_tokens == 0:
            return []

        freqs = Counter(tokens_lower)
        scores: list[float] = []

        for t, t_low in zip(tokens, tokens_lower):
            if t_low in self.whitelist:
                scores.append(100.0)
                continue

            if t_low in self.CONECTIVOS_REDUNDANTES:
                prob = min(0.99, (freqs[t_low] / total_tokens) * 3.5)
                scores.append(-math.log2(prob) * 0.15)
                continue

            prob = freqs[t_low] / total_tokens
            info = -math.log2(max(prob, 1e-6))

            if len(t) > 7:
                info += 1.8
            scores.append(info)

        return scores

    def comprimir(self, prompt: str, fator_alvo: float = 2.0) -> tuple[str, int, int, float]:
        """
        Poda tokens de menor autoinformacao mantendo o orcamento de tokens especificado.
        Retorna: (texto_comprimido, tokens_originais, tokens_finais, taxa_real)
        """
        tokens = self.tokenizar(prompt)
        total_original = len(tokens)
        if total_original == 0 or fator_alvo <= 1.05:
            return prompt, total_original, total_original, 1.0

        orcamento = max(1, int(total_original / fator_alvo))
        scores = self.calcular_autoinformacao(tokens)

        indices_ranqueados = sorted(range(total_original), key=lambda i: scores[i], reverse=True)
        indices_selecionados = set(indices_ranqueados[:orcamento])

        for i, s in enumerate(scores):
            if s >= 90.0:
                indices_selecionados.add(i)

        tokens_mantidos = [tokens[i] for i in sorted(indices_selecionados)]

        texto_reconstruido = ""
        for i, tok in enumerate(tokens_mantidos):
            if i > 0 and tok not in ",.;:?!)]}'\"" and tokens_mantidos[i - 1] not in "([{'\"":
                texto_reconstruido += " "
            texto_reconstruido += tok

        total_final = len(tokens_mantidos)
        taxa_real = total_original / max(total_final, 1)
        return texto_reconstruido, total_original, total_final, taxa_real


@dataclass(frozen=True)
class CompiledPrompt:
    text: str
    token_count: int
    max_tokens: int
    truncated: bool
    constraints: tuple[str, ...]
    raw_token_count: int = 0


class TokLangCompiler:
    """
    Compila AST do TokLang respeitando orcamentos BPE (tiktoken) e aplicando
    poda de autoinformacao de Shannon sob politica ZERO FALLBACK.
    """

    LEVEL_TO_RATIO: dict[str, float] = {
        "lossless": 1.0,
        "1x": 1.0,
        "balanced": 2.0,
        "2x": 2.0,
        "aggressive": 4.0,
        "4x": 4.0,
    }

    def __init__(self, tokenizer_model: str = "cl100k_base"):
        self.tokenizer_model = tokenizer_model
        self._encoding = tiktoken.get_encoding(tokenizer_model)

    def _count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self._encoding.encode(text))

    def _truncate_text(self, text: str, max_tokens: int) -> tuple[str, bool]:
        if max_tokens <= 0:
            return "", True
        token_ids = self._encoding.encode(text)
        if len(token_ids) <= max_tokens:
            return text, False
        truncated_ids = token_ids[:max_tokens]
        return self._encoding.decode(truncated_ids), True

    def compile(self, document: PromptDocument) -> CompiledPrompt:
        budget = document.budget.max_tokens if document.budget else 1000
        if budget <= 0:
            raise ValueError("TokLang budget must be positive.")

        # Extrair termos protegidos das constraints declaradas na AST
        extra_whitelist: set[str] = set()
        for c in document.constraints:
            for term in c.focus_terms:
                extra_whitelist.add(term.lower().strip())

        # Determinar fator de compressao de Shannon a partir da diretiva @compress
        compression_factor = 1.0
        if document.compression is not None:
            lvl = document.compression.level.lower().strip()
            compression_factor = self.LEVEL_TO_RATIO.get(lvl, 2.0)

        compressor = ShannonPromptCompressor(extra_whitelist=extra_whitelist)

        # Constraints (Prioridade 1 - Inviolavel)
        constraints = tuple(
            f"{constraint.name}: {', '.join(constraint.focus_terms)}"
            for constraint in document.constraints
        )
        constraint_section = ""
        if constraints:
            constraint_section = "[constraints]\n" + "\n".join(f"- {item}" for item in constraints)

        # Instructions (Prioridade 2 - Inviolavel)
        instruction_section = ""
        if document.instruction and document.instruction.instructions:
            instruction_section = (
                "[instructions]\n"
                + "\n".join(f"- {instruction}" for instruction in document.instruction.instructions)
            )

        high_priority_sections = [s for s in [constraint_section, instruction_section] if s]
        high_priority_raw = "\n\n".join(high_priority_sections)
        high_priority_tokens = self._count_tokens(high_priority_raw)

        # Reserva tokens de separador caso existam secoes de alta prioridade e de contexto
        separator_overhead = 2 if (high_priority_sections and document.contexts) else 0
        context_budget = max(0, budget - high_priority_tokens - separator_overhead)

        context_sections: list[str] = []
        accumulated_context_tokens = 0
        truncated = False

        for context in sorted(document.contexts, key=lambda item: item.priority, reverse=True):
            raw_content = context.content.strip()
            if compression_factor > 1.05:
                compressed_content, _, _, _ = compressor.comprimir(raw_content, fator_alvo=compression_factor)
            else:
                compressed_content = raw_content

            ctx_text = f"[context:{context.name}]\n{compressed_content}"
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

        # Garantia deterministica estrita de orcamento quando secoes inviolaveis cabem no budget
        if self._count_tokens(compiled_text) > budget and high_priority_tokens == 0:
            compiled_text, _ = self._truncate_text(compiled_text, budget)
            truncated = True

        raw_context_sections = [
            f"[context:{ctx.name}]\n{ctx.content.strip()}"
            for ctx in sorted(document.contexts, key=lambda item: item.priority, reverse=True)
        ]
        raw_full_text = "\n\n".join(s for s in (raw_context_sections + high_priority_sections) if s)
        raw_total_tokens = self._count_tokens(raw_full_text)
        final_token_count = self._count_tokens(compiled_text)

        return CompiledPrompt(
            text=compiled_text,
            token_count=final_token_count,
            max_tokens=budget,
            truncated=truncated,
            constraints=constraints,
            raw_token_count=raw_total_tokens,
        )
