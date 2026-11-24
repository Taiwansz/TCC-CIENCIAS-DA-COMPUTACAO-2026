import os
import urllib.request
import json

API_KEY = os.environ.get('NVIDIA_API_KEY_KIMI', os.environ.get('NVIDIA_API_KEY', ''))

payload = {
    'model': 'moonshotai/kimi-k3',
    'messages': [{'role': 'user', 'content': 'Which number is larger, 9.11 or 9.8?'}],
    'max_tokens': 128,
    'temperature': 0.2
}
req = urllib.request.Request(
    'https://integrate.api.nvidia.com/v1/chat/completions',
    data=json.dumps(payload).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    },
    method='POST'
)
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        msg = data['choices'][0]['message']
        content = msg.get('content') or msg.get('reasoning_content') or ''
        usage = data.get('usage', {})
        print('KIMI-K3 SUCESSO:', content.strip()[:100], '| tokens in:', usage.get('prompt_tokens'))
except Exception as e:
    print('KIMI-K3 ERRO:', e)
