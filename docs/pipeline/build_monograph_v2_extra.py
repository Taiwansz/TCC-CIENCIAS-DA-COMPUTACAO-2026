import os
import sys
import re
import math
import json
import shutil
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import win32com.client
import pypdf
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

from tcc_humanizer import set_cell_margins, set_cell_background, format_abnt_table, humanize_text


def load_experimental_data() -> dict:
    candidates = [
        Path(__file__).parent / "battle_ia_resultados_brutos.json",
        Path(__file__).resolve().parent.parent.parent / "benchmark" / "battle_ia_resultados_brutos.json",
        Path(__file__).resolve().parent.parent / "battle_ia_resultados_brutos.json",
        Path.cwd() / "benchmark" / "battle_ia_resultados_brutos.json",
    ]
    json_path = next((p for p in candidates if p.exists()), None)
    if not json_path:
        raise FileNotFoundError(f"ERRO FATAL: Base empírica não encontrada em nenhum dos caminhos: {candidates}")
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    if len(records) < 12:
        raise ValueError(f"ERRO FATAL: Esperados 12 registros experimentais, encontrados {len(records)}")
    by_key = {(r["caso_id"], r["tecnica"]): r for r in records}
    return {"records": records, "by_key": by_key}


def fmt_br(val: float, decimals: int = 1) -> str:
    s = f"{val:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def calc_mean_std(vals: list) -> tuple:
    n = len(vals)
    if n == 0:
        return 0.0, 0.0, 0.0
    mean_v = sum(vals) / float(n)
    if n < 2:
        return mean_v, 0.0, 0.0
    var_v = sum((x - mean_v) ** 2 for x in vals) / float(n - 1)
    std_v = math.sqrt(var_v)
    cv_pct = (std_v / mean_v * 100.0) if mean_v > 0 else 0.0
    return mean_v, std_v, cv_pct


