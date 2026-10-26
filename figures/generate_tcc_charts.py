"""
=============================================================================
Gerador de Figuras Gráficas Científicas — TCC II (Ciência da Computação)
Autor: Matheus Sousa dos Santos (RA: 52319400)
Orientador: Prof. Luiz Claudio Chiavini Oliveira Junior
Centro Universitário Max Planck (UniMAX) - Indaiatuba, 2026
=============================================================================
Gera os 4 gráficos científicos de bancada em alta resolução (300 DPI):
- Figura 10.1: Volume Médio de Tokens de Entrada por Técnica e Caso
- Figura 10.2: Latência e Redução de Time-to-First-Token (TTFT em ms)
- Figura 10.3: Curva de Retenção Semântica (BERTScore F1) vs Razão de Compressão
- Figura 10.4: Projeção de Custo Financeiro e Redução de FLOPs O(n²)

POLÍTICA DE DADOS: ZERO FALLBACK / ZERO DADOS SINTÉTICOS.
Todos os pontos plotados são estritamente lidos do banco de dados experimental:
'03 - Bancada Experimental (Código)/battle_ia_resultados_brutos.json'
Se qualquer medição estiver ausente, o script encerra imediatamente com erro fatal.
=============================================================================
"""

import os
import sys
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Configuração de estilo sóbrio para publicações científicas ABNT
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#E0E0E0'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.linewidth'] = 0.5

base_dir = Path(__file__).parent
out_dir = base_dir.parent / "04 - Figuras"
out_dir.mkdir(parents=True, exist_ok=True)
json_path = base_dir / "battle_ia_resultados_brutos.json"

# =============================================================================
# CARGA RIGOROSA DE DADOS REAIS (ZERO FALLBACK)
# =============================================================================

if not json_path.exists():
    raise FileNotFoundError(
        f"ERRO FATAL: Arquivo de resultados reais '{json_path}' não encontrado. "
        f"Execute primeiramente 'python battle_ia_benchmark.py' para coletar as métricas reais via API!"
    )

with open(json_path, "r", encoding="utf-8") as f:
    dados_brutos = json.load(f)

if not dados_brutos or len(dados_brutos) < 12:
    raise ValueError(
        f"ERRO FATAL: O arquivo '{json_path.name}' contém apenas {len(dados_brutos)} registros "
        f"(são exigidos exatamente 12 registros correspondentes aos 3 casos sob as 4 técnicas). "
        f"Fallback estritamente proibido."
    )

modelo_nome_raw = dados_brutos[0]["modelo_avaliado"]
print(f"[CARGA REAL] 100% dos {len(dados_brutos)} registros reais carregados de {json_path.name}")

# Formatação limpa do identificador do modelo para exibição acadêmica
nome_modelo_formatado = "Meta Llama-3.2-11B-Vision-Instruct"
if "llama-3.2-11b" in modelo_nome_raw.lower():
    nome_modelo_formatado = "Meta Llama-3.2-11B-Vision-Instruct"
elif "nemotron" in modelo_nome_raw.lower():
    nome_modelo_formatado = "NVIDIA Nemotron-3-Super-120B"
elif "mistral" in modelo_nome_raw.lower():
    nome_modelo_formatado = "Mistral-Large-2407"
else:
    nome_modelo_formatado = modelo_nome_raw

SUBTITULO_MODELO = f"Modelo Avaliado: {nome_modelo_formatado} | Infraestrutura: NVIDIA NIM Cloud (A100 SXM4)"

# Mapeia registros por (caso_id, tecnica)
mapa_dados = {}
for r in dados_brutos:
    k = (r["caso_id"], r["tecnica"])
    mapa_dados[k] = r

def get_real_metric(caso_id: str, tecnica: str, campo: str):
    """
    Recupera o valor medido estritamente real do JSON gerado pela bancada experimental.
    Qualquer ausência dispara erro fatal imediato (ZERO FALLBACK).
    """
    chave = (caso_id, tecnica)
    if chave not in mapa_dados:
        raise KeyError(f"ERRO FATAL: Medição ausente no JSON para a chave {chave}. Fallback proibido.")
    registro = mapa_dados[chave]
    if campo not in registro:
        raise KeyError(f"ERRO FATAL: Campo '{campo}' ausente no registro {chave}. Fallback proibido.")
    return registro[campo]

