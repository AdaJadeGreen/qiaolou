# -*- coding: utf-8 -*-
"""
《楼·溯》第1章·巴丘瞭望 —— 营地建筑 模块化套件（Blender 直接搭建）

  C01 主帅指挥帐   木台基 + 帆布围帐 + 两重檐帐顶（翘角、垂檐、帆布在骨架间下垂）+ 前檐遮阳 + 东吴旗
  C02 营房长帐     脊式长帐，前侧卷帘敞开，两山墙封闭，垂檐、拉绳地桩
  C03 圆帐         毛石矮墙 + 帆布围帐 + 圆锥帐顶（12 根骨架间下垂）+ 门框
  C04 军需敞棚     六柱敞棚，帆布顶，长案与长凳
  C05 旗杆         石座、横杆、燕尾东吴军旗
  C06 篝火灶       石圈、柴堆、三脚吊锅
单位米；正面朝 -Y；原点在底面中心。帆布在 Blender 中加厚 + 细分，呈现柔软布料。
运行后：构件集合（导出 FBX）→ 展示行（每件旁人物 1.78 m）→ 营地组装演示（接城墙与栅栏套件）→ 渲染 → 存 .blend。
"""
import math, os, random, time

OUT = "C:/Users/pjwly/3D Objects/楼溯_资产库/第1章_巴丘瞭望/07_Blender搭建/营地建筑/"
WALL_BLEND = "C:/Users/pjwly/3D Objects/楼溯_资产库/第1章_巴丘瞭望/07_Blender搭建/城墙与栅栏/城墙与栅栏_套件.blend"
FBX_FIG = "D:/Caroline Elvira/ancient chinese robe 3d model/ancient_chinese_robe_3d_model.fbx"
SEED = 21
RENDER = True
EXPORT_FBX = True

COL = {"帆布": (0.66, 0.62, 0.54), "帆布深": (0.30, 0.31, 0.33), "红布": (0.50, 0.10, 0.07),
       "木": (0.40, 0.27, 0.16), "木深": (0.28, 0.19, 0.12), "石": (0.47, 0.44, 0.40), "石深": (0.36, 0.34, 0.31),
       "绳": (0.62, 0.54, 0.40), "铁": (0.20, 0.20, 0.22), "炭": (0.10, 0.09, 0.08), "金": (0.70, 0.55, 0.20)}
CLOTH = ("帆布", "帆布深", "红布")


# ============================================================ 基础几何
def _rot(v, r):
    x, y, z = v
    rx, ry, rz = (math.radians(a) for a in r)
    y, z = y*math.cos(rx)-z*math.sin(rx), y*math.sin(rx)+z*math.cos(rx)
    x, z = x*math.cos(ry)+z*math.sin(ry), -x*math.sin(ry)+z*math.cos(ry)
    x, y = x*math.cos(rz)-y*math.sin(rz), x*math.sin(rz)+y*math.cos(rz)
    return (x, y, z)

_BF = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]

def box(c, s, rot=(0, 0, 0)):
    hx, hy, hz = s[0]/2, s[1]/2, s[2]/2
    p = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz), (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    return [tuple(c[i]+q[i] for i in range(3)) for q in (_rot(v, rot) for v in p)], list(_BF)

def frustum(c, b, t, h):
    x, y, z = c
    v = [(x-b[0]/2, y-b[1]/2, z), (x+b[0]/2, y-b[1]/2, z), (x+b[0]/2, y+b[1]/2, z), (x-b[0]/2, y+b[1]/2, z),
         (x-t[0]/2, y-t[1]/2, z+h), (x+t[0]/2, y-t[1]/2, z+h), (x+t[0]/2, y+t[1]/2, z+h), (x-t[0]/2, y+t[1]/2, z+h)]
    return v, list(_BF)

def log(p0, p1, r, n=8, tip=0.0, rng=None, r1=None):
    d = [p1[i]-p0[i] for i in range(3)]; L = math.sqrt(sum(a*a for a in d)) or 1e-6; d = [a/L for a in d]
    a = (1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0)
    u = [d[1]*a[2]-d[2]*a[1], d[2]*a[0]-d[0]*a[2], d[0]*a[1]-d[1]*a[0]]
    ul = math.sqrt(sum(x*x for x in u)); u = [x/ul for x in u]
    w = [d[1]*u[2]-d[2]*u[1], d[2]*u[0]-d[0]*u[2], d[0]*u[1]-d[1]*u[0]]
    r1 = r*0.97 if r1 is None else r1
    rings = [(0.0, r), (1.0 - (tip/L if tip else 0), r1)]
    V = []
    for t, rr in rings:
        for i in range(n):
            th = 2*math.pi*i/n
            j = 1 + (rng.uniform(-0.05, 0.05) if rng else 0)
            V.append(tuple(p0[k] + d[k]*L*t + (u[k]*math.cos(th) + w[k]*math.sin(th))*rr*j for k in range(3)))
    F = [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)] + [tuple(reversed(range(n)))]
    if tip:
        V.append(tuple(p1)); c = len(V)-1
        F += [(n+i, n+(i+1) % n, c) for i in range(n)]
    else:
        F.append(tuple(range(n, 2*n)))
    return V, F

