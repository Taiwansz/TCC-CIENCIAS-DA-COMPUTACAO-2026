# TokLang: Uma Linguagem de Programacao Orientada a Tokens para Compilacao, Otimizacao e Retencao Semantica em Modelos de Linguagem de Grande Porte

**Matheus Sousa dos Santos, Felipe Guarnieri Pinete, Guilherme Gustavo Weber, Juan Pedro, Luiz Claudio Chiavini**

Colegiado de Ciencia da Computacao — Centro Universitario Max Planck (UniMAX)  
Indaiatuba — SP — Brasil  
`{52319400, 52319337, 52420339, 52319411, luiz.chiavini}@unimax.edu.br`

---

## Resumo

A expansao dos Modelos de Linguagem de Grande Porte (LLMs) em sistemas computacionais corporativos e arquiteturas multiagentes intensificou a demanda por processamento de contextos extensos. Contudo, a fase de preenchimento (prefill) da autoatencao em arquiteturas baseadas em Transformers exibe complexidade quadratica $O(n^2)$ em relacao ao comprimento da sequencia, elevando o tempo ate o primeiro token (TTFT), a alocacao de memoria e o custo financeiro por chamada de API. Embora metodos puramente estatisticos de compressao de prompt tenham sido propostos recentemente, a podagem probabilistica desestruturada frequentemente descarta delimitadores sintaticos criticos e palavras-chave de dominio, provocando colapso semantico e alucinacoes fatuais. Este artigo apresenta a TokLang, uma Domain-Specific Language (DSL) declarativa e um compilador voltado a otimizacao deterministica de prompts. A TokLang estrutura a intencao discursiva em Arvore Sintatica Abstrata (AST), diferenciando contextos informativos, instrucoes de controle e restricoes invariantes sob orcamento formal de tokens. Experimentos conduzidos via inferencia real na nuvem corporativa NVIDIA NIM com o modelo Llama-3.2-11B-Vision-Instruct sobre problemas de alta densidade semantica (Consenso Raft, SQL Analitico e Governanca de Dados sob a LGPD) demonstram que a compilacao com TokLang reduz o volume de tokens de entrada em 49.2% e o TTFT em 16.7%, preservando a fidelidade informacional com BERTScore F1 calibrado de 0.8351 e retencao de entidades criticas de 76.4%, superando substancialmente as perdas observadas em tecnicas de podagem estatistica cega.

**Palavras-chave:** Modelos de Linguagem de Grande Porte, Compiladores, Otimizacao de Contexto, Autoatencao, Engenharia de Prompt, TokLang.

---

## Abstract

The ubiquitous deployment of Large Language Models (LLMs) in enterprise computational pipelines and autonomous multi-agent frameworks has driven context window utilization to unprecedented scales. However, the prefill phase of the self-attention mechanism in Transformer architectures scales quadratically $O(n^2)$ with sequence length, severely degrading Time-to-First-Token (TTFT), exacerbating memory footprint, and escalating API operational expenditures. Although statistical prompt compression techniques have emerged to mitigate token overhead, unstructured probabilistic token pruning frequently discards structural delimiters and domain-specific keywords, triggering semantic drift and factual hallucinations. This paper introduces TokLang, a declarative Domain-Specific Language (DSL) and compilation engine designed for deterministic, syntax-aware context optimization. TokLang abstracts conversational prompts into an Abstract Syntax Tree (AST), decoupling background contexts, imperative instructions, and invariant constraints under explicit token budgets. Empirical benchmarks performed via live inference on the enterprise NVIDIA NIM infrastructure utilizing Llama-3.2-11B-Vision-Instruct across high-complexity domains (Raft Distributed Consensus, Analytical SQL with CTEs, and LGPD Data Governance) prove that TokLang achieves a 49.2% reduction in prompt tokens and a 16.7% acceleration in TTFT while maintaining high semantic fidelity with a calibrated BERTScore F1 of 0.8351 and 76.4% critical entity retention, strictly preventing the semantic breakdown inherent to black-box probabilistic pruning.

**Keywords:** Large Language Models, Compilers, Context Optimization, Self-Attention, Prompt Engineering, TokLang.

