"""
TokLang Recursive Descent Parser
Converte sequencias de tokens em uma Arvore Sintatica Abstrata (PromptDocument AST).
Politica Zero Fallback: Erros sintaticos sao reportados explicitamente com linha e coluna.
Autores: Matheus Sousa dos Santos, Felipe Guarnieri Pinete, Guilherme Gustavo Weber, Juan Pedro Souza de Oliveira
"""

from typing import Any

from .ast_nodes import (
    AttentionConstraint,
    CompressionDirective,
    ContextBlock,
    InstructionBlock,
    PromptDocument,
    TokenBudgetDirective,
)
from .lexer import Token, TokenType


class TokLangParser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token(TokenType.EOF, "", -1, -1)

    def _advance(self) -> Token:
        t = self._peek()
        if self.pos < len(self.tokens):
            self.pos += 1
        return t

    def _match(self, t_type: TokenType, value: str | None = None) -> bool:
        t = self._peek()
        if t.type == t_type:
            if value is None or t.value == value:
                self._advance()
                return True
        return False

    def _expect(self, t_type: TokenType, error_msg: str) -> Token:
        t = self._peek()
        if t.type != t_type:
            raise SyntaxError(f"Erro sintatico [linha {t.line}, col {t.column}]: {error_msg}. Encontrado: '{t.value}'")
        return self._advance()

    def _parse_kwargs(self) -> dict[str, Any]:
        """Analisa argumentos no formato (key="val", key=123, ...)."""
        kwargs: dict[str, Any] = {}
        if not self._match(TokenType.LPAREN):
            return kwargs

        while not self._match(TokenType.RPAREN):
            if self._peek().type == TokenType.EOF:
                t = self._peek()
                raise SyntaxError(f"Erro sintatico [linha {t.line}, col {t.column}]: Esperado ')' para fechar argumentos.")
            key_token = self._expect(TokenType.IDENTIFIER, "Esperado nome de parametro")
            self._expect(TokenType.EQUALS, "Esperado '=' apos parametro")
            val_token = self._peek()

            if val_token.type == TokenType.STRING:
                kwargs[key_token.value] = self._advance().value
            elif val_token.type == TokenType.NUMBER:
                num_str = self._advance().value
                # Suporta sufixo como 2x ou 4x se vier seguido de identificador 'x'
                if self._peek().type == TokenType.IDENTIFIER and self._peek().value.lower() == "x":
                    self._advance()
                    kwargs[key_token.value] = f"{num_str}x"
                else:
                    kwargs[key_token.value] = int(num_str)
            elif val_token.type == TokenType.IDENTIFIER:
                val = self._advance().value
                if val.lower() == "true":
                    kwargs[key_token.value] = True
                elif val.lower() == "false":
                    kwargs[key_token.value] = False
                else:
                    kwargs[key_token.value] = val
            else:
                raise SyntaxError(
                    f"Erro sintatico [linha {val_token.line}, col {val_token.column}]: "
                    f"Valor invalido '{val_token.value}' para o parametro '{key_token.value}'."
                )

            self._match(TokenType.COMMA)

        return kwargs

    def _parse_braced_body(self, block_label: str) -> list[str]:
        self._expect(TokenType.LBRACE, f"Esperado '{{' para iniciar bloco {block_label}")
        parts: list[str] = []
        brace_depth = 1
        while brace_depth > 0:
            if self._peek().type == TokenType.EOF:
                raise SyntaxError(f"Fim de arquivo inesperado dentro do bloco {block_label}.")
            tok = self._advance()
            if tok.type == TokenType.LBRACE:
                brace_depth += 1
                parts.append(tok.value)
            elif tok.type == TokenType.RBRACE:
                brace_depth -= 1
                if brace_depth > 0:
                    parts.append(tok.value)
            else:
                parts.append(tok.value)
        return parts

    def parse(self) -> PromptDocument:
        doc = PromptDocument()

        while self._peek().type != TokenType.EOF:
            t = self._peek()

            # Diretivas declarativas (@compress, @budget, @constraint)
            if t.type == TokenType.DIRECTIVE:
                dir_name = self._advance().value.lower()
                kwargs = self._parse_kwargs()

                if dir_name == "@compress":
                    ratio_val = str(kwargs.get("ratio", "")).lower()
                    default_level = "aggressive" if ratio_val == "4x" else ("balanced" if ratio_val == "2x" else "balanced")
                    doc.compression = CompressionDirective(
                        level=str(kwargs.get("level", default_level)),
                        target=str(kwargs.get("target", "semantic")),
                        drop_stopwords=bool(kwargs.get("drop_stopwords", True))
                    )
                elif dir_name == "@budget":
                    doc.budget = TokenBudgetDirective(
                        max_tokens=int(kwargs.get("max_tokens", 1000)),
                        reserve_completion=int(kwargs.get("reserve_completion", 250))
                    )
                elif dir_name == "@constraint":
                    focus = kwargs.get("focus", "")
                    focus_list = [f.strip() for f in focus.split(",")] if isinstance(focus, str) and focus else []
                    doc.constraints.append(AttentionConstraint(
                        name=str(kwargs.get("name", "unnamed")),
                        focus_terms=focus_list,
                        strictly_inviolable=bool(kwargs.get("strictly_inviolable", True))
                    ))
                else:
                    raise SyntaxError(f"Erro sintatico [linha {t.line}, col {t.column}]: Diretiva desconhecida '{dir_name}'.")
                continue

            # Blocos estruturais: context, instruction, constraint
            if t.type == TokenType.IDENTIFIER:
                block_type = t.value.lower()

                if block_type == "context":
                    self._advance()
                    name = "default"
                    if self._peek().type in (TokenType.STRING, TokenType.IDENTIFIER):
                        name = self._advance().value
                    ctx_kwargs = self._parse_kwargs()
                    priority = int(ctx_kwargs.get("priority", 1))
                    content_parts = self._parse_braced_body("context")
                    doc.contexts.append(ContextBlock(name=name, content=" ".join(content_parts), priority=priority))
                    continue

                if block_type == "instruction":
                    self._advance()
                    inst_parts = self._parse_braced_body("instruction")
                    if doc.instruction is None:
                        doc.instruction = InstructionBlock(instructions=inst_parts)
                    else:
                        doc.instruction.instructions.extend(inst_parts)
                    continue

                if block_type == "constraint":
                    self._advance()
                    name = "unnamed"
                    if self._peek().type in (TokenType.STRING, TokenType.IDENTIFIER):
                        name = self._advance().value
                    raw_parts = self._parse_braced_body("constraint")
                    joined = " ".join(raw_parts)
                    focus_list = [f.strip() for f in joined.split(",") if f.strip()]
                    doc.constraints.append(AttentionConstraint(name=name, focus_terms=focus_list, strictly_inviolable=True))
                    continue

            raise SyntaxError(
                f"Erro sintatico [linha {t.line}, col {t.column}]: "
                f"Elemento inesperado '{t.value}' fora de diretiva ou bloco estrutural."
            )

        return doc