def lathe(rings, n=16, cx=0.0, cy=0.0, cap=True):
    V = []
    for z, r in rings:
        for i in range(n):
            th = 2*math.pi*i/n
            V.append((cx+r*math.cos(th), cy+r*math.sin(th), z))
    m = len(rings)
    F = [(k*n+i, k*n+(i+1) % n, (k+1)*n+(i+1) % n, (k+1)*n+i) for k in range(m-1) for i in range(n)]
    if cap:
        F += [tuple(reversed(range(n))), tuple(range((m-1)*n, m*n))]
    return V, F

def grid(rows, closed=True):
    """rows: list of point-lists（同长）→ 网格面"""
    m, n = len(rows), len(rows[0])
    V = [p for r in rows for p in r]
    cols = n if closed else n-1
    F = [(k*n+i, k*n+(i+1) % n, (k+1)*n+(i+1) % n, (k+1)*n+i) for k in range(m-1) for i in range(cols)]
    return V, F


class Piece:
    def __init__(self, pid, name):
        self.pid, self.name, self.groups = pid, name, {}
    def add(self, g, mat, geo):
        e = self.groups.setdefault(g, [mat, [], []]); o = len(e[1])
        e[1].extend(geo[0]); e[2].extend(tuple(i+o for i in f) for f in geo[1])
    def bbox(self):
        vs = [p for g in self.groups.values() for p in g[1]]
        return [min(p[k] for p in vs) for k in range(3)], [max(p[k] for p in vs) for k in range(3)]
    def nf(self):
        return sum(len(g[2]) for g in self.groups.values())


# ============================================================ 矩形周长参数化
_EN = [(0, -1), (1, 0), (0, 1), (-1, 0)]

def rect_at(W, D, e, t):
    c = [(-W/2, -D/2), (W/2, -D/2), (W/2, D/2), (-W/2, D/2)]
    a, b = c[e], c[(e+1) % 4]
    return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)

def ring_samples(W, D, step):
    """沿外框周长采样：[(edge, t, 边长)]，每个角点只出现一次"""
    out = []
    for e in range(4):
        Le = W if e % 2 == 0 else D
        n = max(4, round(Le/step))
        out += [(e, k/n, Le) for k in range(n)]
    return out


def roof_sheet(W0, D0, z0, W1, D1, z1, v0=0.0, v1=1.0, nv=10, step=0.12, lift=0.4, sag=0.07, rib=1.0):
    """四坡帐顶（帆布）：外框 W0×D0@z0 → 内框 W1×D1@z1；凹曲、翘角、骨架间下垂"""
    S = ring_samples(W0, D0, step)
    rows = []
    for j in range(nv+1):
        v = v0 + (v1-v0)*j/nv
        row = []
        for (e, t, Le) in S:
            a = rect_at(W0, D0, e, t); b = rect_at(W1, D1, e, t)
            x, y = a[0]+(b[0]-a[0])*v, a[1]+(b[1]-a[1])*v
            dc = min(t, 1-t)*Le
            cc = max(0.0, 1 - dc/0.9)**2
            fl = 1 + 0.05*cc*(1-v)**2
            z = z0 + (z1-z0)*(0.32*v + 0.68*v**1.8) + lift*cc*(1-v)**1.6
            nr = max(1, round(Le/rib))
            s = abs(math.sin(math.pi*t*nr))
            z -= sag*s*(0.3 + 0.7*math.sin(math.pi*min(v, 1.0)))*(1-cc)
            row.append((x*fl, y*fl, z))
        rows.append(row)
    return grid(rows)


def valance(W0, D0, z0, drop, lift, step=0.08, period=0.5, out=0.012):
    """檐口垂幔（红布，下缘波浪），跟随翘角"""
    S = ring_samples(W0, D0, step)
    top, bot = [], []
    for (e, t, Le) in S:
        a = rect_at(W0, D0, e, t)
        dc = min(t, 1-t)*Le; cc = max(0.0, 1-dc/0.9)**2
        fl = 1 + 0.05*cc
        n = _EN[e]
        x, y = a[0]*fl + n[0]*out, a[1]*fl + n[1]*out
        zt = z0 + lift*cc - 0.02
        s = t*Le
        zb = zt - drop*(0.72 + 0.28*abs(math.cos(math.pi*s/period)))
        top.append((x, y, zt)); bot.append((x, y, zb))
    return grid([top, bot])


def wall_sheet(W, D, zt, zb, step=0.1, nv=12, amp=0.05, lam=0.5, flare=0.06, door=None, seed=0):
    """帆布围帐：上缘绷直，下部出现竖向褶皱并略外张；door=(edge, t0, t1) 处开门"""
    S = ring_samples(W, D, step)
    rows = []
    sacc = 0.0; prev_e = 0; cum = []
    for (e, t, Le) in S:
        cum.append(sum((W if k % 2 == 0 else D) for k in range(e)) + t*Le)
    for j in range(nv+1):
        v = j/nv
        row = []
        for idx, (e, t, Le) in enumerate(S):
            a = rect_at(W, D, e, t)
            n = _EN[e]
            if t == 0:
                p = _EN[(e-1) % 4]; n = ((n[0]+p[0])/1.414, (n[1]+p[1])/1.414)
            s = cum[idx]
            d = amp*v**1.2*math.sin(2*math.pi*s/lam + 0.8*math.sin(1.3*s + seed)) + flare*v**2
            z = zt + (zb-zt)*v
            if j == nv:
                z += 0.03*abs(math.sin(math.pi*s/0.35))
            row.append((a[0]+n[0]*d, a[1]+n[1]*d, z))
        rows.append(row)
    V, F = grid(rows)
    if door:
        de, t0, t1 = door
        n = len(S)
        keep = []
        for f in F:
            i = f[0] % n
            e, t, Le = S[i]
            if e == de and t0 <= t < t1:
                continue
            keep.append(f)
        F = keep
    return V, F