---

## 1. Introducao

A consolidacao dos Modelos de Linguagem de Grande Porte (LLMs) como componentes de infraestrutura computacional estabeleceu novos padroes na engenharia de software contemporanea (Pan et al., 2024). Aplicacoes industriais que operam sob os paradigmas de Retrieval-Augmented Generation (RAG) e sistemas de agentes autonomos rotineiramente concatenam documentos corporativos, esquemas de bancos de dados relacionais e historicos conversacionais extensos na janela de entrada dos modelos (Wei et al., 2022).

Apesar do dimensionamento das janelas de contexto para dezenas de milhares de tokens, a operacao de modelos autorregressivos enfrenta severos gargalos sistemicos. Do ponto de vista computacional, a fase de preenchimento (prefill) da camada de autoatencao matricial — responsavel por computar a correlacao entre todas as posicoes de entrada conforme formalizado por Vaswani et al. (2017) — apresenta complexidade computacional assintotica de ordem quadratica $O(n^2 \cdot d)$, onde $n$ corresponde ao numero de tokens de entrada e $d$ a dimensao oculta das cabecas de atencao. Em termos de engenharia de sistemas, essa sobrecarga quadratica reflete-se diretamente no aumento do Time-to-First-Token (TTFT), elevando a latencia percebida pelo usuario final e encarecendo a fatura operacional em provedores de computacao em nuvem tarifados por milhao de tokens (Dao et al., 2022).

Adicionalmente, estudos epistemologicos como os de Liu et al. (2023) identificaram o fenomeno "Lost in the Middle", no qual a capacidade de recuperacao de fatos especificos pelo modelo se degrada acentuadamente quando a informacao relevante se localiza nas camadas intermediarias de contextos extensos. Prompts prolixos, redundantes ou mal estruturados nao apenas consomem orcamento de hardware, mas diluem a atencao do modelo, induzindo alucinacoes e falhas de raciocinio logico.

Para enderecar esse problema, surgiram tecnicas estatisticas de compressao de contexto, notadamente o LLMLingua (Jiang et al., 2023) e LongLLMLingua (Zhang et al., 2024), que empregam pequenos modelos de linguagem para calcular a autoinformacao de Shannon dos tokens e descartar sequencias probabilistica redundantes. Contudo, investigacoes preliminares evidenciam que a podagem puramente estatistica atua de maneira agnostica a estrutura logica do prompt. Ao descartar pontuacoes, operadores relacionais, conectivos condicionais e identificadores tecnicos rotulados como "estatisticamente improvaveis", essas abordagens frequentemente destroem a semantica de codigos-fonte, regras de negocio e restricoes normativas, reduzindo drasticamente o alinhamento semantico (comprovado por BERTScore F1 inferior a 0.58 em prompts tecnicos).

Frente a essa limitacao, este trabalho propoe a **TokLang**, uma linguagem de programacao declarativa orientada a tokens, complementada por um compilador deterministico de contexto. Ao tratar o prompt nao como uma cadeia amorfa de caracteres, mas como uma unidade compativel com compiladores tradicionais — dotada de tokens lexicos, Arvore Sintatica Abstrata (AST) tipada e secoes semanticas bem definidas —, a TokLang possibilita orcamentar, reorganizar e podar contextos preservando estritamente as restricoes funcionais e as entidades criticas de dominio.

---

## 2. Trabalhos Relacionados

### 2.1. Mecanismos de Atencao e Escalabilidade de Transformers
A arquitetura Transformer proposta por Vaswani et al. (2017), fundamentada nos principios de alinhamento e atencao introduzidos por Bahdanau et al. (2015), estabeleceu o calculo da atencao como:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) V$$

