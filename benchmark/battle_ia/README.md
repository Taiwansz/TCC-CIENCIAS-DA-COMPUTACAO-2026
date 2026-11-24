# Battle IA - Framework Experimental de Benchmark (TCC II)

> **Tema:** Compressao de Prompts, Tokens e Sustentabilidade da IA  
> **Foco:** Capitulo 10 - Analise Experimental  
> **Turma:** N13208A (UniMAX / UniEduK) | 2026.2

---

## 1. Visao Geral da Arquitetura

O `battle_ia` e o motor de execucao experimental responsavel por enviar simultaneamente prompts em diferentes niveis de compressao (Zero-shot, Few-shot, LLMLingua) para multiplas familias de LLMs, mensurando:
1. **Tokens de Entrada e Saida** (via API usage ou estimativa de byte-pair encoding).
2. **Latencia** (tempo total de ida e volta em milissegundos).
3. **Custo Financeiro Estimado** (em USD, baseado no preco por 1M tokens de cada modelo).
4. **Fator de Compressao Real** ($\text{Ratio} = \frac{\text{Tokens Originais}}{\text{Tokens Comprimidos}}$).
5. **Reducao Percentual de Volume de Tokens**.

---

## 2. Estrutura do Pacote

```
battle_ia/
├── battle_runner.py       # CLI central de execucao do benchmark
├── providers.py           # Adaptadores REST para OpenAI, Anthropic, Gemini, Groq e Mock
├── pricing.py             # Tabela de precos oficiais por 1M tokens
├── metrics.py             # Agregador estatistico, gerador de CSV, JSON e relatorio MD
├── prompts_dataset.json   # Contrato de entrada de prompts (Responsabilidade do Felipe)
├── output/                # Artefatos gerados apos a execucao
│   ├── battle_ia_results.csv     # Para o Guilherme W. (Pandas/Graficos ABNT)
│   ├── battle_ia_results.json    # Para o Felipe Pinete (BERTScore / Semantica)
│   ├── battle_ia_summary.json   # Resumo estruturado com medias e desvios
│   └── battle_ia_report.md       # Relatorio dissertativo para o Juan Pedro (Cap. 10)
└── README.md
```

---

## 3. Como Executar

### 3.1 Teste Rapido Simulado (Sem Chaves de API e Sem Custo)
Para validar que todo o pipeline e a exportacao de dados estao operacionais:

```bash
python battle_runner.py --mock --repeats 2
```

### 3.2 Execucao Real contra as APIs de Producao
Configure as chaves no terminal (PowerShell no Windows):

```powershell
$env:OPENAI_API_KEY = "sua-chave"
$env:ANTHROPIC_API_KEY = "sua-chave"
$env:GEMINI_API_KEY = "sua-chave"
$env:GROQ_API_KEY = "sua-chave"
```

E execute o benchmark com os modelos desejados:

```bash
python battle_runner.py \
  --models "gpt-4o-mini,gemini-1.5-flash,claude-3-haiku-20240307,llama-3.1-8b-instant" \
  --repeats 3 \
  --delay 0.5
```

---

## 4. Guia de Integracao para os Membros da Equipe

### Para Felipe Pinete (Prompting & BERTScore):
- Abra o arquivo `prompts_dataset.json`.
- Cada caso deve conter as chaves:
  - `zero_shot`: Prompt original sem cortes.
  - `few_shot`: Prompt com exemplos.
  - `compressed_llmlingua`: Prompt passado pelo LLMLingua/LongLLMLingua.
- Apos a execucao do runner, consuma `output/battle_ia_results.json` para rodar o script de BERTScore comparando `output_text` da tecnica comprimida com a referencia.

### Para Guilherme W. (Dados & Graficos):
- Abra o arquivo `output/battle_ia_results.csv`.
- Colunas prontas para importar no Jupyter Notebook (`pd.read_csv("battle_ia_results.csv")`):
  - Eixo X: `prompt_tokens` / `compression_ratio`
  - Eixo Y: `latency_ms` / `cost_usd`
  - Hue/Categorias: `model_id` e `technique`

### Para Juan Pedro (Redacao Academica):
- O arquivo `output/battle_ia_report.md` gera automaticamente tabelas ABNT com médias e desvios-padrão prontas para colar no documento do TCC no Capitulo 10.