def wavy_banner(x0, x1, ztop, zbot, y, amp=0.07, waves=1.2, nx=14, nz=12, tail=True):
    rows = []
    for j in range(nz+1):
        v = j/nz
        z = ztop + (zbot-ztop)*v
        row = []
        for i in range(nx+1):
            u = i/nx
            zz = z
            if tail and j == nz:
                zz = z - 0.35*abs(math.sin(math.pi*u*2))   # 燕尾
            row.append((x0+(x1-x0)*u, y + amp*u*math.sin(2*math.pi*waves*u + v*0.8), zz))
        rows.append(row)
    return grid(rows, closed=False)


def guy(P, p_top, p_ground, rng):
    P.add("拉绳", "绳", log(p_top, p_ground, 0.012, n=4))
    P.add("地桩", "木深", log((p_ground[0], p_ground[1], -0.15), (p_ground[0], p_ground[1], 0.28), 0.035, n=6, tip=0.08))


def flag_on(P, x, y, h, rng, g="旗"):
    P.add(g+"_座", "石", frustum((x, y, 0), (0.7, 0.7), (0.45, 0.45), 0.35))
    P.add(g+"_杆", "木深", log((x, y, 0.2), (x, y, h), 0.07, n=10, r1=0.05))
    P.add(g+"_顶", "金", log((x, y, h), (x, y, h+0.35), 0.06, n=8, tip=0.3))
    P.add(g+"_横杆", "木深", log((x-0.05, y, h-0.4), (x+1.15, y, h-0.4), 0.03, n=6))
    P.add(g+"_幡", "红布", wavy_banner(x+0.08, x+1.1, h-0.45, h-3.0, y, amp=0.08))
    P.add(g+"_徽", "金", box((x+0.6, y+0.07*0.5-0.02, h-1.5), (0.45, 0.02, 0.45)))
    for sx in (-1, 1):
        guy(P, (x, y, h*0.62), (x+sx*1.4, y+1.0, 0), rng)


