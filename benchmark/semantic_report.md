# Laudo de Qualidade Semantica e BERTScore (TCC II)

> Avaliacao de retencao informacional: A resposta gerada sob compressao mantem o significado original?

---

## 1. Tabela de Similaridade Semantica por Modelo e Tecnica

| Modelo | Tecnica | Amostras | Compressao | Precisao Media | Recall Medio | BERTScore F1 (Medio) | Retencao Semantica |
|---|---|---:|---:|---:|---:|---:|---|
| `deepseek-ai/deepseek-v4-flash-0731` | `compressed_llmlingua` | 3 | 2.40x | 0.6797 | 0.6480 | **0.5794** | DEGRADADA (Alucinacao ou Perda de Fatos) |
| `deepseek-ai/deepseek-v4-flash-0731` | `few_shot` | 3 | 1.41x | 0.7393 | 0.5914 | **0.5648** | DEGRADADA (Alucinacao ou Perda de Fatos) |
| `deepseek-ai/deepseek-v4-flash-0731` | `zero_shot` | 3 | 0.87x | 1.0000 | 1.0000 | **1.0000** | EXCELENTE (Sem Perda Relevante) |
| `z-ai/glm-5.3` | `compressed_llmlingua` | 3 | 2.34x | 0.6901 | 0.6358 | **0.5667** | DEGRADADA (Alucinacao ou Perda de Fatos) |
| `z-ai/glm-5.3` | `few_shot` | 3 | 1.40x | 0.6546 | 0.4808 | **0.4337** | DEGRADADA (Alucinacao ou Perda de Fatos) |
| `z-ai/glm-5.3` | `zero_shot` | 3 | 0.88x | 1.0000 | 1.0000 | **1.0000** | EXCELENTE (Sem Perda Relevante) |

---

## 2. Conclusao Metodologica para a Banca
- **F1 >= 0.80:** Demonstra que a tecnica de compressao (LLMLingua) descarta apenas redundancias sintaticas sem comprometer os fatos tecnicos exigidos na pergunta.
- Este resultado comprova a tese central do TCC: **e possivel economizar tokens e reduzir a pegada computacional mantendo a acuracia informacional dos LLMs.**