# AI Reference Image Ambiguity — Lessons from FFAR1 无境空刃

> 2026-06-09 — Bambu AI 生成的黄色点云参考图的方向和特征判断问题

## 参考图方向模糊

Bambu AI 生成的侧面点云图没有明确的"上下"标识。对同一张参考图：

| 询问时间 | 上下文 | Qwen3 判断 | Qwen3-VL-Plus判断 |
|---------|--------|-----------|------------------|
| 2026-06-09 初问 | "这是FFAR1无境空刃科幻步枪" | — | "枪口朝上" |
| 2026-06-09 再问 | "只判断形状朝向，不参考背景信息" | "B) 指向下方" | — |
| 2026-06-09 三次 | "看到一个尖锥，指向哪个方向" | "向下" | — |

**结论**：AI对参考图朝向的判断不可靠，同一模型产出的判断随上下文变化。在3D打印中，方向不重要（打印时可在Cura/PrusaSlicer中旋转），**形状对就行**。

## 叠加对比法（Overlay Comparison）

发现被忽略特征的最有效方法：

1. 渲染重建模型的侧视图（白色背景，深蓝填充，与参考图同比例）
2. 用PIL将重建模型半透明叠加在参考图上
3. 观察：**黄色裸露区域** = 漏建模部分，**蓝色溢出区域** = 过度建模
4. 逐区域修复

**关键发现案例**：腰部椭圆空洞（前后贯通结构）——在5次视觉分析中均被忽略，直到叠加对比图才暴露出来。

```python
from PIL import Image

ref = Image.open('reference.png').convert('RGB')
model = Image.open('model_side.png').convert('RGB')

# Resize to same dimensions
model = model.resize(ref.size)

# Overlay: 50% model (blue) + 50% reference (yellow)
overlay = Image.blend(ref, model, 0.5)
overlay.save('overlay.png')
```

## Qwen3-VL-Plus 评估幻觉清单

该模型在3D模型评估中存在以下幻觉模式：

1. **误标类别**：把FFAR1枪管识别为"GPCR蛋白结构"（游离脂肪酸受体1，FFAR1的巧合名称）
2. **虚构成分**：将投影造成的碟片环阴影判断为"分离的悬浮部件"
3. **否定已有内容**：将带有面法线光照着色的渲染图描述为"只有线框无材质"
4. **冲突判断**：同一张图，第一次说"枪口朝上"，第二次说"朝下"

**对策**：评估成品渲染时必须提供原始参考图作为上下文。单独给渲染图做判断不可靠。
