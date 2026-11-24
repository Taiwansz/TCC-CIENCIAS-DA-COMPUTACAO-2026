import os
import urllib.request
import json

models = {
    'z-ai/glm-5.3': os.environ.get('NVIDIA_API_KEY_GLM', os.environ.get('NVIDIA_API_KEY', '')),
    'deepseek-ai/deepseek-v4-flash-0731': os.environ.get('NVIDIA_API_KEY_DEEPSEEK', os.environ.get('NVIDIA_API_KEY', ''))
}

for m, key in models.items():
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': 'Which number is larger, 9.11 or 9.8?'}],
        'max_tokens': 256,
        'temperature': 0.2
    }
    req = urllib.request.Request(
        'https://integrate.api.nvidia.com/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            msg = data['choices'][0]['message']
            content = msg.get('content') or msg.get('reasoning_content') or msg.get('reasoning') or ''
            usage = data.get('usage', {})
            print(f'[{m}] SUCESSO!\nResposta: {content.strip()[:100]}...\nTokens in: {usage.get("prompt_tokens")} | out: {usage.get("completion_tokens")}\n')
    except Exception as e:
        print(f'[{m}] ERRO: {e}\n')
