# Beijing Zhongkao Paper URLs (无忧考网)

Total: 209 papers across 4 subjects, years ~2008-2025.

## Subject Pages (entry points)

| Subject | URL | Papers |
|---------|-----|--------|
| 数学 | https://www.51test.net/zhongkao/beijing/shuxueshijuan/ | 42 |
| 语文 | https://www.51test.net/zhongkao/beijing/yuwenshijuan/ | 42 |
| 英语 | https://www.51test.net/zhongkao/beijing/yingyushijuan/ | 56 |
| 物理 | https://www.51test.net/zhongkao/beijing/wulishijuan/ | 53 |
| 化学 | https://www.51test.net/zhongkao/beijing/huaxueshijuan/ | ~25 |
| 历史 | https://www.51test.net/zhongkao/beijing/lishishijuan/ | ~25 |
| 政治 | https://www.51test.net/zhongkao/beijing/zhengzhishijuan/ | ~25 |
| 真题汇总 | https://www.51test.net/zhongkao/beijing/zhenti/ | 42 |

## Image Extraction Pattern

Each paper page (`/show/{id}.html`) contains 4-6 preview images:

```html
<img src="https://img.51test.net/uploadfile/tiku/2023/0708/1423030552839.png">
```

Images are freely accessible without login. VIP required for Word/PDF download.

## OCR Recipe

```python
import pytesseract
from PIL import Image

img = Image.open('paper_page.png')
# Chinese + English, PSM 6 for uniform blocks
text = pytesseract.image_to_string(img, lang='chi_sim+eng', config='--psm 6')
```

**OCRing math papers**: Math symbols (√, ², π, ≤, ∈) have poor OCR accuracy (~60%).
For math papers, the OCR output is usable for structure analysis (question count,
topic coverage, difficulty distribution) but NOT for verbatim question reproduction.
For generating practice questions, use OCR to understand the pattern and difficulty,
then generate fresh questions matching the style.

## 2023 Beijing Math Paper (Reference)

- Title: 2023年北京延庆中考数学真题及答案
- Score: 100 points, 120 minutes
- Structure:
  - 选择题 (Multiple choice): 8 questions × 2 pts = 16 pts
  - 填空题 (Fill-in-blank): 8 questions × 2 pts = 16 pts
  - 解答题 (Long-form): 11 questions (Q17-28) = 68 pts
- Topics covered: scientific notation, symmetry, angles, algebra, geometry,
  probability, functions, circles, trigonometry, coordinate geometry

## Paper ID List (sample)

Paper IDs are numeric. Full list cached at `/tmp/beijing_zhongkao/paper_ids.txt`.
Example URLs:
- https://www.51test.net/show/10879720.html (2023 延庆 数学)
- https://www.51test.net/show/10896483.html (2025 数学)
