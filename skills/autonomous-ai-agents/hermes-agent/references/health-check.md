# Hermes Agent Health Check Reference

Systematic diagnostics for Hermes Agent on macOS. Run these checks in order when investigating slowness, misconfiguration, or resource pressure.

## 1. Config Validation

```bash
# Missing keys or stale values
hermes config check

# Consistency: top-level provider vs model.provider
# Top-level `provider:` overrides `model.provider:` — if they differ,
# the top-level one wins. Delete the top-level key to let model.provider apply.
cat ~/.hermes/config.yaml

# API keys
hermes doctor
```

**Pitfall — top-level `provider` key:** A `provider: ollama` at the YAML root overrides `model.provider: deepseek`. The correct config for DeepSeek usage is:

```yaml
model:
  provider: deepseek
  default: deepseek-v4-flash
```

Do NOT have a bare `provider: ollama` line at the top level. Only set `model.provider`.

**Pitfall — stale model references:** When switching models (e.g. replacing `qwen3.5-vl:9b` with `qwen3.5:9b`), check that `auxiliary.vision`, `fallback_providers`, and `delegation` don't still reference old model names. Run `hermes doctor` after every config change.

## 2. System Resource Check

```bash
# Memory pressure
memory_pressure | head -10

# Free pages (Mac page size = 16384 bytes)
vm_stat | head -8

# Disk usage
df -h /

# Top processes by RSS
ps axo pid,rss,comm | sort -k2 -rn | head -10
```

**What to look for:**
- `Pages free` below ~20,000 → tight memory
- `memory_pressure` showing "pressure" → swap may be active
- Processes > 1GB RSS → investigate (Safari WebContent, game clients, Electron apps)

## 3. Proxy Check

```bash
# Is the proxy responsive?
curl -s --connect-timeout 3 -x http://127.0.0.1:1087 https://www.google.com > /dev/null && echo "OK" || echo "FAIL"

# Environment variables set?
echo "http_proxy=$http_proxy"
echo "https_proxy=$https_proxy"
```

**Pitfall:** On macOS, proxy env vars must be exported explicitly. GUI apps and launchd services don't inherit shell env.

## 4. Ollama Health

```bash
# Is it running?
ps aux | grep [o]llama

# What models are installed?
~/.local/bin/ollama list
```

**When Ollama is idle** (no models loaded), RSS is ~140MB. Each loaded Q4 model adds ~6-7GB of RSS. Two models = ~13-14GB on a 16GB machine = swap pressure.

**Removing models safely:**
```bash
ollama rm <model-name>
# Keep ollama serve running even with no models — reloads instantly when needed
```

## 5. Hermes Specific Checks

```bash
hermes doctor [--fix]
hermes --version
hermes config | grep -A2 'model:'
```

**"update available" in `hermes doctor`:** The installed version is slightly behind HEAD. Not critical unless features are missing. Do NOT auto-update without asking.

## 6. GPU / M-Series

```bash
system_profiler SPDisplaysDataType | grep -E "Chipset Model|Metal"
# Expected: "Apple M4" + "Metal 3" or "Metal 4"
```
