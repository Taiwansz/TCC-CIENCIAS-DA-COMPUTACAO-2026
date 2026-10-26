# Figuras Cientificas e Graficos do TCC II

Este diretorio reune todas as representacoes visuais em alta definicao (300 DPI) incorporadas ao Capitulo 10 da monografia e prontas para a formulacao do artigo cientifico.

---

## 1. Dicionario de Figuras

| Arquivo | Capitulo | Descricao |
|---|---|---|
| `figura_10_1_volume_tokens.png` | Cap. 10 | Comparativo de volume de tokens de entrada faturados entre baselines (Zero-shot / Few-shot) e TokLang (2x e 4x). |
| `figura_10_2_latencia_ttft.png` | Cap. 10 | Comparativo do Time-to-First-Token (TTFT) e tempo total de inferencia sob streaming SSE. |
| `figura_10_3_bertscore_f1.png` | Cap. 10 | Retencao semantica (BERTScore Proxy F1) em funcao da taxa de compressao, com indicacao do limiar critico de 0,80. |
| `figura_10_4_custo_flops.png` | Cap. 10 | Projecao de custo financeiro por 100 mil requisicoes e reducao quadratica de FLOPs de autoatencao O(n²). |
| `painel_consolidado_battle_ia.png` | Anexo | Painel sintetico consolidado com visualizacao multidimensional da bancada. |

---

## 2. Como Regenerar os Graficos

Todos os graficos sao plotados diretamente a partir dos dados consolidados em `../benchmark/battle_ia_resultados_brutos.json` atraves da biblioteca Matplotlib / Seaborn.

```bash
cd figures
python generate_tcc_charts.py
```
