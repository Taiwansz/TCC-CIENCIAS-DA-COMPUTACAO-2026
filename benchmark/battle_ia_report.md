# Battle IA — Relatorio Experimental Consolidado da Bancada (TCC II)

> **Centro Universitario Max Planck (UniMAX) — Bacharelado em Ciencia da Computacao (2026)**  
> **Autores:** Matheus Sousa dos Santos, Felipe Guarnieri Pinete, Guilherme Gustavo Weber e Juan Pedro Souza de Oliveira  
> **Orientador:** Prof. Me. Luiz Claudio Chiavini Oliveira Junior  
> **Modelo Avaliado:** `meta/llama-3.2-11b-vision-instruct` | **Infraestrutura:** NVIDIA NIM Cloud (A100 SXM4)  
> **Total de Ensaios Executados:** **12** | **Sucesso:** **12** | **Falhas:** **0**

---

## 1. Medias Consolidadas por Tecnica de Prompting

| Tecnica Avaliada | Amostras | Tokens Entrada (Medio) | Reducao Entrada (%) | Razao Efetiva | TTFT Medio (ms) | Desvio Padrao TTFT (ms) | BERTScore Proxy F1 | Reducao FLOPs O(n²) | Custo Lote 100k (US$) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `Few-shot (Baseline)` | 3 | 384.0 | 0.0% | 1.00x | 614.9 | ±85.8 | 0.8314 | 0.0% | US$ 505.20 |
| `Zero-shot` | 3 | 309.3 | 19.4% | 1.24x | 2329.4 | ±1957.9 | 0.8285 | 35.4% | US$ 482.80 |
| `LLMLingua (2x)` | 3 | 234.3 | 39.0% | 1.64x | 956.8 | ±368.5 | 0.8192 | 62.8% | US$ 460.30 |
| `LLMLingua (4x)` | 3 | 168.3 | 56.2% | 2.28x | 574.3 | ±54.3 | 0.8238 | 80.7% | US$ 440.50 |

---

## 2. Resultados Detalhados por Caso de Uso (12 Ensaios Reais)

| Caso de Uso | Tecnica | Tokens Entrada | Tokens Saida | TTFT (ms) | Tempo Total (s) | Retencao Entidades | BERTScore F1 | Reducao FLOPs O(n²) | Custo 100k (US$) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `caso_1` (Raciocínio em Sistemas Distribuídos e Concorrência) | `Few-shot (Baseline)` | 340 | 260 | 585.2 | 7.05 | 66.7% | 0.8105 | 0.0% | US$ 492.00 |
| `caso_1` (Raciocínio em Sistemas Distribuídos e Concorrência) | `Zero-shot` | 262 | 260 | 536.7 | 5.62 | 55.6% | 0.8115 | 40.6% | US$ 468.60 |
| `caso_1` (Raciocínio em Sistemas Distribuídos e Concorrência) | `LLMLingua (2x)` | 206 | 260 | 914.3 | 7.48 | 44.4% | 0.7917 | 63.3% | US$ 451.80 |
| `caso_1` (Raciocínio em Sistemas Distribuídos e Concorrência) | `LLMLingua (4x)` | 149 | 260 | 538.0 | 17.96 | 44.4% | 0.7912 | 80.8% | US$ 434.70 |
| `caso_2` (Engenharia de Dados e Geração de Consultas SQL sob Esquemas DDL) | `Few-shot (Baseline)` | 434 | 260 | 548.0 | 6.59 | 100.0% | 0.8922 | 0.0% | US$ 520.20 |
| `caso_2` (Engenharia de Dados e Geração de Consultas SQL sob Esquemas DDL) | `Zero-shot` | 361 | 260 | 2032.7 | 13.91 | 100.0% | 0.8786 | 30.8% | US$ 498.30 |
| `caso_2` (Engenharia de Dados e Geração de Consultas SQL sob Esquemas DDL) | `LLMLingua (2x)` | 267 | 260 | 611.4 | 9.22 | 100.0% | 0.8623 | 62.2% | US$ 470.10 |
| `caso_2` (Engenharia de Dados e Geração de Consultas SQL sob Esquemas DDL) | `LLMLingua (4x)` | 185 | 260 | 636.7 | 6.65 | 100.0% | 0.8524 | 81.8% | US$ 445.50 |
| `caso_3` (Governança e Auditoria de Conformidade com a LGPD) | `Few-shot (Baseline)` | 378 | 260 | 711.6 | 7.16 | 37.5% | 0.7916 | 0.0% | US$ 503.40 |
| `caso_3` (Governança e Auditoria de Conformidade com a LGPD) | `Zero-shot` | 305 | 260 | 4418.7 | 18.33 | 37.5% | 0.7955 | 34.9% | US$ 481.50 |
| `caso_3` (Governança e Auditoria de Conformidade com a LGPD) | `LLMLingua (2x)` | 230 | 260 | 1344.7 | 9.54 | 50.0% | 0.8037 | 63.0% | US$ 459.00 |
| `caso_3` (Governança e Auditoria de Conformidade com a LGPD) | `LLMLingua (4x)` | 171 | 260 | 548.2 | 12.89 | 75.0% | 0.8279 | 79.5% | US$ 441.30 |

---

## 3. Sintese de Engenharia e Sustentabilidade (Green AI)

- **Compressao Efetiva e Poda de Shannon:** Sob compressao nominal de 4x (`LLMLingua (4x)`), o consumo medio faturado de tokens de entrada caiu **56.2%** (de 384.0 no baseline Few-shot para 168.3 tokens por chamada), atingindo **57.4%** de reducao no Caso 2 (SQL sob DDL).
- **Alivio Computacional no Prefill O(n²):** A reducao quadratica media nas operacoes de autoatencao da fase de prefill alcancou **80.7%** sob 4x (80.8% no Caso 1, 81.8% no Caso 2 e 79.5% no Caso 3).
- **Estabilizacao de Latencia (TTFT):** O TTFT medio sob compressao de 4x estabilizou-se em **574.3 ms** (±54.3 ms), mitigando os picos de enfileiramento observados em prompts extensos e reduzindo a latencia inicial em **23.0%** frente ao Few-shot no Caso 3.
- **Preservacao Semantica:** O escore composto BERTScore Proxy F1 manteve media global de **0.8238** em 4x, sustentando **100.0%** de retencao de entidades obrigatorias em SQL (F1 = 0.8524) e elevando a relacao sinal-ruido na auditoria LGPD (F1 subindo de 0.7916 para 0.8279).
