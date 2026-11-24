#!/usr/bin/env python3
"""
Battle IA - Orquestrador Central de Benchmark Experimental (TCC II)
Avaliacao comparativa de tecnicas de compressao de prompt entre modelos de linguagem.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from providers import get_provider, ProviderResponse
from pricing import calculate_cost
from metrics import BenchmarkRecord, MetricsAggregator


def parse_args():
    parser = argparse.ArgumentParser(
        description="Battle IA - Benchmark de Compressao de Prompt e Eficiencia de Modelos (TCC II)"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="prompts_dataset.json",
        help="Caminho para o arquivo JSON contendo os casos de teste."
    )
    parser.add_argument(
        "--models",
        type=str,
        default="gpt-4o-mini,gemini-1.5-flash,claude-3-haiku-20240307,llama-3.1-8b-instant",
        help="Lista de modelos separados por virgula (ou 'mock-model')."
    )
    parser.add_argument(
        "--techniques",
        type=str,
        default="all",
        help="Tecnicas a avaliar separadas por virgula (ex: 'zero_shot,few_shot,compressed_llmlingua' ou 'all')."
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Numero de repeticoes por caso/tecnica/modelo para significancia estatistica."
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Executar em modo simulado deterministico (sem chamadas reais de API e sem custo)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Diretorio de saida para os artefatos gerados (CSV, JSON e Relatorio Markdown)."
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Intervalo em segundos entre chamadas para prevencao de rate limit."
    )
    return parser.parse_args()


def load_dataset(dataset_path: str) -> Dict[str, Any]:
    p = Path(dataset_path)
    if not p.exists():
        print(f"Erro: Arquivo de dataset '{dataset_path}' nao encontrado.")
        sys.exit(1)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def run_benchmark():
    args = parse_args()
    run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp_iso = datetime.now().isoformat()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(args.dataset)
    cases = dataset.get("cases", [])
    if not cases:
        print("Aviso: Nenhum caso encontrado no dataset.")
        sys.exit(1)

    models_list = [m.strip() for m in args.models.split(",") if m.strip()]
    if args.mock and "mock-model" not in models_list:
        models_list = ["mock-model-a", "mock-model-b"]

    selected_techs = None
    if args.techniques != "all":
        selected_techs = [t.strip() for t in args.techniques.split(",") if t.strip()]

    print("=" * 60)
    print("           BATTLE IA - BENCHMARK RUNNER (TCC II)           ")
    print("=" * 60)
    print(f"Run ID:        {run_id}")
    print(f"Timestamp:     {timestamp_iso}")
    print(f"Casos:         {len(cases)}")
    print(f"Modelos:       {', '.join(models_list)}")
    print(f"Modo:          {'SIMULADO (MOCK)' if args.mock else 'REAL (APIs Remotas)'}")
    print(f"Repeticoes:    {args.repeats} por combinacao")
    print(f"Diretorio:     {out_dir.resolve()}")
    print("-" * 60)

    aggregator = MetricsAggregator()
    total_executions = 0

    for case_idx, case in enumerate(cases, 1):
        case_id = case.get("case_id", f"CASE-{case_idx}")
        case_name = case.get("name", "Sem Nome")
        sys_prompt = case.get("system_prompt")
        tech_dict = case.get("techniques", {})

        # Estima/obtem o tamanho da linha de base (zero_shot)
        zero_shot_prompt = tech_dict.get("zero_shot", "")
        approx_baseline_tokens = max(1, len(zero_shot_prompt) // 4)

        print(f"\n[{case_idx}/{len(cases)}] Processando Caso: {case_id} ({case_name})")

        for tech_name, prompt_text in tech_dict.items():
            if selected_techs and tech_name not in selected_techs:
                continue

            for model_id in models_list:
                provider = get_provider(model_id, is_mock=args.mock)

                for rep in range(1, args.repeats + 1):
                    total_executions += 1
                    resp: ProviderResponse = provider.generate(prompt=prompt_text, system_prompt=sys_prompt)

                    # Se a chamada falhou ou nao retornou prompt_tokens reais, estima por aproximacao
                    p_toks = resp.prompt_tokens if resp.prompt_tokens > 0 else max(1, len(prompt_text) // 4)
                    c_toks = resp.completion_tokens if resp.completion_tokens > 0 else max(1, len(resp.output_text) // 4)
                    tot_toks = p_toks + c_toks

                    # Calcula taxa de compressao e reducao percentual contra zero_shot
                    ratio = round(approx_baseline_tokens / p_toks, 2) if p_toks > 0 else 1.0
                    reduction_pct = round(((approx_baseline_tokens - p_toks) / approx_baseline_tokens) * 100.0, 1) if approx_baseline_tokens > 0 else 0.0

                    cost = calculate_cost(model_id, p_toks, c_toks)

                    record = BenchmarkRecord(
                        run_id=run_id,
                        timestamp=timestamp_iso,
                        case_id=case_id,
                        case_name=case_name,
                        technique=tech_name,
                        provider=resp.provider,
                        model_id=model_id,
                        repeat_index=rep,
                        success=resp.success,
                        prompt_tokens=p_toks,
                        completion_tokens=c_toks,
                        total_tokens=tot_toks,
                        original_prompt_tokens=approx_baseline_tokens,
                        compression_ratio=ratio,
                        token_reduction_pct=reduction_pct,
                        latency_ms=resp.latency_ms,
                        cost_usd=cost,
                        input_prompt=prompt_text,
                        output_text=resp.output_text,
                        error_message=resp.error_message
                    )

                    aggregator.add_record(record)

                    status_str = "OK" if resp.success else f"ERRO ({resp.error_message})"
                    print(f"  -> [{tech_name:<20}] {model_id:<16} rep #{rep} | {resp.latency_ms:>6.1f}ms | {p_toks:>4} tok in | {c_toks:>4} tok out | {status_str}")

                    if args.delay > 0:
                        time.sleep(args.delay)

    print("\n" + "=" * 60)
    print("           EXPORTANDO RESULTADOS E RELATORIOS              ")
    print("=" * 60)

    csv_path = out_dir / "battle_ia_results.csv"
    json_path = out_dir / "battle_ia_results.json"
    summary_path = out_dir / "battle_ia_summary.json"
    report_md_path = out_dir / "battle_ia_report.md"

    aggregator.export_csv(str(csv_path))
    aggregator.export_json(str(json_path))
    aggregator.export_markdown_report(str(report_md_path))

    summary_data = aggregator.compute_summary()
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print(f"1. CSV Bruto (Pandas/Excel/Guilherme):   {csv_path.name}")
    print(f"2. JSON Detalhado (BERTScore/Felipe):    {json_path.name}")
    print(f"3. Resumo Estatistico (JSON):            {summary_path.name}")
    print(f"4. Relatorio Cap. 10 (Markdown/Juan):     {report_md_path.name}")
    print(f"\nTotal de registros gerados com sucesso: {len(aggregator.records)}")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()
