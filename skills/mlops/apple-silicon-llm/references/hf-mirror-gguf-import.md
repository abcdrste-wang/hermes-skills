# HF Mirror GGUF Download + Ollama Import (China)

When `ollama pull` is slow through Chinese networks (Ollama's US registry has no CDN in China), download the GGUF directly from HF Mirror (8-14 MB/s) and import into Ollama.

## Workflow

### 1. Find the GGUF on HF Mirror

```bash
# Search by model name
curl -s "https://hf-mirror.com/api/models?search=unsloth%2FQwen3.5-4B-GGUF&sort=downloads&direction=-1&limit=5" | \
  python3 -c "import sys,json; data=json.load(sys.stdin); [print(m['modelId'], m['lastModified']) for m in data]"

# Or browse in browser
# https://hf-mirror.com/unsloth/Qwen3.5-4B-GGUF/tree/main
```

Look for GGUF files — typically named like:
- `Qwen3.5-4B-Q4_K_M.gguf` (Q4, 2.4-2.6 GB, recommended for 16GB Macs)
- `Qwen3.5-4B-Q3_K_M.gguf` (Q3, ~2.0 GB, lower quality)
- `Qwen3.5-4B-Q5_K_M.gguf` (Q5, ~3.2 GB, higher quality but more memory)

### 2. Download via curl (direct, no proxy needed)

Chinese domestic models (Qwen series) download at 8-14 MB/s from hf-mirror.com without proxy:

```bash
# Download Q4_K_M (recommended for 16GB Mac Mini M4)
curl -L -o /tmp/Qwen3.5-4B-Q4_K_M.gguf \
  "https://hf-mirror.com/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q4_K_M.gguf"
```

Typical download times on M4 with 100Mbps domestic connection:
- Q4_K_M (2.4 GB): **~3 minutes** (at 14 MB/s)
- Q8_0 (4.9 GB): ~5-7 minutes
- Q2_K (1.6 GB): ~2 minutes

### 3. Create Modelfile and Import into Ollama

```bash
# Create Modelfile
cat > /tmp/Modelfile << 'EOF'
FROM /tmp/Qwen3.5-4B-Q4_K_M.gguf
TEMPLATE "{{ if .System }}{{ .System }}{{ end }}{{ if .Prompt }{{ .Prompt }}{{ end }}{{ .Response }}"
PARAMETER num_ctx 65536
EOF

# Import into Ollama
ollama create qwen3.5:4b -f /tmp/Modelfile

# Verify
ollama list
# Should show: qwen3.5:4b  2.7 GB
```

### 4. Clean up

```bash
rm -f /tmp/Qwen3.5-4B-Q4_K_M.gguf /tmp/Modelfile
```

## Alternative: Python Download with Resume Support

If `curl -L` is interrupted and you need resume:

```python
import urllib.request, urllib.error, os, sys

url = "https://hf-mirror.com/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q4_K_M.gguf"
path = "/tmp/Qwen3.5-4B-Q4_K_M.gguf"

# Check for partial download
resume_bytes = os.path.getsize(path) if os.path.exists(path) else 0

req = urllib.request.Request(url)
if resume_bytes > 0:
    req.add_header('Range', f'bytes={resume_bytes}-')

try:
    with urllib.request.urlopen(req) as response:
        total = int(response.headers.get('Content-Length', 0)) + resume_bytes
        mode = 'ab' if resume_bytes > 0 else 'wb'
        with open(path, mode) as f:
            chunk_size = 8192 * 16
            downloaded = resume_bytes
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                pct = downloaded * 100 // total
                mb = downloaded / 1024 / 1024
                print(f"\r{pct}% ({mb:.1f} MB)", end='', flush=True)
    print(f"\nDownloaded to {path}")
except Exception as e:
    print(f"\nInterrupted at {downloaded or resume_bytes} bytes: {e}")
    sys.exit(1)
```

**Note:** `urllib.request` with range headers is the most reliable resume method in Python. Do NOT pass `resume=True` as a keyword argument to urlopen — it's not a supported parameter and will error.

## Speed Comparison

| Method | Speed | Notes |
|--------|-------|-------|
| `ollama pull qwen3.5:4b` | 200 KB/s - 4 MB/s | Ollama US registry, slow in China |
| `ollama pull qwen3.5:4b` (via V2rayU proxy) | 92 KB/s - 4.4 MB/s | Proxy adds overhead, unreliable |
| `curl -L` from hf-mirror.com | **8-14 MB/s** | ✅ Domestic CDN, no proxy needed |
| `curl -L` from modelscope.cn | **15-30 MB/s** | ✅ Alternative domestic mirror |

## Pitfalls

- **GGUF file size doesn't match Ollama's model size exactly.** Ollama adds ~0.3 GB metadata when creating from Modelfile.
- **Ollama must be running** (`ollama serve` or background service) before `ollama create`.
- **Modelfile path in `FROM` must be absolute** — relative paths may fail.
- **HF Mirror rate limits apply** — about 10-20 concurrent downloads per IP. Sequential downloads are fine.
- **Don't use `ollama pull` with domestic proxy on Chinese models** — Qwen is Ali's model and downloads fastest from domestic mirrors without proxy.
- **`resume=True` parameter does NOT exist in `urllib.request.urlopen()`** — old code snippets often show this incorrectly. Use HTTP `Range` headers for resume instead.