labels = ['Caso 1: Sist. Distribuídos', 'Caso 2: SQL sob DDL', 'Caso 3: Auditoria LGPD']
casos = ['caso_1', 'caso_2', 'caso_3']

# -------------------------------------------------------------
# FIGURA 10.1: Volume Real de Tokens de Entrada por Técnica
# -------------------------------------------------------------
few_shot = [get_real_metric(c, 'Few-shot (Baseline)', 'tokens_entrada') for c in casos]
zero_shot = [get_real_metric(c, 'Zero-shot', 'tokens_entrada') for c in casos]
llmlingua_2x = [get_real_metric(c, 'LLMLingua (2x)', 'tokens_entrada') for c in casos]
llmlingua_4x = [get_real_metric(c, 'LLMLingua (4x)', 'tokens_entrada') for c in casos]

fig, ax = plt.subplots(figsize=(7.8, 4.5), dpi=300)
x = np.arange(len(labels))
width = 0.18

rects1 = ax.bar(x - width*1.5, few_shot, width, label='Few-shot (Baseline)', color='#4A5568', edgecolor='#2D3748')
rects2 = ax.bar(x - width*0.5, zero_shot, width, label='Zero-shot', color='#718096', edgecolor='#4A5568')
rects3 = ax.bar(x + width*0.5, llmlingua_2x, width, label='LLMLingua (2x)', color='#2B6CB0', edgecolor='#1A365D')
rects4 = ax.bar(x + width*1.5, llmlingua_4x, width, label='LLMLingua (4x)', color='#319795', edgecolor='#234E52')

ax.set_ylabel('Tokens de Entrada (Prompt Real)', fontsize=9.5, fontweight='bold')
ax.set_title(f'Consumo Real de Tokens de Entrada por Técnica de Prompting\n[{SUBTITULO_MODELO}]', 
             fontsize=10.0, fontweight='bold', pad=12, color='#1A202C')
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9.0)
ax.legend(frameon=True, facecolor='white', edgecolor='#CBD5E0', fontsize=8.0, loc='upper right')
ax.grid(axis='y', alpha=0.7)
ax.set_axisbelow(True)
ax.set_ylim(0, max(few_shot) * 1.25)

def autolabel(rects, ax_target, fmt="{:.0f}"):
    for rect in rects:
        height = rect.get_height()
        ax_target.annotate(fmt.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 2),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=7.2, fontweight='bold')

autolabel(rects1, ax)
autolabel(rects2, ax)
autolabel(rects3, ax)
autolabel(rects4, ax)

fig.tight_layout()
fig1_path = out_dir / "figura_10_1_volume_tokens.png"
fig.savefig(fig1_path, dpi=300)
plt.close(fig)
print(f"[OK] Gerada Figura 10.1 (100% Real): {fig1_path}")

# -------------------------------------------------------------
# FIGURA 10.2: Latência e Time-to-First-Token (TTFT em ms)
# -------------------------------------------------------------
ttft_few = [get_real_metric(c, 'Few-shot (Baseline)', 'ttft_ms') for c in casos]
ttft_zero = [get_real_metric(c, 'Zero-shot', 'ttft_ms') for c in casos]
ttft_2x = [get_real_metric(c, 'LLMLingua (2x)', 'ttft_ms') for c in casos]
ttft_4x = [get_real_metric(c, 'LLMLingua (4x)', 'ttft_ms') for c in casos]