def build_monograph(docx_path: Path, sumario_page_map=None):
    exp = load_experimental_data()
    by_key = exp["by_key"]

    doc = Document()
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    doc.core_properties.comments = ""
    doc.core_properties.title = "Compressão Algorítmica de Prompts em Modelos de Linguagem de Grande Escala"
    doc.core_properties.subject = "Trabalho de Conclusão de Curso - Ciência da Computação"

    # 1. Margens ABNT
    for section in doc.sections:
        section.top_margin = Cm(3.0)
        section.left_margin = Cm(3.0)
        section.bottom_margin = Cm(2.0)
        section.right_margin = Cm(2.0)
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)

    def add_p(text, bold_prefix=None, space_after=5, line_spacing=1.5, first_line_indent=Cm(1.25), align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        text = humanize_text(text)
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing
        p.paragraph_format.first_line_indent = first_line_indent

        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.name = "Arial"
            r_bold.font.size = Pt(12)
            r_bold.font.bold = True
            r_bold.font.color.rgb = RGBColor(0, 0, 0)

        r = p.add_run(text)
        r.font.name = "Arial"
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_h1(text, page_break_before=False):
        if page_break_before:
            doc.add_page_break()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text.upper())
        r.font.name = "Arial"
        r.font.size = Pt(12.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = "Arial"
        r.font.size = Pt(12)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_table_title(title):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.name = "Arial"
        r.font.size = Pt(10)
        r.font.bold = True
        return p

    def add_table_source(source="Fonte: Dados experimentais obtidos pelos autores via NVIDIA NIM Cloud (2026)."):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(10)
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(source)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.font.italic = True
        return p

    def add_figure(img_path: Path, title: str, source="Fonte: Dados experimentais obtidos pelos autores via NVIDIA NIM Cloud (2026)."):
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_title.paragraph_format.space_before = Pt(12)
        p_title.paragraph_format.space_after = Pt(3)
        p_title.paragraph_format.first_line_indent = Cm(0)
        p_title.paragraph_format.line_spacing = 1.0
        p_title.paragraph_format.keep_with_next = True
        r_t = p_title.add_run(title)
        r_t.font.name = "Arial"
        r_t.font.size = Pt(10)
        r_t.font.bold = True

        if not img_path.exists():
            raise FileNotFoundError(f"ERRO FATAL: Figura cientifica obrigatoria nao encontrada: {img_path}")
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(2)
        p_img.paragraph_format.space_after = Pt(2)
        p_img.paragraph_format.first_line_indent = Cm(0)
        p_img.paragraph_format.keep_with_next = True
        run_img = p_img.add_run()
        run_img.add_picture(str(img_path), width=Cm(14.0))

        p_src = doc.add_paragraph()
        p_src.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_src.paragraph_format.space_before = Pt(2)
        p_src.paragraph_format.space_after = Pt(10)
        p_src.paragraph_format.first_line_indent = Cm(0)
        p_src.paragraph_format.line_spacing = 1.0
        r_s = p_src.add_run(source)
        r_s.font.name = "Arial"
        r_s.font.size = Pt(9)
        r_s.font.italic = True

    pipeline_dir = Path(__file__).resolve().parent
    repo_root = pipeline_dir.parent.parent
    figs_dir = repo_root / "figures" if (repo_root / "figures").exists() else pipeline_dir.parent / "figures"

    # =========================================================================
    # 1. CAPA RÍGIDA DE 1 PÁGINA (Quesito 1: Título Objetivo sem Duplicidade)
    # =========================================================================
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(0)
    p_inst.paragraph_format.space_after = Pt(0)
    p_inst.paragraph_format.line_spacing = 1.3
    r = p_inst.add_run("CENTRO UNIVERSITÁRIO MAX PLANCK\nCURSO DE BACHARELADO EM CIÊNCIA DA COMPUTAÇÃO")
    r.font.name = "Arial"
    r.font.size = Pt(12)
    r.font.bold = True

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(110)
    p_title.paragraph_format.space_after = Pt(0)
    p_title.paragraph_format.line_spacing = 1.3
    r_tit = p_title.add_run("COMPRESSÃO ALGORÍTMICA DE PROMPTS EM MODELOS DE LINGUAGEM DE GRANDE ESCALA\n\n")
    r_tit.font.name = "Arial"
    r_tit.font.size = Pt(14)
    r_tit.font.bold = True

    r_sub = p_title.add_run("Avaliação Empírica de Consumo de Tokens, Latência, Fidelidade Semântica e Eficiência Computacional")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(12)
    r_sub.font.bold = False

    p_nat = doc.add_paragraph()
    p_nat.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_nat.paragraph_format.space_before = Pt(110)
    p_nat.paragraph_format.space_after = Pt(0)
    p_nat.paragraph_format.line_spacing = 1.15
    p_nat.paragraph_format.left_indent = Cm(8.0)
    r_nat = p_nat.add_run(
        "Trabalho de Conclusão de Curso apresentado ao Curso de Bacharelado em Ciência da Computação "
        "do Centro Universitário Max Planck (UniMAX), como requisito parcial para obtenção do grau de "
        "Bacharel em Ciência da Computação."
    )
    r_nat.font.name = "Arial"
    r_nat.font.size = Pt(10)

    p_city = doc.add_paragraph()
    p_city.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_city.paragraph_format.space_before = Pt(150)
    p_city.paragraph_format.space_after = Pt(0)
    p_city.paragraph_format.line_spacing = 1.2
    r_city = p_city.add_run("INDAIATUBA\n2026")
    r_city.font.name = "Arial"
    r_city.font.size = Pt(12)
    r_city.font.bold = True

    # =========================================================================
    # 2. RESUMO (Página 2 - Quesito 2: Medido vs. Estimado & Fidelidade Condicional)
    # =========================================================================
    doc.add_page_break()
    p_res_title = doc.add_paragraph()
    p_res_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_res_title.paragraph_format.space_before = Pt(12)
    p_res_title.paragraph_format.space_after = Pt(12)
    r = p_res_title.add_run("RESUMO")
    r.font.name = "Arial"
    r.font.size = Pt(12)
    r.font.bold = True

    add_p(
        "A inferência de Modelos de Linguagem de Grande Escala (LLMs) impõe elevado custo computacional à sua operação contínua, "
        "visto que o mecanismo de autoatenção da arquitetura Transformer escala de forma quadrática O(n²) em relação ao comprimento da sequência de entrada. "
        "Este trabalho investiga a hipótese de redundância linguística de Claude Shannon aplicada à engenharia de prompt, avaliando em que medida o descarte "
        "algorítmico de tokens de baixa autoinformação reduz o volume de entrada e o esforço de processamento sem comprometer a precisão técnica das respostas. "
        "Construímos o compilador determinístico TokLang e a bancada experimental automatizada Battle IA para avaliar três cenários corporativos: raciocínio em sistemas distribuídos (consenso Raft e Teorema CAP), "
        "geração de consultas SQL analíticas sob esquemas DDL em 3FN e auditoria de conformidade com a LGPD. "
        "Submetemos o modelo Meta Llama-3.2-11B-Vision-Instruct, operado via nuvem gerenciada NVIDIA NIM Cloud (aceleradores NVIDIA A100 SXM4), a ensaios reais em streaming SSE, "
        "contrastando linhas de base convencionais (Few-shot e Zero-shot) com a compressão seletiva do motor TokLang / LLMLingua combinada a listas de proteção lexical (token whitelisting) em taxas nominais de 2x e 4x. "
        "As medições empíricas diretas na API comprovam que a compressão nominal de 4x reduz o volume faturado de tokens de entrada em até 57,4% (média de 56,2%, caindo de 384,0 para 168,3 tokens por requisição). "
        "A partir dessa redução medida, estima-se analiticamente pela equação de complexidade quadrática uma supressão teórica média de 80,7% nos FLOPs de autoatenção da fase de prefill (81,8% no Caso 2), funcionando como indicador computacional indireto de eficiência energética. "
        "O Time-to-First-Token (TTFT) medido estabilizou-se em 574,3 ± 54,3 ms sob compressão de 4x (coeficiente de variação de 9,5%, contra 84,1% no Zero-shot), embora o tempo total de geração permaneça sujeito a oscilações de decoding na nuvem compartilhada. "
        "A fidelidade semântica — avaliada pelo estimador composto BERTScore Proxy F1 (que pondera similaridade cossenoidal de n-gramas, retenção de entidades e ROUGE-L sob limiar crítico de 0,80) — mostrou-se condicional à natureza da tarefa: "
        "manteve-se elevada na síntese de SQL (0,8524 em 4x, com 100% de retenção de entidades) e apresentou ganho de sinal-ruído na auditoria LGPD (subindo de 0,7916 no baseline para 0,8279 em 4x), mas recuou a 0,7912 no Caso 1 pela sensibilidade de modelos de 11B parâmetros à poda de conectivos causais. "
        "Em projeção financeira parametrizada para 100.000 requisições, estima-se redução de 56,2% no custo de entrada e de 12,8% no custo global (de US$ 505,20 para US$ 440,50).",
        space_after=10, line_spacing=1.22, first_line_indent=Cm(0)
    )

    add_p("Compressão de Prompts. TokLang. Modelos de Linguagem de Grande Escala. Engenharia de Prompt. Green AI. BERTScore Proxy. NVIDIA NIM.",
          bold_prefix="Palavras-chave: ", line_spacing=1.22, first_line_indent=Cm(0))

    # =========================================================================
    # 3. ABSTRACT (Página 3)
    # =========================================================================
    doc.add_page_break()
    p_abs_title = doc.add_paragraph()
    p_abs_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs_title.paragraph_format.space_before = Pt(12)
    p_abs_title.paragraph_format.space_after = Pt(12)
    r = p_abs_title.add_run("ABSTRACT")
    r.font.name = "Arial"
    r.font.size = Pt(12)
    r.font.bold = True

    add_p(
        "Inference in Large Language Models (LLMs) imposes a substantial computational burden on modern infrastructure, as inner product "
        "calculations in the Transformer self-attention mechanism scale quadratically O(n²) with input sequence length. This study investigates Claude Shannon's "
        "linguistic redundancy hypothesis applied to prompt engineering, evaluating to what extent algorithmic pruning of low-self-information tokens reduces input "
        "volume and computational overhead while preserving technical accuracy. We developed the deterministic TokLang compiler and the automated Battle IA experimental testbed covering three enterprise "
        "workloads: distributed systems consensus reasoning (Raft and CAP Theorem), analytical SQL query generation under 3NF relational DDL schemas, and LGPD data privacy auditing. "
        "Evaluating Meta Llama-3.2-11B-Vision-Instruct deployed on managed NVIDIA NIM Cloud (NVIDIA A100 SXM4 GPUs) via real-time SSE streaming, we benchmarked "
        "conventional baselines (Few-shot and Zero-shot) against TokLang / LLMLingua selective compression with domain token whitelisting at 2x and 4x nominal target ratios. "
        "Direct empirical API measurements confirm that 4x nominal compression reduces billed input token volume by up to 57.4% (averaging 56.2%, from 384.0 to 168.3 input tokens per request). "
        "From these empirical token counts, analytical complexity modeling estimates an average theoretical reduction of 80.7% in quadratic prefill self-attention FLOPs (81.8% in Case 2), serving as an indirect computational proxy for energy efficiency rather than direct hardware wattmeter telemetry. "
        "Measured Time-to-First-Token (TTFT) stabilized at 574.3 ± 54.3 ms under 4x compression (9.5% coefficient of variation versus 84.1% in Zero-shot), whereas total generation time remained subject to multi-tenant cloud decoding variance. "
        "Semantic retention — quantified via the composite BERTScore Proxy F1 estimator (integrating n-gram cosine similarity, strict domain entity retention, and ROUGE-L against a 0.80 threshold) — proved task-dependent: "
        "remaining robust in SQL generation (0.8524 at 4x with 100% entity retention) and exhibiting signal-to-noise gains in LGPD auditing (rising from 0.7916 to 0.8279 at 4x), while dipping to 0.7912 in Case 1 due to causal connective sensitivity in an 11B-parameter model. "
        "In a parameterized financial projection across 100,000 requests, the technique is estimated to reduce input expenditure by 56.2% and total batch cost by 12.8% (from US$ 505.20 to US$ 440.50).",
        space_after=10, line_spacing=1.22, first_line_indent=Cm(0)
    )

    add_p("Prompt Compression. TokLang. Large Language Models. Prompt Engineering. Green AI. BERTScore Proxy. NVIDIA NIM.",
          bold_prefix="Keywords: ", line_spacing=1.22, first_line_indent=Cm(0))

    # =========================================================================
    # 4. SUMÁRIO (Página 4)
    # =========================================================================
    doc.add_page_break()
    p_sum_title = doc.add_paragraph()
    p_sum_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sum_title.paragraph_format.space_before = Pt(12)
    p_sum_title.paragraph_format.space_after = Pt(10)
    r = p_sum_title.add_run("SUMÁRIO")
    r.font.name = "Arial"
    r.font.size = Pt(12)
    r.font.bold = True

    toc_items = [
        ("1 INTRODUÇÃO", 1),
        ("1.1 Contextualização, Motivação e Problema de Pesquisa", 2),
        ("1.2 Objetivos", 2),
        ("1.3 Justificativa e Relevância", 2),
        ("1.4 Protocolo Metodológico da Revisão da Literatura", 2),
        ("2 FUNDAMENTOS DOS MODELOS DE LINGUAGEM DE GRANDE ESCALA", 1),
        ("2.1 Evolução Histórica", 2),
        ("2.2 Arquitetura Transformer e Mecanismo de Atenção", 2),
        ("2.3 Tokenização e Janela de Contexto", 2),
        ("3 ENGENHARIA DE PROMPT", 1),
        ("3.1 Principais Técnicas", 2),
        ("3.2 Relação entre Estrutura do Prompt e Qualidade da Resposta", 2),
        ("4 TEORIA DA INFORMAÇÃO E REDUNDÂNCIA LINGUÍSTICA", 1),
        ("4.1 Entropia de Shannon e Linguagem Natural", 2),
        ("4.2 Perplexidade e Autoinformação como Critérios de Poda", 2),
        ("5 IMPACTO COMPUTACIONAL DOS TOKENS", 1),
        ("5.1 Complexidade Quadrática na Fase de Prefill versus Fase de Decoding", 2),
        ("5.2 Custos Financeiros em APIs Comerciais", 2),
        ("6 MÉTODOS DE COMPRESSÃO DE PROMPTS", 1),
        ("6.1 LLMLingua e LLMLingua-2", 2),
        ("6.2 LongLLMLingua", 2),
        ("6.3 Selective Context e AutoCompressor", 2),
        ("6.4 Análise Comparativa Crítica e Confrontação com o Compilador TokLang", 2),
        ("7 COMPRESSÃO EM SISTEMAS RAG", 1),
        ("8 AVALIAÇÃO SEMÂNTICA COM BERTSCORE E MÉTRICAS COMPOSTAS", 1),
        ("9 SUSTENTABILIDADE E GREEN AI", 1),
        ("10 RESULTADOS E DISCUSSÃO EXPERIMENTAL", 1),
        ("10.1 Metodologia Experimental, Algoritmo Reprodutível e Bancada", 2),
        ("10.2 Avaliação Empírica do Volume de Tokens e Taxas de Compressão", 2),
        ("10.3 Latência (TTFT vs. Tempo Total) e Variação Estatística em Nuvem", 2),
        ("10.4 Fidelidade Semântica e Composição da Métrica BERTScore Proxy F1", 2),
        ("10.5 Projeção Financeira e Estimativa Analítica de Eficiência (FLOPs)", 2),
        ("10.6 Diretrizes de Engenharia e Análise de Trade-offs", 2),
        ("11 CONCLUSÃO, LIMITAÇÕES E TRABALHOS FUTUROS", 1),
        ("REFERÊNCIAS", 1),
    ]

    page_map = sumario_page_map or {}

    for item, lvl in toc_items:
        pg_num = str(page_map.get(item, "5"))
        p_sum = doc.add_paragraph()
        p_sum.paragraph_format.tab_stops.add_tab_stop(Cm(16.0), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        p_sum.paragraph_format.space_before = Pt(1.0)
        p_sum.paragraph_format.space_after = Pt(1.0)
        p_sum.paragraph_format.line_spacing = 1.0
        p_sum.paragraph_format.first_line_indent = Cm(0)
        p_sum.paragraph_format.left_indent = Cm(0)

        r_item = p_sum.add_run(f"{item}\t{pg_num}")
        r_item.font.name = "Arial"
        r_item.font.size = Pt(9.5)
        r_item.font.bold = (lvl == 1)

    # =========================================================================
    # CORPO DO TEXTO (CAPÍTULOS 1 A 9 COM QUADRO COMPARATIVO NO CAPÍTULO 6.4)
    # =========================================================================
    doc.add_page_break()

    structured_json_path = Path(__file__).parent / "structured_ch1_9_v2_extra.json"
    with open(structured_json_path, "r", encoding="utf-8") as f:
        structured_data = json.load(f)

    for elem in structured_data:
        etype = elem["type"]
        etext = elem["text"]
        if etype == "h1" and (etext.startswith("10 ") or etext.startswith("11 ")):
            break
        if etype == "h1":
            add_h1(etext, page_break_before=False)
        elif etype == "h2":
            add_h2(etext)
        elif etype == "bullet":
            p_b = add_p(etext, first_line_indent=Cm(-0.45))
            p_b.paragraph_format.left_indent = Cm(1.25)
        else:
            add_p(etext)
            # Injeta o Quadro 1 Comparativo da Literatura logo após o fechamento da Seção 6.4 (Quesitos 4 e 5)
            if "conforme sintetizado comparativamente na Tabela 1 do Capítulo 10" in etext or "garante retenção de 100% dos operadores críticos protegidos" in etext:
                add_table_title("Quadro 1 – Matriz comparativa entre os métodos de compressão da literatura e o compilador experimental TokLang")
                headers_q1 = [
                    "Método / Autor",
                    "Critério Matemático de Poda",
                    "Granularidade",
                    "Requer GPU / Pesos Alvo?",
                    "Compatível API Fechada?",
                    "Vantagens e Limitações Confrontadas"
                ]
                data_q1 = [
                    [
                        "LLMLingua\n(Jiang et al., 2023)",
                        "Perplexidade condicional via SLM auxiliar (Llama-7B / GPT-2)",
                        "Grossa (demos) e Fina (tokens)",
                        "Requer GPU p/ SLM auxiliar (sem pesos do alvo)",
                        "Sim",
                        "Comprime até 20x em prompts longos, mas adiciona latência de SLM e pode podar sintaxe SQL sem whitelist."
                    ],
                    [
                        "LLMLingua-2\n(Pan et al., 2024)",
                        "Classificação binária supervisionada (XLM-RoBERTa destilado)",
                        "Fina (nível de token)",
                        "Requer inferência neural do classificador",
                        "Sim",
                        "3x a 6x mais veloz que LLMLingua, porém sensível a domínios fora da distribuição de treino (DDL/LGPD)."
                    ],
                    [
                        "LongLLMLingua\n(Jiang et al., 2024)",
                        "Perplexidade contrastiva condicionada à pergunta do usuário",
                        "Documento (RAG) e Token",
                        "Requer GPU p/ SLM auxiliar",
                        "Sim",
                        "Mitiga Lost-in-the-Middle e eleva sinal-ruído em RAG (>10k tokens); ganho menor em instruções curtas."
                    ],
                    [
                        "Selective Context\n(Li et al., 2023)",
                        "Autoinformação de Shannon agregada em sintagmas",
                        "Frases e sintagmas nominais",
                        "Modelo causal base local",
                        "Sim",
                        "Mantém legibilidade humana superior, mas o corte de sintagmas inteiros pode remover cláusulas críticas."
                    ],
                    [
                        "AutoCompressor\n(Chevalier et al., 2023)",
                        "Condensação em vetores latentes contínuos (soft prompts)",
                        "Representação latente densa",
                        "Sim (Exige fine-tuning e pesos do LLM alvo)",
                        "Não (Inviável em API black-box)",
                        "Alta retenção semântica abstrata, mas inaplicável a serviços gerenciados como NVIDIA NIM ou OpenAI."
                    ],
                    [
                        "TokLang / ShannonCompressor\n(Autores, 2026)",
                        "Autoinformação I(w) = -log₂P(w) + Bônus morfológico + Token Whitelisting",
                        "Fina com blindagem léxica de domínio",
                        "Não (100% CPU determinístico, O(n) < 1 ms)",
                        "Sim",
                        "Zero overhead de GPU auxiliar e 100% de retenção em SQL; em modelos 11B, poda 4x afeta conectivos causais (Caso 1)."
                    ]
                ]
                col_w_q1 = [Cm(3.0), Cm(3.2), Cm(2.3), Cm(2.4), Cm(2.0), Cm(4.6)]
                tq1 = doc.add_table(rows=1, cols=6)
                format_abnt_table(tq1, col_w_q1, headers_q1, data_q1)
                add_table_source("Fonte: Elaborado pelos autores a partir da revisão comparativa da literatura (2026).")

    # =========================================================================
    # CAPÍTULO 10: RESULTADOS E DISCUSSÃO EXPERIMENTAL (100% AUDITADO POS-BANCA)
    # =========================================================================
    add_h1("10 RESULTADOS E DISCUSSÃO EXPERIMENTAL", page_break_before=False)

    add_h2("10.1 Metodologia Experimental, Algoritmo Reprodutível e Bancada")
    add_p(
        "Para validar empiricamente os pressupostos teóricos sem recorrer a simulações sintéticas, "
        "desenvolvemos o compilador determinístico TokLang e a bancada experimental automatizada Battle IA, "
        "cujo código-fonte integral, scripts de auditoria e registros brutos de telemetria encontram-se "
        "publicamente disponíveis para verificação e reprodução científica no repositório oficial do projeto "
        "(https://github.com/Taiwansz/TCC-CIENCIAS-DA-COMPUTACAO-2026; Santos et al., 2026). "
        "A infraestrutura realiza chamadas HTTP reais em regime de streaming contínuo via Server-Sent Events (SSE) "
        "contra o endpoint corporativo NVIDIA NIM Cloud (integrate.api.nvidia.com; NVIDIA Corporation, 2024), "
        "executando o modelo fundacional Meta Llama-3.2-11B-Vision-Instruct (identificador meta/llama-3.2-11b-vision-instruct; Dubey et al., 2024) "
        "alocado em aceleradores NVIDIA A100 SXM4. Para controle estrito de variáveis, todas as chamadas operaram com "
        "system prompt invariante ('Você é um especialista acadêmico sênior em Ciência da Computação...'), "
        "temperatura fixada em 0,1 (reduzindo variância estocástica de amostragem), teto padronizado de 260 tokens "
        "de saída (max_tokens = 260) e flag stream_options.include_usage = True ativada."
    )
    add_p(
        "Para assegurar reprodutibilidade algorítmica completa (atendendo aos critérios de engenharia experimental), "
        "o motor ShannonPromptCompressor integrado ao TokLang executa a compressão em quatro etapas matemáticas determinísticas "
        "sobre a sequência de tokens W = (w₁, w₂, ..., w_N) extraída pela expressão regular [\\wºª\\-\\.]+|[^\\w\\s]: "
        "(1) Proteção Lexical Estrita (Token Whitelisting): vocábulos pertencentes ao conjunto de 39 identificadores críticos de domínio "
        "(incluindo operadores SQL como SELECT, WITH, CTE, DENSE_RANK, OVER, JOIN, GROUP BY; conceitos distribuídos como raft, split-brain, "
        "quórum, linearizável, cap, cp, leasing; e termos normativos como lgpd, artigo, 7º, 11º, legítimo, interesse, sensível, biometria) "
        "recebem pontuação invariante S(w_i) = 100,0, garantindo imunidade absoluta ao descarte; "
        "(2) Penalização de Conectivos Funcionais: tokens contidos no dicionário de 55 preposições, artigos e conjunções acessórias "
        "têm sua probabilidade empírica P(w_i) = freq(w_i)/N escalonada pelo fator 3,5 (limitada a 0,99) e sua autoinformação atenuada por 0,15, "
        "resultando em S(w_i) = -0,15 · log₂(min(0,99, 3,5 · P(w_i))); "
        "(3) Autoinformação de Shannon com Bônus Morfológico: os demais tokens são avaliados pela equação canônica I(w_i) = -log₂(max(P(w_i), 10⁻⁶)), "
        "recebendo um incremento morfológico Δ = +1,8 sempre que o comprimento lexical exceder 7 caracteres (|w_i| > 7), privilegiando termos técnicos densos; e "
        "(4) Seleção por Orçamento (Token Budget): dado o fator nominal de compressão r ∈ {2,0; 4,0}, define-se o orçamento alvo B = max(20, ⌊N / r⌋), "
        "retendo-se os B índices de maior pontuação S(w_i) em união com todos os tokens protegidos (S(w_i) ≥ 90,0) e remontando o prompt em sua ordem sintática original."
    )
    add_p("Os ensaios abrangeram três cargas de trabalho representativas da Ciência da Computação, avaliadas sob quatro configurações (Few-shot Baseline, Zero-shot, TokLang/LLMLingua 2x e TokLang/LLMLingua 4x):")

    c1_few = by_key[("caso_1", "Few-shot (Baseline)")]["tokens_entrada"]
    c1_zero = by_key[("caso_1", "Zero-shot")]["tokens_entrada"]
    c2_few = by_key[("caso_2", "Few-shot (Baseline)")]["tokens_entrada"]
    c2_zero = by_key[("caso_2", "Zero-shot")]["tokens_entrada"]
    c3_few = by_key[("caso_3", "Few-shot (Baseline)")]["tokens_entrada"]
    c3_zero = by_key[("caso_3", "Zero-shot")]["tokens_entrada"]

    add_p(
        f"1. Caso 1 — Raciocínio em Sistemas Distribuídos e Concorrência: Análise de particionamento de rede "
        f"em cluster Raft de 5 nós (partição A com 2 nós e partição B com 3 nós, latência de 250 ms) sob o Teorema CAP, "
        f"prevenção de split-brain via quórum de maioria (N/2 + 1) e linearizabilidade por leasing de liderança "
        f"({c1_few} tokens faturados no Few-shot e {c1_zero} no Zero-shot; entidades obrigatórias auditadas: "
        f"raft, split-brain, quórum, maioria, linearizável, consistência, partição, cap, cp);"
    )
    add_p(
        f"2. Caso 2 — Engenharia de Dados e Geração de Consultas SQL sob Esquemas DDL: Mapeamento de esquema "
        f"relacional em Terceira Forma Normal (3FN) com as tabelas clientes, pedidos, itens_pedido e faturas, "
        f"exigindo consulta ANSI SQL com Common Table Expression (WITH / CTE) e função de janela DENSE_RANK() "
        f"({c2_few} tokens faturados no Few-shot e {c2_zero} no Zero-shot; entidades obrigatórias auditadas: "
        f"with, dense_rank, over, sum, join, clientes, pedidos, itens_pedido, group by);"
    )
    add_p(
        f"3. Caso 3 — Governança e Auditoria de Conformidade com a LGPD: Parecer técnico-jurídico sob a Lei "
        f"nº 13.709/2018 contrastando coleta de telemetria comportamental via Legítimo Interesse (Art. 7º, IX) "
        f"e captura biométrica facial enquadrada como Dado Pessoal Sensível (Art. 5º, II e Art. 11º) "
        f"({c3_few} tokens faturados no Few-shot e {c3_zero} no Zero-shot; entidades obrigatórias auditadas: "
        f"lgpd, artigo 7, artigo 11, legítimo interesse, sensível, biometria, consentimento, titular)."
    )

    add_h2("10.2 Avaliação Empírica do Volume de Tokens e Taxas de Compressão")
    add_p(
        "A contabilização de tokens foi extraída diretamente do manifesto oficial usage retornado pelo servidor "
        "NVIDIA NIM (prompt_tokens, completion_tokens e total_tokens), constituindo medição empírica direta e não estimativa local. "
        "A Tabela 1 apresenta o consumo exato faturado em cada configuração e a respectiva redução percentual frente à linha de base Few-shot."
    )

    add_table_title("Tabela 1 – [Medição Empírica via API] Consumo real de tokens faturados na NVIDIA NIM e taxas efetivas de compressão")
    headers_t1 = ["Caso de Uso", "Técnica de Prompting", "Tokens Entrada (Medido)", "Tokens Saída (Medido)", "Razão Efetiva", "Redução Entrada (%)"]

    def fmt_tec(tec: str, short_baseline: bool = True) -> str:
        if tec == "Few-shot (Baseline)":
            return "Few-shot" if short_baseline else "Few-shot (Baseline)"
        if tec == "LLMLingua (2x)":
            return "TokLang / LLMLingua (2x)"
        if tec == "LLMLingua (4x)":
            return "TokLang / LLMLingua (4x)"
        return tec

    casos_meta = [
        ("caso_1", "Caso 1: Sistemas Distribuídos"),
        ("caso_2", "Caso 2: SQL sob DDL"),
        ("caso_3", "Caso 3: Auditoria LGPD"),
    ]
    tecnicas_ordem_t1 = ["Few-shot (Baseline)", "Zero-shot", "LLMLingua (2x)", "LLMLingua (4x)"]

    data_t1 = []
    for cid, c_label in casos_meta:
        base_in = by_key[(cid, "Few-shot (Baseline)")]["tokens_entrada"]
        for tec in tecnicas_ordem_t1:
            rec = by_key[(cid, tec)]
            t_in = rec["tokens_entrada"]
            t_out = rec["tokens_saida"]
            razao = base_in / t_in
            if tec == "Few-shot (Baseline)":
                razao_str = "1,00x (Ref)"
                red_str = "Baseline (0,0%)"
            else:
                red_pct = ((t_in - base_in) / base_in) * 100.0
                razao_str = f"{fmt_br(razao, 2)}x"
                red_str = f"{fmt_br(red_pct, 1)}%"
            data_t1.append([c_label, fmt_tec(tec), str(t_in), str(t_out), razao_str, red_str])

    col_w_t1 = [Cm(4.5), Cm(3.4), Cm(2.2), Cm(2.1), Cm(2.3), Cm(2.5)]
    t1 = doc.add_table(rows=1, cols=6)
    format_abnt_table(t1, col_w_t1, headers_t1, data_t1)
    add_table_source("Fonte: Medições empíricas extraídas do manifesto usage da API NVIDIA NIM Cloud (2026).")

    add_p(
        "A Figura 10.1 reproduz graficamente as medições empíricas da Tabela 1, evidenciando o degrau de redução "
        "no volume de tokens de entrada processados pelo modelo Meta Llama-3.2-11B-Vision-Instruct."
    )

    add_figure(
        figs_dir / "figura_10_1_volume_tokens.png",
        "Figura 10.1 – [Medição Empírica] Consumo real de tokens de entrada por técnica de prompting nos três cenários avaliados"
    )

    add_p(
        "Confrontando nossos resultados empíricos com os números teóricos reportados por Jiang et al. (2023) e Pan et al. (2024), "
        "emerge uma constatação de engenharia fundamental: enquanto a literatura avalia prompts massivos (>2.000 tokens) nos quais "
        "o fator nominal de 4x se aproxima da razão faturada, em instruções corporativas de médio porte (340 a 434 tokens) as taxas nominais "
        "de 2x e 4x convertem-se em razões efetivas faturadas de 1,63x a 1,65x (para 2x) e de 2,21x a 2,35x (para 4x frente ao baseline Few-shot). "
        "Essa diferença ocorre por dois motivos estruturais: (a) a requisição real contabilizada em prompt_tokens pela API inclui o system prompt "
        "invariante e os tokens especiais de controle do template de chat do Llama-3.2 (<|begin_of_text|>, <|start_header_id|>, <|eot_id|>), que não sofrem poda; e "
        "(b) a união obrigatória com os tokens blindados pela whitelist preserva integralmente as cláusulas SQL e artigos da LGPD mesmo quando o orçamento nominal B é atingido. "
        "Ainda assim, a compressão de 4x eliminou empiricamente 56,2% dos tokens de entrada no Caso 1 (de 340 para 149 tokens), "
        "57,4% no Caso 2 (de 434 para 185 tokens) e 54,8% no Caso 3 (de 378 para 171 tokens)."
    )

    add_h2("10.3 Latência (TTFT vs. Tempo Total) e Variação Estatística em Nuvem")
    add_p(
        "Em arquiteturas de inferência baseadas em streaming SSE, o desempenho temporal divide-se em duas grandezas fisicamente distintas: "
        "o Time-to-First-Token (TTFT, em milissegundos), que mede a latência inicial desde o envio da requisição HTTP até a chegada do primeiro "
        "token gerado (refletindo o custo de rede, fila e processamento paralelo O(n²) do prompt na fase de prefill), e o Tempo Total de inferência "
        "(em segundos), que contabiliza a duração completa até o encerramento dos 260 tokens de saída (fase de decoding autoregressivo). "
        "Para atender ao rigor de análise de dispersão estatística, a Tabela 2 apresenta tanto as medições individuais por cenário quanto "
        "os indicadores estatísticos consolidados por técnica: Média amostral (μ), Desvio-Padrão amostral (s) e Coeficiente de Variação (CV = s/μ)."
    )

    add_table_title("Tabela 2 – [Medição Empírica e Dispersão Estatística] Latência inicial (TTFT), Tempo Total de inferência, Média (μ), Desvio-Padrão (s) e Coeficiente de Variação (CV%)")
    headers_t2 = ["Caso de Uso / Estatística", "Técnica", "TTFT (ms)", "Tempo Total (s)", "Var. TTFT vs Few-shot", "Var. TTFT vs Zero-shot"]

    data_t2 = []
    for cid, c_label in casos_meta:
        base_ttft = by_key[(cid, "Few-shot (Baseline)")]["ttft_ms"]
        zero_ttft = by_key[(cid, "Zero-shot")]["ttft_ms"]
        for tec in tecnicas_ordem_t1:
            rec = by_key[(cid, tec)]
            ttft = rec["ttft_ms"]
            t_tot = rec["tempo_total_s"]
            if tec == "Few-shot (Baseline)":
                var_few = "Baseline (0,0%)"
            else:
                diff_few = ((ttft - base_ttft) / base_ttft) * 100.0
                sinal = "+" if diff_few > 0 else ""
                var_few = f"{sinal}{fmt_br(diff_few, 1)}%"

            if tec == "Zero-shot":
                var_zero = "Ref. Zero-shot"
            else:
                diff_zero = ((ttft - zero_ttft) / zero_ttft) * 100.0
                sinal_z = "+" if diff_zero > 0 else ""
                var_zero = f"{sinal_z}{fmt_br(diff_zero, 1)}%"

            data_t2.append([
                c_label,
                fmt_tec(tec),
                fmt_br(ttft, 1),
                fmt_br(t_tot, 2),
                var_few,
                var_zero
            ])

    # Cálculo programático de Média, Desvio-Padrão e Coeficiente de Variação por Técnica (Quesitos 7, 8 e 9)
    cids_all = ["caso_1", "caso_2", "caso_3"]
    base_mean_ttft, _, _ = calc_mean_std([by_key[(c, "Few-shot (Baseline)")]["ttft_ms"] for c in cids_all])
    zero_mean_ttft, _, _ = calc_mean_std([by_key[(c, "Zero-shot")]["ttft_ms"] for c in cids_all])

    for tec in tecnicas_ordem_t1:
        ttft_vals = [by_key[(c, tec)]["ttft_ms"] for c in cids_all]
        tot_vals = [by_key[(c, tec)]["tempo_total_s"] for c in cids_all]
        m_ttft, s_ttft, cv_ttft = calc_mean_std(ttft_vals)
        m_tot, s_tot, cv_tot = calc_mean_std(tot_vals)

        if tec == "Few-shot (Baseline)":
            vf_str = f"CV = {fmt_br(cv_ttft, 1)}%"
        else:
            df = ((m_ttft - base_mean_ttft) / base_mean_ttft) * 100.0
            sinal = "+" if df > 0 else ""
            vf_str = f"{sinal}{fmt_br(df, 1)}% (CV {fmt_br(cv_ttft, 1)}%)"

        if tec == "Zero-shot":
            vz_str = f"CV = {fmt_br(cv_ttft, 1)}%"
        else:
            dz = ((m_ttft - zero_mean_ttft) / zero_mean_ttft) * 100.0
            sinal_z = "+" if dz > 0 else ""
            vz_str = f"{sinal_z}{fmt_br(dz, 1)}%"

        data_t2.append([
            "Estatística Consolidada (μ ± s)",
            fmt_tec(tec),
            f"{fmt_br(m_ttft, 1)} ± {fmt_br(s_ttft, 1)}",
            f"{fmt_br(m_tot, 2)} ± {fmt_br(s_tot, 2)}",
            vf_str,
            vz_str
        ])

    col_w_t2 = [Cm(4.5), Cm(3.1), Cm(2.4), Cm(2.3), Cm(2.5), Cm(2.2)]
    t2 = doc.add_table(rows=1, cols=6)
    format_abnt_table(t2, col_w_t2, headers_t2, data_t2)
    add_table_source("Fonte: Medições cronométricas via SSE streaming e consolidação estatística (μ ± s) pelos autores (2026).")

    add_p(
        "A Figura 10.2 ilustra o comportamento do TTFT nos doze ensaios realizados sobre o cluster NVIDIA A100 SXM4."
    )

    add_figure(
        figs_dir / "figura_10_2_latencia_ttft.png",
        "Figura 10.2 – [Medição Empírica] Comportamento real do Time-to-First-Token (TTFT em ms) sob diferentes técnicas de prompting"
    )

    add_p(
        "A análise estatística da Tabela 2 revela dois fenômenos cruciais de arquitetura de sistemas que exigem interpretação rigorosa. "
        "Em primeiro lugar, no que tange à latência inicial (TTFT), a compressão de 4x obteve a menor média global (574,3 ms) e a menor dispersão "
        "estatística entre todos os cenários avaliados, com desvio-padrão de apenas ± 54,3 ms e coeficiente de variação (CV) de 9,5%, "
        "contra 614,9 ± 85,8 ms no Few-shot (CV = 13,9%), 956,8 ± 368,5 ms na compressão de 2x (CV = 38,5%) e 2.329,4 ± 1.957,9 ms no Zero-shot (CV = 84,1%). "
        "Em um ambiente de nuvem multi-inquilino (multi-tenant cloud), onde TTFT = T_rede + T_fila + T_prefill, requisições sem compressão "
        "sofreram picos agudos de enfileiramento (notadamente 2.032,7 ms no Zero-shot do Caso 2 e 4.418,7 ms no Caso 3), ao passo que prompts compactos "
        "(149 a 185 tokens em 4x) demandam blocos contíguos menores de memória KV-Cache, facilitando o encaixe imediato no escalonador da GPU."
    )
    add_p(
        "Em segundo lugar, é fundamental explicar tecnicamente por que a redução e estabilização do TTFT não implica necessariamente redução "
        "do Tempo Total de resposta (T_total), fenômeno visível de forma emblemática no Caso 1: sob compressão de 4x, o TTFT caiu 8,1% frente ao "
        "Few-shot (de 585,2 ms para 538,0 ms), mas o Tempo Total de conclusão do streaming passou de 7,05 s (no Few-shot) para 17,96 s (na compressão 4x), "
        "elevando a média de tempo total da técnica 4x para 12,50 ± 5,67 s. A causa física reside no desacoplamento entre a fase de prefill e a fase de decoding: "
        "como o orçamento de saída foi travado em exatamente 260 tokens (completion_tokens = 260 em ambas as rodadas), o tempo total responde à equação "
        "T_total = TTFT + ∑(ITL_k), onde ITL_k é a latência inter-token (Inter-Token Latency) de cada um dos 260 passos autoregressivos de geração. "
        "Enquanto a compressão do prompt otimiza exclusivamente o prefill (governado pelos tokens de entrada e concluído nos primeiros 538,0 ms), "
        "os 17,42 segundos restantes no Caso 1 (4x) ocorreram durante a geração dos 260 tokens de saída, na qual a vazão do servidor NVIDIA NIM oscilou "
        "de 36,9 tokens/s (no Few-shot) para 14,5 tokens/s devido ao compartilhamento dinâmico de fatias de tempo (continuous batching throttling) entre "
        "múltiplos usuários concorrentes na nuvem. Registra-se, portanto, como limitação metodológica deste estudo que ensaios em nuvem pública sem reserva "
        "de nó dedicado (bare-metal isolation) estão sujeitos a variância exógena na fase de decoding, exigindo em trabalhos futuros baterias multi-amostrais "
        "(ex.: N ≥ 30 repetições por ponto em janelas horárias distintas) para isolar o jitter de rede da latência intrínseca de hardware."
    )

    add_h2("10.4 Fidelidade Semântica e Composição da Métrica BERTScore Proxy F1")
    add_p(
        "Para avaliar objetivamente a preservação de conteúdo técnico após a poda lexical, todas as respostas recebidas da API foram "
        "submetidas ao motor determinístico SemanticFidelityEvaluator (implementado em benchmark/battle_ia_benchmark.py; Santos et al., 2026). "
        "Cumpre esclarecer explicitamente a distinção metodológica entre o BERTScore neural convencional (Zhang et al., 2020) e a métrica denominada "
        "neste trabalho como BERTScore Proxy F1. Enquanto o BERTScore convencional extrai embeddings densos de camadas intermediárias de um modelo BERT/RoBERTa, "
        "testes preliminares revelaram que embeddings genéricos atribuem pontuações artificialmente altas (> 0,90) mesmo quando o LLM omite operadores "
        "sintáticos inegociáveis (como substituir DENSE_RANK() por ROW_NUMBER() em SQL ou omitir o Artigo 11º na auditoria da LGPD). "
        "Para eliminar esse ponto cego e assegurar reprodutibilidade determinística sem dependência de pesos externos de avaliação, "
        "o BERTScore Proxy F1 foi formulado como uma combinação linear ponderada de três indicadores complementares auditados sobre o texto gerado Y e o gabarito de referência Y*:"
    )
    add_p(
        "1. Similaridade Cossenoidal de N-gramas Ponderados (CosSim, peso w₁ = 0,50): Constrói-se a representação vetorial esparsa v(Y) e v(Y*) "
        "contabilizando unigramas com peso unitário (1,0) e bigramas contíguos com peso reforçado (1,6) para capturar preservação de expressões compostas "
        "(como 'legítimo interesse', 'consistência linearizável' e 'group by'), calculando-se o cosseno do ângulo entre os vetores: CosSim = (v(Y) · v(Y*)) / (||v(Y)|| · ||v(Y*)||);"
    )
    add_p(
        "2. Taxa Estrita de Retenção de Entidades de Domínio (Ret_Ent, peso w₂ = 0,35): Mede a proporção exata de presença das entidades técnicas "
        "obrigatórias E_obrig definidas para cada caso de uso na Seção 10.1: Ret_Ent = |{e ∈ E_obrig : e ∈ Y}| / |E_obrig|;"
    )
    add_p(
        "3. Índice ROUGE-L F1 de Subsequência Comum Mais Longa (peso w₃ = 0,15): Calculado via programação dinâmica O(m·n) (Lin, 2004) para medir "
        "a coerência de ordenação estrutural entre a resposta gerada e o gabarito: S_base = 0,50 · CosSim + 0,35 · Ret_Ent + 0,15 · ROUGE-L_F1. "
        "Por fim, aplica-se a transformação de calibração afim BERTScore_Proxy_F1 = min(0,985, max(0,60, 0,70 + 0,28 · S_base)), que projeta o escore "
        "composto para o intervalo operacional [0,60; 0,985] equivalente à distribuição empírica do RoBERTa-large, mantendo o limiar crítico de aprovação em 0,80. "
        "A Tabela 3 apresenta os valores medidos de cada componente individual e o índice composto resultante."
    )

    add_table_title("Tabela 3 – [Medição Empírica sobre Respostas Geradas] Componentes de fidelidade semântica: Similaridade de Cosseno, ROUGE-L, Retenção de Entidades e BERTScore Proxy F1")
    headers_t3 = ["Caso de Uso", "Técnica / Taxa", "Cosine Sim.", "ROUGE-L", "Ret. Entidades", "BERTScore Proxy F1", "Status (≥ 0,80)"]

    data_t3 = []
    for cid, c_label in casos_meta:
        for tec in tecnicas_ordem_t1:
            rec = by_key[(cid, tec)]
            cos_v = rec["cosine_similarity"]
            rouge_v = rec["rouge_l_f1"]
            ent_v = rec["entity_retention"] * 100.0
            f1_v = rec["bertscore_proxy_f1"]
            if f1_v >= 0.85:
                status = "Excelente (≥ 0,85)"
            elif f1_v >= 0.80:
                status = "Aprovado (≥ 0,80)"
            else:
                status = "Atenção (< 0,80)"
            data_t3.append([
                c_label,
                fmt_tec(tec),
                fmt_br(cos_v, 4),
                fmt_br(rouge_v, 4),
                f"{fmt_br(ent_v, 1)}%",
                fmt_br(f1_v, 4),
                status
            ])

    col_w_t3 = [Cm(4.1), Cm(2.8), Cm(1.9), Cm(1.8), Cm(2.1), Cm(2.3), Cm(2.5)]
    t3 = doc.add_table(rows=1, cols=7)
    format_abnt_table(t3, col_w_t3, headers_t3, data_t3)
    add_table_source("Fonte: Avaliação determinística via SemanticFidelityEvaluator sobre outputs reais do Llama-3.2-11B (2026).")

    add_p(
        "A Figura 10.3 apresenta a curva de retenção semântica em função da taxa de compressão (1x Zero-shot, 2x e 4x), "
        "demarcando a linha horizontal do limiar crítico de aceitação (F1 = 0,80)."
    )

    add_figure(
        figs_dir / "figura_10_3_bertscore_f1.png",
        "Figura 10.3 – [Medição Empírica] Curva de retenção semântica (BERTScore Proxy F1) por razão de compressão e limiar crítico (0,80)"
    )

    add_p(
        "A comparação transversal dos três cenários na Tabela 3 comprova que a preservação da qualidade sob compressão de prompts "
        "depende diretamente da estrutura formal da tarefa submetida ao modelo. "
        "No Caso 2 (SQL sob DDL), o mecanismo de token whitelisting do TokLang preservou 100,0% das entidades obrigatórias em todas as configurações "
        "(incluindo os nomes das quatro tabelas e as cláusulas WITH, DENSE_RANK e OVER), sustentando BERTScore Proxy F1 na faixa de excelência tanto em 2x (0,8623) quanto em 4x (0,8524). "
        "No Caso 3 (Auditoria LGPD), observou-se o efeito de ganho de relação sinal-ruído fundamentado por Jiang et al. (2024) e Liu et al. (2024): "
        "enquanto os prompts longos (Few-shot com F1 de 0,7916 e Zero-shot com 0,7955) levaram o modelo a consumir parte dos 260 tokens de saída com "
        "introduções genéricas — retendo apenas 37,5% das entidades jurídicas antes do corte de geração —, os prompts comprimidos eliminaram a redundância "
        "e focalizaram a autoatenção diretamente nos dispositivos protegidos (Art. 7º, Art. 11º, dado sensível e biometria), elevando a retenção de entidades para "
        "50,0% (F1 = 0,8037 em 2x) e 75,0% (F1 = 0,8279 em 4x). "
        "Em contrapartida, no Caso 1 (Sistemas Distribuídos), o índice F1 recuou de 0,8105 (Few-shot) e 0,8115 (Zero-shot) para 0,7917 (2x) e 0,7912 (4x), "
        "situando-se marginalmente abaixo do limiar de 0,80 (-0,0088), com a retenção de entidades caindo de 66,7% para 44,4%. "
        "Esse resultado negativo no Caso 1 é cientificamente revelador: demonstra que, em modelos compactos de 11B parâmetros, tarefas de raciocínio "
        "teórico discursivo e multi-causal (como explicar simultaneamente quórum Raft, split-brain, Teorema CAP e leasing de relógio) sofrem perda de encadeamento "
        "lógico quando preposições e conectivos relacionais são podados agressivamente."
    )

    add_h2("10.5 Projeção Financeira e Estimativa Analítica de Eficiência (FLOPs)")
    add_p(
        "Em conformidade com o rigor metodológico, esta seção separa explicitamente as variáveis medidas das projeções teóricas derivadas. "
        "A partir das médias reais de tokens faturados nos três cenários (medidas na Tabela 1), realizaram-se duas extrapolações analíticas: "
        "(1) uma Projeção Financeira Parametrizada para um lote corporativo de 100.000 requisições sob tarifa de mercado de referência "
        "(US$ 3,00 por milhão de tokens de entrada e US$ 15,00 por milhão de tokens de saída, onde os 260 tokens fixos de saída representam US$ 390,00 invariantes por lote); e "
        "(2) uma Estimativa Teórica de Redução de FLOPs de Autoatenção no Prefill, computada pela fórmula analítica 1 - (T_comprimido / T_baseline)² "
        "derivada da complexidade quadrática O(n²) do mecanismo de atenção (Vaswani et al., 2017). "
        "Ressalta-se que os percentuais de FLOPs e seus reflexos em Green AI constituem estimativas computacionais indiretas baseadas na redução "
        "de operações algébricas de prefill, e não medições elétricas diretas de consumo em watts/joules nos sensores físicos da placa NVIDIA A100. "
        "A Tabela 4 sintetiza os valores medidos de base e as respectivas projeções analíticas."
    )

    add_table_title("Tabela 4 – [Projeção Analítica Derivada] Estimativa financeira para 100.000 requisições e redução teórica média de FLOPs de autoatenção O(n²) a partir dos tokens reais medidos")
    headers_t4 = [
        "Cenário / Técnica",
        "Tokens Entrada [Medido: Média → 100k]",
        "Custo Entrada [Projeção US$]",
        "Custo Total [Projeção US$]",
        "Economia Projetada (Entrada / Total)",
        "Redução FLOPs O(n²) [Estimativa Teórica]"
    ]

    cids = ["caso_1", "caso_2", "caso_3"]
    base_avg_in = sum(by_key[(c, "Few-shot (Baseline)")]["tokens_entrada"] for c in cids) / 3.0
    base_avg_cost_in = (base_avg_in * 100_000 / 1_000_000.0) * 3.00
    base_avg_cost_tot = sum(by_key[(c, "Few-shot (Baseline)")]["custo_total_100k_usd"] for c in cids) / 3.0

    data_t4 = []
    for idx_t, tec in enumerate(tecnicas_ordem_t1, start=1):
        avg_in = sum(by_key[(c, tec)]["tokens_entrada"] for c in cids) / 3.0
        vol_m = (avg_in * 100_000) / 1_000_000.0
        cost_in = vol_m * 3.00
        cost_tot = sum(by_key[(c, tec)]["custo_total_100k_usd"] for c in cids) / 3.0
        avg_flops = sum(by_key[(c, tec)]["reducao_flops_atencao_pct"] for c in cids) / 3.0

        if tec == "Few-shot (Baseline)":
            econ_str = "Baseline (0,0%)"
            flops_str = "0,0% (Ref)"
        else:
            ec_in_pct = ((cost_in - base_avg_cost_in) / base_avg_cost_in) * 100.0
            ec_tot_pct = ((cost_tot - base_avg_cost_tot) / base_avg_cost_tot) * 100.0
            econ_str = f"{fmt_br(ec_in_pct, 1)}% / {fmt_br(ec_tot_pct, 1)}%"
            flops_str = f"-{fmt_br(avg_flops, 1)}%"

        tec_label = fmt_tec(tec, short_baseline=False)
        data_t4.append([
            f"Cenário {idx_t}: {tec_label}",
            f"{fmt_br(avg_in, 1)} → {fmt_br(vol_m, 2)} M",
            f"US$ {fmt_br(cost_in, 2)}",
            f"US$ {fmt_br(cost_tot, 2)}",
            econ_str,
            flops_str
        ])

    col_w_t4 = [Cm(4.2), Cm(2.9), Cm(2.3), Cm(2.3), Cm(2.8), Cm(2.5)]
    t4 = doc.add_table(rows=1, cols=6)
    format_abnt_table(t4, col_w_t4, headers_t4, data_t4)
    add_table_source("Fonte: Projeções analíticas calculadas pelos autores a partir da contagem empírica de tokens na API NVIDIA NIM (2026).")

    add_p(
        "A Figura 10.4 confronta em eixo duplo o custo total médio projetado para 100.000 requisições "
        "(US$ 505,20 no Few-shot, US$ 482,80 no Zero-shot, US$ 460,30 no TokLang / LLMLingua 2x e US$ 440,50 no TokLang / LLMLingua 4x) "
        "com a estimativa teórica de redução percentual nos cálculos quadráticos de autoatenção durante a fase de prefill."
    )

    add_figure(
        figs_dir / "figura_10_4_custo_flops.png",
        "Figura 10.4 – [Projeção Analítica] Economia financeira estimada (100k requisições) e redução teórica média de FLOPs na autoatenção O(n²)"
    )

    add_p(
        "Os dados da Tabela 4 demonstram que a redução empírica média de 56,2% nos tokens de entrada sob TokLang / LLMLingua 4x "
        "(caindo de uma média medida de 384,0 para 168,3 tokens por chamada, ou de 38,40 milhões para 16,83 milhões de tokens em 100.000 requisições) "
        "projeta uma supressão teórica média de 80,7% nos FLOPs quadráticos de autoatenção do prefill (80,8% no Caso 1, 81,8% no Caso 2 e 79,5% no Caso 3). "
        "No plano financeiro, o dispêndio estimado com tokens de entrada cai exatamente na mesma proporção de 56,2% (de US$ 115,20 para US$ 50,50), "
        "resultando em economia líquida projetada de US$ 64,70 por lote (-12,8% sobre o custo global, visto que a componente de saída permanece fixa em US$ 390,00). "
        "Embora não substitua a telemetria física de wattímetros em hardware dedicado, a eliminação teórica de mais de 80% das operações de produto interno "
        "na matriz de autoatenção inicial constitui evidência analítica consistente de mitigação de esforço computacional sob os princípios de Green AI (Schwartz et al., 2020)."
    )

    add_h2("10.6 Diretrizes de Engenharia e Análise de Trade-offs")
    add_p(
        "A consolidação dos resultados experimentais permite estabelecer três diretrizes práticas para arquitetos de software: "
        "(1) obrigatoriedade de listas de proteção de vocabulário (token whitelisting) em tarefas formais como geração de SQL "
        "e análise normativa, garantindo 100% de preservação de operadores e cláusulas críticas com custo zero de GPU auxiliar; "
        "(2) adoção preferencial da taxa de 4x em tarefas de extração e auditoria regulatória (como LGPD), nas quais a remoção "
        "de verbosidade acessória atua como filtro de ruído e melhora a concentração semântica da resposta; e "
        "(3) restrição da poda agressiva sobre modelos compactos (porte de 8B a 11B parâmetros) em problemas "
        "de raciocínio causal encadeado (como algoritmos de consenso distribuído), nos quais se recomenda operar em taxas conservadoras (≤ 1,5x) "
        "ou incluir conectivos lógicos de causa e consequência na lista de proteção lexical."
    )

    # =========================================================================
    # CAPÍTULO 11: CONCLUSÃO, LIMITAÇÕES E TRABALHOS FUTUROS (Quesitos 9 e 10)
    # =========================================================================
    add_h1("11 CONCLUSÃO, LIMITAÇÕES E TRABALHOS FUTUROS", page_break_before=False)
    add_p(
        "Este trabalho investigou os fundamentos matemáticos e avaliou experimentalmente a compressão algorítmica de prompts "
        "baseada na autoinformação de Shannon como estratégia de otimização para Modelos de Linguagem de Grande Escala. "
        "Retomando diretamente a questão de pesquisa formulada na Introdução, os resultados empíricos obtidos na bancada Battle IA "
        "com o compilador determinístico TokLang e o modelo Meta Llama-3.2-11B-Vision-Instruct (via NVIDIA NIM Cloud) permitem "
        "responder de forma precisa e nuançada ao problema investigado: a compressão nominal de 4x combinada a token whitelisting "
        "reduz comprovadamente o volume faturado de tokens de entrada em 56,2% na média dos cenários (atingindo 57,4% no Caso 2) "
        "e estabiliza a latência inicial de prefill (TTFT) em 574,3 ± 54,3 ms (coeficiente de variação de 9,5%); contudo, a preservação "
        "da fidelidade semântica acima do limiar crítico de 0,80 não é universalmente agnóstica, mostrando-se estritamente dependente "
        "da natureza sintática e causal da tarefa."
    )
    add_p(
        "Especificamente, comprovou-se que a questão de pesquisa é respondida positivamente para domínios formais e normativos: "
        "na geração de consultas SQL analíticas sob esquemas DDL (Caso 2), a blindagem de palavras reservadas assegurou 100% de retenção "
        "de entidades e BERTScore Proxy F1 de 0,8524 sob poda de 4x; na auditoria jurídica da LGPD (Caso 3), a remoção de texto periférico "
        "elevou a relação sinal-ruído e fez a fidelidade evoluir de 0,7916 (Few-shot) para 0,8279 (4x). Em contrapartida, no raciocínio "
        "teórico sobre consenso distribuído Raft e Teorema CAP (Caso 1), o índice recuou para 0,7912 sob 4x, demonstrando que modelos "
        "compactos de 11B parâmetros ressentem-se da supressão de conectivos causais em explicações abstratas multi-etapas."
    )
    add_p(
        "Em respeito à transparência científica, destacam-se três limitações metodológicas deste estudo que delimitam a generalização "
        "de suas conclusões: (i) os ganhos de eficiência computacional (redução média de 80,7% nos FLOPs de autoatenção O(n²)) e de economia "
        "financeira (redução de 12,8% no custo total para 100.000 requisições) representam projeções analíticas derivadas da contagem empírica "
        "de tokens, e não medições físicas diretas de consumo elétrico em watts nas GPUs remotas; (ii) as medições de latência em nuvem "
        "multi-inquilino evidenciaram que a otimização do TTFT (fase de prefill) não impede oscilações exógenas no Tempo Total de resposta "
        "durante a fase de decoding autoregressivo dos 260 tokens de saída (como os 17,96 s registrados no Caso 1 em 4x); e (iii) o escopo "
        "empírico concentrou-se em um único modelo de 11B parâmetros e na métrica composta determinística BERTScore Proxy F1."
    )
    add_p(
        "Para trabalhos futuros, propõem-se quatro frentes diretas de expansão: "
        "(a) execução de baterias experimentais multi-amostrais (N ≥ 30 repetições por cenário com intervalos de confiança de 95%) "
        "comparando inferência em nuvem compartilhada versus execução local isolada com telemetria física de energia via NVML (nvidia-smi em joules/token); "
        "(b) avaliação cruzada da mesma suíte de prompts entre modelos de diferentes escalas de parâmetros (8B, 11B, 70B e 405B) para quantificar "
        "a resiliência à poda causal em função do porte do LLM; "
        "(c) comparação direta entre o estimador BERTScore Proxy F1, o BERTScore neural com pesos RoBERTa-large e avaliadores LLM-as-a-Judge; e "
        "(d) integração de poda adaptativa sensível a conectivos causais no compilador TokLang para arquiteturas RAG corporativas."
    )

    # =========================================================================
    # REFERÊNCIAS BIBLIOGRÁFICAS (27 REFERÊNCIAS AUDITADAS - ABNT NBR 6023)
    # =========================================================================
    add_h1("REFERÊNCIAS", page_break_before=True)

    referencias = [
        "BAHDANAU, Dzmitry; CHO, Kyunghyun; BENGIO, Yoshua. Neural machine translation by jointly learning to align and translate. In: INTERNATIONAL CONFERENCE ON LEARNING REPRESENTATIONS (ICLR), 3., 2015, San Diego. Proceedings [...]. San Diego: ICLR, 2015. p. 1–15. Disponível em: https://arxiv.org/abs/1409.0473. Acesso em: 23 nov. 2026.",
        "BROWN, Tom B. et al. Language models are few-shot learners. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS (NeurIPS), 33., 2020, San Diego (Virtual). Proceedings [...]. Red Hook: Curran Associates, 2020. v. 33, p. 1877–1901. Disponível em: https://proceedings.neurips.cc/paper/2020/hash/1457c0d6bfcb4967418bfb8ac142f64a-Abstract.html. Acesso em: 23 nov. 2026.",
        "CHEVALIER, Alexis et al. Adapting language models to compress contexts. In: CONFERENCE ON EMPIRICAL METHODS IN NATURAL LANGUAGE PROCESSING (EMNLP), 2023, Singapore. Proceedings [...]. Stroudsburg: Association for Computational Linguistics, 2023. p. 3829–3846. DOI: https://doi.org/10.18653/v1/2023.emnlp-main.232. Disponível em: https://aclanthology.org/2023.emnlp-main.232/. Acesso em: 23 nov. 2026.",
        "DEVLIN, Jacob et al. BERT: pre-training of deep bidirectional transformers for language understanding. In: CONFERENCE OF THE NORTH AMERICAN CHAPTER OF THE ASSOCIATION FOR COMPUTATIONAL LINGUISTICS: HUMAN LANGUAGE TECHNOLOGIES (NAACL-HLT), 2019, Minneapolis. Proceedings [...]. Stroudsburg: Association for Computational Linguistics, 2019. v. 1, p. 4171–4186. DOI: https://doi.org/10.18653/v1/N19-1423. Disponível em: https://aclanthology.org/N19-1423/. Acesso em: 23 nov. 2026.",
        "DUBEY, Abhimanyu; GRATTAFIORI, Aaron et al. The Llama 3 herd of models. arXiv preprint arXiv:2407.21783, 2024. DOI: https://doi.org/10.48550/arXiv.2407.21783. Disponível em: https://arxiv.org/abs/2407.21783. Acesso em: 23 nov. 2026.",
        "JIANG, Huiqiang et al. LLMLingua: compressing prompts for accelerated inference of large language models. In: CONFERENCE ON EMPIRICAL METHODS IN NATURAL LANGUAGE PROCESSING (EMNLP), 2023, Singapore. Proceedings [...]. Stroudsburg: Association for Computational Linguistics, 2023. p. 13358–13376. DOI: https://doi.org/10.18653/v1/2023.emnlp-main.825. Disponível em: https://aclanthology.org/2023.emnlp-main.825/. Acesso em: 23 nov. 2026.",
        "JIANG, Huiqiang et al. LongLLMLingua: accelerating and enhancing LLMs in long context scenarios via prompt compression. In: ANNUAL MEETING OF THE ASSOCIATION FOR COMPUTATIONAL LINGUISTICS (ACL), 62., 2024, Bangkok. Proceedings [...]. Stroudsburg: Association for Computational Linguistics, 2024. v. 1, p. 1658–1677. DOI: https://doi.org/10.18653/v1/2024.acl-long.91. Disponível em: https://aclanthology.org/2024.acl-long.91/. Acesso em: 23 nov. 2026.",
        "KOJIMA, Takeshi et al. Large language models are zero-shot reasoners. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS (NeurIPS), 35., 2022, New Orleans. Proceedings [...]. Red Hook: Curran Associates, 2022. v. 35, p. 22199–22213. Disponível em: https://proceedings.neurips.cc/paper_files/paper/2022/hash/8bb0d291acd4acf06ef112099c16f326-Abstract-Conference.html. Acesso em: 23 nov. 2026.",
        "LEWIS, Patrick et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS (NeurIPS), 33., 2020, San Diego (Virtual). Proceedings [...]. Red Hook: Curran Associates, 2020. v. 33, p. 9459–9474. Disponível em: https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html. Acesso em: 23 nov. 2026.",
        "LI, Yucheng et al. Compressing context to enhance inference efficiency of large language models. In: CONFERENCE ON EMPIRICAL METHODS IN NATURAL LANGUAGE PROCESSING (EMNLP), 2023, Singapore. Proceedings [...]. Stroudsburg: Association for Computational Linguistics, 2023. p. 6346–6365. DOI: https://doi.org/10.18653/v1/2023.emnlp-main.391. Disponível em: https://aclanthology.org/2023.emnlp-main.391/. Acesso em: 23 nov. 2026.",
        "LIN, Chin-Yew. ROUGE: a package for automatic evaluation of summaries. In: ACL WORKSHOP ON TEXT SUMMARIZATION BRANCHES OUT, 2004, Barcelona. Proceedings [...]. Stroudsburg: Association for Computational Linguistics, 2004. p. 74–81. Disponível em: https://aclanthology.org/W04-1013/. Acesso em: 23 nov. 2026.",
        "LIU, Nelson F. et al. Lost in the middle: how language models use long contexts. Transactions of the Association for Computational Linguistics (TACL), Cambridge, v. 12, p. 157–173, 2024. DOI: https://doi.org/10.1162/tacl_a_00638. Disponível em: https://aclanthology.org/2024.tacl-1.9/. Acesso em: 23 nov. 2026.",
        "LIU, Pengfei et al. Pre-train, prompt, and predict: a systematic survey of prompting methods in natural language processing. ACM Computing Surveys, New York, v. 55, n. 9, art. 195, p. 1–35, jan. 2023. DOI: https://doi.org/10.1145/3560815. Disponível em: https://dl.acm.org/doi/10.1145/3560815. Acesso em: 23 nov. 2026.",
        "LUCCIONI, Sasha; JERNITE, Yacine; STRUBELL, Emma. Power hungry processing: watts driving the cost of AI deployment? In: ACM CONFERENCE ON FAIRNESS, ACCOUNTABILITY, AND TRANSPARENCY (FAccT), 2024, Rio de Janeiro. Proceedings [...]. New York: ACM, 2024. p. 85–99. DOI: https://doi.org/10.1145/3630106.3658542. Disponível em: https://dl.acm.org/doi/10.1145/3630106.3658542. Acesso em: 23 nov. 2026.",
        "MIKOLOV, Tomas et al. Efficient estimation of word representations in vector space. In: INTERNATIONAL CONFERENCE ON LEARNING REPRESENTATIONS (ICLR) WORKSHOP TRACK, 1., 2013, Scottsdale. Proceedings [...]. Scottsdale: ICLR, 2013. p. 1–12. Disponível em: https://arxiv.org/abs/1301.3781. Acesso em: 23 nov. 2026.",
        "NVIDIA CORPORATION. NVIDIA NIM for Large Language Models (LLMs): deployment, continuous batching, and API reference (meta/llama-3.2-11b-vision-instruct). Santa Clara: NVIDIA Technical Documentation, 2024. Disponível em: https://docs.nvidia.com/nim/large-language-models/latest/index.html. Acesso em: 23 nov. 2026.",
        "PAN, Zhuoshi et al. LLMLingua-2: data distillation for efficient and faithful task-agnostic prompt compression. In: FINDINGS OF THE ASSOCIATION FOR COMPUTATIONAL LINGUISTICS: ACL 2024, 2024, Bangkok. Proceedings [...]. Stroudsburg: Association for Computational Linguistics, 2024. p. 949–967. DOI: https://doi.org/10.18653/v1/2024.findings-acl.57. Disponível em: https://aclanthology.org/2024.findings-acl.57/. Acesso em: 23 nov. 2026.",
        "PAPINENI, Kishore et al. BLEU: a method for automatic evaluation of machine translation. In: ANNUAL MEETING OF THE ASSOCIATION FOR COMPUTATIONAL LINGUISTICS (ACL), 40., 2002, Philadelphia. Proceedings [...]. Stroudsburg: Association for Computational Linguistics, 2002. p. 311–318. DOI: https://doi.org/10.3115/1073083.1073135. Disponível em: https://aclanthology.org/P02-1040/. Acesso em: 23 nov. 2026.",
        "PATTERSON, David et al. Carbon emissions and large neural network training. arXiv preprint arXiv:2104.10350, 2021. DOI: https://doi.org/10.48550/arXiv.2104.10350. Disponível em: https://arxiv.org/abs/2104.10350. Acesso em: 23 nov. 2026.",
        "PENNINGTON, Jeffrey; SOCHER, Richard; MANNING, Christopher D. GloVe: global vectors for word representation. In: CONFERENCE ON EMPIRICAL METHODS IN NATURAL LANGUAGE PROCESSING (EMNLP), 2014, Doha. Proceedings [...]. Stroudsburg: Association for Computational Linguistics, 2014. p. 1532–1543. DOI: https://doi.org/10.3115/v1/D14-1162. Disponível em: https://aclanthology.org/D14-1162/. Acesso em: 23 nov. 2026.",
        "SANTOS, Matheus Sousa dos; PINETE, Felipe Guarnieri; WEBER, Guilherme Gustavo; PEDRO, Juan. TokLang & Battle IA Benchmark: compilador determinístico de compressão de prompts baseado na entropia de Shannon e bancada experimental via NVIDIA NIM Cloud. Indaiatuba: GitHub Repository, 2026. Disponível em: https://github.com/Taiwansz/TCC-CIENCIAS-DA-COMPUTACAO-2026. Acesso em: 23 nov. 2026.",
        "SCHWARTZ, Roy et al. Green AI. Communications of the ACM, New York, v. 63, n. 12, p. 54–63, dez. 2020. DOI: https://doi.org/10.1145/3381831. Disponível em: https://dl.acm.org/doi/10.1145/3381831. Acesso em: 23 nov. 2026.",
        "SHANNON, Claude E. A mathematical theory of communication. The Bell System Technical Journal, Murray Hill, v. 27, n. 3, p. 379–423, jul. 1948; v. 27, n. 4, p. 623–656, out. 1948. DOI: https://doi.org/10.1002/j.1538-7305.1948.tb01338.x. Disponível em: https://archive.org/details/bstj27-3-379. Acesso em: 23 nov. 2026.",
        "STRUBELL, Emma; GANESH, Ananya; McCALLUM, Andrew. Energy and policy considerations for deep learning in NLP. In: ANNUAL MEETING OF THE ASSOCIATION FOR COMPUTATIONAL LINGUISTICS (ACL), 57., 2019, Florence. Proceedings [...]. Stroudsburg: Association for Computational Linguistics, 2019. p. 3645–3650. DOI: https://doi.org/10.18653/v1/P19-1355. Disponível em: https://aclanthology.org/P19-1355/. Acesso em: 23 nov. 2026.",
        "VASWANI, Ashish et al. Attention is all you need. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS (NeurIPS), 30., 2017, Long Beach. Proceedings [...]. Red Hook: Curran Associates, 2017. v. 30, p. 5998–6008. Disponível em: https://proceedings.neurips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html. Acesso em: 23 nov. 2026.",
        "WEI, Jason et al. Chain-of-thought prompting elicits reasoning in large language models. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS (NeurIPS), 35., 2022, New Orleans. Proceedings [...]. Red Hook: Curran Associates, 2022. v. 35, p. 24824–24837. Disponível em: https://proceedings.neurips.cc/paper_files/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4-Abstract-Conference.html. Acesso em: 23 nov. 2026.",
        "ZHANG, Tianyi et al. BERTScore: evaluating text generation with BERT. In: INTERNATIONAL CONFERENCE ON LEARNING REPRESENTATIONS (ICLR), 8., 2020, Addis Ababa. Proceedings [...]. Addis Ababa: ICLR, 2020. p. 1–43. Disponível em: https://openreview.net/forum?id=SkeHuCVFDr. Acesso em: 23 nov. 2026."
    ]

    for ref in referencias:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(4.5)
        p_ref.paragraph_format.line_spacing = 1.0
        p_ref.paragraph_format.first_line_indent = Cm(0)
        r = p_ref.add_run(ref)
        r.font.name = "Arial"
        r.font.size = Pt(9.5)

    docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(docx_path))
    print(f"[OK] DOCX EXTRA gerado em: {docx_path}")


def convert_to_pdf(docx_path: Path, pdf_path: Path):
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc = word.Documents.Open(str(docx_path.resolve()))
        doc.SaveAs2(str(pdf_path.resolve()), FileFormat=17)  # 17 = wdFormatPDF
        doc.Close()
    finally:
        word.Quit()

    if fitz is not None:
        pdf_doc = fitz.open(str(pdf_path))
        pdf_doc.set_metadata({
            "title": "Compressão Algorítmica de Prompts em Modelos de Linguagem de Grande Escala",
            "author": "",
            "subject": "Trabalho de Conclusão de Curso - Ciência da Computação",
            "keywords": "Compressão de Prompts, TokLang, LLMs, Green AI, BERTScore Proxy",
            "creator": "",
            "producer": "",
        })
        pdf_doc.del_xml_metadata()
        tmp_pdf = pdf_path.with_suffix(".clean.pdf")
        pdf_doc.save(str(tmp_pdf), garbage=4, deflate=True)
        pdf_doc.close()
        tmp_pdf.replace(pdf_path)

    print(f"[OK] PDF EXTRA compilado e anonimizado via Word COM: {pdf_path}")
    return True


def scan_heading_pages(pdf_path: Path):
    if fitz is not None:
        doc = fitz.open(pdf_path)
        pages_text = [p.get_text() for p in doc]
    else:
        reader = pypdf.PdfReader(str(pdf_path))
        pages_text = [p.extract_text() or "" for p in reader.pages]

    search_keys = [
        ("1 INTRODUÇÃO", "1 INTRODUÇÃO"),
        ("1.1 Contextualização, Motivação e Problema de Pesquisa", "1.1 Contextualização"),
        ("1.2 Objetivos", "1.2 Objetivos"),
        ("1.3 Justificativa e Relevância", "1.3 Justificativa"),
        ("1.4 Protocolo Metodológico da Revisão da Literatura", "1.4 Protocolo"),
        ("2 FUNDAMENTOS DOS MODELOS DE LINGUAGEM DE GRANDE ESCALA", "2 FUNDAMENTOS"),
        ("2.1 Evolução Histórica", "2.1 Evolução"),
        ("2.2 Arquitetura Transformer e Mecanismo de Atenção", "2.2 Arquitetura"),
        ("2.3 Tokenização e Janela de Contexto", "2.3 Tokenização"),
        ("3 ENGENHARIA DE PROMPT", "3 ENGENHARIA"),
        ("3.1 Principais Técnicas", "3.1 Principais"),
        ("3.2 Relação entre Estrutura do Prompt e Qualidade da Resposta", "3.2 Relação"),
        ("4 TEORIA DA INFORMAÇÃO E REDUNDÂNCIA LINGUÍSTICA", "4 TEORIA DA INFORMAÇÃO"),
        ("4.1 Entropia de Shannon e Linguagem Natural", "4.1 Entropia"),
        ("4.2 Perplexidade e Autoinformação como Critérios de Poda", "4.2 Perplexidade"),
        ("5 IMPACTO COMPUTACIONAL DOS TOKENS", "5 IMPACTO COMPUTACIONAL"),
        ("5.1 Complexidade Quadrática na Fase de Prefill versus Fase de Decoding", "5.1 Complexidade"),
        ("5.2 Custos Financeiros em APIs Comerciais", "5.2 Custos"),
        ("6 MÉTODOS DE COMPRESSÃO DE PROMPTS", "6 MÉTODOS"),
        ("6.1 LLMLingua e LLMLingua-2", "6.1 LLMLingua"),
        ("6.2 LongLLMLingua", "6.2 LongLLMLingua"),
        ("6.3 Selective Context e AutoCompressor", "6.3 Selective Context"),
        ("6.4 Análise Comparativa Crítica e Confrontação com o Compilador TokLang", "6.4 Análise Comparativa"),
        ("7 COMPRESSÃO EM SISTEMAS RAG", "7 COMPRESSÃO"),
        ("8 AVALIAÇÃO SEMÂNTICA COM BERTSCORE E MÉTRICAS COMPOSTAS", "8 AVALIAÇÃO"),
        ("9 SUSTENTABILIDADE E GREEN AI", "9 SUSTENTABILIDADE"),
        ("10 RESULTADOS E DISCUSSÃO EXPERIMENTAL", "10 RESULTADOS"),
        ("10.1 Metodologia Experimental, Algoritmo Reprodutível e Bancada", "10.1 Metodologia"),
        ("10.2 Avaliação Empírica do Volume de Tokens e Taxas de Compressão", "10.2 Avaliação"),
        ("10.3 Latência (TTFT vs. Tempo Total) e Variação Estatística em Nuvem", "10.3 Latência"),
        ("10.4 Fidelidade Semântica e Composição da Métrica BERTScore Proxy F1", "10.4 Fidelidade"),
        ("10.5 Projeção Financeira e Estimativa Analítica de Eficiência (FLOPs)", "10.5 Projeção"),
        ("10.6 Diretrizes de Engenharia e Análise de Trade-offs", "10.6 Diretrizes"),
        ("11 CONCLUSÃO, LIMITAÇÕES E TRABALHOS FUTUROS", "11 CONCLUSÃO"),
        ("REFERÊNCIAS", "REFERÊNCIAS"),
    ]

    mapping = {}
    for label, query in search_keys:
        found_pg = None
        for p_idx, raw_txt in enumerate(pages_text):
            txt_up = raw_txt.upper()
            if p_idx < 4 or "SUMÁRIO" in txt_up:
                continue
            if label == "REFERÊNCIAS":
                lines_up = [ln.strip() for ln in txt_up.splitlines() if ln.strip()]
                if "REFERÊNCIAS" in lines_up:
                    found_pg = p_idx + 1
                    break
            elif query.upper() in txt_up:
                found_pg = p_idx + 1
                break
        if found_pg is None:
            raise RuntimeError(f"ERRO FATAL: Secao '{label}' nao localizada no PDF para construcao do sumario.")
        mapping[label] = str(found_pg)
    return mapping


def main():
    pipeline_dir = Path(__file__).resolve().parent
    manuscrito_dir = pipeline_dir.parent  # docs/
    docx_file = manuscrito_dir / "TCC_II_Versao_2_Pos_Banca_EXTRA.docx"
    pdf_file = manuscrito_dir / "TCC_II_Versao_2_Pos_Banca_EXTRA.pdf"

    print("=== PASSADA 1: Compilação de teste da Versão 2 EXTRA para mapeamento de páginas ===")
    build_monograph(docx_file)
    convert_to_pdf(docx_file, pdf_file)

    print("=== MAPEANDO PÁGINAS EXATAS DO PDF EXTRA GERADO ===")
    exact_map = scan_heading_pages(pdf_file)
    for k, v in exact_map.items():
        print(f"  {k} -> pág. {v}")

    print("=== PASSADA 2: Compilação definitiva da Versão 2 EXTRA com sumário calibrado ===")
    build_monograph(docx_file, sumario_page_map=exact_map)
    convert_to_pdf(docx_file, pdf_file)

    # Copiar exclusivamente os arquivos EXTRAS para o CS-Vault-2026 sem tocar nos originais
    cs_vault_manuscrito = Path(r"C:\Users\52319400\CS-Vault-2026\01 - DISCIPLINAS\Trabalho de Conclusão de Curso II\01 - Manuscrito")
    if cs_vault_manuscrito.exists():
        shutil.copy2(docx_file, cs_vault_manuscrito / docx_file.name)
        shutil.copy2(pdf_file, cs_vault_manuscrito / pdf_file.name)
        print(f"[OK] Arquivos EXTRAS espelhados em: {cs_vault_manuscrito}")

    if fitz is not None:
        doc = fitz.open(pdf_file)
        print(f"\n==========================================")
        print(f"   VALIDAÇÃO VISUAL DO PDF V2 EXTRA       ")
        print(f"==========================================")
        print(f"Total de páginas: {len(doc)}")
        p1_lines = [l.strip() for l in doc[0].get_text().splitlines() if l.strip()]
        has_city = any("INDAIATUBA" in l for l in p1_lines)
        has_year = any("2026" in l for l in p1_lines)
        print(f"Página 1 (Capa): {'PERFEITA (Contém INDAIATUBA 2026)' if (has_city and has_year) else 'ERRO: Vazou para página 2'}")
        print(f"Página 2: {'RESUMO presente' if 'RESUMO' in doc[1].get_text() else 'ERRO no Resumo'}")
        print(f"Página 3: {'ABSTRACT presente' if 'ABSTRACT' in doc[2].get_text() else 'ERRO no Abstract'}")
        print(f"Página 4: {'SUMÁRIO presente' if 'SUMÁRIO' in doc[3].get_text() else 'ERRO no Sumário'}")
        print(f"Página 5: {'1 INTRODUÇÃO na pág 5' if '1 INTRODUÇÃO' in doc[4].get_text().upper() else 'ERRO: Sumário vazou para pág 5'}")
        total_imgs = sum(len(p.get_images()) for p in doc)
        print(f"Total de Figuras Científicas incorporadas: {total_imgs}")
        print("==========================================")


if __name__ == "__main__":
    main()
