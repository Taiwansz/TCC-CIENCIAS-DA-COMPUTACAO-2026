# Battle IA - Relatorio Experimental de Benchmark (TCC II)

> Eixo: Compressao de Prompts, Consumo de Tokens, Latencia e Custo Operacional.
> Total de Chamadas Executadas: **18** | Sucesso: **11** | Falhas: **7**

---

## 1. Tabela Consolidada de Resultados (Por Modelo e Tecnica)

| Modelo | Tecnica | Amostras | Latencia Media (ms) | Desvio Padrao (ms) | Tokens Entrada (Medio) | Tokens Saida (Medio) | Fator Compressao | Custo Total (USD) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `deepseek-ai/deepseek-v4-flash-0731` | `compressed_llmlingua` | 1 | 38014.17 | ±0.0 | 113.0 | 673.0 | 2.72x | $0.000561 |
| `deepseek-ai/deepseek-v4-flash-0731` | `few_shot` | 1 | 56576.52 | ±0.0 | 189.0 | 564.0 | 1.62x | $0.000489 |
| `deepseek-ai/deepseek-v4-flash-0731` | `zero_shot` | 1 | 35167.97 | ±0.0 | 355.0 | 676.0 | 0.86x | $0.000612 |
| `z-ai/glm-5.3` | `compressed_llmlingua` | 3 | 23277.35 | ±9870.5 | 121.0 | 963.0 | 2.34x | $0.004515 |
| `z-ai/glm-5.3` | `few_shot` | 2 | 13740.33 | ±842.02 | 221.5 | 887.0 | 1.46x | $0.002883 |
| `z-ai/glm-5.3` | `zero_shot` | 3 | 21862.31 | ±10742.41 | 318.0 | 967.0 | 0.88x | $0.004828 |

---

## 2. Analise de Eficiencia e Reducao de Custos

Comparativo das tecnicas comprimidas em relacao a linha de base (Zero-shot):

### Modelo: `deepseek-ai/deepseek-v4-flash-0731`
- **Tecnica `compressed_llmlingua` vs `zero_shot`:**
  - Reducao de Tokens de Entrada: **68.2%**
  - Variacao de Latencia: **-8.1%** (Baseline: 35167.97ms -> Comprimido: 38014.17ms)
  - Taxa de Compressao Efetiva: **2.72x**
- **Tecnica `few_shot` vs `zero_shot`:**
  - Reducao de Tokens de Entrada: **46.8%**
  - Variacao de Latencia: **-60.9%** (Baseline: 35167.97ms -> Comprimido: 56576.52ms)
  - Taxa de Compressao Efetiva: **1.62x**

### Modelo: `z-ai/glm-5.3`
- **Tecnica `compressed_llmlingua` vs `zero_shot`:**
  - Reducao de Tokens de Entrada: **61.9%**
  - Variacao de Latencia: **-6.5%** (Baseline: 21862.31ms -> Comprimido: 23277.35ms)
  - Taxa de Compressao Efetiva: **2.34x**
- **Tecnica `few_shot` vs `zero_shot`:**
  - Reducao de Tokens de Entrada: **30.3%**
  - Variacao de Latencia: **+37.2%** (Baseline: 21862.31ms -> Comprimido: 13740.33ms)
  - Taxa de Compressao Efetiva: **1.46x**

---

## 3. Instrucoes de Uso para os Membros da Equipe
- **Felipe Pinete (BERTScore):** Consumir o arquivo `battle_ia_results.json` e aplicar o script de avaliacao semantica comparando o campo `output_text` da tecnica comprimida contra o `output_text` da tecnica `zero_shot` de referencia.
- **Guilherme W. (Graficos e ABNT):** Importar `battle_ia_results.csv` para gerar os graficos de dispersao (Latencia vs Tamanho de Prompt) e barras (Economia de Tokens por Modelo) para o Capitulo 10.
- **Juan Pedro (Discussao):** Utilizar as secoes 1 e 2 deste relatorio para redigir a argumentacao empírica de Green AI e Teoria da Informacao.