fig, ax = plt.subplots(figsize=(7.8, 4.5), dpi=300)
rects1 = ax.bar(x - width*1.5, ttft_few, width, label='Few-shot (Baseline)', color='#4A5568', edgecolor='#2D3748')
rects2 = ax.bar(x - width*0.5, ttft_zero, width, label='Zero-shot', color='#718096', edgecolor='#4A5568')
rects3 = ax.bar(x + width*0.5, ttft_2x, width, label='LLMLingua (2x)', color='#C53030', edgecolor='#742A2A')
rects4 = ax.bar(x + width*1.5, ttft_4x, width, label='LLMLingua (4x)', color='#DD6B20', edgecolor='#7B341E')

ax.set_ylabel('Time-to-First-Token - TTFT Real (ms)', fontsize=9.5, fontweight='bold')
ax.set_title(f'Impacto da Compressão na Latência Inicial de Inferência (Prefill Time)\n[{SUBTITULO_MODELO}]', 
             fontsize=10.0, fontweight='bold', pad=12, color='#1A202C')
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9.0)
ax.legend(frameon=True, facecolor='white', edgecolor='#CBD5E0', fontsize=8.0, loc='upper left')
ax.grid(axis='y', alpha=0.7)
ax.set_axisbelow(True)
max_ttft_all = max(ttft_few + ttft_zero + ttft_2x + ttft_4x)
ax.set_ylim(0, max_ttft_all * 1.18)

autolabel(rects1, ax, "{:.0f}ms")
autolabel(rects2, ax, "{:.0f}ms")
autolabel(rects3, ax, "{:.0f}ms")
autolabel(rects4, ax, "{:.0f}ms")

fig.tight_layout()
fig2_path = out_dir / "figura_10_2_latencia_ttft.png"
fig.savefig(fig2_path, dpi=300)
plt.close(fig)
print(f"[OK] Gerada Figura 10.2 (100% Real): {fig2_path}")

# -------------------------------------------------------------
# FIGURA 10.3: Curva de Retenção Semântica (BERTScore F1)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.8, 4.5), dpi=300)
ratios = [1.0, 2.0, 4.0]

def get_case_curve(cid):
    f1_1 = get_real_metric(cid, 'Zero-shot', 'bertscore_proxy_f1')
    f1_2 = get_real_metric(cid, 'LLMLingua (2x)', 'bertscore_proxy_f1')
    f1_4 = get_real_metric(cid, 'LLMLingua (4x)', 'bertscore_proxy_f1')
    return [f1_1, f1_2, f1_4]

c1_f1 = get_case_curve('caso_1')
c2_f1 = get_case_curve('caso_2')
c3_f1 = get_case_curve('caso_3')

ax.plot(ratios, c1_f1, marker='o', markersize=7, linewidth=2.2, label='Caso 1: Sist. Distribuídos (Raft)', color='#2B6CB0')
ax.plot(ratios, c2_f1, marker='s', markersize=7, linewidth=2.2, label='Caso 2: SQL Analítico (DDL)', color='#2C7A7B')
ax.plot(ratios, c3_f1, marker='^', markersize=7, linewidth=2.2, label='Caso 3: Auditoria LGPD', color='#805AD5')

ax.axhline(0.80, color='#E53E3E', linestyle=':', linewidth=1.6, label='Limiar Crítico de Aceitação Acadêmica (F1 = 0,80)')

for r, val in zip(ratios, c1_f1):
    offset_y = 7 if r == 1.0 else -13
    ax.annotate(f"{val:.3f}", (r, val), textcoords="offset points", xytext=(0, offset_y), ha='center', fontsize=7.5, fontweight='bold', color='#1A365D')
for r, val in zip(ratios, c2_f1):
    ax.annotate(f"{val:.3f}", (r, val), textcoords="offset points", xytext=(0, 7), ha='center', fontsize=7.5, fontweight='bold', color='#1D4044')
for r, val in zip(ratios, c3_f1):
    offset_y = -13 if r == 1.0 else 7
    ax.annotate(f"{val:.3f}", (r, val), textcoords="offset points", xytext=(0, offset_y), ha='center', fontsize=7.5, fontweight='bold', color='#44337A')