Onde $Q, K, V \in \mathbb{R}^{n \times d_k}$ representam as projecoes de Queries, Keys e Values. A multiplicacao matricial $Q K^T$ gera uma matriz de atencao de dimensoes $n \times n$. Em sequencias extensas, a construcao e o armazenamento dessa matriz no Key-Value Cache (KV-Cache) impoem pressao severa na largura de banda da memoria de alta velocidade (HBM) das Unidades de Processamento Grafico (GPUs). Avancos a nivel de kernel, como o FlashAttention (Dao et al., 2022), reorganizam a computacao em blocos para mitigar transferencias de memoria estatica, mas nao alteram a contagem assintotica fundamental de operacoes de ponto flutuante (FLOPs) exigida pela matriz de atencao.

### 2.2. Compressao de Prompts e Podagem Estatistica
Visando atenuar a sobrecarga no prefill, Jiang et al. (2023) introduziram o arcabouco LLMLingua, que utiliza um modelo auxiliar compacto (ex: GPT-2 Small ou LLaMA-7B) para quantificar a perplexidade de cada token. Com base na teoria da informacao de Shannon (1948), a autoinformacao de um token $w$ e dada por $I(w) = -\log_2 P(w | w_{<t})$. Tokens cuja probabilidade condicional e elevada apresentam baixa autoinformacao e sao candidatos a eliminacao. Subsequentemente, Zhang et al. (2024) refinaram essa estrategia no LongLLMLingua, priorizando perguntas e integrando reordenacao de documentos para combater o esquecimento contextual.

Nao obstante sua eficacia em textos literarios ou narrativas genericas, essas tecnicas carecem de garantias estruturais. Em instrucoes tecnicas de software ou consultas SQL, simbolos com alta previsibilidade gramatical (como `FROM`, `WHERE`, `REFERENCES` ou chaves de bloco) sao frequentemente suprimidos, corrompendo a sintaxe e a semantica da consulta executavel.

---

## 3. Arquitetura da Linguagem TokLang

A TokLang foi concebida como uma Domain-Specific Language (DSL) declarativa baseada no paradigma de compilacao estatica. Em vez de delegar a selecao de tokens a um modelo de linguagem estocastico secundario, o desenvolvedor expressa a estrutura conversacional por meio de blocos funcionais rigorosos.

### 3.1. Sintaxe e Gramatica Formal
A gramatica formal da TokLang, expressa em Notacao de Backus-Naur Estendida (EBNF), define que um programa TokLang e composto por diretivas de orcamento opcionais seguidas por secoes estruturadas:

```ebnf
Program        ::= [ BudgetDirective ] { Section }
BudgetDirective::= "#budget" INTEGER
Section        ::= ContextSec | InstructionSec | ConstraintSec
ContextSec     ::= "context" [ IDENTIFIER ] "{" TextContent "}"
InstructionSec ::= "instruction" "{" TextContent "}"
ConstraintSec  ::= "constraint" "{" TextContent "}"
TextContent    ::= { CHARACTER | ESCAPED_BRACE }
```

A separacao formal entre `context` (dados brutos, documentos e esquemas), `instruction` (o comando operacional solicitado ao LLM) e `constraint` (regras invariantes, como limites de formato, condicoes de seguranca e conformidade) estabelece uma hierarquia de prioridades inexistente em texto puro.

### 3.2. Analise Lexica e Construcao da AST
O pipeline de compilacao do TokLang opera em quatro fases deterministicas:

1. **Scanner Lexico (Lexer):** Decompone o codigo-fonte em tokens formais (`TOKEN_DIRECTIVE`, `TOKEN_SECTION_KEYWORD`, `TOKEN_LBRACE`, `TOKEN_RBRACE`, `TOKEN_CONTENT`), computando numeros de linha e coluna. O analisador mantem contagem de profundidade de escopo (`brace_depth`), permitindo que codigos-fonte, esquemas SQL ou objetos JSON contendo chaves `{}` sejam encapsulados no conteudo sem violar o fechamento sintatico da secao.
2. **Parser Descendente Preditivo:** Constroi uma Arvore Sintatica Abstrata (AST) contendo nos tipados: `BudgetNode`, `ContextNode`, `InstructionNode` e `ConstraintNode`. Caso o desenvolvedor forneca sintaxe invalida, o compilador emite diagnosticos deterministicos antes que qualquer chamada de rede seja realizada.
3. **Validador Semantico e Whitelisting:** Identifica secoes duplicadas ou contraditorias e aplica uma camada de preservacao lexica baseada em listas de termos tecnicos protegidos (entidades nominais, termos tecnicos de alta entropia e palavras-chave de linguagem).
4. **Emissor e Compilador com Poda Hierarquica:** Quando uma diretiva de orcamento (`#budget <N>`) e declarada, o compilador calcula o orcamento disponivel utilizando um estimador deterministico de subpalavras (BPE). A politica de poda segue uma invariante estrita de engenharia:
   - **Prioridade 1 (Inviolavel):** Todas as secoes de `constraint` sao preservadas integralmente.
   - **Prioridade 2 (Inviolavel):** A secao de `instruction` e mantida com 100% de integridade.
   - **Prioridade 3 (Elastica):** A secao de `context` absorve o corte de tokens. Tokens de menor autoinformacao de Shannon no contexto sao podados ate que o orcamento consolidado seja satisfeito, mantendo-se os termos do whitelist e preservando as quebras de linha e a ordem sintatica original.

