# Documentacao Oficial e Manuscrito do TCC II

> **Centro Universitario Max Planck (UniMAX) — Bacharelado em Ciencia da Computacao (2026)**  
> **Tema:** Compressao de Prompts, Otimizacao de Tokens e Sustentabilidade da IA  
> **Autores:**  
> - Matheus Sousa dos Santos (RA: 52319400)  
> - Felipe Guarnieri Pinete (RA: 52319337)  
> - Guilherme Gustavo Weber (RA: 52420339)  
> - Juan Pedro (RA: 52319411)  
> **Orientador:** Prof. Me. Luiz Claudio Chiavini Oliveira Junior  

---

## 1. Arquivos Oficiais de Avaliacao

| Arquivo | Formato | Paginas | Descricao |
|---|---|---|---|
| `TCC_II_Monografia_Final_Matheus_Santos.pdf` | PDF (ABNT) | 30 paginas | Manuscrito oficial com 11 capitulos, 4 tabelas dinamicas, 4 figuras cientificas e 21 referencias auditadas. |
| `TCC_II_Monografia_Final_Matheus_Santos.docx` | DOCX (Word) | 30 paginas | Documento fonte editavel formatado estritamente sob as diretrizes ABNT NBR 14724 e NBR 6023:2018. |
| `bibliografia_oficial_auditada_abnt.md` | Markdown | - | 21 referencias seminais com DOIs, links e fundamentacao teorica. |

---

## 2. Divisao de Responsabilidades na Bancada e Monografia

* **Matheus Sousa dos Santos (RA: 52319400) — Dev Core & Pipeline de Testes:**
  * Engenharia do compilador TokLang, automacao dos testes contra a API NVIDIA NIM e medicao de telemetria HTTPS SSE.
* **Felipe Guarnieri Pinete (RA: 52319337) — Engenharia de Prompt & Avaliacao Semantica:**
  * Formalizacao dos prompts tecnicos (Zero-shot, Few-shot e TokLang) e auditoria de fidelidade semantica via BERTScore Proxy F1.
* **Guilherme Gustavo Weber (RA: 52420339) — Tabulacao de Dados & Figuras Cientificas:**
  * Tabulacao dos dados brutos, geracao dos graficos a 300 DPI (tokens, TTFT, BERTScore e custos) e formatacao de estilo ABNT.
* **Juan Pedro (RA: 52319411) — Pesquisa, Problematizacao & Green AI:**
  * Fundamentacao teorica de Teoria da Informacao (Shannon), analise de sustentabilidade (Green AI) e redacao analitica das conclusoes.

---

## 3. Pipeline Automatizado de Compilacao (`pipeline/`)

A monografia foi estruturada atraves de um pipeline deterministico em Python:

* `build_monograph.py`: Realiza a injecao dos dados brutos experimentais (`benchmark/battle_ia_resultados_brutos.json`) diretamente nas tabelas da monografia e orquestra a formatacao de estilos via Microsoft Word COM em duas passadas para calibracao de sumario e paginacao sem paginas orfas.
* `structured_ch1_9.json`: Armazena a estrutura integral textual dos Capitulos 1 ao 9.
* `tcc_humanizer.py`: Motor de auditoria estilistica e densidade textual academica.

### Como recompilar a monografia

Requisitos: Ambiente Windows com Microsoft Word instalado (para automacao COM).

```bash
cd docs/pipeline
python build_monograph.py
```
