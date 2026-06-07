# Local Model + Cloud Fallback Setup

Working configuration for **local Ollama model as primary** with **cloud fallback** (e.g., DeepSeek).

## Config Format

```yaml
model:
  provider: ollama           # Maps to "custom" type internally
  default: qwen2.5:7b        # Ollama tag name
  base_url: http://127.0.0.1:11434/v1

auxiliary:
  vision:
    provider: openai-compatible
    model: glm-4v-flash
    base_url: https://open.bigmodel.cn/api/paas/v4/

fallback_providers:          # TOP-LEVEL key, NOT nested under model
  - provider: deepseek
    model: deepseek-v4-flash
    base_url: https://api.deepseek.com/v1
```

## Key Facts

### `provider: ollama` → Maps to `"custom"` internally
- In `hermes_cli/providers.py` (line 359): `"ollama": "custom"` — bare "ollama" = local
- Uses `model.base_url` for the endpoint
- API key not required for localhost; code auto-provides `"no-key-required"` placeholder
- `hermes doctor` does NOT list `ollama` in its recognized provider set (it only shows `ollama-cloud`), but the mapping works at runtime

### `hermes doctor` recognized providers (does NOT include bare `ollama`)
```
ai-gateway, alibaba, alibaba-coding-plan, anthropic, arcee, auto,
azure-foundry, bedrock, copilot, copilot-acp, custom, deepseek, gemini, gmi,
google-gemini-cli, huggingface, kilocode, kimi-coding, kimi-coding-cn, lmstudio,
minimax, minimax-cn, minimax-oauth, nous, novita, novita-ai, novitaai, nvidia,
ollama-cloud, openai-codex, opencode-go, opencode-zen, openrouter, qwen-oauth,
stepfun, tencent-tokenhub, xai, xai-oauth, xiaomi, zai
```

### `fallback_providers` must be a top-level list
- Read via `CLI_CONFIG.get("fallback_providers")` in `cli.py`, `fallback_cmd.py`, `gateway/run.py`, `cron/scheduler.py`
- Format: list of dicts with `{provider, model, base_url?}`
- NOT `model.fallback` (no code path reads that format)
- Legacy `fallback_model` single-dict format auto-migrates on first edit via `hermes fallback add`
- DEFAULT_CONFIG defines `"fallback_providers": []`

### Fallback triggers
- Rate-limit (429), server overload (5xx), connection timeouts, DNS failures, credential pool exhaustion
- For local Ollama: connection refused (Ollama not running) triggers fallback immediately

## Memory Budget (16GB Mac Mini M4)

| Component | Memory |
|-----------|--------|
| Qwen 2.5 7B (Q4_K_M) | ~4.5 GB |
| KV cache (8K context) | ~0.5 GB |
| Hermes Agent | ~0.3 GB |
| macOS | ~4.5 GB |
| **Total** | **~9.8 GB / 16 GB** ✅ |

For the Ollama plist, pin `OLLAMA_CONTEXT_LENGTH=8192` via EnvironmentVariables to prevent Ollama from allocating oversized KV caches.

## Verification

```bash
# Check Ollama is running
~/.local/bin/ollama ps

# Check model is pulled
~/.local/bin/ollama list

# Test model inference
~/.local/bin/ollama run qwen2.5:7b "你好"

# Verify Hermes config
hermes doctor
hermes fallback list
```
