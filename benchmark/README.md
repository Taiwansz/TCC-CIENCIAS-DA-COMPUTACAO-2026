# Bancada Experimental Battle IA

A Bancada Experimental Battle IA foi concebida para quantificar em ambiente real de nuvem o impacto da compressao algoritmica de prompts frente a tecnicas convencionais de engenharia de prompt (Zero-shot e Few-shot).

---

## 1. Infraestrutura Experimental

* **Modelo Avaliado:** `meta/llama-3.2-11b-vision-instruct` (Meta Llama 3.2 11B Vision Instruct).
* **Nuvem de Hospedagem:** NVIDIA NIM Cloud sobre cluster de aceleradores NVIDIA A100 SXM4.
* **Metodo de Medicao de Latencia:** SSE (Server-Sent Events) Streaming real em conexao HTTPS direta, capturando o Time-to-First-Token (TTFT) exato em milissegundos.
* **Contabilidade de Tokens:** Extraida diretamente dos metadados de telemetria retornados pela API oficial da NVIDIA NIM.

---

## 2. Casos de Teste Avaliados

A bancada foi submetida a tres cenarios de alta complexidade tecnica em engenharia de software e ciencia da computacao:

1. **Caso 1 — Engenharia de Dados & SQL (DDL e Query Complexa):** Esquema relacional com 4 tabelas, restricoes de integridade e requisitos analiticos.
2. **Caso 2 — Auditoria Regulatoria & Seguranca (LGPD / Art. 46):** Politica de conformidade corporativa para deteccao de vulnerabilidades e fluxo de dados.
3. **Caso 3 — Arquitetura de Sistemas Distribuidos (Consenso Raft & Concorrencia):** Diagnostico de particionamento de rede (*Split-Brain*), quorum e eleicao de lider.

---

## 3. Arquivos de Dados

| Arquivo | Descricao |
|---|---|
| `battle_ia_resultados_brutos.json` | Registro individual de cada uma das 12 rodadas experimentais com resposta integral gerada pelo modelo, contagem de tokens, TTFT e metricas de avaliacao. |
| `battle_ia_results.csv` | Planilha tabular para analise estatistica e agregacao de resultados. |
| `battle_ia_summary.json` | Estatisticas consolidadas por tecnica (Zero-shot, Few-shot, TokLang 2x, TokLang 4x). |
| `battle_ia_report.md` | Relatorio analitico completo da bancada. |
| `semantic_report.md` | Auditoria detalhada de retencao semantica e correlacao BERTScore. |

---

## 4. Instrucoes de Reproducao

Para reexecutar a bancada contra o cluster da NVIDIA NIM:

1. Instale as dependencias:
```bash
pip install -r ../requirements.txt
```

2. Defina a chave de API da NVIDIA NIM:
```bash
# Windows PowerShell
$env:NVIDIA_API_KEY="nvapi-sua-chave-aqui"

# Linux / macOS
export NVIDIA_API_KEY="nvapi-sua-chave-aqui"
```

3. Dispare a bancada completa:
```bash
python battle_ia_benchmark.py
```

Opcoes disponiveis:
* `--model <id>`: Define o modelo alvo na NVIDIA NIM (padrao: `meta/llama-3.2-11b-vision-instruct`).
* `--caso <caso_1|caso_2|caso_3>`: Executa apenas um caso especifico.
* `--api-key <chave>`: Permite informar a chave via parametro de linha de comando.
* `--no-stream`: Suprime a saida de streaming token-a-token no console.
