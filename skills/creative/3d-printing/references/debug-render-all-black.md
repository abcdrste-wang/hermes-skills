# Debugging "All Black" Render — OPPO Find N5 Phone Case Case Study

> 实盘记录：Blender 5.1.2 headless 模式渲染手机壳时连续 8 次失败（v1-v8）的诊断和修复过程。

## 时间线

| 迭代 | 尝试 | 结果 | 关键发现 |
|------|------|------|---------|
| v1 | EEVEE 默认设置 | 全黑 (mean=57) | 首次渲染，模型尺寸未知 |
| v2 | 亮灰材质+浅背景 | 全黑 (mean=57) | 材质颜色无影响 |
| v3 | 红蓝双色+三光系统 | 全黑 (mean=57) | 光源无效 |
| v4 | Workbench 引擎+MATERIAL模式 | 极暗 (mean=62) | 引擎切换无效 |
| v5 | Cycles 引擎+三光 | 全均匀 (mean=58.5) | 所有引擎均不可见 |
| v6 | 新STL(numpy-stl)+Workbench | 全均匀 (mean=58.6) | 换 STL 也不行 |
| v7 | 修复相机创建顺序 | 偏暗 (mean=46.7) | 相机位置有变化但颜色不对 |
| v8 | OpenGL viewport render | RuntimeError | background模式无opengl context |

## 根因

**STL 模型尺寸错误**：最初的 Blender BMesh 脚本生成的手机壳在 Y 方向仅 5mm（期望 160mm），且位置 Z=-4~-5mm（在地平面以下）。STL 顶点范围：

```
FindN5_Case_Left.stl (old Blender version):
  X: -111.0 ~ -41.0  (70mm ✓)
  Y: 75.0 ~ 80.0     (5mm ✗ — 应为 160mm)
  Z: -5.0 ~ -4.0     (1mm ✗ — 应为 10mm, 且在地面以下)
```

8 次渲染迭代完全在追逐错误的模型。改用 numpy-stl 重新生成后，一个方向渲染也没做过（直接交给用户 STL 文件+2D线稿）。

## 关键教训

1. **永远先检查 STL 顶点范围** — 发 STL 给用户前先跑一次 bounding box 检查
2. **模型不能在地面以下** — Z 轴质心必须 > 0
3. **不要假设 Blender 生成的 STL 是正确的** — BMesh 脚本容易在尺寸/位置上有 bug
4. **当 3 个渲染引擎都失败时，问题 90% 在模型本身**
5. **2D Pillow 预览是可靠的 fallback** — 不需要 Blender，直接读二进制 STL 画线框

## 修复后的 STL 正确范围

```
FindN5_Case_Left.stl (numpy-stl):
  X: -74.0 ~ 0.0     (74mm)
  Y: -80.0 ~ 80.0    (160mm ✓)
  Z: 0.0 ~ 10.0      (10mm ✓)
  Tri: 248

FindN5_Case_Right.stl (numpy-stl):
  X: 0.0 ~ 74.0      (74mm)
  Y: -80.0 ~ 80.0    (160mm ✓)
  Z: -0.5 ~ 12.0     (12.5mm, 含摄像头凸起)
  Tri: 472
```

## 推荐做法

生成 STL 后，立即执行以下检查脚本：

```bash
python3 -c "
import numpy as np

def check_stl(fname):
    with open(fname, 'rb') as f:
        data = f.read()
    num_tris = int.from_bytes(data[80:84], 'little')
    verts = []
    for i in range(num_tris):
        offset = 84 + i * 50
        for j in range(3):
            v = np.frombuffer(data[offset+12+j*12:offset+24+j*12], dtype=np.float32)
            verts.append(v)
    verts = np.array(verts)
    ranges = [verts[:,i].max()-verts[:,i].min() for i in range(3)]
    print(f'{fname}: {num_tris} tris, 尺寸={ranges[0]:.1f}x{ranges[1]:.1f}x{ranges[2]:.1f}mm')
    okay = True
    if min(ranges) < 2.0:
        print('  ❌ 某轴压扁！')
        okay = False
    if verts[:,2].mean() < 0:
        print('  ❌ Z 轴在地面以下')
        okay = False
    if num_tris < 50:
        print('  ❌ 三角面太少')
        okay = False
    if okay:
        print('  ✅ 模型尺寸合理')

check_stl('model.stl')
"
```
