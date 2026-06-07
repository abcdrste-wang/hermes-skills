---
name: llama-cpp
description: llama.cpp local GGUF inference + HF Hub model discovery.
version: 2.1.2
author: Orchestra Research
license: MIT
dependencies: [llama-cpp-python>=0.2.0]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [llama.cpp, GGUF, Quantization, Hugging Face Hub, CPU Inference, Apple Silicon, Edge Deployment, AMD GPUs, Intel GPUs, NVIDIA, URL-first]
---

# llama.cpp + GGUF

Use this skill for local GGUF inference, quant selection, or Hugging Face repo discovery for llama.cpp.

## When to use

- Run local models on CPU, Apple Silicon, CUDA, ROCm, or Intel GPUs
- Find the right GGUF for a specific Hugging Face repo
- Build a `llama-server` or `llama-cli` command from the Hub
- Search the Hub for models that already support llama.cpp
- Enumerate available `.gguf` files and sizes for a repo
- Decide between Q4/Q5/Q6/IQ variants for the user's RAM or VRAM

## Model Discovery workflow

Prefer URL workflows before asking for `hf`, Python, or custom scripts.

1. Search for candidate repos on the Hub:
   - Base: `https://huggingface.co/models?apps=llama.cpp&sort=trending`
   - Add `search=<term>` for a model family
   - Add `num_parameters=min:0,max:24B` or similar when the user has size constraints
2. Open the repo with the llama.cpp local-app view:
   - `https://huggingface.co/<repo>?local-app=llama.cpp`
3. Treat the local-app snippet as the source of truth when it is visible:
   - copy the exact `llama-server` or `llama-cli` command
   - report the recommended quant exactly as HF shows it
4. Read the same `?local-app=llama.cpp` URL as page text or HTML and extract the section under `Hardware compatibility`:
   - prefer its exact quant labels and sizes over generic tables
   - keep repo-specific labels such as `UD-Q4_K_M` or `IQ4_NL_XL`
   - if that section is not visible in the fetched page source, say so and fall back to the tree API plus generic quant guidance
5. Query the tree API to confirm what actually exists:
   - `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`
   - keep entries where `type` is `file` and `path` ends with `.gguf`
   - use `path` and `size` as the source of truth for filenames and byte sizes
   - separate quantized checkpoints from `mmproj-*.gguf` projector files and `BF16/` shard files
   - use `https://huggingface.co/<repo>/tree/main` only as a human fallback
6. If the local-app snippet is not text-visible, reconstruct the command from the repo plus the chosen quant:
   - shorthand quant selection: `llama-server -hf <repo>:<QUANT>`
   - exact-file fallback: `llama-server --hf-repo <repo> --hf-file <filename.gguf>`
7. Only suggest conversion from Transformers weights if the repo does not already expose GGUF files.

## Quick start

### Install llama.cpp

```bash
# macOS / Linux (simplest)
brew install llama.cpp
```

```bash
winget install llama.cpp
```

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release
```

### Run directly from the Hugging Face Hub

```bash
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

```bash
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

### Run an exact GGUF file from the Hub

Use this when the tree API shows custom file naming or the exact HF snippet is missing.

```bash
llama-server \
    --hf-repo microsoft/Phi-3-mini-4k-instruct-gguf \
    --hf-file Phi-3-mini-4k-instruct-q4.gguf \
    -c 4096
```

### OpenAI-compatible server check

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a limerick about Python exceptions"}
    ]
  }'
```

## Python bindings (llama-cpp-python)

`pip install llama-cpp-python` (CUDA: `CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir`; Metal: `CMAKE_ARGS="-DGGML_METAL=on" ...`).

### Basic generation

```python
from llama_cpp import Llama

llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,     # 0 for CPU, 99 to offload everything
    n_threads=8,
)

out = llm("What is machine learning?", max_tokens=256, temperature=0.7)
print(out["choices"][0]["text"])
```

### Chat + streaming

```python
llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,
    chat_format="llama-3",   # or "chatml", "mistral", etc.
)

resp = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
    ],
    max_tokens=256,
)
print(resp["choices"][0]["message"]["content"])

# Streaming
for chunk in llm("Explain quantum computing:", max_tokens=256, stream=True):
    print(chunk["choices"][0]["text"], end="", flush=True)
```

### Embeddings

```python
llm = Llama(model_path="./model-q4_k_m.gguf", embedding=True, n_gpu_layers=35)
vec = llm.embed("This is a test sentence.")
print(f"Embedding dimension: {len(vec)}")
```

You can also load a GGUF straight from the Hub:

```python
llm = Llama.from_pretrained(
    repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
    filename="*Q4_K_M.gguf",
    n_gpu_layers=35,
)
```

## Choosing a quant

Use the Hub page first, generic heuristics second.