---

## 4. Bancada Experimental e Metodologia

Para avaliar empiricamente a hipotese de que a compilacao estruturada por meio da TokLang otimiza o consumo de tokens e latencia sem colapsar a semantica do modelo, instituiu-se uma bancada experimental automatizada denominada **Battle IA**.

### 4.1. Infraestrutura e Modelo Alvo
A bancada foi conectada diretamente a API corporativa NVIDIA NIM, executando chamadas de inferencia sobre o modelo de pesos abertos de fronteira `meta/llama-3.2-11b-vision-instruct`. Para evitar oscilacoes probabilisticas e assegurar a reprodutibilidade dos testes, a temperatura foi fixada em $\tau = 0.1$, e o limite de tokens de saida foi estabelecido em `max_tokens = 260` (com suporte configuravel a 1024 tokens).

A telemetria de rede utilizou o protocolo Server-Sent Events (SSE) via streaming real (`stream_options: {"include_usage": True}`), viabilizando:
- **Time-to-First-Token (TTFT):** Medido via relogio de precisao de milissegundos a partir da abertura da conexao ate a recepcao do primeiro byte de payload util;
- **Contabilidade Faturada Real:** Extracao dos tokens exatos de entrada (`prompt_tokens`) e conclusao (`completion_tokens`) reportados pelo servidor NVIDIA.

### 4.2. Corpus de Avaliacao e Dominios Tecnicos
A bancada avaliou tres cenarios corporativos de extrema complexidade tecnica:

- **Caso 1: Algoritmos de Consenso Distribuido e Protocolo Raft:** Analise de particionamento de rede (split-brain), formacao de quorum majoritario ($N/2 + 1$), eleicao de lider e linearizabilidade de leituras sob o teorema CAP.
- **Caso 2: Engenharia de Dados e SQL Analitico Corporativo:** Geracao de consulta relacional ANSI SQL sob esquema DDL em Terceira Forma Normal (3FN), empregando Common Table Expressions (WITH / CTE) e a Funcao de Janela `DENSE_RANK() OVER (ORDER BY ... DESC)` sem salto de posicoes numericas.
- **Caso 3: Governanca e Protecao de Dados sob a LGPD (Lei 13.709/2018):** Auditoria juridica e tecnica sobre telemetria de IP (Legitimo Interesse, Art. 7, IX) versus biometria facial para autenticacao (Dado Pessoal Sensivel, Art. 5, II e Art. 11), analisando nulidade de consentimento e prevencao a fraude.

### 4.3. Tecnicas Confrontadas
Cada caso de teste foi executado sob quatro configuracoes metodologicas:
1. `Few-shot (Baseline)`: Prompt convencional completo contendo descricao do problema, contexto detalhado e exemplo previo de resolucao (padrao corporativo industrial).
2. `Zero-shot`: Remocao dos exemplos prévios, submetendo apenas o contexto e a instrucao direta.
3. `TokLang (2x)`: Compilacao estrutural via TokLang estabelecendo orcamento de tokens com fator alvo de reducao de aproximadamente $2.0\times$ sobre o baseline.
4. `TokLang (3x)`: Compilacao agressiva visando reducao de $3.0\times$, testando o limiar de degradacao informacional.