ax.set_xlabel('Razão de Compressão de Prompt', fontsize=9.5, fontweight='bold')
ax.set_ylabel('Fidelidade Semântica (BERTScore Proxy F1)', fontsize=9.5, fontweight='bold')
ax.set_title(f'Retenção Semântica Real em Função da Taxa de Compressão de Prompt\n[{SUBTITULO_MODELO}]', 
             fontsize=10.0, fontweight='bold', pad=12, color='#1A202C')
ax.set_ylim(0.72, 0.94)
ax.set_xticks(ratios)
ax.set_xticklabels(['1x (Zero-shot / Integral)', '2x (~50% Poda Shannon)', '4x (~75% Poda Shannon)'], fontsize=9.0)
ax.legend(frameon=True, facecolor='white', edgecolor='#CBD5E0', fontsize=8.0, loc='upper right')
ax.grid(True, alpha=0.6)

fig.tight_layout()
fig3_path = out_dir / "figura_10_3_bertscore_f1.png"
fig.savefig(fig3_path, dpi=300)
plt.close(fig)
print(f"[OK] Gerada Figura 10.3 (100% Real): {fig3_path}")

# -------------------------------------------------------------
# FIGURA 10.4: Projeção de Custo Financeiro e Redução de FLOPs
# -------------------------------------------------------------
fig, ax1 = plt.subplots(figsize=(7.8, 4.5), dpi=300)

scenarios = ['Few-shot', 'Zero-shot', 'LLMLingua 2x', 'LLMLingua 4x']
tecs = ['Few-shot (Baseline)', 'Zero-shot', 'LLMLingua (2x)', 'LLMLingua (4x)']

# Médias consolidadas estritamente sobre os registros reais dos 3 casos
cost_usd = [
    float(np.mean([get_real_metric(c, t, 'custo_total_100k_usd') for c in casos]))
    for t in tecs
]
flops_reduction = [
    float(np.mean([get_real_metric(c, t, 'reducao_flops_atencao_pct') for c in casos]))
    for t in tecs
]

x_pos = np.arange(len(scenarios))
w_bar = 0.35

rects_cost = ax1.bar(x_pos - w_bar/2, cost_usd, w_bar, label='Custo Médio 100k Req. (US$)', color='#2B6CB0', edgecolor='#1A365D')
ax1.set_ylabel('Custo Financeiro Projetado em Lotes (US$)', color='#2B6CB0', fontsize=9.5, fontweight='bold')
ax1.tick_params(axis='y', labelcolor='#2B6CB0')
ax1.set_ylim(0, max(cost_usd) * 1.30)

ax2 = ax1.twinx()
rects_flops = ax2.bar(x_pos + w_bar/2, flops_reduction, w_bar, label='Redução FLOPs Atenção O(n²)', color='#38A169', edgecolor='#22543D')
ax2.set_ylabel('Redução Teórica de FLOPs no Prefill O(n²) (%)', color='#38A169', fontsize=9.5, fontweight='bold')
ax2.tick_params(axis='y', labelcolor='#38A169')
ax2.set_ylim(0, 115)

ax1.set_xticks(x_pos)
ax1.set_xticklabels(scenarios, fontsize=9.0)
ax1.set_title(f'Economia Financeira e Redução de Complexidade Computacional (100k Requisições)\n[{SUBTITULO_MODELO}]', 
             fontsize=10.0, fontweight='bold', pad=12, color='#1A202C')

for rect in rects_cost:
    h = rect.get_height()
    ax1.annotate(f'US${h:.1f}',
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 2),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=7.8, color='#1A365D', fontweight='bold')

for rect in rects_flops:
    h = rect.get_height()
    ax2.annotate(f'{h:.1f}%',
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 2),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=7.8, color='#22543D', fontweight='bold')

lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right', frameon=True, facecolor='white', edgecolor='#CBD5E0', fontsize=7.8)

fig.tight_layout()
fig4_path = out_dir / "figura_10_4_custo_flops.png"
fig.savefig(fig4_path, dpi=300)
plt.close(fig)
print(f"[OK] Gerada Figura 10.4 (100% Real): {fig4_path}")
