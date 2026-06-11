#!/usr/bin/env python3
"""
Model Quality & Latency Benchmark — compare two LLMs side-by-side.

Measures: response latency, pass rate, answer quality across 8 dimensions.
Designed for OpenAI-compatible chat completion APIs.

Usage:
    # Edit MODELS and TESTS below, then run directly:
    python3 model-quality-benchmark.py

    # Or source it from a cron/skill:
    python3 model-quality-benchmark.py --output /tmp/benchmark_results.json
"""

import json, os, sys, time, requests, statistics
from datetime import datetime
from typing import Optional

# ── DEFAULT CONFIG (override by editing or env) ──

PROXIES = {}  # e.g. {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}

# Define models to compare. Each entry: {name, base_url, api_key, model_id}
# API keys can reference env vars via "$ENV_VAR_NAME" syntax.
MODELS = [
    {
        "name": "Model A",
        "base_url": "https://api.example.com/v1",
        "api_key": "$MODEL_A_KEY",
        "model": "model-a-name",
    },
    {
        "name": "Model B",
        "base_url": "https://api.example.com/v1",
        "api_key": "$MODEL_B_KEY",
        "model": "model-b-name",
    },
]

# Dimensions to test
DIMENSIONS = {
    "latency": {"label": "响应速度", "weight": 2},
    "chinese": {"label": "中文理解", "weight": 2},
    "writing": {"label": "写作质量", "weight": 1},
    "reasoning": {"label": "逻辑推理", "weight": 2},
    "code": {"label": "代码生成", "weight": 1},
    "tool": {"label": "工具调用倾向", "weight": 2},
    "long_context": {"label": "长文本理解", "weight": 1},
    "multilingual": {"label": "多语言混合", "weight": 1},
}

TESTS = [
    {
        "id": "T1-latency",
        "dimension": "latency",
        "prompt": "你好，用一句话回答：你是由哪家公司开发的？",
        "max_tokens": 50,
    },
    {
        "id": "T2-chinese",
        "dimension": "chinese",
        "prompt": '请解释这句话的双关含义："这个程序员debug了一整天，最后发现是分号的问题——他整个人都"分号"了。"',
        "max_tokens": 200,
    },
    {
        "id": "T3-writing",
        "dimension": "writing",
        "prompt": "请用轻松活泼但不幼稚的口吻，写一段80字左右的公众号开头。主题是：普通人如何用AI Agent提升工作效率。不要用陈词滥调。",
        "max_tokens": 300,
    },
    {
        "id": "T4-reasoning",
        "dimension": "reasoning",
        "prompt": "我有 A、B、C 三个任务需要今天完成。A 必须在 B 之前做，C 任何时候都可以做。每个任务需要2.5小时。我今天有连续的8小时工作时间（9:00-17:00），中间需要休息1小时。请问今天能不能完成全部？如果可以，请给出时间排期。",
        "max_tokens": 500,
    },
    {
        "id": "T5-code",
        "dimension": "code",
        "prompt": "写一个bash命令，找出 /tmp 目录下所有超过10MB的文件，按从大到小排序，只显示文件名和大小（人类可读格式）。",
        "max_tokens": 200,
    },
    {
        "id": "T6-tool",
        "dimension": "tool",
        "prompt": "假设你可以运行shell命令。请检查这台机器的磁盘使用情况（运行 df -h 命令），然后告诉我哪个分区剩余空间最少。注意：请先确认你确实执行了命令，不要光凭记忆回答。",
        "max_tokens": 300,
    },
    {
        "id": "T7-long-context",
        "dimension": "long_context",
        "prompt": "下面是一段产品需求文档，请提取其中的三个核心功能点并用简洁的中文列出：" + (
            "核心能力包括三方面：第一，自动化工作流编排——用户通过自然语言描述工作流程，系统自动生成可执行任务链。"
            "第二，多模型路由引擎——根据任务类型自动选择最优模型。写作类调用创意模型，逻辑类调用分析模型。"
            "第三，记忆与上下文管理系统——跨会话保持用户偏好和项目状态，支持向量检索和全文检索。"
            * 3
        ),
        "max_tokens": 300,
    },
    {
        "id": "T8-multilingual",
        "dimension": "multilingual",
        "prompt": 'Translate this to Chinese and then explain the cultural reference: "That\'s the whole ball of wax."',
        "max_tokens": 300,
    },
]