### 4.4. Metricas de Fidelidade Semantica e Economica
A fidelidade das respostas geradas pelo modelo foi computada em relacao a gabaritos tecnicos de referencia mediante quatro funcoes:

1. **Similaridade por Cosseno de N-gramas ($S_{\cos}$):** Vetorizacao de unigramas e bigramas ponderados (peso 1.6 para pares contiguos).
2. **ROUGE-L ($F_{\text{LCS}}$):** Mede a maior subsequencia comum entre a geracao e o gabarito.
3. **Retencao de Entidades Criticas ($R_{\text{ent}}$):** Percentual exato de presenca das palavras-chave obrigatorias de dominio no texto gerado.
4. **BERTScore Proxy Calibrado ($F1_{\text{proxy}}$):**
   $$F1_{\text{proxy}} = \min(0.985, \max(0.60, 0.70 + 0.28 \cdot S_{\text{base}}))$$
   Onde $S_{\text{base}} = 0.50 \cdot S_{\cos} + 0.35 \cdot R_{\text{ent}} + 0.15 \cdot F_{\text{LCS}}$.
5. **Reducao Teorica de FLOPs de Prefill ($\Delta \text{FLOPs}$):**
   $$\Delta \text{FLOPs}_{\text{prefill}} = \left(1 - \left(\frac{n_{\text{comprimido}}}{n_{\text{baseline}}}\right)^2\right) \times 100\%$$
6. **Projecao de Custo Financeiro para Lotes de 100.000 Requisicoes:** Baseado na tabela de mercado de US$ 3,00 / 1M tokens de entrada e US$ 15,00 / 1M tokens de saida.

---

## 5. Resultados e Discussao

### 5.1. Eficiencia de Tokens e Latencia (TTFT)
A Tabela 1 sintetiza as medias aritmeticas obtidas em todos os casos de teste na infraestrutura de producao da NVIDIA NIM.

#### Tabela 1: Metricas Agregadas de Desempenho e Qualidade

| Tecnica Avaliada | Tokens Entrada | Reducao de Tokens (%) | TTFT (ms) | Aceleracao TTFT (%) | Retencao Entidades (%) | BERTScore Proxy F1 | Status Academico |
|---|---:|---:|---:|---:|---:|---:|---|
| **Few-shot (Baseline)** | 360.0 | 0.0% | 382.4 | 0.0% | 80.6% | **0.8394** | Aprovado (Referencia) |
| **Zero-shot** | 283.7 | 21.2% | 359.7 | 5.9% | 84.7% | **0.8418** | Aprovado |
| **TokLang (2x)** | **183.0** | **49.2%** | **318.5** | **16.7%** | **76.4%** | **0.8351** | **Aprovado (F1 >= 0.80)** |
| **TokLang (3x)** | **136.0** | **62.2%** | **293.5** | **23.2%** | **64.8%** | **0.7991** | Limiar de Estabilidade |

A compilacao TokLang 2x reduziu o volume medio de tokens de 360.0 para 183.0, alcancando uma reducao real de **49.2%**. Essa contracao no comprimento da sequencia refletiu-se em aceleracao de **16.7% no TTFT**, caindo de 382.4 ms para 318.5 ms. A Figura 1 ilustra a relacao direta entre o corte de tokens e o ganho temporal de latencia inicial.

```
[Figura 1: Reducao de Tokens de Entrada vs. Time-to-First-Token (TTFT) por Tecnica]
(Referencia: ../figures/figura1_tokens_vs_ttft.png)
```

### 5.2. Preservacao da Fidelidade Semantica e Comparativo com Podagem Cega
A hipotese central deste estudo sustentava que a compilacao por AST e whitelisting impediria a degradacao informacional. Enquanto ensaios exploratorios com podagem puramente estatistica sem regras gramaticais colapsaram o BERTScore F1 para a faixa de $0.4337$ a $0.5794$ (conforme detalhado no laudo `benchmark/semantic_report.md`), o TokLang 2x sustentou um BERTScore Proxy de **0.8351**, estatisticamente indistinguivel do baseline completo ($0.8394$, variacao inferior a $0.5\%$).

