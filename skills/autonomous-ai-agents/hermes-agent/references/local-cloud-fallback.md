# Local Model + Cloud Fallback Pattern

Use a free local model (Ollama) as the everyday default, with a cloud model as instant fallback when the local server is down or overloaded.

## Configuration

```yaml
model:
  provider: ollama                 # Local default
  default: qwen2.5:7b
  base_url: http://127.0.0.1:11434/v1

fallback_providers:
  - provider: deepseek             # Cloud fallback
    model: deepseek-v4-flash
    base_url: https://api.deepseek.com/v1

auxiliary:
  vision:
    provider: zai                  # Separate vision model
    model: glm-4v-flash
    base_url: https://open.bigmodel.cn/api/paas/v4/
```

## How It Works

| Local Ollama status | Active model |
|---------------------|-------------|
| Running, loads model | Qwen 2.5 7B (zero latency, free) |
| Not running / connection refused | Auto-fallback to DeepSeek |
| Model loading timeout | Auto-fallback to DeepSeek |

The fallback triggers on: connection refused, DNS failure, 5xx, timeout, credential pool exhaustion. It does NOT trigger on model response quality issues or tool execution failures inside a working session.

## Validating the Setup

```bash
# 1. Test local model
~/.local/bin/ollama run qwen2.5:7b "Hi" 2>&1

# 2. Verify Hermes sees the provider
hermes doctor 2>&1 | grep -i provider

# 3. Quick end-to-end test
hermes chat -q "Hello" -Q

# 4. Simulate fallback: stop Ollama, then run again
# hermes will automatically fall back to DeepSeek
```

## Pitfalls

- `openai-compatible` is NOT a valid provider name. Use `ollama` or `custom`.
- `provider: ollama` maps to `custom` type internally — no special Ollama integration.
- Local Ollama needs to stay running in background (`launchctl` recommended on macOS).
- Ollama's context length default is 2048 tokens — set via `OLLAMA_CONTEXT_LENGTH=8192` for Qwen 2.5 7B.
