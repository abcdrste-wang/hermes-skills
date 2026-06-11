# User Task-Brief Protocol (User-Specific Style Preference)

## Pattern: User gives task briefs in numbered checklist format

When the user says something like:
> "三个主要问题：1.枪口三改一 2.瞄准镜削高留矮 3.加发光部件"

This is **a precise instruction checklist**, not suggestions. You must:
1. **Treat each numbered item as an exact requirement**
2. **Do NOT add your own extras** — "中间不需要特效" means exactly that: no extra effects
3. **Follow the list order** — items are prioritized, do #1 before #2
4. **Do NOT merge/reinterpret items** — e.g., don't combine #1+3 and decide "maybe they want a glowing muzzle instead"
5. **Check off each item explicitly in the response** — "✅ 1: done, ✅ 2: done, ✅ 3: done"

### Reverse direction

When YOU need to convey task requirements to the user, present as a numbered checklist:
```
三个主要问题需要确认：
1. X — [question/option]
2. Y — [question/option]
3. Z — [question/option]
```
