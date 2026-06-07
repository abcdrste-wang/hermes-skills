# Hermes + Ollama Local on macOS — Complete Setup Recipe

This is the exact configuration that works for running Hermes Agent (v0.14.0+) on macOS
with a local Ollama instance and GLM-4V-Flash for vision (free).

## Machine Specs
- Mac Mini M4 (16GB RAM, 256GB SSD)
- macOS, zsh shell
- Hermes v0.14.0

## Prerequisites
- Ollama installed and running (`ollama serve`)
- Model pulled: `ollama pull qwen2.5:7b`
- Ollama health check: `curl http://127.0.0.1:11434/api/tags`

## The Config

### Single-line write command (immune to Feishu whitespace stripping)

```python
python3 -c "p='/Users/a1/.hermes/config.yaml';s=chr(32)*2;t='model:\n'+s+'default: qwen2.5:7b\n'+s+'provider: ollama\n'+s+'base_url: http://127.0.0.1:11434/v1\n'+s+'context_length: 64000\n\ncustom_providers:\n'+s+'- name: ollama\n'+s*2+'base_url: http://127.0.0.1:11434/v1\n'+s*2+'default_model: qwen2.5:7b\n\nauxiliary:\n'+s+'vision:\n'+s*2+'provider: openai-compatible\n'+s*2+'model: glm-4v-flash\n'+s*2+'base_url: https://open.bigmodel.cn/api/paas/v4/\n\napprovals:\n'+s+'mode: manual\n';open(p,'w').write(t);import pathlib;print(repr(pathlib.Path(p).read_text()))"
```

### Equivalent YAML
```yaml
model:
  default: qwen2.5:7b
  provider: ollama
  base_url: http://127.0.0.1:11434/v1
  context_length: 64000

custom_providers:
  - name: ollama
    base_url: http://127.0.0.1:11434/v1
    default_model: qwen2.5:7b

auxiliary:
  vision:
    provider: openai-compatible
    model: glm-4v-flash
    base_url: https://open.bigmodel.cn/api/paas/v4/

approvals:
  mode: manual
```

## Key Findings

### 1. `context_length: 64000` is required
qwen2.5:7b auto-detects at 32K context. Hermes hard-rejects models with <64K context
(`MINIMUM_CONTEXT_LENGTH = 64_000` in `agent/model_metadata.py`). Setting
`context_length: 64000` in the model config bypasses this check — Hermes trusts your
override. The model will handle truncation beyond its actual 32K naturally.

### 2. `provider: ollama` maps to `custom` internally
In `hermes_cli/auth.py`, `"ollama": "custom"`. The runtime resolution chain
(`_resolve_openrouter_runtime` in `runtime_provider.py`) reads `model.base_url` from
config and returns `api_key="no-key-required"` as a placeholder for the OpenAI SDK.

### 3. `custom_providers` entry is optional but helpful
Adding a `custom_providers` entry for ollama gives the runtime resolver an explicit
match, which helps if the provider alias resolution chain doesn't work for some reason.

### 4. The auxiliary compression model also needs the override
If the main model passes the 64K check but auxiliary compression fails, you must add
`context_length: 64000` under `auxiliary:` too (or set `auxiliary.compression.context_length`).

## Startup & Restart

```bash
pkill -f "hermes_cli" && sleep 2 && nohup hermes gateway start > /tmp/hermes-gateway.log 2>&1 &
```

Or in foreground (for debugging):
```bash
hermes gateway run --replace
```
Run this in a dedicated terminal and leave it open.

## Adding `personality` Field (Self-Awareness + Behavioral Guide)

Hermes config.yaml supports a `personality:` field at the top level that acts as a **persistent system prompt override** — it's injected into every user session so the bot knows its identity and behavior expectations without needing a skill or memory query.

### Use Cases

1. **Self-awareness**: Tell the bot which model it's running, so when asked "what model are you?" it can answer directly instead of searching session memory or hallucinating.
2. **Conciseness enforcement**: Embed the user's verbosity preference — "不展示推理过程" (don't show reasoning), "不列出步骤" (don't list steps), "直接给结论" (give conclusions directly).
3. **Role definition**: Set the bot's tone, scope, and constraints per instance.

### Example

```yaml
personality: 你是运行在Mac Mini上的AI助手，使用本地Ollama部署的qwen2.5:7b模型。
回答简洁直接，不展示推理过程，不列出步骤。当用户问你的身份或模型时，直接回答你是qwen2.5:7b（Ollama本地模型）。
不讲废话，一句话给结论。
```

### Delivering `personality` + Full Config via Base64 Through Feishu

The `personality` field must be embedded in a full config.yaml. Use the same base64 pattern as the main config delivery (see the `feishu-command-pasting` skill). Generate the base64 on YOUR server first, verify the decode produces correct YAML including the `personality:` line, then send the single base64 command to the user.

### Pitfall: Personality Must Include Conciseness If User Complains About Verbosity

The Mac Mini bot's default Hermes behavior is verbose — it shows reasoning, suggests terminal commands, lists steps. The user explicitly told it: **"你的推理过程不用发给我，你直接把结果告诉我就可以了"** (Don't send me your reasoning, just tell me the result directly).

If the `personality` only covers self-identification without also addressing conciseness, the bot will still be verbose. Any personality for a user who values conciseness MUST include both:
1. Self-awareness (what model/identity)
2. Conciseness instruction (no reasoning/step display)

## Verification

The gateway banner should show:
```
◆ Model: qwen2.5:7b
◆ Provider: ollama
◆ Context: 32K tokens (config)    # or 64K if context_length override matches
◆ Endpoint: http://127.0.0.1:11434/v1
```

Send a test message. If the bot responds, it's working.
