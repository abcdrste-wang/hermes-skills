---
name: beijing-zhongkao-resources
description: Free Beijing Zhongkao (中考) past papers resource index — 无忧考网 (51test.net) has 209+ papers across math, Chinese, English, physics. Papers stored as images, accessible via Playwright screenshot + OCR.
version: 1.0.0
---

# Beijing Zhongkao Free Resources

## Source: 无忧考网 (51test.net)

URL pattern: `https://www.51test.net/zhongkao/beijing/{subject}shijuan/`

Subjects available:
- 数学 (shuxue): 42 papers
- 语文 (yuwen): 42 papers
- 英语 (yingyu): 56 papers
- 物理 (wuli): 53 papers
- 化学 (huaxue), 历史 (lishi), 政治 (zhengzhi): also available

Years: 2008-2025+ (shown as year tabs on each page)

## Access Method

1. Navigate to subject page with Playwright
2. Extract paper URLs (`/show/{id}.html`)
3. Each paper page has 4-6 preview images in `<img src="https://img.51test.net/uploadfile/tiku/{year}/{date}/{hash}.png">`
4. Download images directly (no login required)
5. OCR with pytesseract (Chinese + English, PSM 6)

## Paper Structure (2023 Beijing Math)

- Total: 100 points, 120 minutes
- Part 1: 选择题 (Multiple choice) — 16 points, 8 questions × 2pts
- Part 2: 填空题 (Fill-in-blank) — 16 points, 8 questions × 2pts
- 解答题 (Long-form) — 68 points, 11 questions (17-28)

## Key Finding

Images are freely accessible without login. VIP required for Word/PDF downloads but images serve as workable alternative with OCR.

## References

- `references/paper-index.md` — Full subject listing, image extraction pattern, OCR recipe, and 2023 reference paper structure.