# ============================================================ C01 主帅指挥帐
def C01():
    P = Piece("C01", "主帅指挥帐"); rng = random.Random(SEED)
    DW, DD, DH = 9.4, 7.4, 0.38
    # 台基：石脚 + 木平台 + 前踏步
    P.add("台基_石", "石", frustum((0, 0, 0), (DW+0.3, DD+0.3), (DW+0.1, DD+0.1), 0.18))
    for i in range(int(DW/0.3)):
        x = -DW/2 + 0.15 + i*0.3
        P.add("台基_木板", "木", box((x, 0, 0.18+(DH-0.18)/2), (0.28, DD, DH-0.18)))
    for k in range(3):
        P.add("台基_踏步", "木深", box((0, -DD/2-0.3-k*0.3, (DH*(3-k)/3)/2), (2.6, 0.3, DH*(3-k)/3)))
    z0 = DH
    W, D = 8.0, 6.0
    # 立柱
    for e in range(4):
        Le = W if e % 2 == 0 else D
        for k in range(round(Le/2)):
            x, y = rect_at(W, D, e, k/round(Le/2))
            P.add("立柱", "木深", log((x, y, z0), (x, y, z0+2.45), 0.09, n=8, rng=rng))
    for sx in (-1, 1):
        P.add("中柱", "木深", log((sx*1.0, 0, z0), (sx*1.0, 0, 6.65), 0.12, n=10, rng=rng))
    # 围帐（正面开门）
    P.add("围帐", "帆布", wall_sheet(W, D, z0+2.35, z0+0.04, door=(0, 0.39, 0.61), seed=1))
    for sx in (-1, 1):   # 门帘卷起，扎在门两侧
        P.add("门帘卷", "帆布", log((sx*0.95, -D/2-0.08, z0+0.05), (sx*0.95, -D/2-0.08, z0+2.3), 0.12, n=10, r1=0.09))
        for zz in (z0+0.7, z0+1.6):
            P.add("门帘绳", "红布", log((sx*0.95-0.14, -D/2-0.08, zz), (sx*0.95+0.14, -D/2-0.08, zz), 0.02, n=6))
    P.add("门楣帘", "帆布", wavy_banner(-0.95, 0.95, z0+2.35, z0+2.0, -D/2-0.05, amp=0.03, waves=2, nx=10, nz=3, tail=False))
    # 下重檐
    zl0, zl1 = z0+2.25, z0+3.55
    P.add("下檐_垂幔", "红布", valance(9.6, 7.6, zl0, 0.32, 0.32))
    P.add("下檐", "帆布深", roof_sheet(9.6, 7.6, zl0, 5.2, 3.4, zl1, lift=0.32, sag=0.06))
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.add("角梁", "木深", log((sx*W/2, sy*D/2, z0+2.42), (sx*9.6/2*1.05, sy*7.6/2*1.05, zl0+0.3), 0.05, n=6))
            P.add("角梁_翘头", "木深", log((sx*9.6/2*1.05, sy*7.6/2*1.05, zl0+0.3), (sx*9.6/2*1.12, sy*7.6/2*1.12, zl0+0.55), 0.04, n=6, tip=0.12))
    # 上层短围帐 + 上重檐
    P.add("上围帐", "帆布深", wall_sheet(5.0, 3.2, zl1+0.75, zl1-0.15, step=0.12, nv=5, amp=0.02, flare=0.0, seed=2))
    zu0, zu1 = zl1+0.6, 6.55
    P.add("上檐_垂幔", "红布", valance(6.3, 4.5, zu0, 0.26, 0.42))
    P.add("上檐", "帆布深", roof_sheet(6.3, 4.5, zu0, 2.2, 0.0, zu1, lift=0.42, sag=0.05, nv=12))
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.add("角梁", "木深", log((sx*2.5, sy*1.6, zu0+0.1), (sx*6.3/2*1.05, sy*4.5/2*1.05, zu0+0.42), 0.04, n=6))
            P.add("角梁_翘头", "木深", log((sx*6.3/2*1.05, sy*4.5/2*1.05, zu0+0.42), (sx*6.3/2*1.12, sy*4.5/2*1.12, zu0+0.66), 0.035, n=6, tip=0.1))
    P.add("脊杆", "木深", log((-1.35, 0, zu1+0.06), (1.35, 0, zu1+0.06), 0.07, n=8))
    for sx in (-1, 1):
        P.add("脊饰", "金", log((sx*1.35, 0, zu1), (sx*1.35, 0, zu1+0.55), 0.05, n=8, tip=0.2))
        P.add("脊饰", "金", lathe([(zu1+0.22, 0.0), (zu1+0.26, 0.09), (zu1+0.34, 0.09), (zu1+0.38, 0.0)], n=10, cx=sx*1.35))
    # 前檐遮阳
    AW, AY = 3.6, 2.4
    rows = []
    for j in range(9):
        v = j/8
        y = -D/2 - 0.1 - AY*v
        z = zl0 - 0.15 - 0.45*v
        rows.append([(-AW/2 + AW*i/12, y, z - 0.09*math.sin(math.pi*i/12)*math.sin(math.pi*max(v, 0.15))) for i in range(13)])
    P.add("前檐遮阳", "帆布", grid(rows, closed=False))
    P.add("前檐遮阳_垂幔", "红布", grid([[(-AW/2 + AW*i/24, -D/2-0.1-AY-0.01, zl0-0.62) for i in range(25)],
                                    [(-AW/2 + AW*i/24, -D/2-0.1-AY-0.01, zl0-0.62-0.2*(0.7+0.3*abs(math.cos(math.pi*i/3)))) for i in range(25)]], closed=False))
    for sx in (-1, 1):
        px, py = sx*AW/2, -D/2-0.1-AY
        P.add("遮阳柱", "木深", log((px, py, z0 if abs(py) < DD/2 else 0), (px, py, zl0-0.55), 0.06, n=8))
        guy(P, (px, py, zl0-0.6), (px+sx*0.8, py-1.4, 0), rng)
    # 檐角拉绳
    for sx in (-1, 1):
        for sy in (-1, 1):
            guy(P, (sx*9.6/2, sy*7.6/2, zl0), (sx*(DW/2+1.4), sy*(DD/2+1.4), 0), rng)
    # 门前旗
    for sx in (-1, 1):
        flag_on(P, sx*3.4, -DD/2-2.8, 6.4, rng, g="门旗")
    return P


