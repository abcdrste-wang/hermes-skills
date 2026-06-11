# Cura 作为临时渲染替代方案

> 发现时间：2026-06-08
> 场景：Blender EEVEE headless 在 Mac Mini M4 (16GB, 无独显) 上渲染全灰，无法用于模型预览审核。

## 背景

Mac Mini M4 没有独立 GPU，Blender EEVEE headless 渲染输出：
- World background 0.95 → 实际 ~0.74-0.77（灰色偏移）
- 物体材料色 0.5 与背景对比度仅 5%
- 完全没有立体感，用户反馈"看不到全貌"

## 问题

在 Mac Mini M4 环境下，**没有任何一种手段能在 5 秒内生成有质量的彩色 3D 预览**：
- EEVEE 渲染：全灰不可用
- Cycles CPU：30-60 秒/帧，太慢不适合迭代
- Workbench：也无法提供实体质感
- stl_2d_preview.py：只能看轮廓线框，不能看实体体积

## 解决方案

**Cura 5.13.0 切片预览可以充当临时渲染替代。**

原因是 Cura 导入 STL 后，在切片预览模式下会：
1. 自动检测模型边界和缩放
2. 显示带填充纹理的实体切片层（视觉上能看到模型轮廓、厚度和比例）
3. 内置自动修复功能（补洞、水密检查）
4. 渲染不受 GPU 限制（Cura 是基于 OpenGL 渲染的，M4 集成 GPU 完全够用）

## 操作方式

```bash
# 方案1：截图 Cura 窗口（手动）
open -a Ultimaker\ Cura
# 拖入 STL → 自动切片 → cmd+shift+4 截取预览区域

# 方案2：如果能在 headless 模式下截图（待验证）
# /Applications/Ultimaker\ Cura.app/Contents/MacOS/cura -l /path/to/model.stl --slice
# 但 Cura 没有官方的 CLI 批量渲染接口
```

## 局限性

- Cura 不是真正的渲染器：它显示的是切片层，不是表面材质/纹理/光照
- 颜色方案有限：只能看浅灰/深灰/渐变色的切片层，不能展示彩色材质
- 无法设置相机角度：Cura 默认使用等轴测视角，不能自由旋转到特定角度
- 无法批量生成：每张预览图需要手动操作

## 与 stl_2d_preview.py 配合使用

| 用途 | 方案 |
|------|------|
| 快速形状验证（<5s） | stl_2d_preview.py（PIL 2D线框） |
| 体积/实体预览（10s） | Cura 切片预览截图 |
| 最终展示（60s+） | Cycles CPU 渲染 |

**结论：Cura 切片预览是 M4 无独显环境下最好的"实体填充预览"方案，与 stl_2d_preview.py 互补使用。**