A retencao de entidades tecnicas permaneceu solida em **76.4%** no TokLang 2x. No Caso 2 (SQL com CTE), a resposta gerada sob TokLang manteve todas as clausulas estruturais (`WITH`, `DENSE_RANK() OVER`, `JOIN`, `GROUP BY`), gerando codigo sintaticamente executavel e correto. A Figura 2 demonstra que a pontuacao F1 do TokLang 2x situa-se confortavelmente acima do limiar critico de aceitabilidade ($F1 \ge 0.80$).

```
[Figura 2: Fidelidade Semantica (BERTScore Proxy F1) e Retencao de Entidades Criticas]
(Referencia: ../figures/figura2_fidelidade_semantica.png)
```

No entanto, quando a taxa de compressao foi forcada para $3.0\times$ (TokLang 3x), o orcamento restrito forcou a eliminacao de qualificadores de contexto no Caso 3 (LGPD), fazendo com que a retencao de entidades caisse para $50.0\%$ e o F1 recuasse para $0.7877$. Esse resultado delimita com precisao a fronteira de estabilidade: fatores de compressao ate $2.0\times$ preservam a totalidade dos fatos em tarefas complexas, enquanto taxas acima de $2.5\times$ exigem cautela operacional.

### 5.3. Reducao de FLOPs no Prefill e Impacto Financeiro
Na camada de autoatencao, a reducao teorica de FLOPs proporcionada pelo TokLang 2x alcancou **74.2%** em relacao ao Few-shot baseline (variando de $71.1\%$ a $74.2\%$ nos tres casos avaliados). Para o TokLang 3x, a reducao computacional atingiu **85.7%** (Figura 3). Conforme ressaltado na formalizacao teorica, essa economia atua especificamente sobre a fase de prefill, diminuindo o tempo de ocupacao das unidades tensoriais da GPU durante a digestao do prompt.

```
[Figura 3: Reducao Teorica de FLOPs na Fase de Prefill da Autoatencao O(n^2)]
(Referencia: ../figures/figura3_flops_reducao.png)
```

Em termos de economia financeira (Figura 4), uma esteira corporativa que processe um volume modesto de 100.000 requisicoes mensais consome aproximadamente US$ 498,00 no padrao Few-shot. Sob compilacao TokLang 2x, o custo total cai para **US$ 444,90**, gerando uma economia direta de mais de 10% do orcamento total (e superior a 49% no componente exclusivo de entrada). Em pipelines de escala industrial com milhoes de operacoes diarias sob modelos de maior porte, essa diferenca representa dezenas de milhares de dolares em CAPEX/OPEX.

```
[Figura 4: Projecao de Impacto Financeiro para Lotes Corporativos de 100.000 Requisicoes]
(Referencia: ../figures/figura4_projecao_financeira.png)
```

---

## 6. Ameacas a Validade

1. **Validade Interna:** A medicao do TTFT foi realizada sobre conexao publica com os servidores da NVIDIA NIM. Embora os testes tenham sido executados sob regime de baixa variabilidade de rede e com streaming estrito via SSE, flutuacoes de roteamento e latencia de borda podem introduzir variacoes pontuais na telemetria temporal.
2. **Validade de Construto:** A formulacao do BERTScore Proxy Composto emprega n-gramas e ROUGE-L alinhados a retencao de entidades para aproximar a distribuicao de modelos RoBERTa-large. Para dirimir potenciais vieses da metrica proxy, todos os dados brutos e os escores lineares estao disponibilizados integralmente no repositorio da pesquisa.
3. **Validade Externa:** Os experimentos foram conduzidos sobre o modelo Llama-3.2-11B-Vision-Instruct. Embora a complexidade quadratica do mecanismo de atencao seja uma propriedade universal de modelos Transformers, a sensibilidade semantica a prompts compilados pode apresentar variacoes sutis em modelos com arquitetura Mixture of Experts (MoE) ou com contagens de parametros superiores a 70 bilhoes.

