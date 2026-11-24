"""
Modulo de Metricas, Agregacao Estatistica e Exportacao - Battle IA (TCC II)
Gera CSV padronizado para analise no Pandas/Excel, JSON para o laudo de BERTScore e relatorio executivo em Markdown.
"""

import csv
import json
import math
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from collections import defaultdict


@dataclass
class BenchmarkRecord:
    run_id: str
    timestamp: str
    case_id: str
    case_name: str
    technique: str
    provider: str
    model_id: str
    repeat_index: int
    success: bool
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    original_prompt_tokens: int
    compression_ratio: float
    token_reduction_pct: float
    latency_ms: float
    cost_usd: float
    input_prompt: str
    output_text: str
    error_message: Optional[str] = None


class MetricsAggregator:
    def __init__(self):
        self.records: List[BenchmarkRecord] = []

    def add_record(self, record: BenchmarkRecord):
        self.records.append(record)

    def export_csv(self, file_path: str):
        """Exporta todos os registros brutos em formato CSV compatível com Pandas/Excel."""
        if not self.records:
            return

        fieldnames = [
            "run_id", "timestamp", "case_id", "case_name", "technique",
            "provider", "model_id", "repeat_index", "success",
            "prompt_tokens", "completion_tokens", "total_tokens",
            "original_prompt_tokens", "compression_ratio", "token_reduction_pct",
            "latency_ms", "cost_usd", "error_message"
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for rec in self.records:
                writer.writerow(asdict(rec))

    def export_json(self, file_path: str):
        """Exporta todos os registros brutos em JSON, incluindo os textos integrais de entrada e saida."""
        data = [asdict(rec) for rec in self.records]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def compute_summary(self) -> Dict[str, Any]:
        """Calcula estatisticas descritivas agrupadas por (modelo, tecnica)."""
        grouped = defaultdict(list)
        for r in self.records:
            if r.success:
                key = (r.model_id, r.technique)
                grouped[key].append(r)

        summary_rows = []
        for (model_id, technique), items in grouped.items():
            n = len(items)
            latencies = [x.latency_ms for x in items]
            prompt_toks = [x.prompt_tokens for x in items]
            comp_toks = [x.completion_tokens for x in items]
            ratios = [x.compression_ratio for x in items]
            costs = [x.cost_usd for x in items]

            mean_lat = sum(latencies) / n
            var_lat = sum((x - mean_lat) ** 2 for x in latencies) / n if n > 1 else 0.0
            std_lat = math.sqrt(var_lat)

            mean_prompt = sum(prompt_toks) / n
            mean_comp = sum(comp_toks) / n
            mean_ratio = sum(ratios) / n
            total_cost = sum(costs)

            summary_rows.append({
                "model_id": model_id,
                "technique": technique,
                "samples_count": n,
                "mean_latency_ms": round(mean_lat, 2),
                "std_latency_ms": round(std_lat, 2),
                "mean_prompt_tokens": round(mean_prompt, 1),
                "mean_completion_tokens": round(mean_comp, 1),
                "mean_compression_ratio": round(mean_ratio, 2),
                "total_cost_usd": round(total_cost, 6),
            })

        return {
            "total_records": len(self.records),
            "successful_records": sum(1 for r in self.records if r.success),
            "failed_records": sum(1 for r in self.records if not r.success),
            "aggregated_by_model_and_technique": summary_rows
        }

    def export_markdown_report(self, file_path: str):
        """Gera um relatorio consolidado em Markdown pronto para inclusao no Capitulo 10."""
        summary = self.compute_summary()
        rows = summary["aggregated_by_model_and_technique"]

        # Ordena por modelo e tecnica
        rows.sort(key=lambda x: (x["model_id"], x["technique"]))

        lines = []
        lines.append("# Battle IA - Relatorio Experimental de Benchmark (TCC II)")
        lines.append("")
        lines.append("> Eixo: Compressao de Prompts, Consumo de Tokens, Latencia e Custo Operacional.")
        lines.append(f"> Total de Chamadas Executadas: **{summary['total_records']}** | Sucesso: **{summary['successful_records']}** | Falhas: **{summary['failed_records']}**")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 1. Tabela Consolidada de Resultados (Por Modelo e Tecnica)")
        lines.append("")
        lines.append("| Modelo | Tecnica | Amostras | Latencia Media (ms) | Desvio Padrao (ms) | Tokens Entrada (Medio) | Tokens Saida (Medio) | Fator Compressao | Custo Total (USD) |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")

        for r in rows:
            lines.append(
                f"| `{r['model_id']}` | `{r['technique']}` | {r['samples_count']} | {r['mean_latency_ms']} | ±{r['std_latency_ms']} | {r['mean_prompt_tokens']} | {r['mean_completion_tokens']} | {r['mean_compression_ratio']}x | ${r['total_cost_usd']:.6f} |"
            )

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 2. Analise de Eficiencia e Reducao de Custos")
        lines.append("")
        lines.append("Comparativo das tecnicas comprimidas em relacao a linha de base (Zero-shot):")
        lines.append("")

        # Agrupa por modelo para calcular economia percentual
        models = sorted(list(set(r["model_id"] for r in rows)))
        for m in models:
            m_rows = {r["technique"]: r for r in rows if r["model_id"] == m}
            baseline = m_rows.get("zero_shot") or m_rows.get("baseline")
            if baseline:
                base_tokens = baseline["mean_prompt_tokens"]
                base_lat = baseline["mean_latency_ms"]
                lines.append(f"### Modelo: `{m}`")
                for tech, data in m_rows.items():
                    if tech in ["zero_shot", "baseline"]:
                        continue
                    token_diff_pct = ((base_tokens - data["mean_prompt_tokens"]) / base_tokens) * 100 if base_tokens > 0 else 0
                    lat_diff_pct = ((base_lat - data["mean_latency_ms"]) / base_lat) * 100 if base_lat > 0 else 0
                    lines.append(f"- **Tecnica `{tech}` vs `zero_shot`:**")
                    lines.append(f"  - Reducao de Tokens de Entrada: **{token_diff_pct:.1f}%**")
                    lines.append(f"  - Variacao de Latencia: **{lat_diff_pct:+.1f}%** (Baseline: {base_lat}ms -> Comprimido: {data['mean_latency_ms']}ms)")
                    lines.append(f"  - Taxa de Compressao Efetiva: **{data['mean_compression_ratio']}x**")
                lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## 3. Instrucoes de Uso para os Membros da Equipe")
        lines.append("- **Felipe Pinete (BERTScore):** Consumir o arquivo `battle_ia_results.json` e aplicar o script de avaliacao semantica comparando o campo `output_text` da tecnica comprimida contra o `output_text` da tecnica `zero_shot` de referencia.")
        lines.append("- **Guilherme W. (Graficos e ABNT):** Importar `battle_ia_results.csv` para gerar os graficos de dispersao (Latencia vs Tamanho de Prompt) e barras (Economia de Tokens por Modelo) para o Capitulo 10.")
        lines.append("- **Juan Pedro (Discussao):** Utilizar as secoes 1 e 2 deste relatorio para redigir a argumentacao empírica de Green AI e Teoria da Informacao.")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
