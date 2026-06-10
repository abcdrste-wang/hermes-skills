# Darwin-skill & Skill-Evolver (WeChat Article Summary)

## Source
"这样做可以让Hermes Agent'打通任督二脉'，闪电般进化！" — 大叔笔记, 2026-06-01
https://mp.weixin.qq.com/s/VTAwjgWJ5QR2bsaUuNh_hQ

## Two Core Components

### darwin-skill (Evaluator)
- **Origin**: GitHub user alchaincyf, inspired by Microsoft Research SkillLens paper
- **Mechanism**: 9-dimension evaluation system, 0-100 scale
  - frontmatter quality, workflow clarity, failure mode encoding, checkpoint design, executability, anti-example blacklist, etc.
- **Key design**: Ratchet mechanism — score can only go up. If score drops after optimization, auto-revert.
- **Independent review**: The agent that modifies the skill and the agent that evaluates it MUST be different. MS paper found self-scoring accuracy is only 46.4%.

### skill-evolver (Optimizer)
- **Origin**: Tsinghua SkillEvolver paper, adapted for Hermes Agent
- **Core principle**: Role separation + closed-loop evolution
  - One AI writes the skill (author), another uses it (executor). Information asymmetry exposes defects naturally.
- **Three phases**:
  1. Strategy diversification — generate 3-4 different execution strategies with substantive differences
  2. Contrastive update — compare success/failure traces at the first divergence point. Patch-only, no full rewrites.
  3. Independent audit — new AI session checks 9 rules, blind to author's justification
- **Failure attribution** (from EmbodiSkill paper): 4 categories
  - Skill defect → fix skill
  - Execution error → log appendix only, don't change skill

## Results
4 rounds of mutual optimization: skill-evolver went from 61 → 86 points.
Key insight: No model swap, no hyperparameter tuning, no data augmentation. Just better skill text.

## Relevance
This is the user-facing implementation of the same self-improvement loop described in `agentic-self-improvement/SKILL.md`. The GEPA optimization framework (Tier 1: skill files) maps directly to skill-evolver's approach. The independent review requirement maps to the benchmark gate hierarchy.