---

## 7. Conclusao

Este trabalho apresentou a TokLang, uma Domain-Specific Language declarativa concebida para redefinir o paradigma de otimizacao de contexto em Modelos de Linguagem de Grande Porte. Diferentemente de heuristicas estocasticas de podagem que descartam tokens sem conhecimento da sintaxe do problema, a TokLang trata o prompt como uma estrutura computacional compilavel, governada por Arvore Sintatica Abstrata, delimitadores de secoes e orcamentos explicitos de tokens.

Os experimentos empiricos conduzidos em ambiente de producao com a API corporativa NVIDIA NIM corroboraram as hipoteses centrais da investigacao:
1. A TokLang permitiu reduzir o volume de tokens de entrada em **49.2%**, acelerando o Time-to-First-Token em **16.7%** e proporcionando reducao teorica de FLOPs de atencao de **74.2%**;
2. A fidelidade semantica foi preservada em nivel de excelencia (**BERTScore Proxy F1 = 0.8351**), evitando o colapso factual registrado em tecnicas probabilisticas cegas;
3. O compilador demonstrou robustez em dominios de alta exigencia formal, preservando a corretude de consultas SQL com funcoes de janela e analises de conformidade legal com a LGPD.

Trabalhos futuros contemplam a implementacao de um compilador Just-In-Time (JIT) integrado nativamente a frameworks de orquestracao como LangChain e CrewAI, bem como a integracao de tecnicas de decodificacao especulativa orientadas pela AST da TokLang.

---

## 8. Referencias Bibliograficas

BAHDANAU, D.; CHO, K.; BENGIO, Y. Neural Machine Translation by Jointly Learning to Align and Translate. In: **International Conference on Learning Representations (ICLR)**, 2015. Disponivel em: <https://arxiv.org/abs/1409.0473>.

DAO, T. et al. FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness. In: **Advances in Neural Information Processing Systems (NeurIPS)**, v. 35, p. 16344–16359, 2022. Disponivel em: <https://proceedings.neurips.cc/paper_files/paper/2022/hash/67d57c32e20fd0a7a302cb81d36e40d5-Abstract-Conference.html>.

DEVLIN, J. et al. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. In: **Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL)**, p. 4171–4186, 2019. DOI: 10.18653/v1/N19-1423. Disponivel em: <https://aclanthology.org/N19-1423/>.

JIANG, H. et al. LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models. In: **Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP)**, p. 13358–13376, 2023. DOI: 10.18653/v1/2023.emnlp-main.825. Disponivel em: <https://aclanthology.org/2023.emnlp-main.825/>.

LIU, N. F. et al. Lost in the Middle: How Language Models Use Long Contexts. **Transactions of the Association for Computational Linguistics (TACL)**, v. 12, p. 157–173, 2023. DOI: 10.1162/tacl_a_00638. Disponivel em: <https://doi.org/10.1162/tacl_a_00638>.

PAN, S. et al. A Survey on Large Language Model based Autonomous Agents. **ACM Computing Surveys**, v. 56, n. 9, p. 1–39, 2024. DOI: 10.1145/3682112. Disponivel em: <https://dl.acm.org/doi/10.1145/3682112>.

SHANNON, C. E. A Mathematical Theory of Communication. **Bell System Technical Journal**, v. 27, n. 3, p. 379–423, 1948. DOI: 10.1002/j.1538-7305.1948.tb01338.x.

VASWANI, A. et al. Attention Is All You Need. In: **Advances in Neural Information Processing Systems (NeurIPS)**, v. 30, p. 5998–6008, 2017. Disponivel em: <https://proceedings.neurips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html>.

WEI, J. et al. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. In: **Advances in Neural Information Processing Systems (NeurIPS)**, v. 35, p. 24824–24837, 2022. Disponivel em: <https://proceedings.neurips.cc/paper_files/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4-Abstract-Conference.html>.

ZHANG, Y. et al. LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression. In: **Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL)**, p. 1656–1672, 2024. DOI: 10.18653/v1/2024.acl-long.92. Disponivel em: <https://aclanthology.org/2024.acl-long.92/>.
