# -*- coding: utf-8 -*-
"""
《楼·溯》第1章·巴丘瞭望 —— 水域与港口结构 模块化套件（Blender 直接搭建）

（原点 z=0 为水面；岸面/堤顶 1.2 m，与「地面建筑与码头」套件一致）
  H01 石砌防波堤段   6 m，堤顶 3 m 宽铺石 + 边石，两侧抛石护坡（1:1.5）
  H02 防波堤端头·烽火台  半径 4 m 圆形石台 + 木构烽火台（火盆、梯、信号旗）
  H03 水寨木栅      6 m，削尖木桩入水 + 横档 + 内侧斜撑（阻船）
  H04 水门          8 m 通航口，两侧桩群门楼 + 双横梁 + 吊起的尖木闸门 + 绞盘
  H05 修船滑道      宽 5 m，从岸面 1.2 m 斜入水下 1.6 m，轨木 + 枕木 + 帆布船棚 + 绞盘；原点在岸沿中心
  H06 浮台          4×3 m，木桶浮筒托木板，半浸水
  H07 浅滩岸坡      6 m，自然土坡入水，卵石与芦苇；左右可无缝拼接
  H08 水面块        24×24 m 轻微波纹水面，周期对齐可平铺
依赖：同目录上级的 地面建筑与码头/ground_kit.py（复用石作与木作函数）。
"""
import math, os, random, time, importlib.util

BLD = "C:/Users/pjwly/3D Objects/楼溯_资产库/第1章_巴丘瞭望/07_Blender搭建/"
OUT = BLD + "水域与港口结构/"
FBX_FIG = "D:/Caroline Elvira/ancient chinese robe 3d model/ancient_chinese_robe_3d_model.fbx"
SEED = 41
RENDER = True
EXPORT_FBX = True

for _p in (BLD + "地面建筑与码头/ground_kit.py", "/home/claude/ground_kit.py"):
    if os.path.isfile(_p):
        _s = importlib.util.spec_from_file_location("ground_kit_lib", _p)
        GK = importlib.util.module_from_spec(_s); _s.loader.exec_module(GK); break
box, log, lathe, prism_x, Piece = GK.box, GK.log, GK.lathe, GK.prism_x, GK.Piece
ashlar, coping, flagstones, _mat, H = GK.ashlar, GK.coping, GK.flagstones, GK._mat, GK.H

COL = dict(GK.COL)
COL.update({"芦苇": (0.58, 0.56, 0.32), "泥": (0.40, 0.36, 0.28), "帆布深": (0.30, 0.31, 0.33), "红布": (0.50, 0.10, 0.07),
            "火": (0.85, 0.42, 0.10)})


def rock(c, s, rng):
    """不规则石块：八顶点随机扰动的盒子"""
    V, F = box((0, 0, 0), s, (rng.uniform(0, 360), rng.uniform(0, 360), rng.uniform(0, 360)))
    V = [(c[0] + v[0]*rng.uniform(0.75, 1.25), c[1] + v[1]*rng.uniform(0.75, 1.25), c[2] + v[2]*rng.uniform(0.75, 1.25)) for v in V]
    return V, F


def grid(rows, closed=False):
    m, n = len(rows), len(rows[0])
    V = [p for r in rows for p in r]
    cols = n if closed else n-1
    return V, [(k*n+i, k*n+(i+1) % n, (k+1)*n+(i+1) % n, (k+1)*n+i) for k in range(m-1) for i in range(cols)]


# ============================================================ H01 防波堤段
def H01():
    P = Piece("H01", "石砌防波堤段", fig=(0.4, 0.2, H)); rng = random.Random(SEED)
    L, cw, zb, k = 6.0, 1.5, -2.0, 1.5
    bw = cw + (H - zb)*k
    P.add("堤芯", "泥", prism_x([(-bw, zb), (bw, zb), (cw, H-0.1), (-cw, H-0.1)], -L/2, L/2))
    a = math.atan2(1, k)
    for side in (-1, 1):
        sl = math.hypot(H - 0.25 - zb, (H - 0.25 - zb)*k)
        t = 0.4
        while t < sl:
            x = -L/2 + rng.uniform(0, 0.5)
            while x < L/2:
                s = rng.uniform(0.55, 1.1)
                z = H - 0.25 - t*math.sin(a); y = side*(cw + 0.1 + t*math.cos(a))
                ny, nz = side*math.sin(a), math.cos(a)
                c = (x + s/2, y + ny*s*0.28, z + nz*s*0.28)
                if z > -1.4:
                    P.add("抛石", _mat(rng), rock(c, (s, s*rng.uniform(0.7, 1.0), s*rng.uniform(0.5, 0.8)), rng))
                x += s*rng.uniform(0.75, 0.95)
            t += rng.uniform(0.5, 0.75)
    flagstones(P, rng, -L/2, L/2, -cw+0.32, cw-0.32, H, size=(0.5, 0.9))
    for sy in (-1, 1):
        x = -L/2
        while x < L/2 - 0.05:
            l = min(rng.uniform(0.8, 1.3), L/2 - x)
            P.add("边石", _mat(rng), box((x+l/2, sy*(cw-0.15), H-0.02), (l-0.03, 0.4, 0.34), (rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(-1, 1))))
            x += l
    return P


