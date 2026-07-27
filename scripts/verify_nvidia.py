"""NVIDIA build API 诊断脚本 v3：探测多个候选模型，判定配额范围。

用法:
  python scripts/verify_nvidia.py            # 测试内置候选列表
  python scripts/verify_nvidia.py --model <id>  # 测单个自定义模型 ID

判定逻辑:
  200/201 = 模型在架且可用（可直接设为 LLM_MODEL）
  404     = 模型 ID 错误或已下架
  429     = 限流/配额（请求已到达 NVIDIA，key 与请求格式正确）
  SSL/超时 = 网络层问题（代理/节点）

核心结论:
  - 只有一个模型 429，其他 200 -> 该模型配额问题，换模型即可
  - 所有模型都 429 -> 账户级每日配额/被标记，需等重置或换 key
"""
import argparse
import os
import sys

print('HTTP_PROXY :', os.environ.get('HTTP_PROXY') or '(无)')
print('HTTPS_PROXY:', os.environ.get('HTTPS_PROXY') or '(无)')
print('NO_PROXY   :', os.environ.get('NO_PROXY') or '(无)')

# 读 backend/.env 里的 NVIDIA_API_KEY
env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
key = ''
with open(env_path, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('NVIDIA_API_KEY='):
            key = line.split('=', 1)[1].strip()

if not key:
    print('!! backend/.env 中没有 NVIDIA_API_KEY，请先填入')
    sys.exit(1)
print('key: ' + key[:8] + '...（长度 ' + str(len(key)) + '）')

# 候选模型（2026 年在架/较新；探测结果会告诉我们哪些仍有效）
DEFAULT_MODELS = [
    'minimaxai/minimax-m3',                          # 当前默认
    'z-ai/glm-5.2',                               # 智谱 GLM-5.2（用户指定）
    'zai-org/glm-5',                                 # GLM-5 变体
    'zai-org/glm-4.5',                               # GLM-4.5（较老）
    'nvidia/llama-3.3-nemotron-super-49b-v1',        # NVIDIA 自家旗舰
    'meta/llama-4-maverick-17b-128e-instruct',       # Llama-4
    'google/gemma-3-27b-it',                         # Gemma-3
]

from openai import OpenAI

client = OpenAI(
    api_key=key,
    base_url='https://integrate.api.nvidia.com/v1',
    timeout=30.0,
)


def probe(model_id):
    """返回 (status, 判定, 说明)。"""
    try:
        resp = client.chat.completions.create(
            model=model_id,
            messages=[{'role': 'user', 'content': 'hi'}],
            max_tokens=8,
        )
        return 200, '可用', (resp.choices[0].message.content or '')[:40]
    except Exception as e:
        resp = getattr(e, 'response', None)
        status = getattr(resp, 'status_code', None) if resp is not None else None
        body = getattr(resp, 'text', '') if resp is not None else str(e)
        if status == 429:
            return 429, '限流/配额', body[:120]
        if status in (401, 403):
            return status, 'key 无效/未授权', body[:120]
        if status in (400, 404, 422, 410):
            return status, '模型不在架/已下架', body[:80]
        return None, '网络/TLS', type(e).__name__ + ': ' + str(e)[:100]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='只测单个模型 ID')
    args = parser.parse_args()

    models = [args.model] if args.model else DEFAULT_MODELS
    results = []
    print()
    for m in models:
        status, verdict, detail = probe(m)
        results.append((m, status, verdict))
        tag = 'OK ' if status == 200 else ('429' if status == 429 else (str(status) if status else 'NET'))
        print('[' + tag + '] ' + m + '  -> ' + verdict + '  ' + detail)

    print()
    print('=== 判定总结 ===')
    ok = [m for m, s, v in results if s == 200]
    rl = [m for m, s, v in results if s == 429]
    if ok:
        print('可用模型: ' + ', '.join(ok))
        print('  若 minimax-m3 在 429 列表里，直接把 LLM_MODEL 换成可用模型即可绕过配额')
    if rl and not ok:
        print('所有模型都 429 -> 账户级每日配额耗尽/被标记，需等重置、换 key，或查 build.nvidia.com 用量')
    elif rl:
        print('429 模型: ' + ', '.join(rl) + '（模型级配额）')
    if not ok and not rl:
        print('无模型成功且无 429 -> 网络/TLS 问题，检查代理与节点')


if __name__ == '__main__':
    main()