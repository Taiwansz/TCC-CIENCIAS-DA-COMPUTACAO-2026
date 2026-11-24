import json

with open(r'C:\Users\52319400\battle_ia\output\battle_ia_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for i, d in enumerate(data):
    model = d['model_id'].split('/')[-1]
    out = d.get('output_text', '')
    err = d.get('error_message')
    print(f"{i+1:02d} | {d['case_id']} | {model:25s} | {d['technique']:20s} | len={len(out):5d} | succ={d['success']}")
    if len(out) > 0:
        first_line = out.strip().split('\n')[0][:80]
        print(f"     -> {first_line}")
    elif err:
        print(f"     -> ERR: {err}")