# ============================================================ H02 端头 · 烽火台
def H02():
    P = Piece("H02", "防波堤端头烽火台", fig=(2.2, -2.0, H)); rng = random.Random(SEED+1)
    R, zb = 4.0, -1.6
    P.add("台芯", "泥", lathe([(zb, R-0.1), (H-0.12, R-0.1)], n=32))
    z = zb; row = 0
    while z < H - 0.25:
        h = rng.uniform(0.24, 0.36)
        th = rng.uniform(0, 0.4) + (0.3 if row % 2 else 0)
        while th < 2*math.pi + 0.01:
            l = rng.uniform(0.7, 1.2); dth = l/R
            m = th + dth/2
            pro = rng.uniform(0.03, 0.09)
            P.add("台壁条石", _mat(rng), box(((R+pro/2-0.04)*math.cos(m), (R+pro/2-0.04)*math.sin(m), z+h/2),
                                         (l*0.96, 0.22+pro, h*rng.uniform(0.86, 0.96)), (rng.uniform(-2, 2), rng.uniform(-2, 2), math.degrees(m)+90)))
            th += dth
        z += h; row += 1
    th = 0.0
    while th < 2*math.pi:
        l = rng.uniform(0.9, 1.3); dth = l/(R-0.2); m = th + dth/2
        P.add("压阑石", _mat(rng), box(((R-0.22)*math.cos(m), (R-0.22)*math.sin(m), H-0.1), (l*0.97, 0.5, 0.2), (0, 0, math.degrees(m)+90)))
        th += dth
    for _ in range(70):
        a = rng.uniform(0, 2*math.pi); r = rng.uniform(R+0.2, R+1.8); s = rng.uniform(0.5, 1.0)
        z = -0.2 - (r-R)*0.55
        if a > math.pi*0.3 and a < math.pi*0.7:
            continue   # 与堤身相接一侧（+Y）不抛石
        P.add("抛石", _mat(rng), rock((r*math.cos(a), r*math.sin(a), z + s*0.3), (s, s*0.8, s*0.6), rng))
    y = -R+0.5
    while y < R-0.5:
        x = -R+0.5
        while x < R-0.5:
            w = rng.uniform(0.5, 0.9)
            if math.hypot(x+w/2, y+0.35) < R-0.5:
                P.add("台面石板", _mat(rng), box((x+w/2, y+0.35, H-0.04), (w-0.03, 0.67, 0.08), (0, 0, rng.uniform(-1.5, 1.5))))
            x += w
        y += 0.7
    # 烽火台
    zb2 = H
    P.add("台座", "石", box((0, 0, zb2+0.5), (2.4, 2.4, 1.0)))
    zt = zb2 + 1.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.add("立柱", "木深", log((sx*0.95, sy*0.95, zt), (sx*0.8, sy*0.8, zt+5.0), 0.12, n=8, rng=rng))
    for z in (zt+1.6, zt+3.2):
        for sx in (-1, 1):
            P.add("横撑", "木深", log((sx*0.92, -0.92, z), (sx*0.92, 0.92, z), 0.06, n=6))
            P.add("横撑", "木深", log((-0.92, sx*0.92, z), (0.92, sx*0.92, z), 0.06, n=6))
    for sx in (-1, 1):
        P.add("剪刀撑", "木湿", log((sx*0.93, -0.93, zt), (sx*0.85, 0.85, zt+3.2), 0.05, n=6))
        P.add("剪刀撑", "木湿", log((-0.93, sx*0.93, zt), (0.85, sx*0.85, zt+3.2), 0.05, n=6))
    zp = zt + 4.7
    P.add("平台", "木", box((0, 0, zp), (2.6, 2.6, 0.12)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.add("栏杆柱", "木深", log((sx*1.25, sy*1.25, zp), (sx*1.25, sy*1.25, zp+1.0), 0.05, n=6))
        P.add("栏杆", "木", log((sx*1.25, -1.25, zp+0.95), (sx*1.25, 1.25, zp+0.95), 0.04, n=6))
        P.add("栏杆", "木", log((-1.25, sx*1.25, zp+0.95), (1.25, sx*1.25, zp+0.95), 0.04, n=6))
    P.add("火盆", "铁", lathe([(zp+0.06, 0.12), (zp+0.6, 0.12), (zp+0.65, 0.35), (zp+0.95, 0.5), (zp+1.0, 0.52)], n=14))
    P.add("火盆_柴", "火", lathe([(zp+0.9, 0.44), (zp+1.15, 0.25), (zp+1.3, 0.0)], n=10))
    for k in range(14):   # 竖梯
        z = zt + 0.3 + k*0.32
        P.add("梯", "木", log((-0.35, -1.15, z), (0.35, -1.15, z), 0.025, n=5))
    for sx in (-1, 1):
        P.add("梯", "木深", log((sx*0.38, -1.15, zt), (sx*0.38, -1.15, zp+0.9), 0.04, n=6))
    P.add("信号旗杆", "木深", log((1.25, 1.25, zp), (1.25, 1.25, zp+3.0), 0.04, n=6))
    P.add("信号旗", "红布", grid([[(1.27, 1.25+0.9*i/8, zp+2.9 - 0.04*math.sin(i)) for i in range(9)],
                                [(1.27 + 0.06*math.sin(i*0.9), 1.25+0.9*i/8, zp+2.3 - 0.15*(i/8)) for i in range(9)]]))
    return P


# ============================================================ H03 水寨木栅 / H04 水门
def H03():
    P = Piece("H03", "水寨木栅"); rng = random.Random(SEED+2)
    L = 6.0
    x = -L/2 + 0.05
    while x < L/2 - 0.1:
        r = rng.uniform(0.11, 0.15)
        P.add("栅桩", "木湿", log((x+r, rng.uniform(-0.04, 0.04), -2.6), (x+r+rng.uniform(-0.06, 0.06), 0, 1.7 + rng.uniform(-0.25, 0.2)), r, n=8, tip=0.32, rng=rng))
        x += 2*r + rng.uniform(0.02, 0.08)
    for z in (0.75, 1.4):
        P.add("横档", "木深", log((-L/2, 0.22, z), (L/2, 0.22, z + rng.uniform(-0.04, 0.04)), 0.1, n=8, rng=rng))
        for xx in [-L/2 + 0.4 + i*1.04 for i in range(6)]:
            P.add("绑绳", "绳", log((xx, 0.1, z-0.08), (xx, 0.1, z+0.08), 0.2, n=8))
    for xx in (-2.0, 0.0, 2.0):
        P.add("斜撑", "木湿", log((xx, 2.0, -1.0), (xx, 0.3, 1.3), 0.09, n=7, rng=rng))
    return P


def H04():
    P = Piece("H04", "水门", fig=(-4.6, 0.0, 5.7)); rng = random.Random(SEED+3)
    gx, top = 4.6, 6.1
    for sx in (-1, 1):
        for dx in (-0.35, 0.35):
            for dy in (-0.35, 0.35):
                P.add("门楼桩", "木湿", log((sx*gx+dx, dy, -2.6), (sx*gx+dx*0.9, dy*0.9, top), 0.17, n=10, rng=rng))
        for z in (1.0, 2.6, 4.2):
            P.add("桩箍绳", "绳", lathe([(z, 0.72), (z+0.18, 0.72)], n=16, cx=sx*gx))
        P.add("门楼平台", "木", box((sx*gx, 0, 5.6), (2.0, 2.0, 0.14)))
        for ex in (-1, 1):
            for ey in (-1, 1):
                P.add("门楼栏杆", "木深", log((sx*gx+ex*0.95, ey*0.95, 5.6), (sx*gx+ex*0.95, ey*0.95, 6.6), 0.05, n=6))
            P.add("门楼栏杆", "木", log((sx*gx+ex*0.95, -0.95, 6.5), (sx*gx+ex*0.95, 0.95, 6.5), 0.04, n=6))
            P.add("门楼栏杆", "木", log((sx*gx-0.95, ex*0.95, 6.5), (sx*gx+0.95, ex*0.95, 6.5), 0.04, n=6))
    for y, z in ((-0.35, top-0.1), (0.35, top-0.1)):
        P.add("横梁", "木深", log((-gx-0.8, y, z), (gx+0.8, y, z), 0.2, n=10, rng=rng))
    # 吊起的闸门（尖头朝下）
    x = -gx + 0.85
    while x < gx - 0.85:
        r = rng.uniform(0.1, 0.12)
        P.add("闸门木", "木", log((x+r, -0.75, 5.3), (x+r, -0.75, 2.4 + rng.uniform(-0.1, 0.1)), r, n=7, tip=0.28, rng=rng))
        x += 2*r + 0.02
    for z in (3.0, 4.9):
        P.add("闸门横档", "木深", log((-gx+0.8, -0.92, z), (gx-0.8, -0.92, z), 0.08, n=7))
    for xx in (-2.4, 2.4):
        P.add("吊索", "绳", log((xx, -0.6, top-0.2), (xx, -0.8, 5.25), 0.025, n=5))
    P.add("绞盘", "木", log((-gx-0.6, 0.55, 6.0), (-gx+0.6, 0.55, 6.0), 0.22, n=12))
    for k in range(4):
        a = k*math.pi/2
        P.add("绞盘柄", "木深", log((-gx-0.65, 0.55, 6.0), (-gx-0.65, 0.55+0.6*math.cos(a), 6.0+0.6*math.sin(a)), 0.03, n=5))
    P.add("门额幡", "红布", grid([[(-1.0+2.0*i/10, -0.6, top-0.35) for i in range(11)],
                              [(-1.0+2.0*i/10, -0.62-0.03*math.sin(i), top-1.25-0.18*abs(math.sin(i*math.pi/5))) for i in range(11)]]))
    return P


# ============================================================ H05 修船滑道
def H05():
    P = Piece("H05", "修船滑道", fig=(2.4, -1.2, 1.0)); rng = random.Random(SEED+4)
    Lr, zb = 14.0, -1.6
    zr = lambda y: H + (zb - H)*(-y/Lr)
    y = -0.3
    while y > -Lr:
        P.add("枕木", "木深", box((0, y, zr(y)-0.12), (4.4, 0.24, 0.16), (math.degrees(math.atan2(H-zb, Lr)), 0, 0)))
        y -= 0.7
    for sx in (-1, 1):
        P.add("滑轨", "木", log((sx*1.2, 0.0, H-0.02), (sx*1.2, -Lr, zb-0.02), 0.13, n=10, rng=rng))
    for yy in (-3.5, -6.5, -9.5, -12.5):
        for sx in (-1.8, 1.8):
            P.add("托桩", "木湿", log((sx, yy, -2.6), (sx, yy, zr(yy)-0.2), 0.15, n=8, rng=rng))
        P.add("托梁", "木深", box((0, yy, zr(yy)-0.26), (4.2, 0.24, 0.2)))
    for yy in (-1.0, -2.6):
        P.add("船托", "木", box((0, yy, zr(yy)+0.25), (1.6, 0.4, 0.4)))
    # 船棚：六柱帆布棚
    zt, ze = 7.6, 5.8
    ys = (-0.6, -4.6, -8.6)
    for yy in ys:
        for sx in (-1, 1):
            base = max(-2.6, zr(yy) - 0.5) if yy < -2 else zr(yy) - 0.1
            P.add("棚柱", "木深", log((sx*3.3, yy, -2.6 if yy < -2 else zr(yy)-0.6), (sx*3.3, yy, ze+0.05), 0.15, n=8, rng=rng))
        P.add("棚梁", "木深", log((-3.5, yy, ze), (3.5, yy, ze), 0.1, n=8))
        P.add("棚脊柱", "木深", log((0, yy, ze), (0, yy, zt), 0.09, n=8))
    P.add("棚脊", "木深", log((0, ys[0]+0.4, zt+0.03), (0, ys[-1]-0.4, zt+0.03), 0.09, n=8))
    for sx in (-1, 1):
        rows = []
        for j in range(9):
            v = j/8
            x = sx*3.7*(1-v); z = (ze-0.1) + (zt-ze+0.1)*v
            rows.append([(x, ys[0]+0.5 - (ys[0]-ys[-1]+1.0)*i/40, z - 0.1*abs(math.sin(math.pi*i/20))*(0.3+0.7*math.sin(math.pi*v))) for i in range(41)])
        P.add("棚顶", "帆布深", grid(rows))
        top = [(sx*3.71, ys[0]+0.5 - (ys[0]-ys[-1]+1.0)*i/60, ze-0.12) for i in range(61)]
        P.add("棚顶垂幔", "红布", grid([top, [(p[0], p[1], p[2]-0.26*(0.72+0.28*abs(math.cos(math.pi*i/6)))) for i, p in enumerate(top)]]))
    # 岸上绞盘
    P.add("绞盘柱", "木", lathe([(H, 0.32), (H+1.0, 0.28), (H+1.1, 0.36), (H+1.2, 0.36)], n=14, cy=1.6))
    for k in range(4):
        a = k*math.pi/2
        P.add("绞盘杆", "木深", log((0, 1.6, H+1.0), (1.3*math.cos(a), 1.6+1.3*math.sin(a), H+1.0), 0.04, n=6))
    P.add("拖索", "绳", log((0, 1.3, H+0.5), (0, -1.0, zr(-1.0)+0.45), 0.03, n=5))
    return P


# ============================================================ H06 浮台 / H07 浅滩 / H08 水面
def H06():
    P = Piece("H06", "浮台", fig=(0.4, 0.2, 0.46)); rng = random.Random(SEED+5)
    for yy in (-0.95, 0.95):
        for xx in (-1.35, 0.0, 1.35):
            P.add("浮桶", "木湿", log((xx-0.6, yy, 0.02), (xx+0.6, yy, 0.02), 0.33, n=12, r1=0.33))
            for dx in (-0.4, 0.4):
                P.add("浮桶箍", "铁", log((xx+dx-0.03, yy, 0.02), (xx+dx+0.03, yy, 0.02), 0.345, n=12))
    for yy in (-0.95, 0.95):
        P.add("纵梁", "木深", box((0, yy, 0.31), (4.0, 0.16, 0.14)))
    x = -2.0
    while x < 2.0 - 0.05:
        w = 0.22*rng.uniform(0.9, 1.1)
        P.add("桥板", "木", box((x+w/2, 0, 0.42), (w-0.025, 3.0, 0.06), (0, rng.uniform(-0.5, 0.5), 0)))
        x += w
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.add("系缆桩", "木深", log((sx*1.85, sy*1.35, 0.42), (sx*1.85, sy*1.35, 0.85), 0.07, n=8))
    P.add("缆绳", "绳", log((1.85, 1.35, 0.75), (3.6, 2.6, 0.0), 0.02, n=4))
    return P


def H07():
    P = Piece("H07", "浅滩岸坡", fig=(0.5, -0.3, H)); rng = random.Random(SEED+6)
    L, Ly, zl = 6.0, 7.0, -1.3
    def zf(x, y):
        t = -y/Ly
        base = H + (zl - H)*(t**0.85)
        return base + 0.07*math.sin(2*math.pi*x/3)*math.sin(math.pi*t) + 0.04*math.sin(2*math.pi*x/2 + 1)*math.sin(2*math.pi*t)
    rows = []
    for j in range(21):
        y = -Ly*j/20
        rows.append([(-L/2 + L*i/24, y, zf(-L/2 + L*i/24, y)) for i in range(25)])
    P.add("岸坡", "泥", grid(rows))
    for _ in range(40):
        x = rng.uniform(-L/2+0.3, L/2-0.3); y = rng.uniform(-Ly*0.6, -Ly*0.25); s = rng.uniform(0.15, 0.45)
        P.add("卵石", _mat(rng), rock((x, y, zf(x, y) + s*0.25), (s, s*0.8, s*0.55), rng))
    for _ in range(9):
        cx = rng.uniform(-L/2+0.6, L/2-0.6); cy = rng.uniform(-Ly*0.5, -Ly*0.3)
        for k in range(16):
            x = cx + rng.uniform(-0.35, 0.35); y = cy + rng.uniform(-0.35, 0.35)
            h = rng.uniform(0.9, 1.7); lean = (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25))
            z0 = zf(x, y) - 0.05
            P.add("芦苇", "芦苇", log((x, y, z0), (x+lean[0], y+lean[1], z0+h), 0.012, n=4, tip=0.3))
    return P


def H08():
    P = Piece("H08", "水面块"); rng = random.Random(SEED+7)
    S, st = 24.0, 0.6
    n = int(S/st)
    rows = []
    for j in range(n+1):
        y = -S/2 + S*j/n
        rows.append([(-S/2 + S*i/n, y, 0.03*math.sin(2*math.pi*(-S/2 + S*i/n)/6 + 2*math.pi*y/8)
                      + 0.02*math.sin(2*math.pi*y/4 - 2*math.pi*(-S/2 + S*i/n)/12)) for i in range(n+1)])
    P.add("水面", "水", grid(rows))
    return P


PIECES = [H01, H02, H03, H04, H05, H06, H07, H08]


# ============================================================ Blender
def run():
    import bpy, bmesh
    from mathutils import Vector

    T0 = time.time(); logl = []
    def L(s):
        logl.append("[%5.1fs] %s" % (time.time()-T0, s)); print(logl[-1])
    for d in ("renders/", "fbx/"):
        os.makedirs(OUT + d, exist_ok=True)

    sc = bpy.data.scenes.get("水域与港口结构")
    if sc:
        for ob in list(sc.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(sc)
    for c in list(bpy.data.collections):
        if c.name.startswith("港口套件_") or c.name.startswith("港口展示") or c.name == "港口组装演示":
            for ob in list(c.all_objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    sc = bpy.data.scenes.new("水域与港口结构")
    bpy.context.window.scene = sc
    root = sc.collection

    mats = {}
    for k, rgb in COL.items():
        m = bpy.data.materials.get("港口_" + k) or bpy.data.materials.new("港口_" + k)
        m.diffuse_color = (*rgb, 1)
        try:
            m.use_nodes = True
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.1 if k == "水" else 0.9
            if k == "火":
                b.inputs["Emission Color"].default_value = (1.0, 0.45, 0.1, 1); b.inputs["Emission Strength"].default_value = 3.0
        except Exception:
            pass
        mats[k] = m

    kit, built = {}, {}
    for fn in PIECES:
        P = fn(); built[P.pid] = P
        col = bpy.data.collections.new("港口套件_%s_%s" % (P.pid, P.name)); root.children.link(col)
        for g, (mat, V, F) in P.groups.items():
            me = bpy.data.meshes.new("%s_%s" % (P.pid, g))
            me.from_pydata(V, [], F); me.validate()
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
            me.materials.append(mats[mat])
            ob = bpy.data.objects.new("%s_%s" % (P.pid, g), me); col.objects.link(ob)
            if mat in ("帆布深", "红布", "水", "泥"):
                for p in me.polygons:
                    p.use_smooth = True
            if g == "岸坡":
                so = ob.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = 0.4; so.offset = -1.0
            if mat in ("帆布深", "红布"):
                so = ob.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = 0.018
                su = ob.modifiers.new("Subdivision", "SUBSURF"); su.levels = 1; su.render_levels = 2
            if mat in ("石", "石深", "石浅") and len(F) < 30000:
                bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = 0.03; bv.segments = 1; bv.limit_method = "ANGLE"
        kit[P.pid] = col
        lo, hi = P.bbox()
        L("%s %s  %.2f×%.2f×%.2f m  面数 %d" % (P.pid, P.name, hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2], P.nf()))

    fig_col = None
    for nm in ("套件_人物参照", "营地套件_人物参照", "地码套件_人物参照", "港口套件_人物参照"):
        c = bpy.data.collections.get(nm)
        if c and [o for o in c.objects if o.type == "MESH"]:
            fig_col = c; break
    if fig_col is None:
        fig_col = bpy.data.collections.new("港口套件_人物参照"); root.children.link(fig_col)
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=FBX_FIG)
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            fig_col.objects.link(o)
        fig = [o for o in new if o.type == "MESH"][0]
        bpy.context.view_layer.update()
        zs = [(fig.matrix_world @ v.co).z for v in fig.data.vertices]
        k = 1.78/(max(zs)-min(zs)); fig.scale = [s*k for s in fig.scale]
        bpy.context.view_layer.update()
        ws = [fig.matrix_world @ v.co for v in fig.data.vertices]
        fig.location.x -= (max(w.x for w in ws)+min(w.x for w in ws))/2
        fig.location.y -= (max(w.y for w in ws)+min(w.y for w in ws))/2
        fig.location.z -= min(w.z for w in ws)
    L("人物参照：" + fig_col.name)

    ext = {}
    for blend, names in ((BLD + "地面建筑与码头/地面建筑与码头_套件.blend", ("地码套件_D01_石砌岸壁", "地码套件_D02_木栈桥段", "地码套件_D03_栈桥端头平台", "地码套件_D04_系船桩群", "地码套件_G04_石板路")),
                         (BLD + "营地建筑/营地建筑_套件.blend", ("营地套件_C02_营房长帐", "营地套件_C04_军需敞棚", "营地套件_C05_旗杆"))):
        for nm in names:
            c = bpy.data.collections.get(nm)
            if c is None and os.path.isfile(blend):
                try:
                    d_ = blend + "/Collection/"
                    bpy.ops.wm.append(filepath=d_ + nm, directory=d_, filename=nm)
                    c = bpy.data.collections.get(nm)
                    if c and sc.collection.children.get(c.name):
                        sc.collection.children.unlink(c)
                except Exception as e:
                    L("追加 %s 失败 %r" % (nm, e))
            if c:
                ext[nm.split("_")[1]] = c
    L("外部套件：%s" % list(ext.keys()))

    if EXPORT_FBX:
        for pid, col in kit.items():
            sc.view_layers[0].active_layer_collection = sc.view_layers[0].layer_collection.children[col.name]
            try:
                bpy.ops.export_scene.fbx(filepath=OUT + "fbx/%s.fbx" % col.name.replace("港口套件_", ""),
                                         use_active_collection=True, use_mesh_modifiers=True, axis_forward="-Z", axis_up="Y")
            except Exception as e:
                L("FBX %s 失败 %r" % (pid, e))
        L("FBX 导出完成")
    for col in kit.values():
        sc.view_layers[0].layer_collection.children[col.name].exclude = True
    lcf = sc.view_layers[0].layer_collection.children.get(fig_col.name)
    if lcf:
        lcf.exclude = True

    def inst(col, loc, rz=0, parent=None, name=None):
        e = bpy.data.objects.new(name or ("实例_" + col.name), None)
        e.instance_type = "COLLECTION"; e.instance_collection = col
        e.location = loc; e.rotation_euler = (0, 0, math.radians(rz))
        (parent or root).objects.link(e)
        return e

    # ---------------- 展示
    show = bpy.data.collections.new("港口展示"); root.children.link(show)
    cams, subs = [], []
    x = 0.0
    for fn in PIECES:
        pid = fn.__name__
        P = built[pid]; lo, hi = P.bbox()
        x += -lo[0] + 3
        sub = bpy.data.collections.new("港口展示_" + pid); show.children.link(sub); subs.append(sub)
        inst(kit[pid], (x, 0, 0), parent=sub)
        if P.fig:
            inst(fig_col, (x + P.fig[0], P.fig[1], P.fig[2]), parent=sub, name="人物_" + pid)
        cx, cz = x + (lo[0]+hi[0])/2, (lo[2]+hi[2])/2
        span = max(hi[0]-lo[0]+1.5, hi[2]-lo[2], hi[1]-lo[1]) * 1.12
        for vn, loc, rot in (("正视", (cx, -120, cz), (90, 0, 0)), ("侧视", (x+hi[0]+120, (lo[1]+hi[1])/2, cz), (90, 0, 90)),
                             ("顶视", (cx, (lo[1]+hi[1])/2, 120), (0, 0, 0))):
            cd = bpy.data.cameras.new("CAM_%s_%s" % (pid, vn)); cd.type = "ORTHO"; cd.ortho_scale = span; cd.clip_end = 500
            co = bpy.data.objects.new(cd.name, cd); sub.objects.link(co); co.location = loc
            co.rotation_euler = tuple(math.radians(a) for a in rot)
            cams.append(("%s_%s_%s" % (pid, P.name, vn), co, (1400, 1100), [sub]))
        cd = bpy.data.cameras.new("CAM_%s_透视" % pid); cd.lens = 40; cd.clip_end = 500
        co = bpy.data.objects.new(cd.name, cd); sub.objects.link(co)
        tgt = Vector((x + (lo[0]+hi[0])/2, (lo[1]+hi[1])/2, (lo[2]+hi[2])/2))
        R = max(hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2])
        co.location = tgt + Vector((-0.6, -1.0, 0.55)).normalized()*max(R*2.0, 7.0)
        co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()
        cams.append(("%s_%s_透视" % (pid, P.name), co, (1500, 1150), [sub]))
        x += hi[0] + 5

    # ---------------- 港湾组装演示
    demo = bpy.data.collections.new("港口组装演示"); root.children.link(demo)
    oy = 120.0
    D = lambda x, y, z=0.0: (x, y + oy, z)
    for xx in (-6, 0, 6, 12):
        if "D01" in ext:
            inst(ext["D01"], D(xx, 0), parent=demo)
    for xx in (-18, -24, -30, 18, 24, 30):
        inst(kit["H07"], D(xx, 0), parent=demo)
    inst(kit["H05"], D(-12, 0), parent=demo)
    if "D02" in ext:
        inst(ext["D02"], D(-1.5, 0), parent=demo); inst(ext["D02"], D(-1.5, -6), parent=demo)
    if "D03" in ext:
        inst(ext["D03"], D(-1.5, -12), parent=demo)
    for k in range(4):
        inst(kit["H01"], D(22, -3 - 6*k), rz=90, parent=demo)
    inst(kit["H02"], D(22, -27.5), parent=demo)
    gate_x = 4.0
    inst(kit["H04"], D(gate_x, -30), parent=demo)
    for xx in (gate_x - 8.6, gate_x - 14.6, gate_x - 20.6):
        inst(kit["H03"], D(xx, -30), parent=demo)
    for yy in (-26.9, -20.9, -14.9, -8.9):       # 西侧折向岸边
        inst(kit["H03"], D(gate_x - 23.6, yy), rz=90, parent=demo)
    for xx in (gate_x + 8.6, gate_x + 13.0):
        inst(kit["H03"], D(xx, -30), parent=demo)
    inst(kit["H06"], D(8, -9), rz=12, parent=demo)
    inst(kit["H06"], D(12.5, -14), rz=-8, parent=demo)
    if "D04" in ext:
        for p in ((-7, -14), (9.5, -20), (-14, -18)):
            inst(ext["D04"], D(*p), parent=demo)
    for xx in (-24, 0, 24):
        for yy in (-12, -36):
            inst(kit["H08"], D(xx, yy), parent=demo)
    if "G04" in ext:
        inst(ext["G04"], D(-1.5, 4.4, H), rz=90, parent=demo)
    if "C04" in ext:
        inst(ext["C04"], D(-12, 8.5, H), rz=90, parent=demo)
    if "C02" in ext:
        inst(ext["C02"], D(9, 9, H), parent=demo)
    if "C05" in ext:
        for p in ((-4.2, 2.5), (1.2, 2.5), (19.2, -6)):
            inst(ext["C05"], D(p[0], p[1], H), parent=demo)
    for p, z, r in (((-1.0, -4.0), H, 10), ((-2.2, -14.5), H, 180), ((21.6, -12.0), H, 200), ((24.0, -25.5), H, 160),
                    ((8.3, -9.0), 0.45, 30), ((-11.0, -2.5), 0.9, 0), ((gate_x - 4.6, -30.1), 5.7, 180), ((-12.0, 3.2), H, 200)):
        inst(fig_col, D(p[0], p[1], z), rz=r, parent=demo, name="人物_演示")
    gm = bpy.data.meshes.new("港口岸地"); gm.from_pydata([(-36, oy+0.0, H-0.01), (36, oy+0.0, H-0.01), (36, oy+40, H-0.01), (-36, oy+40, H-0.01)], [], [(0, 1, 2, 3)])
    gm.materials.append(mats["地"]); demo.objects.link(bpy.data.objects.new("港口岸地", gm))
    for nm, loc, tgt, lens in (("港湾_鸟瞰", (-34, oy-70, 38), (2, oy-14, 0), 30),
                               ("港湾_水门近景", (13, oy-46, 5.0), (gate_x, oy-30, 3.2), 32),
                               ("港湾_防波堤与烽火台", (38, oy-42, 9.0), (22, oy-23, 3.5), 30),
                               ("港湾_修船滑道", (-25, oy-15, 7.0), (-12, oy-4, 2.0), 30)):
        cd = bpy.data.cameras.new("CAM_" + nm); cd.lens = lens; cd.clip_end = 600
        co = bpy.data.objects.new(cd.name, cd); demo.objects.link(co); co.location = loc
        co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        cams.append((nm, co, (1800, 1100), [demo]))

    sc.render.engine = "BLENDER_WORKBENCH"
    try:
        sh = sc.display.shading
        sh.light = "STUDIO"; sh.color_type = "MATERIAL"
        sh.show_cavity = True; sh.cavity_type = "BOTH"; sh.show_object_outline = True; sh.show_shadows = True
        sc.display.shadow_focus = 0.15; sc.display.render_aa = "16"
    except Exception as e:
        L("shading %r" % (e,))
    sc.render.film_transparent = True
    if RENDER:
        for nm, co, (rx, ry), vis in cams:
            for c in subs + [demo]:
                c.hide_render = c not in vis
            sc.camera = co; sc.render.resolution_x, sc.render.resolution_y = rx, ry
            sc.render.filepath = OUT + "renders/%s.png" % nm
            bpy.ops.render.render(write_still=True)
        for c in subs + [demo]:
            c.hide_render = False
        L("渲染 %d 张" % len(cams))
    sc.camera = cams[-4][1]
    bpy.ops.wm.save_as_mainfile(filepath=OUT + "水域与港口结构_套件.blend")
    L("saved")
    with open(OUT + "构建日志.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(logl) + "\nOK\n")


if __name__ == "__main__":
    try:
        import bpy  # noqa
        HAVE = True
    except ImportError:
        HAVE = False
    if HAVE:
        try:
            run()
        except Exception:
            import traceback
            tb = traceback.format_exc(); print(tb)
            os.makedirs(OUT, exist_ok=True)
            with open(OUT + "构建日志.txt", "w", encoding="utf-8") as fh:
                fh.write("FAILED\n" + tb)
            raise
    else:
        for fn in PIECES:
            P = fn(); lo, hi = P.bbox()
            print("%s %-10s %.2f×%.2f×%.2f  z %.2f→%.2f  面数 %d" % (P.pid, P.name, hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2], lo[2], hi[2], P.nf()))
