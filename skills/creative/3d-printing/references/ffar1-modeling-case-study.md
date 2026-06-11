# FFAR1 无境空刃 建模案例研究

> 2026-06-09 会话 — 记录从参考图点云到可打印STL的完整迭代过程

## 参考图信息

- 来源：Bambu AI 生成的黄色点云图（无明确朝向标识）
- 关键发现：参考图的方向是**模糊的**。同一个AI先后判断"枪口朝上"和"枪口朝下"。在3D打印中，方向不重要（打印时可旋转），**形状对就行**
- Qwen3-VL-Plus 在3D模型评估中存在幻觉风险：曾把FFAR1枪管误认为"GPCR蛋白结构"，把渲染图判为"纯黑色空白图"
- 对策：评估成品渲染时必须提供原始参考图作为上下文，不能只给渲染图做判断

## 建模方法迭代

| 版本 | 方法 | 顶点数 | 效果 | 结论 |
|------|------|--------|------|------|
| v3-v4 | 侧面轮廓挤出 | 276-780 | 扁平薄片 | ❌ 看不出立体感 |
| v5 | 参考图点云轮廓提取→挤出 | 290 | 稍好但仍是薄片 | ❌ |
| v6 | 椭圆截面堆叠（20段顶点） | 840 | 有立体感，碟片可见 | ⚠️ 方法正确，细节不足 |
| v7 | 椭圆截面+腰部空洞+翼 | 1176 | 对称性好，翼结构清晰 | ✅ 叠加对齐7.5/10 |
| v8 | 椭圆截面48段+空洞+对称+碟片辐条 | 2080 | 最佳版本，90%对齐 | ✅ 9/10 |

## 椭圆截面堆叠法核心代码模板

```python
# sections = [(y_pos, x_radius, z_radius), ...]
# 沿Y轴从下到上排列

import bpy, bmesh, math, numpy as np

bm = bmesh.new()

# 定义截面（以FFAR1无境空刃为例，约150mm高）
sections = [
    (-75, 20, 12),   # 底部锥尖
    (-65, 35, 18),   # 扩展
    (-50, 48, 24),   # 下部最宽
    (-35, 55, 28),   # 过渡
    (-20, 65, 30),   # 碟片环位置
    (0, 70, 32),     # 腰部最宽（碟片中心）
    (20, 68, 30),    # 腰部上沿
    (35, 60, 26),    # 收窄
    (50, 55, 22),    # 瞄准镜区域
    (60, 50, 20),    # 上部
    (70, 35, 15),    # 枪口环
    (78, 20, 10),    # 枪口开口
]

segments = 24

def make_ring(bm, y, rx, rz, segs):
    verts = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        x = rx * math.cos(a)
        z = rz * math.sin(a)
        v = bm.verts.new((x, y, z))
        verts.append(v)
    return verts

rings = []
for sec in sections:
    rings.append(make_ring(bm, *sec, segments))

# Bridge adjacent rings
for i in range(len(rings) - 1):
    r1 = rings[i]
    r2 = rings[i+1]
    for j in range(segments):
        j2 = (j + 1) % segments
        face = bm.faces.new([r1[j], r1[j2], r2[j2], r2[j]])
    bm.faces.ensure_lookup_table()

# Cap ends
bm.faces.new(reversed(rings[0]))
bm.faces.new(rings[-1])

# Export
mesh = bpy.data.meshes.new("LoftedModel")
bm.to_mesh(mesh)
```

## 关键教训

1. **建模范式比参数调优重要**：v3-v4在同一范式（侧面挤出）上迭代了5版，全是薄片。v5换椭圆截面堆叠后第一版就有质的提升。当用户说"看不出样子"时，必须切换建模范式而不是迭代参数。

2. **腰部椭圆空洞容易被忽略**：参考图侧视点云的腰部有密度稀疏区域（前后贯通的椭圆空洞），但多次分析都被忽略。叠加对比是发现这类特征的最有效手段——把重建模型半透明叠在参考图上，看哪里黄色裸露/蓝色溢出。

3. **对称性必须显式保证**：Blender脚本中必须用镜像约束或直接对称生成，否则不对称的特征会被视觉识别捕捉到。v7之前的版本都有不对称问题，v7加镜像后改善明显。

4. **EEVEE渲染在M4 Mac上不可用**：Blender 5.1在M4（16GB，无独立GPU）的`--background`模式下，EEVEE渲染输出纯黑帧。替代方案：PIL+trimesh面法线光照模拟渲染。

5. **视觉模型评估幻觉**：Qwen3-VL-Plus对3D模型渲染的评估不可靠——会幻觉出不存在特征（"分离部件悬浮"），或把3D物体误认为完全不同的东西（"GPCR蛋白质"）。评估渲染图时必须附带原始参考图作为上下文。
