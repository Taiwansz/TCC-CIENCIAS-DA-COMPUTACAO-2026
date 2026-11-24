import json
import time
from pathlib import Path
from providers import get_provider
from pricing import calculate_cost

results_file = Path(r'C:\Users\52319400\battle_ia\output\battle_ia_results.json')
with open(results_file, 'r', encoding='utf-8') as f:
    results = json.load(f)

dataset_file = Path(r'C:\Users\52319400\battle_ia\prompts_dataset.json')
with open(dataset_file, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

cases_map = {c['case_id']: c for c in dataset['cases']}

failed_count = sum(1 for r in results if not r['success'])
print(f"Total registros: {len(results)} | Registros com falha: {failed_count}")

# Para cada registro que falhou, executa com o provedor streaming atualizado
for idx, r in enumerate(results):
    if r['success']:
        continue
        
    case_id = r['case_id']
    model_id = r['model_id']
    tech = r['technique']
    case_data = cases_map.get(case_id, {})
    sys_prompt = case_data.get('system_prompt')
    prompt = case_data.get('techniques', {}).get(tech, r.get('input_prompt', ''))
    
    print(f"\n[Recuperando {idx+1}/{len(results)}] {case_id} | {model_id.split('/')[-1]} | {tech}...")
    provider = get_provider(model_id)
    
    # Executa inferencia com streaming
    max_toks = 800 if 'deepseek' in model_id else 1200
    resp = provider.generate(prompt=prompt, system_prompt=sys_prompt, max_tokens=max_toks)
    
    print(f"  Resultado: success={resp.success} | latency={resp.latency_ms/1000:.1f}s | in={resp.prompt_tokens} | out={resp.completion_tokens}")
    
    if resp.success:
        cost = calculate_cost(model_id, resp.prompt_tokens, resp.completion_tokens)
        orig_tokens = r.get('original_prompt_tokens', resp.prompt_tokens)
        comp_ratio = round(orig_tokens / resp.prompt_tokens, 2) if resp.prompt_tokens > 0 else 1.0
        reduction_pct = round(((orig_tokens - resp.prompt_tokens) / orig_tokens) * 100, 1) if orig_tokens > 0 else 0.0
        
        r['success'] = True
        r['prompt_tokens'] = resp.prompt_tokens
        r['completion_tokens'] = resp.completion_tokens
        r['total_tokens'] = resp.total_tokens
        r['latency_ms'] = resp.latency_ms
        r['cost_usd'] = round(cost, 6)
        r['output_text'] = resp.output_text
        r['error_message'] = None
        r['compression_ratio'] = comp_ratio
        r['token_reduction_pct'] = reduction_pct

# Grava os resultados curados
with open(results_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\nRecuperacao concluida. Todos os registros foram processados e gravados.")