# ============================================================ C02 营房长帐
def C02():
    P = Piece("C02", "营房长帐"); rng = random.Random(SEED+1)
    L, D, ze, zr, ov = 8.0, 4.4, 1.75, 3.35, 0.35
    nraf = 6
    for k in range(nraf+1):
        x = -L/2 + L*k/nraf
        for sy in (-1, 1):
            P.add("檐柱", "木深", log((x, sy*D/2, -0.2), (x, sy*D/2, ze+0.05), 0.07, n=8, rng=rng))
        if k in (0, nraf//2, nraf):
            P.add("脊柱", "木深", log((x, 0, -0.2), (x, 0, zr+0.1), 0.09, n=8, rng=rng))
    P.add("脊杆", "木深", log((-L/2-0.3, 0, zr+0.04), (L/2+0.3, 0, zr+0.04), 0.07, n=8))
    for sy in (-1, 1):
        P.add("檐杆", "木深", log((-L/2-0.1, sy*D/2, ze), (L/2+0.1, sy*D/2, ze), 0.05, n=6))
        rows = []
        for j in range(11):
            v = j/10
            y = sy*(D/2+ov)*(1-v)
            z = (ze-0.12) + (zr-ze+0.12)*(0.4*v + 0.6*v**1.3)
            row = []
            for i in range(nraf*8+1):
                u = i/(nraf*8)
                x = -L/2-0.25 + (L+0.5)*u
                s = abs(math.sin(math.pi*u*nraf))
                row.append((x, y, z - 0.08*s*(0.3+0.7*math.sin(math.pi*v))))
            rows.append(row)
        P.add("帐顶", "帆布", grid(rows, closed=False))
        # 垂幔
        top = [(-L/2-0.25+(L+0.5)*i/80, sy*(D/2+ov+0.01), ze-0.14) for i in range(81)]
        bot = [(p[0], p[1], p[2]-0.24*(0.72+0.28*abs(math.cos(math.pi*(p[0]+L/2)/0.5)))) for p in top]
        P.add("垂幔", "红布", grid([top, bot], closed=False))
        for k in range(nraf+1):
            x = -L/2 + L*k/nraf
            guy(P, (x, sy*(D/2+ov), ze-0.1), (x, sy*(D/2+1.6), 0), rng)
    # 侧围帐：背面放下，正面中段卷起
    for sy, open_mid in ((1, False), (-1, True)):
        rows = []
        for j in range(9):
            v = j/8
            z = ze - 0.12 - (ze-0.15)*v
            row = []
            for i in range(81):
                x = -L/2 + L*i/80
                d = 0.04*v**1.2*math.sin(2*math.pi*x/0.5 + sy) + 0.05*v**2
                row.append((x, sy*(D/2 + d), z if j < 8 else z + 0.03*abs(math.sin(math.pi*x/0.35))))
            rows.append(row)
        V, F = grid(rows, closed=False)
        if open_mid:
            F = [f for f in F if not (-2.0 < V[f[0]][0] < 2.0)]
        P.add("围帐", "帆布", (V, F))
        if open_mid:
            P.add("卷帘", "帆布", log((-2.0, -D/2-0.1, ze-0.25), (2.0, -D/2-0.1, ze-0.25), 0.13, n=10))
            for x in (-1.4, 0, 1.4):
                P.add("卷帘绳", "红布", log((x, -D/2-0.1, ze-0.1), (x, -D/2-0.1, ze-0.42), 0.02, n=6))
    # 山墙（三角帆布）
    for sx in (-1, 1):
        rows = []
        for j in range(9):
            v = j/8
            z = zr*(1-v)
            half = D/2 * min(1.0, (zr - z)/(zr-ze)) if z > ze else D/2
            row = [(sx*(L/2 + 0.03*math.sin(i*1.7)*v), -half + 2*half*i/14, z if j < 8 else 0.03) for i in range(15)]
            rows.append(row)
        P.add("山墙", "帆布", grid(rows, closed=False))
    # 帐内铺草席 + 两张木榻
    P.add("草席", "绳", box((0, 0.3, 0.02), (L-0.6, D-1.4, 0.04)))
    for x in (-2.4, 2.4):
        P.add("木榻", "木", box((x, 1.1, 0.22), (2.0, 0.9, 0.08)))
        for dx in (-0.85, 0.85):
            for dy in (-0.35, 0.35):
                P.add("木榻", "木深", box((x+dx, 1.1+dy, 0.09), (0.08, 0.08, 0.18)))
    return P


# ============================================================ C03 圆帐
def C03():
    P = Piece("C03", "圆帐"); rng = random.Random(SEED+2)
    R, n = 2.6, 72
    door = (-math.pi/2 - 0.24, -math.pi/2 + 0.24)
    indoor = lambda th: door[0] < ((th + math.pi) % (2*math.pi)) - math.pi < door[1]
    # 毛石矮墙
    z = 0.0
    for row in range(3):
        h = 0.27
        th = rng.uniform(0, 0.3)
        while th < 2*math.pi:
            L = rng.uniform(0.35, 0.6)
            a = th + L/2/R
            if not indoor(a):
                P.add("石墙", "石深" if rng.random() < 0.25 else "石",
                      box((R*math.cos(a), R*math.sin(a), z+h/2), (L-0.03, 0.5, h-0.03),
                          (rng.uniform(-3, 3), rng.uniform(-3, 3), math.degrees(a)+90+rng.uniform(-4, 4))))
            th += L/R
        z += h
    zw = 0.8
    # 帆布围帐
    rows = []
    for j in range(9):
        v = j/8
        zz = 2.15 - (2.15 - zw + 0.05)*v
        row = []
        for i in range(n):
            th = 2*math.pi*i/n
            r = R - 0.12 + 0.04*v**1.2*math.sin(14*th) + 0.03*v**2
            row.append((r*math.cos(th), r*math.sin(th), zz))
        rows.append(row)
    V, F = grid(rows)
    F = [f for f in F if not indoor(2*math.pi*(f[0] % n)/n + math.pi/n)]
    P.add("围帐", "帆布", (V, F))
    # 圆锥帐顶（12 骨架间下垂）
    nr = 12
    rows = []
    for j in range(11):
        v = j/10
        r = 3.0*(1-v) + 0.22*v
        zz = 2.05 + (4.25-2.05)*(0.35*v + 0.65*v**1.7)
        row = []
        for i in range(n):
            th = 2*math.pi*i/n
            s = abs(math.sin(nr*th/2))
            row.append((r*math.cos(th), r*math.sin(th), zz - 0.07*s*(0.3+0.7*math.sin(math.pi*v))))
        rows.append(row)
    P.add("帐顶", "帆布深", grid(rows))
    top = [(3.01*math.cos(2*math.pi*i/n), 3.01*math.sin(2*math.pi*i/n), 2.03) for i in range(n)]
    bot = [(p[0], p[1], p[2]-0.25*(0.72+0.28*abs(math.cos(i*math.pi/3)))) for i, p in enumerate(top)]
    P.add("垂幔", "红布", grid([top, bot]))
    P.add("顶帽", "帆布深", lathe([(4.2, 0.26), (4.42, 0.2), (4.5, 0.0)], n=16))
    P.add("顶饰", "金", log((0, 0, 4.45), (0, 0, 5.0), 0.04, n=8, tip=0.2))
    P.add("中柱", "木深", log((0, 0, 0), (0, 0, 4.4), 0.1, n=10))
    # 门框
    for s in (-1, 1):
        a = -math.pi/2 + s*0.26
        P.add("门框", "木深", log((R*math.cos(a), R*math.sin(a)-0.1, 0), (R*math.cos(a), R*math.sin(a)-0.1, 2.05), 0.07, n=8))
    P.add("门楣", "木深", log((R*math.cos(-math.pi/2-0.3), -R-0.05, 2.05), (R*math.cos(-math.pi/2+0.3), -R-0.05, 2.05), 0.07, n=8))
    P.add("门帘", "红布", wavy_banner(-0.55, 0.55, 2.0, 1.55, -R-0.12, amp=0.02, waves=2, nx=8, nz=3, tail=False))
    for k in range(6):
        a = 2*math.pi*k/6 + 0.5
        guy(P, (3.0*math.cos(a), 3.0*math.sin(a), 2.0), (4.3*math.cos(a), 4.3*math.sin(a), 0), rng)
    return P


# ============================================================ C04 军需敞棚
def C04():
    P = Piece("C04", "军需敞棚"); rng = random.Random(SEED+3)
    L, D, ze, zr = 6.0, 4.0, 2.25, 3.1
    for x in (-L/2, 0, L/2):
        for sy in (-1, 1):
            P.add("立柱", "木深", log((x, sy*D/2, 0), (x, sy*D/2, ze+0.05), 0.08, n=8, rng=rng))
        P.add("脊柱", "木深", log((x, 0, ze), (x, 0, zr+0.05), 0.07, n=8))
        P.add("梁", "木深", log((x, -D/2, ze), (x, D/2, ze), 0.06, n=6))
    P.add("脊杆", "木深", log((-L/2-0.3, 0, zr+0.03), (L/2+0.3, 0, zr+0.03), 0.06, n=8))
    for sy in (-1, 1):
        rows = []
        for j in range(9):
            v = j/8
            y = sy*(D/2+0.3)*(1-v); z = (ze-0.1) + (zr-ze+0.1)*v
            rows.append([(-L/2-0.3+(L+0.6)*i/48, y, z - 0.07*abs(math.sin(math.pi*i/24))*(0.3+0.7*math.sin(math.pi*v))) for i in range(49)])
        P.add("棚顶", "帆布", grid(rows, closed=False))
        top = [(-L/2-0.3+(L+0.6)*i/60, sy*(D/2+0.31), ze-0.12) for i in range(61)]
        P.add("垂幔", "红布", grid([top, [(p[0], p[1], p[2]-0.22*(0.72+0.28*abs(math.cos(math.pi*(p[0]+3)/0.5)))) for p in top]], closed=False))
    # 长案与长凳
    P.add("长案", "木", box((0, 0, 0.78), (3.6, 0.9, 0.08)))
    for dx in (-1.6, 1.6):
        for dy in (-0.35, 0.35):
            P.add("长案", "木深", box((dx, dy, 0.38), (0.09, 0.09, 0.74)))
    for sy in (-1, 1):
        P.add("长凳", "木", box((0, sy*0.95, 0.45), (3.2, 0.3, 0.06)))
        for dx in (-1.4, 1.4):
            P.add("长凳", "木深", box((dx, sy*0.95, 0.21), (0.08, 0.24, 0.42)))
    P.add("案上竹简", "绳", box((-0.6, 0, 0.86), (0.5, 0.35, 0.06), (0, 0, 8)))
    P.add("案上陶碗", "石深", lathe([(0.82, 0.0), (0.82, 0.07), (0.9, 0.1), (0.9, 0.09)], n=12, cx=0.7, cy=0.1))
    return P


# ============================================================ C05 旗杆 / C06 篝火灶
def C05():
    P = Piece("C05", "旗杆"); rng = random.Random(SEED+4)
    flag_on(P, 0, 0, 7.0, rng)
    return P


def C06():
    P = Piece("C06", "篝火灶"); rng = random.Random(SEED+5)
    for k in range(12):
        a = 2*math.pi*k/12
        P.add("石圈", "石深" if k % 3 == 0 else "石", box((0.62*math.cos(a), 0.62*math.sin(a), 0.12), (0.32, 0.28, 0.24),
                                                   (rng.uniform(-8, 8), rng.uniform(-8, 8), math.degrees(a)+rng.uniform(-10, 10))))
    P.add("灰烬", "炭", lathe([(0.0, 0.5), (0.04, 0.45), (0.06, 0.0)], n=16))
    for k in range(5):
        a = 2*math.pi*k/5
        P.add("柴", "木深", log((0.45*math.cos(a), 0.45*math.sin(a), 0.05), (0.05*math.cos(a+0.4), 0.05*math.sin(a+0.4), 0.38), 0.05, n=6, rng=rng))
    apex = (0, 0, 1.55)
    for k in range(3):
        a = 2*math.pi*k/3 + 0.3
        P.add("三脚架", "木深", log((0.95*math.cos(a), 0.95*math.sin(a), 0), apex, 0.04, n=6))
    P.add("吊链", "铁", log(apex, (0, 0, 0.82), 0.012, n=4))
    P.add("吊锅", "铁", lathe([(0.5, 0.06), (0.52, 0.2), (0.62, 0.26), (0.76, 0.25), (0.8, 0.27), (0.78, 0.0)], n=16))
    return P


PIECES = [C01, C02, C03, C04, C05, C06]


# ============================================================ Blender
def run():
    import bpy, bmesh
    from mathutils import Vector

    T0 = time.time(); logl = []
    def L(s):
        logl.append("[%5.1fs] %s" % (time.time()-T0, s)); print(logl[-1])
    for d in ("renders/", "fbx/"):
        os.makedirs(OUT + d, exist_ok=True)

    sc = bpy.data.scenes.get("营地建筑")
    if sc:
        for ob in list(sc.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(sc)
    for c in list(bpy.data.collections):
        if c.name.startswith("营地套件_") or c.name.startswith("营地展示") or c.name == "营地组装演示":
            for ob in list(c.all_objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    sc = bpy.data.scenes.new("营地建筑")
    bpy.context.window.scene = sc
    root = sc.collection

    mats = {}
    for k, rgb in COL.items():
        m = bpy.data.materials.get("营地_" + k) or bpy.data.materials.new("营地_" + k)
        m.diffuse_color = (*rgb, 1)
        try:
            m.use_nodes = True
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.85
            if k in ("金", "铁"):
                b.inputs["Metallic"].default_value = 0.7
        except Exception:
            pass
        mats[k] = m

    kit, built = {}, {}
    for fn in PIECES:
        P = fn(); built[P.pid] = P
        col = bpy.data.collections.new("营地套件_%s_%s" % (P.pid, P.name)); root.children.link(col)
        for g, (mat, V, F) in P.groups.items():
            me = bpy.data.meshes.new("%s_%s" % (P.pid, g))
            me.from_pydata(V, [], F); me.validate()
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
            me.materials.append(mats[mat])
            ob = bpy.data.objects.new("%s_%s" % (P.pid, g), me); col.objects.link(ob)
            if mat in CLOTH:
                for p in me.polygons:
                    p.use_smooth = True
                so = ob.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = 0.018; so.offset = 0.0
                su = ob.modifiers.new("Subdivision", "SUBSURF"); su.levels = 1; su.render_levels = 2
        kit[P.pid] = col
        lo, hi = P.bbox()
        L("%s %s  %.2f×%.2f×%.2f m  面数 %d" % (P.pid, P.name, hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2], P.nf()))

    # 人物
    fig_col = bpy.data.collections.get("套件_人物参照")
    if fig_col is None or not [o for o in fig_col.objects if o.type == "MESH"]:
        fig_col = bpy.data.collections.new("营地套件_人物参照"); root.children.link(fig_col)
        if os.path.isfile(FBX_FIG):
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
    L("人物参照：%s" % fig_col.name)

    # 城墙与栅栏套件（组装演示用）
    wall = {}
    for nm in ("套件_P01_木栅栏直段", "套件_P02_栅栏门", "套件_P03_石柱墩", "套件_P04_拒马"):
        c = bpy.data.collections.get(nm)
        if c is None and os.path.isfile(WALL_BLEND):
            try:
                d_ = WALL_BLEND + "/Collection/"
                bpy.ops.wm.append(filepath=d_ + nm, directory=d_, filename=nm)
                c = bpy.data.collections.get(nm)
                if sc.collection.children.get(c.name):
                    sc.collection.children.unlink(c)
            except Exception as e:
                L("追加 %s 失败 %r" % (nm, e))
        if c:
            wall[nm[3:6]] = c
    L("城墙栅栏套件：%s" % list(wall.keys()))

    if EXPORT_FBX:
        for pid, col in kit.items():
            lc = sc.view_layers[0].layer_collection.children[col.name]
            sc.view_layers[0].active_layer_collection = lc
            try:
                bpy.ops.export_scene.fbx(filepath=OUT + "fbx/%s.fbx" % col.name.replace("营地套件_", ""),
                                         use_active_collection=True, use_mesh_modifiers=True, axis_forward="-Z", axis_up="Y")
            except Exception as e:
                L("FBX %s 失败 %r" % (pid, e))
        L("FBX 导出完成")
    for col in kit.values():
        sc.view_layers[0].layer_collection.children[col.name].exclude = True
    if fig_col.name in [c.name for c in sc.view_layers[0].layer_collection.children]:
        sc.view_layers[0].layer_collection.children[fig_col.name].exclude = True

    def inst(col, loc, rz=0, parent=None, name=None):
        e = bpy.data.objects.new(name or ("实例_" + col.name), None)
        e.instance_type = "COLLECTION"; e.instance_collection = col
        e.location = loc; e.rotation_euler = (0, 0, math.radians(rz))
        (parent or root).objects.link(e)
        return e

    # ---------------- 展示
    show = bpy.data.collections.new("营地展示"); root.children.link(show)
    cams, subs = [], []
    x = 0.0
    for pid in ["C01", "C02", "C03", "C04", "C05", "C06"]:
        lo, hi = built[pid].bbox()
        x += -lo[0] + 2
        sub = bpy.data.collections.new("营地展示_" + pid); show.children.link(sub); subs.append(sub)
        inst(kit[pid], (x, 0, 0), parent=sub)
        inst(fig_col, (x + hi[0] + 0.9, lo[1] + 0.4, 0), parent=sub, name="人物_" + pid)
        cx, cz = x + (lo[0]+hi[0])/2 + 0.5, (lo[2]+hi[2])/2
        span = max(hi[0]-lo[0]+2.4, hi[2]-lo[2], hi[1]-lo[1]) * 1.15
        for vn, loc, rot in (("正视", (cx, -80, cz), (90, 0, 0)), ("侧视", (x+hi[0]+80, (lo[1]+hi[1])/2, cz), (90, 0, 90)),
                             ("顶视", (cx, (lo[1]+hi[1])/2, 90), (0, 0, 0))):
            cd = bpy.data.cameras.new("CAM_%s_%s" % (pid, vn)); cd.type = "ORTHO"; cd.ortho_scale = span; cd.clip_end = 400
            co = bpy.data.objects.new(cd.name, cd); sub.objects.link(co); co.location = loc
            co.rotation_euler = tuple(math.radians(a) for a in rot)
            cams.append(("%s_%s_%s" % (pid, built[pid].name, vn), co, (1400, 1100), [sub]))
        cd = bpy.data.cameras.new("CAM_%s_透视" % pid); cd.lens = 40; cd.clip_end = 400
        co = bpy.data.objects.new(cd.name, cd); sub.objects.link(co)
        tgt = Vector((x + (lo[0]+hi[0])/2, (lo[1]+hi[1])/2, hi[2]*0.42))
        R = max(hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2])
        co.location = tgt + Vector((-0.6, -1.0, 0.42)).normalized()*max(R*1.4, 5.5)
        co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()
        cams.append(("%s_%s_透视" % (pid, built[pid].name), co, (1500, 1150), [sub]))
        x += hi[0] + 5

    # ---------------- 营地组装演示
    demo = bpy.data.collections.new("营地组装演示"); root.children.link(demo)
    oy = 80.0
    D = lambda x, y: (x, y + oy, 0)
    inst(kit["C01"], D(0, 6), parent=demo)
    inst(kit["C02"], D(-12, 3), rz=90, parent=demo)
    inst(kit["C02"], D(-12, 12), rz=90, parent=demo)
    inst(kit["C02"], D(12, 3), rz=-90, parent=demo)
    inst(kit["C03"], D(-9, -8), parent=demo)
    inst(kit["C03"], D(12, 13), rz=40, parent=demo)
    inst(kit["C04"], D(10, -8), rz=0, parent=demo)
    for p in ((-4, -12), (4, -12)):
        inst(kit["C05"], D(*p), parent=demo)
    for p in ((0, -5), (-5, -13)):
        inst(kit["C06"], D(*p), parent=demo)
    gy = -19.0
    if "P02" in wall:
        inst(wall["P02"], D(0, gy), parent=demo)
    if "P01" in wall:
        for k in range(1, 5):
            for s in (-1, 1):
                inst(wall["P01"], D(s*(4.1*k), gy), parent=demo)
    if "P03" in wall:
        for s in (-1, 1):
            inst(wall["P03"], D(s*19.3, gy), parent=demo)
    if "P04" in wall:
        for p, r in (((-3.6, gy-5), 8), ((3.8, gy-5.4), -6), ((-9, gy-4.6), 0), ((9, gy-4.8), 4)):
            inst(wall["P04"], D(*p), rz=r, parent=demo)
    for p, r in (((-0.9, gy+1.2), 0), ((0.9, gy+1.4), 10), ((0.6, -4.0), 160), ((-0.9, -4.3), 200),
                 ((-0.6, 6-4.9), 0), ((1.6, 6-5.5), 15), ((8.4, -8.5), 70), ((-7.5, -12.5), 120)):
        e = inst(fig_col, D(*p), rz=r, parent=demo, name="人物_演示")
        if abs(p[1]-(6-4.9)) < 0.01:
            e.location.z = 0.38
    gm = bpy.data.materials.get("营地_地面") or bpy.data.materials.new("营地_地面"); gm.diffuse_color = (0.56, 0.51, 0.42, 1)
    gd = bpy.data.meshes.new("营地地面"); gd.from_pydata([(-34, oy-34, 0), (34, oy-34, 0), (34, oy+30, 0), (-34, oy+30, 0)], [], [(0, 1, 2, 3)])
    gd.materials.append(gm); demo.objects.link(bpy.data.objects.new("营地地面", gd))
    for nm, loc, tgt, lens in (("营地_鸟瞰", (-19, oy-34, 22), (0, oy-2, 0), 32),
                               ("营地_主帐近景", (-4.5, oy-12.5, 2.6), (0, oy+5, 3.4), 30),
                               ("营地_营门", (6, oy-33, 5.0), (0, oy-6, 2.5), 32)):
        cd = bpy.data.cameras.new("CAM_" + nm); cd.lens = lens; cd.clip_end = 500
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
    sc.camera = cams[-3][1]
    bpy.ops.wm.save_as_mainfile(filepath=OUT + "营地建筑_套件.blend")
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
            print("%s %-8s %.2f×%.2f×%.2f  面数 %d" % (P.pid, P.name, hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2], P.nf()))