- Prefer the exact quant that HF marks as compatible for the user's hardware profile.
- For general chat, start with `Q4_K_M`.
- For code or technical work, prefer `Q5_K_M` or `Q6_K` if memory allows.
- For very tight RAM budgets, consider `Q3_K_M`, `IQ` variants, or `Q2` variants only if the user explicitly prioritizes fit over quality.
- For multimodal repos, mention `mmproj-*.gguf` separately. The projector is not the main model file.
- Do not normalize repo-native labels. If the page says `UD-Q4_K_M`, report `UD-Q4_K_M`.

## Extracting available GGUFs from a repo

When the user asks what GGUFs exist, return:

- filename
- file size
- quant label
- whether it is a main model or an auxiliary projector

Ignore unless requested:

- README
- BF16 shard files
- imatrix blobs or calibration artifacts

Use the tree API for this step:

- `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`

For a repo like `unsloth/Qwen3.6-35B-A3B-GGUF`, the local-app page can show quant chips such as `UD-Q4_K_M`, `UD-Q5_K_M`, `UD-Q6_K`, and `Q8_0`, while the tree API exposes exact file paths such as `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` and `Qwen3.6-35B-A3B-Q8_0.gguf` with byte sizes. Use the tree API to turn a quant label into an exact filename.

## Search patterns

Use these URL shapes directly:

```text
https://huggingface.co/models?apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&num_parameters=min:0,max:24B&sort=trending
https://huggingface.co/<repo>?local-app=llama.cpp
https://huggingface.co/api/models/<repo>/tree/main?recursive=true
https://huggingface.co/<repo>/tree/main
```

## Output format

When answering discovery requests, prefer a compact structured result like:

```text
Repo: <repo>
Recommended quant from HF: <label> (<size>)
llama-server: <command>
Other GGUFs:
- <filename> - <size>
- <filename> - <size>
Source URLs:
- <local-app URL>
- <tree API URL>
```

## References

- **[hub-discovery.md](references/hub-discovery.md)** - URL-only Hugging Face workflows, search patterns, GGUF extraction, and command reconstruction
- **[advanced-usage.md](references/advanced-usage.md)** — speculative decoding, batched inference, grammar-constrained generation, LoRA, multi-GPU, custom builds, benchmark scripts
- **[quantization.md](references/quantization.md)** — quant quality tradeoffs, when to use Q4/Q5/Q6/IQ, model size scaling, imatrix
- **[server.md](references/server.md)** — direct-from-Hub server launch, OpenAI API endpoints, Docker deployment, NGINX load balancing, monitoring
- **[optimization.md](references/optimization.md)** — CPU threading, BLAS, GPU offload heuristics, batch tuning, benchmarks
- **[troubleshooting.md](references/troubleshooting.md)** — install/convert/quantize/inference/server issues, Apple Silicon, debugging

## Ollama (llama.cpp-based model runner)

Ollama wraps llama.cpp with a model registry, OpenAI-compatible API, and easy pull/run workflow. Use it when the user wants a turnkey local inference server rather than running `llama-server` directly.

### Installing Ollama on macOS

**Brew** (simplest when bottles are available):
```bash
brew install ollama
```

**From source** (when brew fails — network issues, missing bottles):
```bash
# Clone from a domestic mirror if GitHub is slow
git clone --depth 1 https://gitee.com/mirrors/ollama.git /tmp/ollama-source
cd /tmp/ollama-source

# Build with Chinese Go module proxy
export GOPROXY=https://goproxy.cn,direct
go build -o ~/.local/bin/ollama .

# Start the server
~/.local/bin/ollama serve
# Server listens on http://127.0.0.1:11434
# Ollama's built-in runner detects Apple Silicon / Metal automatically
```

### Installing Models in China / Behind Slow Networks

The Ollama registry (`registry.ollama.ai`) can be unreliable from China. Preferred strategy:

1. **Try direct `ollama pull <model>` first** — Chinese domestic models (Qwen, InternVL) may download at 5–20 MB/s without proxy
2. **If slow, kill and retry through a proxy** — speeds fluctuate wildly (11 MB/s → 18 KB/s). Retrying through V2rayU/Surge proxy sometimes stabilizes it
3. **Fallback: download GGUF from hf-mirror.com and import:**
   ```bash
   # 1. Find the GGUF on hf-mirror.com
   # Search: https://hf-mirror.com/models?search=<model-name>+GGUF
   # Community quantizers like `mradermacher` often have Q4_K_M variants
   
   # 2. Download GGUF + mmproj (multimodal projector)
   curl -L -o /tmp/model.q4.gguf \
     "https://hf-mirror.com/<repo>/resolve/main/<file>.Q4_K_M.gguf"
   curl -L -o /tmp/model.mmproj.gguf \
     "https://hf-mirror.com/<repo>/resolve/main/<file>.mmproj-Q8_0.gguf"
   
   # 3. Create Modelfile and import into Ollama
   cat > /tmp/Modelfile << 'EOF'
   FROM /tmp/model.q4.gguf
   TEMPLATE "{{ .System }}\n{{ .Prompt }}"
   EOF
   ollama create my-model -f /tmp/Modelfile
   ```

