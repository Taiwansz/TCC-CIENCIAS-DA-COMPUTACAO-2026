# Documentacao Oficial e Manuscrito do TCC II

Este diretorio contem a monografia completa, bibliografia auditada e o pipeline automatizado de compilacao ABNT.

---

## 1. Arquivos Oficiais de Avaliacao

| Arquivo | Formato | Paginas | Descricao |
|---|---|---|---|
| `TCC_II_Monografia_Final_Matheus_Santos.pdf` | PDF (ABNT) | 30 paginas | Manuscrito oficial com 11 capitulos, 4 tabelas dinamicas, 4 figuras cientificas e 21 referencias auditadas. |
| `TCC_II_Monografia_Final_Matheus_Santos.docx` | DOCX (Word) | 30 paginas | Documento fonte editavel formatado estritamente sob as diretrizes ABNT NBR 14724 e NBR 6023:2018. |
| `bibliografia_oficial_auditada_abnt.md` | Markdown | - | 21 referencias seminais com DOIs, links e fundamentacao teorica. |

---

## 2. Pipeline Automatizado de Compilacao (`pipeline/`)

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
