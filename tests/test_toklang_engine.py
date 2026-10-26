"""
Suite de Testes Unitarios e Integrados do Nucleo TokLang
Testa:
- Analisador Lexico (TokLangLexer)
- Analisador Sintatico LL(1) (TokLangParser) e Geracao de AST
- Compilador Deterministico (TokLangCompiler)
- Estimador de Autoinformacao e Reducao Quadratica O(n²) (CompressionEstimator)
- Integridade Estrutural dos Dados Empiricos da Bancada Battle IA
"""

import json
from pathlib import Path
import unittest

from engine import (
    AttentionConstraint,
    CompiledPrompt,
    CompressionDirective,
    CompressionEstimator,
    ContextBlock,
    InstructionBlock,
    PromptDocument,
    Token,
    TokenBudgetDirective,
    TokLangCompiler,
    TokLangLexer,
    TokLangParser,
    TokenType,
)


class TestTokLangLexer(unittest.TestCase):
    def test_tokenize_directives_and_arguments(self):
        source = '@compress(level="aggressive", drop_stopwords=true) @budget(max_tokens=250)'
        lexer = TokLangLexer(source)
        tokens = lexer.tokenize()

        self.assertGreater(len(tokens), 5)
        self.assertEqual(tokens[0].type, TokenType.DIRECTIVE)
        self.assertEqual(tokens[0].value, "@compress")
        self.assertEqual(tokens[1].type, TokenType.LPAREN)
        self.assertEqual(tokens[-1].type, TokenType.EOF)

    def test_tokenize_blocks_and_strings(self):
        source = 'context "sistema" { "tabela usuario id int" }'
        lexer = TokLangLexer(source)
        tokens = lexer.tokenize()

        types = [t.type for t in tokens]
        self.assertIn(TokenType.IDENTIFIER, types)
        self.assertIn(TokenType.STRING, types)
        self.assertIn(TokenType.LBRACE, types)
        self.assertIn(TokenType.RBRACE, types)

    def test_empty_source(self):
        lexer = TokLangLexer("")
        tokens = lexer.tokenize()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TokenType.EOF)


class TestTokLangParser(unittest.TestCase):
    def test_parse_complete_document(self):
        source = """
        @compress(level="aggressive", target="semantic")
        @budget(max_tokens=400, reserve_completion=100)
        @constraint(name="seguranca", focus="token, hash, senha")

        context db { "CREATE TABLE users (id INT PRIMARY KEY);" }
        instruction { "Gerar query de contagem" }
        """
        lexer = TokLangLexer(source)
        parser = TokLangParser(lexer.tokenize())
        doc = parser.parse()

        self.assertIsInstance(doc, PromptDocument)
        self.assertIsNotNone(doc.compression)
        self.assertEqual(doc.compression.level, "aggressive")
        self.assertEqual(doc.compression.target, "semantic")

        self.assertIsNotNone(doc.budget)
        self.assertEqual(doc.budget.max_tokens, 400)
        self.assertEqual(doc.budget.reserve_completion, 100)

        self.assertEqual(len(doc.constraints), 1)
        self.assertEqual(doc.constraints[0].name, "seguranca")
        self.assertEqual(doc.constraints[0].focus_terms, ["token", "hash", "senha"])

        self.assertEqual(len(doc.contexts), 1)
        self.assertEqual(doc.contexts[0].name, "db")

        self.assertIsNotNone(doc.instruction)
        self.assertIn("Gerar query de contagem", doc.instruction.instructions)

    def test_syntax_error_unclosed_brace(self):
        source = 'context db { "incompleto"'
        lexer = TokLangLexer(source)
        parser = TokLangParser(lexer.tokenize())
        with self.assertRaises(SyntaxError):
            parser.parse()