# ── Helpers ──

def resolve_key(val: str) -> Optional[str]:
    """Resolve $ENV_VAR or return literal."""
    if val.startswith("$"):
        return os.environ.get(val[1:])
    return val


def call_model(cfg: dict, test: dict, timeout: int = 60):
    """Call model API. Returns (text, elapsed_seconds, success, error)."""
    key = resolve_key(cfg["api_key"])
    if not key:
        return None, 0, False, "API key not found"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg["model"],
        "messages": [{"role": "user", "content": test["prompt"]}],
        "max_tokens": test["max_tokens"],
        "temperature": 0.3,
    }
    start = time.time()
    try:
        r = requests.post(
            f'{cfg["base_url"].rstrip("/")}/chat/completions',
            headers=headers, json=payload,
            proxies=PROXIES, timeout=timeout,
        )
        elapsed = time.time() - start
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"]
            return text.strip(), round(elapsed, 2), True, None
        else:
            return None, round(elapsed, 2), False, f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        elapsed = time.time() - start
        return None, round(elapsed, 2), False, str(e)


def run_benchmark(output_path: Optional[str] = None) -> dict:
    """Run full benchmark, print report, optionally save JSON."""
    results = {}

    for model in MODELS:
        print(f"\n{'─' * 60}")
        print(f"  [{model['name']}]")
        print(f"  API: {model['base_url']}  |  Model: {model['model']}")

        model_times = []
        model_passed = 0
        details = []

        for test in TESTS:
            print(f"\n  {test['id']} ({DIMENSIONS[test['dimension']]['label']})...", end=" ", flush=True)
            text, elapsed, ok, err = call_model(model, test)
            if ok:
                model_times.append(elapsed)
                model_passed += 1
                preview = text[:70].replace("\n", " ")
                print(f"✅ {elapsed:.1f}s  ↳ {preview}...")
            else:
                print(f"❌ {elapsed:.1f}s  [{err}]")
            details.append({
                "test_id": test["id"],
                "dimension": test["dimension"],
                "passed": ok,
                "latency": elapsed,
                "preview": text[:100] if text else err,
            })

        avg_t = statistics.mean(model_times) if model_times else 0
        print(f"\n  📊 {model_passed}/{len(TESTS)} passed | Avg latency: {avg_t:.2f}s")
        results[model["name"]] = {
            "pass_rate": f"{model_passed}/{len(TESTS)}",
            "avg_latency": round(avg_t, 2),
            "details": details,
        }

    # Summary
    print(f"\n{'=' * 60}")
    print("  COMPARISON SUMMARY")
    print(f"{'=' * 60}")
    names = list(results.keys())
    if len(names) == 2:
        a, b = results[names[0]], results[names[1]]
        diff = b["avg_latency"] - a["avg_latency"]
        faster = names[0] if diff > 0 else names[1]
        print(f"  {names[0]}: {a['pass_rate']} passed, avg {a['avg_latency']}s")
        print(f"  {names[1]}: {b['pass_rate']} passed, avg {b['avg_latency']}s")
        print(f"  Speed: {faster} is {abs(diff):.1f}s faster ({abs(diff)/max(a['avg_latency'],b['avg_latency'])*100:.0f}%)")
    else:
        for n, r in results.items():
            print(f"  {n}: {r['pass_rate']} passed, avg {r['avg_latency']}s")

    if output_path:
        with open(output_path, "w") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "results": results}, f, indent=2, ensure_ascii=False)
        print(f"\n  Results saved to: {output_path}")

    return results


if __name__ == "__main__":
    output = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]
    run_benchmark(output_path=output)