4. **Tested Chinese mirrors and their typical speeds:**
   - `hf-mirror.com` — 0.4–19 MB/s (best for GGUF files)
   - `gh.ddlc.top` — 0.3–10 MB/s (GitHub release mirror)
   - `ghproxy.net` — 14–30 KB/s (slow, avoid for large files)
   - Direct Ollama registry — 0.02–11 MB/s (unstable)

### Memory Planning for Apple Silicon (Unified Memory)

GGUF models share RAM with the system — there is no dedicated VRAM.

| Quant | 7B model | 9B model | 14B model | Context 4K | Context 16K | Context 32K |
|-------|----------|----------|-----------|------------|-------------|-------------|
| Q4_K_M | ~4.5 GB | ~5.5 GB | ~8.5 GB | +0.8 GB | +2.5 GB | +4.0 GB |
| Q5_K_M | ~5.5 GB | ~7.0 GB | ~10.5 GB | +0.8 GB | +2.5 GB | +4.0 GB |
| Q8_0 | ~7.5 GB | ~9.5 GB | ~14.5 GB | +0.8 GB | +2.5 GB | +4.0 GB |

**16GB M4 Mac mini recommendation (running Hermes + Ollama):**
- System base: ~3.5 GB, Hermes: ~1.5 GB, Ollama server: ~0.15 GB
- Best 9B Q4_K_M config: model 5.5 GB + 16K context 2.5 GB = ~8 GB → total ~13 GB, safe
- 32K context: +4 GB → total ~15 GB, tight — enable swap or use 16K
- 4K context: fastest, only 6.5 GB total

Set environment variables before starting Ollama server to control memory:
```bash
export OLLAMA_KV_CACHE_TYPE=q8_0      # Quantize KV cache to save ~0.5-1 GB
export OLLAMA_NUM_PARALLEL=1           # Single request at a time
export OLLAMA_MAX_LOADED_MODELS=1      # One model loaded
export OLLAMA_KEEP_ALIVE=-1            # Keep model loaded permanently
ollama serve
```

At inference time, set context length explicitly:
```bash
ollama run <model> --num_ctx 16384     # 16K — best balance
ollama run <model> --num_ctx 4096      # 4K — most memory-efficient
```

**Context size reference:**
- 4K (~4096 tokens) = ~8,000 Chinese chars = ~30 pages of dialogue
- 16K (~16384 tokens) = ~32,000 Chinese chars = short document + conversation
- 32K (~32768 tokens) = ~65,000 Chinese chars = long document

### Model Selection for M4/16GB

| Model | Size | Type | Speed (Q4) | Verdict |
|-------|------|------|------------|---------|
| qwen3.5:9b | 6.6 GB | Multimodal VL | 18-25 tok/s | ✅ Best Chinese multimodal |
| qwen2.5vl:7b | 6.0 GB | Multimodal VL | 25-35 tok/s | ✅ Good, older gen |
| qwen2.5:7b | 4.5 GB | Text only | 30-40 tok/s | ✅ Fastest, but no vision |
| moondream | 1.6 GB | Tiny VL | 50+ tok/s | ⚠️ Lightweight, limited quality |

### PaddleOCR Integration

For high-accuracy Chinese handwriting/printed text OCR, PaddleOCR outperforms LLM vision:
```bash
pip install paddleocr
```
```python
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch')
result = ocr.ocr('image.jpg')  # Returns structured text with bounding boxes
```
Best for: exam papers, handwritten notes, printed documents with complex layouts.

## Resources

- **GitHub**: https://github.com/ggml-org/llama.cpp
- **Ollama**: https://ollama.com
- **Ollama Library**: https://ollama.com/library
- **Hugging Face GGUF + llama.cpp docs**: https://huggingface.co/docs/hub/gguf-llamacpp
- **Hugging Face Local Apps docs**: https://huggingface.co/docs/hub/main/local-apps
- **Hugging Face Local Agents docs**: https://huggingface.co/docs/hub/agents-local
- **Example local-app page**: https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF?local-app=llama.cpp
- **Example tree API**: https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main?recursive=true
- **Example llama.cpp search**: https://huggingface.co/models?num_parameters=min:0,max:24B&apps=llama.cpp&sort=trending
- **Chinese HF mirror**: https://hf-mirror.com
- **PaddleOCR GitHub**: https://github.com/PaddlePaddle/PaddleOCR
- **License**: MIT