class TestTokLangCompiler(unittest.TestCase):
    def test_deterministic_compilation_and_budget_truncation(self):
        doc = PromptDocument()
        doc.budget = TokenBudgetDirective(max_tokens=5)
        doc.contexts.append(
            ContextBlock(name="ctx", content="palavra1 palavra2 palavra3 palavra4 palavra5 palavra6 palavra7")
        )

        compiler = TokLangCompiler()
        compiled = compiler.compile(doc)

        self.assertIsInstance(compiled, CompiledPrompt)
        self.assertTrue(compiled.truncated)
        self.assertLessEqual(compiled.token_count, 5)

    def test_compiler_with_constraints_and_instructions(self):
        doc = PromptDocument()
        doc.budget = TokenBudgetDirective(max_tokens=50)
        doc.constraints.append(AttentionConstraint(name="schema", focus_terms=["id", "nome"]))
        doc.instruction = InstructionBlock(instructions=["Retorne em JSON"])

        compiler = TokLangCompiler()
        compiled = compiler.compile(doc)

        self.assertIn("[constraints]", compiled.text)
        self.assertIn("schema: id, nome", compiled.text)
        self.assertIn("[instructions]", compiled.text)
        self.assertIn("Retorne em JSON", compiled.text)
        self.assertFalse(compiled.truncated)

    def test_invalid_negative_budget(self):
        doc = PromptDocument()
        doc.budget = TokenBudgetDirective(max_tokens=-10)

        compiler = TokLangCompiler()
        with self.assertRaises(ValueError):
            compiler.compile(doc)


class TestCompressionEstimator(unittest.TestCase):
    def test_estimate_token_count(self):
        text = "O mecanismo de autoatencao no Transformer possui complexidade quadratica."
        tokens = CompressionEstimator.estimate_token_count(text)
        self.assertGreater(tokens, 0)
        self.assertGreaterEqual(tokens, len(text.split()))

    def test_flops_reduction_formula(self):
        raw = "texto longo com muitas informacoes repetidas e prolixas " * 10
        compressed = "texto comprimido essencial"

        metrics = CompressionEstimator.estimate_metrics(raw, compressed)

        self.assertIn("raw_tokens", metrics)
        self.assertIn("compiled_tokens", metrics)
        self.assertIn("tokens_saved", metrics)
        self.assertIn("attention_flops_reduction_percent", metrics)

        # Se houve compressao, a reducao quadratica deve ser positiva
        self.assertGreater(metrics["raw_tokens"], metrics["compiled_tokens"])
        self.assertGreater(metrics["attention_flops_reduction_percent"], 0.0)


class TestBattleIABenchmarkDataIntegrity(unittest.TestCase):
    def test_empirical_dataset_presence_and_structure(self):
        repo_root = Path(__file__).resolve().parent.parent
        json_file = repo_root / "benchmark" / "battle_ia_resultados_brutos.json"

        self.assertTrue(json_file.exists(), "battle_ia_resultados_brutos.json deve existir em benchmark/")

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data), 12, "A bancada completa deve conter exatamente 12 rodadas (3 casos x 4 tecnicas)")

        casos_esperados = {"caso_1", "caso_2", "caso_3"}
        tecnicas_esperadas = {"Zero-shot", "Few-shot (Baseline)", "LLMLingua (2x)", "LLMLingua (4x)"}

        casos_encontrados = set()
        tecnicas_encontrados = set()

        for item in data:
            self.assertIn("caso_id", item)
            self.assertIn("tecnica", item)
            self.assertIn("tokens_entrada", item)
            self.assertIn("tokens_saida", item)
            self.assertIn("ttft_ms", item)
            self.assertIn("bertscore_proxy_f1", item)
            self.assertIn("reducao_flops_atencao_pct", item)

            casos_encontrados.add(item["caso_id"])
            tecnicas_encontrados.add(item["tecnica"])

            # Verificacoes de sanidade numerica
            self.assertGreater(item["tokens_entrada"], 0)
            self.assertGreater(item["ttft_ms"], 0.0)
            self.assertGreaterEqual(item["bertscore_proxy_f1"], 0.0)
            self.assertLessEqual(item["bertscore_proxy_f1"], 1.0)

        self.assertEqual(casos_encontrados, casos_esperados)
        self.assertEqual(tecnicas_encontrados, tecnicas_esperadas)


if __name__ == "__main__":
    unittest.main()
