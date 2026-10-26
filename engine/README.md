# TokLang Engine — Compilador Deterministico de Prompts

O pacote `engine` implementa o compilador formal da linguagem TokLang. Sua finalidade e transformar especificacoes declarativas de prompts em estruturas textuais otimizadas com orcamentos rigidos de tokens, preservacao semantica de contexto e eliminacao de redundancias lexicais.

---

## 1. Arquitetura do Compilador

O fluxo de traducao e analise e estritamente deterministico, operando em tempo de compilacao sem necessidade de chamadas a modelos fundacionais:

```
[ Entrada TokLang ]
       |
       v
[ Lexer: TokLangLexer ] ----> Tokens (DIRECTIVE, IDENTIFIER, STRING, NUMBER, etc.)
       |
       v
[ Parser: TokLangParser ] --> Arvore de Sintaxe Abstrata (AST / PromptDocument)
       |
       v
[ Estimator / Compiler ] ---> CompiledPrompt (Texto podado, metadados e restricoes)
```

---

## 2. Modulos

| Modulo | Responsabilidade |
|---|---|
| `ast_nodes.py` | Definicoes dos nos da AST (`PromptDocument`, `CompressionDirective`, `AttentionConstraint`, `ContextBlock`, `InstructionBlock`). |
| `lexer.py` | Tokenizador baseado em expressoes regulares com rastreamento posicional de linha e coluna. |
| `parser.py` | Parser preditivo LL(1) com suporte a diretivas declarativas e profundidade de chaves. |
| `estimator.py` | Calculo de autoinformacao lexical e projecao de economia de tokens. |
| `compiler.py` | Tradutor de AST para prompt final comprimido com preservacao de quebras de linha e protecao de instrucoes sob orcamento. |

---

## 3. Exemplo de Uso em Python

```python
from engine import TokLangLexer, TokLangParser, TokLangCompiler

codigo_toklang = """
@compress(level="aggressive", target="semantic")
@budget(max_tokens=120, reserve_completion=40)
@constraint(name="schema", focus="transacoes, valor, conta_id")

context sistema_bancario {
    "Tabela transacoes: id INT, valor DECIMAL, data TIMESTAMP, conta_id INT."
}

instruction {
    "Retorne apenas a query SQL para saldo total por conta."
}
"""

lexer = TokLangLexer(codigo_toklang)
parser = TokLangParser(lexer.tokenize())
documento = parser.parse()

compiler = TokLangCompiler()
prompt_compilado = compiler.compile(documento)

print("Texto Comprimido:")
print(prompt_compilado.text)
print("\nTokens Faturados:", prompt_compilado.token_count)
print("Truncamento Ocorrido:", prompt_compilado.truncated)
```
