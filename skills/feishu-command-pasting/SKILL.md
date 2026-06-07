---
name: feishu-command-pasting
description: How to deliver shell commands through Feishu without losing indentation or formatting. Covers one-shot delivery patterns, config-writing strategies, and the root cause of whitespace stripping.
---

# Feishu Command Pasting

Feishu (Lark) **always strips leading whitespace** from code blocks when the user copies them — every ` ` or ` ` at the start of a line inside a code block is silently removed. This makes heredocs, multi-line Python snippets, and any indented block **unusable** through Feishu.

## ❌ What DOESN'T work (tested and confirmed broken)

| Approach | Why it fails |
|----------|-------------|
| `cat > file << 'EOF'` with indented lines | Feishu strips every leading space inside the heredoc |
| `python3 << 'PYEOF'` with indented list entries | Same — the Python source loses its indentation |
| `printf '...'` with literal spaces inside quotes | The shell runs it correctly (spaces are in the string), but the user rarely runs this correctly on first try — it's visually confusing |
| `base64 ... \\| base64 -d > file` | **Does work** when the base64 is correct — but I generated the first base64 with wrong indentation (1 space instead of 2) because I wrote the source YAML with wrong indentation in the code block. Generate the base64 on YOUR server first, verify the decode produces correct YAML, then send the base64 string. |
| `echo '...' > file` (single line per command) | **Actually DOES work**, but the user hates receiving 10+ separate commands — they want one command that does everything |
| Code blocks ending with `&&` chaining | Feishu's "Copy" button copies the visible text, which has already lost its leading whitespace |

## ✅ What WORKS (verified)

### Option 1: Single-line `python3 -c` with programmatic spaces (⭐ most reliable)
Generate indentation INSIDE Python so it's immune to copy-paste corruption:

```python
python3 -c "p='/path/to/file';s=chr(32)*2;t='key:\n'+s+'subkey: value\n';open(p,'w').write(t)"
```

Key technique: `chr(32)*N` produces exactly N space characters within Python's runtime — no leading whitespace exists anywhere in the command text that Feishu could strip. For `custom_providers` YAML with nested list items, use `s` for top-level indent and `s*2` for sub-items.

### Option 2: `hermes config edit`
Opens vim/nano — user types the content directly with their own keyboard. Indentation is whatever they type, no copy-paste involved. **Best when the file is small and the user knows vim basics.**

### Option 3: `hermes config set` for individual values
```bash
hermes config set model.provider ollama
```
Only works for flat key-value pairs. Cannot write nested YAML structures like `custom_providers:`, `auxiliary.vision:`, etc.

## 🚫 Golden Rule: NEVER split into multiple commands

The user **strongly hates** being given 2+ separate commands to copy-paste one at a time. Every command you send must be a **single compound command** that does everything:
- Write the file
- Verify the content
- Kill old processes
- Restart the service

One copy → one paste → done. The user should never have to paste twice.

Example of a WRONG approach (what I did in this session, got yelled at):
```
# Step 1: write config
echo '...' > file
# Step 2: verify
cat file
# Step 3: restart
pkill ...
```

Example of a CORRECT approach:
```bash
python3 -c "..." && cat file && pkill ... && nohup ... &
```

## ⚠️ Critical Failure Pattern: Don't Blindly Try Multiple Approaches

**If the first 2-3 command-writing attempts fail, STOP and research the root cause instead of trying 4+ different variants.**

In this session, I wasted the user's time by sending 6+ different approaches (base64, printf, heredoc, multi-echo, Python heredoc, Python single-line) in rapid succession without verifying why each one failed. The user explicitly called me out: "不要瞎试了，你去搜索找原因" (stop blindly trying, go research the root cause).

**Correct workflow when Feishu commands fail:**
1. On first failure (e.g. indentation wrong), try 1-2 alternative delivery methods
2. If those also fail, **stop sending commands to the user**. Instead, write the exact command on YOUR server, verify it produces the right output, then send the VERIFIED command once.
3. If you can't verify on your server (wrong OS, missing dependencies), explain to the user what you want them to check and WHY, rather than sending another untested variant.

The root cause of every single failure in this session was the same: Feishu strips leading whitespace. Every alternative approach I tried had the exact same root cause. I should have identified this after 2 failures and switched to the one approach that truly works: single-line `python3 -c` with `chr(32)*N`, verified on my own server first.

## 🧠 Root Cause Detail

Feishu's markdown rendering has two copy mechanisms:

1. **The "Copy" button on code blocks** (users click this) — **strips leading whitespace** from every line. A line like `  key: value` becomes `key: value` after copying. This is the primary culprit.

2. **Manual text selection + Ctrl+C** — preserves whitespace but requires the user to precisely select the text, which is tedious.

When writing code blocks in Feishu responses, you MUST assume that any line starting with spaces will have those spaces stripped when the user clicks "Copy". The only safe text is text where every line starts at column 0.

## ⚠️ API Key Truncation via `.env` Edits

When delivering or describing `.env` file edits through Feishu, API keys can get **truncated with literal `...` characters** if:
1. The user or an agent script edits `.env` and the key value includes `...` (e.g., `DEEPSEEK_API_KEY=sk-1e7...979a`)
2. Feishu's display truncation of long strings gets copy-pasted as-is into the file

This produces a **silent 401 error**: the key appears to be there (right prefix + right suffix), but the middle bytes are literally `...` (three dots, 0x2E 0x2E 0x2E), not the real key bytes.

**Detection:**
```bash
grep DEEPSEEK_API_KEY ~/.hermes/.env
# If output contains literal '...' between prefix and suffix → corrupted
```

**Fix:** Write the full key from the original source (password manager, server backup, DeepSeek console), not from a Feishu-displayed truncated version.

**Prevention:** Never include API key values in Feishu code blocks. If you need to show the user an example, use placeholder text (`sk-your-key-here`). When generating rescue.sh or config updates, embed the real key in base64 on YOUR server first, then send the base64 — the key never appears as visible text in Feishu.

## 🧠 Related: Injecting Behavior via `personality` Field

When setting up a Hermes Agent instance via Feishu (e.g. Mac Mini bot), the `personality:` field in `config.yaml` is delivered as part of the base64 config payload. This field acts as a persistent system prompt override and is the right place to embed:

- **Self-awareness** — what model it runs, what provider
- **Behavioral constraints** — be concise, don't show reasoning
- **Role/identity** — who the bot is for this device

If the user later complains that the bot is too verbose or doesn't know its own model, the fix is to update the `personality` field in config.yaml and restart. See `references/hermes-ollama-macos-config.md` for the exact personality payload and delivery recipe.

## 📚 References

See `references/hermes-ollama-macos-config.md` for the exact one-liner that configures Hermes to use a local Ollama instance on macOS — the concrete recipe that emerged from debugging this problem.
