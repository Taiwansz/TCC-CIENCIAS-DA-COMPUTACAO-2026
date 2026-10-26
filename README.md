# TCC Ciencia da Computacao 2026: Compressao de Prompts, Otimizacao de Tokens e Sustentabilidade Computacional em LLMs

> **Repositorio Oficial de Artefatos, Codigo-Fonte, Bancada Empirica e Manuscrito do Trabalho de Conclusao de Curso (TCC II)**  
> **Centro Universitario Max Planck (UniMAX) — Bacharelado em Ciencia da Computacao (2026)**  
> 
> **Autores:**  
> - **Matheus Sousa dos Santos** (RA: 52319400)  
> - **Felipe Guarnieri Pinete** (RA: 52319337)  
> - **Guilherme Gustavo Weber** (RA: 52420339)  
> - **Juan Pedro** (RA: 52319411)  
> 
> **Orientador:** Prof. Me. Luiz Claudio Chiavini Oliveira Junior  

---

[![CI Pipeline](https://github.com/Taiwansz/TCC-CIENCIAS-DA-COMPUTACAO-2026/actions/workflows/ci.yml/badge.svg)](https://github.com/Taiwansz/TCC-CIENCIAS-DA-COMPUTACAO-2026/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![ABNT NBR 14724](https://img.shields.io/badge/ABNT-NBR_14724-green.svg)](docs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![NVIDIA NIM](https://img.shields.io/badge/Hardware-NVIDIA_A100_SXM4-76B900.svg)](https://build.nvidia.com/)
[![Status](https://img.shields.io/badge/Status-Pronto_para_Avaliacao_Final-success.svg)](docs/TCC_II_Monografia_Final_Ciencia_da_Computacao_2026.pdf)

---

## 1. Integrantes e Divisao de Responsabilidades

| Integrante | RA | Frente Principal de Atuacao | Entregaveis e Responsabilidades |
|---|---|---|---|
| **Matheus Sousa dos Santos** | 52319400 | Dev Core, Compilador & Pipeline | Engenharia da arquitetura do compilador TokLang, automacao dos scripts de inferencia na nuvem NVIDIA NIM e medicao HTTPS SSE streaming. |
| **Felipe Guarnieri Pinete** | 52319337 | Engenharia de Prompt & Avaliacao | Modelagem das tecnicas de prompting (Zero-shot, Few-shot e TokLang), analise semantica e calculo de BERTScore Proxy F1. |
| **Guilherme Gustavo Weber** | 52420339 | Ciencia de Dados & Visualizacao | Tabulacao dos dados brutos em CSV/JSON, plotagem das figuras cientificas a 300 DPI e padronizacao das normas graficas ABNT. |
| **Juan Pedro** | 52319411 | Pesquisa, Fundamentacao & Green AI | Pesquisa teorica sobre Teoria da Informacao (Shannon), analise de sustentabilidade energetica (Green AI) e redacao analitica de conclusao. |

---

## 2. Resumo do Trabalho

O aumento exponencial das janelas de contexto nos Modelos de Linguagem de Grande Porte (*Large Language Models* — LLMs) transferiu o gargalo computacional das aplicacoes inteligentes para a fase de *prefill* do mecanismo de autoatencao, cuja complexidade computacional e quadratica $O(n^2)$ em relacao a quantidade de tokens de entrada. Em pipelines corporativos e sistemas de geracao aumentada por recuperacao (*Retrieval-Augmented Generation* — RAG), o envio rotineiro de contextos verbosos, esquemas relacionais integrais e historicos de conversa acarreta degradacao acentuada da latencia de primeiro token (*Time-to-First-Token* — TTFT), custos financeiros proibitivos e consumo energetico desproporcional.

Este projeto apresenta o **TokLang**, uma linguagem declarativa de especificacao de prompts acoplada a um compilador deterministico e a uma bancada experimental empirica (*Battle IA Benchmark*). A metodologia combina compressao lexical orientada por autoinformacao de Shannon, selecao por densidade de perplexidade e controle estrito de orcamento de tokens.

Experimentos conduzidos em ambiente real de nuvem utilizando o modelo **Meta Llama 3.2 11B Vision Instruct** sobre infraestrutura acelerada por cluster **NVIDIA A100 SXM4 (NVIDIA NIM)** demonstraram:

1. **Reducao Faturada de Tokens de Entrada:** Queda media de **56,2%** no volume faturado sob compressao de 4x (caindo de 384,0 para 168,3 tokens por requisicao), alcancando ate **57,4%** no cenario de Engenharia de Dados.
2. **Reducao de Operacoes de Atencao:** Alivio quadratico medio de **80,7%** nos FLOPs de autoatencao da fase de prefill (80,8% no Caso 1, 81,8% no Caso 2 e 79,5% no Caso 3).
3. **Estabilizacao e Reducao de Latencia (TTFT):** Estabilizacao do tempo de resposta inicial entre 538,0 ms e 636,7 ms sob 4x, cortando **23,0%** em relacao ao baseline *Few-shot* e **87,6%** frente ao pico de contencao *Zero-shot* sob alta verbosidade.
4. **Preservacao da Fidelidade Semantica:** Retencao avaliada por BERTScore Proxy F1 acima do limiar critico de 0,80 para tarefas estruturadas (0,8524 em SQL sob DDL e 0,8279 em Auditoria LGPD).
5. **Economia Financeira Projetada:** Reducao de **56,2%** nos custos de entrada e **12,8%** no custo consolidado de lotes corporativos de 100 mil requisicoes.

---

## 3. Abstract

The exponential growth of context windows in Large Language Models (LLMs) has shifted the computational bottleneck of intelligent applications to the prefill phase of the self-attention mechanism, characterized by quadratic computational complexity $O(n^2)$ relative to the input sequence length. In enterprise pipelines and Retrieval-Augmented Generation (RAG) architectures, the recurring transmission of verbose documentation, database schemas, and dialogue history leads to substantial degradation of Time-to-First-Token (TTFT), prohibitive operational costs, and disproportionate energy dissipation.

This study presents **TokLang**, a declarative prompt specification language coupled with a deterministic compiler and an empirical evaluation bench (*Battle IA Benchmark*). The methodology integrates Shannon self-information lexical filtering, perplexity-density pruning, and strict token-budget enforcement.

Empirical evaluations conducted on the **Meta Llama 3.2 11B Vision Instruct** model hosted on **NVIDIA A100 SXM4** infrastructure via **NVIDIA NIM** demonstrated a **56.2% average reduction** in billable prompt tokens under 4x compression, an **80.7% quadratic reduction** in self-attention prefill FLOPs, stabilization of TTFT with latency cuts up to **87.6%** during high-contention scenarios, and sustained semantic fidelity (BERTScore Proxy F1 >= 0.80) across mission-critical software engineering domains.

---

## 4. Tabela Consolidada de Evidencias Empiricas

Os dados abaixo foram extraidos diretamente da execucao real via streaming SSE sobre o cluster NVIDIA NIM (`benchmark/battle_ia_resultados_brutos.json`):

| Dominio / Caso de Teste | Tecnica Avaliada | Tokens Entrada | Tokens Saida | TTFT (ms) | Tempo Total (s) | BERTScore F1 | Reducao FLOPs O(n²) | Custo Lote (100k req) |
|---|---|---|---|---|---|---|---|---|
| **Caso 1: SQL & DDL** | Zero-shot | 200 | 171 | 754.2 ms | 3.51 s | 0.8144 | 0.0% (Ref.) | US$ 316.50 |
| | Few-shot | 387 | 158 | 703.1 ms | 3.21 s | 0.8653 | -274.5% | US$ 353.10 |
| | TokLang 2x | 239 | 179 | 583.5 ms | 3.42 s | 0.8359 | -42.8% | US$ 340.20 |
| | **TokLang 4x** | **165** | 163 | **636.7 ms** | 3.32 s | **0.8524** | **+31.9%** | **US$ 294.00** |
| **Caso 2: LGPD Art. 46** | Zero-shot | 208 | 199 | 569.1 ms | 3.73 s | 0.7916 | 0.0% (Ref.) | US$ 360.90 |
| | Few-shot | 396 | 185 | 693.3 ms | 3.65 s | 0.8406 | -262.5% | US$ 396.30 |
| | TokLang 2x | 244 | 183 | 682.3 ms | 3.53 s | 0.8378 | -37.4% | US$ 347.70 |
| | **TokLang 4x** | **169** | 190 | **538.0 ms** | 3.55 s | **0.8279** | **+34.0%** | **US$ 335.70** |
| **Caso 3: Sistemas Dist.** | Zero-shot | 196 | 321 | 4330.1 ms | 7.97 s | 0.7963 | 0.0% (Ref.) | US$ 540.30 |
| | Few-shot | 369 | 203 | 821.3 ms | 4.14 s | 0.8374 | -254.4% | US$ 415.20 |
| | TokLang 2x | 230 | 258 | 830.4 ms | 5.09 s | 0.8166 | -37.5% | US$ 456.00 |
| | **TokLang 4x** | **171** | 207 | **588.6 ms** | 3.99 s | **0.7912** | **+24.0%** | **US$ 361.80** |

---

## 5. Estrutura do Repositorio

```
TCC-CIENCIAS-DA-COMPUTACAO-2026/
├── README.md                           # Visao geral, resultados, integrantes, reproducao e BibTeX
├── LICENSE                             # Licenca de codigo aberto MIT (2026) - Credito aos 4 autores
├── pyproject.toml                      # Empacotamento moderno PEP 517/621 com metadados dos autores
├── requirements.txt                    # Dependencias Python exatas para reproducao
├── .gitignore                          # Regras de exclusao de arquivos e credenciais
├── .env.example                        # Modelo de configuracao para chave da NVIDIA NIM
│
├── article/                            # Artigo cientifico derivado no padrao SBC (10-12 paginas)
│   ├── README.md                       # Diretrizes de submissao e compilacao LaTeX SBC
│   ├── artigo_toklang_sbc.md           # Manuscrito integral formatado para eventos da SBC
│   └── referencias_sbc.bib             # Base bibliografica BibTeX canonica
│
├── .github/workflows/                  # Automacao de Integracao Continua (CI)
│   └── ci.yml                          # Testes unitarios automatizados em Python 3.10, 3.11 e 3.12
│
├── tests/                              # Suite de Testes Automatizados Unitarios
│   ├── __init__.py
│   └── test_toklang_engine.py          # Testes de Lexer, Parser, Compilador e Integridade dos Dados
│
├── docs/                               # Manuscrito oficial da monografia e ABNT
│   ├── README.md                       # Protocolo de avaliacao cega e diretrizes ABNT
│   ├── TCC_II_Monografia_Final_Ciencia_da_Computacao_2026.pdf   # Manuscrito oficial canonico (30 paginas)
│   ├── TCC_II_Monografia_Final_Ciencia_da_Computacao_2026.docx  # Documento fonte editavel ABNT
│   ├── TCC_II_Versao_1_Acompanhamento_Matheus_Santos.pdf        # Espelho de acompanhamento protocolado
│   ├── bibliografia_oficial_auditada_abnt.md                    # 21 referencias seminais catalogadas
│   └── pipeline/
│       ├── build_monograph.py          # Script de orquestracao ABNT via Word COM
│       ├── structured_ch1_9.json       # Conteudo textual estruturado dos Caps. 1 ao 9
│       └── tcc_humanizer.py            # Validador e normalizador estilistico
│
├── engine/                             # Nucleo do compilador deterministico TokLang
│   ├── README.md                       # Especificacao formal da sintaxe e exemplos
│   ├── ast_nodes.py                    # Estruturas da Arvore de Sintaxe Abstrata (AST)
│   ├── lexer.py                        # Analisador lexico deterministico com tracking de linha
│   ├── parser.py                       # Parser descendente recursivo LL(1)
│   ├── estimator.py                    # Estimador de autoinformacao e orcamento
│   ├── compiler.py                     # Compilador final de traducao de prompts
│   └── __init__.py                     # Interface publica do pacote
│
├── benchmark/                          # Bancada experimental Battle IA (NVIDIA NIM)
│   ├── README.md                       # Metodologia e parametros de medicao
│   ├── battle_ia_benchmark.py          # Motor de medicao automatizada SSE streaming
│   ├── battle_ia_resultados_brutos.json# Dados brutos completos da execucao em nuvem
│   ├── battle_ia_results.csv           # Base tabular para analise estatistica
│   ├── battle_ia_summary.json          # Sumario estatistico consolidado por tecnica
│   ├── battle_ia_report.md             # Relatorio analitico da bancada
│   └── semantic_report.md              # Auditoria de correlacao e BERTScore Proxy F1
│
└── figures/                            # Figuras cientificas oficiais em 300 DPI
    ├── README.md                       # Metodologia de geracao e plotagem
    ├── generate_tcc_charts.py          # Script de geracao automatizada (Matplotlib)
    ├── figura_10_1_volume_tokens.png   # Comparativo de volume de tokens de entrada
    ├── figura_10_2_latencia_ttft.png   # Comparativo de TTFT e tempo total de resposta
    ├── figura_10_3_bertscore_f1.png    # BERTScore F1 vs Compressao (limiar 0.80)
    ├── figura_10_4_custo_flops.png     # Reducao de FLOPs O(n²) e projecao financeira
    └── dashboard_executivo_battle_ia.png # Painel sintetico consolidado da bancada
```

---

## 6. Como Reproduzir os Experimentos

### 6.1. Clonagem e Instalacao de Dependencias

```bash
git clone https://github.com/Taiwansz/TCC-CIENCIAS-DA-COMPUTACAO-2026.git
cd TCC-CIENCIAS-DA-COMPUTACAO-2026

python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 6.2. Execucao da Suite de Testes Automatizados

```bash
python -m unittest discover -s tests -v
```

### 6.3. Compilacao de Prompts via TokLang Engine

```python
from engine import TokLangLexer, TokLangParser, TokLangCompiler

codigo = """
@budget max_tokens: 150
@compress ratio: 4x

[context:banco_dados, priority: 1]
CREATE TABLE usuarios (id INT PRIMARY KEY, nome VARCHAR(100), saldo DECIMAL(10,2));

[constraints]
- schema: usuarios, saldo

[instructions]
- Retorne apenas a query de saldo positivo agrupada por usuario.
"""

lexer = TokLangLexer(codigo)
parser = TokLangParser(lexer.tokenize())
documento = parser.parse()

compiler = TokLangCompiler()
prompt_otimizado = compiler.compile(documento)

print("Prompt Otimizado:", prompt_otimizado.text)
print("Tokens Estimados:", prompt_otimizado.token_count)
```

### 6.4. Execucao da Bancada Experimental (Requer Chave NVIDIA NIM)

```bash
# Definir variavel de ambiente
# Windows PowerShell:
$env:NVIDIA_API_KEY="nvapi-sua-chave-aqui"

# Linux / macOS:
export NVIDIA_API_KEY="nvapi-sua-chave-aqui"

# Executar todos os cenarios de teste
cd benchmark
python battle_ia_benchmark.py
```

### 6.5. Regeneracao dos Graficos Cientificos

```bash
cd figures
python generate_tcc_charts.py
```

---

## 7. Citacao Academica (BibTeX)

Caso utilize este trabalho, dados da bancada ou o compilador TokLang em sua pesquisa ou artigo derivado, utilize a seguinte citacao:

```bibtex
@monography{santos2026toklang,
  author    = {Matheus Sousa dos Santos and Felipe Guarnieri Pinete and Guilherme Gustavo Weber and Juan Pedro},
  title     = {TokLang: Compress{\~a}o de Prompts, Otimiza{\c{c}}{\~a}o de Tokens e Sustentabilidade Computacional em Large Language Models},
  school    = {Centro Universit{\'a}rio Max Planck (UniMAX)},
  year      = {2026},
  address   = {Indaiatuba, SP, Brasil},
  type      = {Trabalho de Conclus{\~a}o de Curso (Bacharelado em Ci{\^e}ncia da Computa{\c{c}}{\~a}o)},
  advisor   = {Luiz Claudio Chiavini Oliveira Junior},
  pages     = {30},
  url       = {https://github.com/Taiwansz/TCC-CIENCIAS-DA-COMPUTACAO-2026}
}
```

Formato ABNT NBR 6023:2018:

> SANTOS, Matheus Sousa dos; PINETE, Felipe Guarnieri; WEBER, Guilherme Gustavo; PEDRO, Juan. **TokLang: Compressão de Prompts, Otimização de Tokens e Sustentabilidade Computacional em Large Language Models**. Orientador: Prof. Me. Luiz Claudio Chiavini Oliveira Junior. 2026. 30 f. Trabalho de Conclusão de Curso (Bacharelado em Ciência da Computação) – Centro Universitário Max Planck (UniMAX), Indaiatuba, 2026. Disponível em: <https://github.com/Taiwansz/TCC-CIENCIAS-DA-COMPUTACAO-2026>.

---

## 8. Licenca

Este projeto e distribuido sob os termos da licenca **MIT**. Consulte o arquivo [`LICENSE`](LICENSE) para mais detalhes.
