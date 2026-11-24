# -*- coding: utf-8 -*-
"""
《楼·溯》第1章·巴丘瞭望 —— 城墙与栅栏 模块化套件（Blender 直接搭建）

套件（单位米，正面/外侧朝 -Y，原点在构件底面中心，可按 6 m 网格拼接）：
  W01 城墙直段      6 m 长，毛石砌筑、外墙收分，顶部步道 + 外沿木栅女墙
  W02 城墙转角石台  4.4 m 见方，比城墙高，石砌垛口，射孔
  W03 城门段        6 m 长，3 m 宽门洞，木过梁 + 双扇木门
  W04 登城石阶      贴城墙内侧，16 级，带护墙
  P01 木栅栏直段    4 m 长，削尖原木 + 横档 + 斜撑 + 石脚
  P02 栅栏门        4 m 宽，门柱、门楣、双扇原木门
  P03 石柱墩        栅栏端头 / 转折处的石墩，带垛口
  P04 拒马          营地路障
运行后：每个构件一个集合（位于原点，可直接导出），展示与组装用集合实例；
导出每个构件 FBX，渲染三视图 + 透视 + 组装场景，存 .blend。
"""
import math, os, random, time

OUT = "C:/Users/pjwly/3D Objects/楼溯_资产库/第1章_巴丘瞭望/07_Blender搭建/城墙与栅栏/"
FBX_FIG = "D:/Caroline Elvira/ancient chinese robe 3d model/ancient_chinese_robe_3d_model.fbx"
SEED = 11
RENDER = True
EXPORT_FBX = True

WALL_H = 4.8          # 城墙高（步道面）
WALL_T0 = 3.4         # 底厚
WALL_T1 = 2.8         # 顶厚（收分）
SEG_L = 6.0           # 直段长度
PAL_H = 1.8           # 女墙木栅高

COL = {"石": (0.47, 0.44, 0.40), "石深": (0.36, 0.34, 0.31), "石浅": (0.58, 0.55, 0.49), "夯土": (0.50, 0.44, 0.36),
       "木": (0.40, 0.27, 0.16), "木深": (0.28, 0.19, 0.12), "铁": (0.22, 0.22, 0.24),
       "绳": (0.62, 0.54, 0.40), "孔": (0.08, 0.07, 0.07)}


# ============================================================ 几何工具
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
    """底 b=(w,d) 顶 t=(w,d) 高 h，c 为底面中心"""
    x, y, z = c
    v = [(x-b[0]/2, y-b[1]/2, z), (x+b[0]/2, y-b[1]/2, z), (x+b[0]/2, y+b[1]/2, z), (x-b[0]/2, y+b[1]/2, z),
         (x-t[0]/2, y-t[1]/2, z+h), (x+t[0]/2, y-t[1]/2, z+h), (x+t[0]/2, y+t[1]/2, z+h), (x-t[0]/2, y+t[1]/2, z+h)]
    return v, list(_BF)

def log(p0, p1, r, n=8, tip=0.0, rng=None):
    """原木：p0→p1 圆柱，tip>0 时顶端削尖"""
    d = [p1[i]-p0[i] for i in range(3)]; L = math.sqrt(sum(a*a for a in d)); d = [a/L for a in d]
    a = (1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0)
    u = [d[1]*a[2]-d[2]*a[1], d[2]*a[0]-d[0]*a[2], d[0]*a[1]-d[1]*a[0]]
    ul = math.sqrt(sum(x*x for x in u)); u = [x/ul for x in u]
    w = [d[1]*u[2]-d[2]*u[1], d[2]*u[0]-d[0]*u[2], d[0]*u[1]-d[1]*u[0]]
    rings = [(0.0, r), (1.0 - (tip/L if tip else 0), r*0.97)]
    V = []
    for t, rr in rings:
        for i in range(n):
            th = 2*math.pi*i/n
            j = 1 + (rng.uniform(-0.06, 0.06) if rng else 0)
            V.append(tuple(p0[k] + d[k]*L*t + (u[k]*math.cos(th) + w[k]*math.sin(th))*rr*j for k in range(3)))
    F = [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)] + [tuple(reversed(range(n)))]
    if tip:
        V.append(tuple(p1)); c = len(V)-1
        F += [(n+i, n+(i+1) % n, c) for i in range(n)]
    else:
        F.append(tuple(range(n, 2*n)))
    return V, F

def prism_y(poly, y0, y1):
    """XZ 平面多边形沿 Y 挤出"""
    n = len(poly)
    V = [(x, y0, z) for x, z in poly] + [(x, y1, z) for x, z in poly]
    F = [tuple(reversed(range(n))), tuple(range(n, 2*n))] + [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
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


# ============================================================ 毛石砌面
def rubble_face(P, rng, x0, x1, z0, z1, y_at, side, g="毛石", skip=None, course=(0.30, 0.48), blen=(0.45, 1.0), quoin=True):
    """在 y=y_at(z) 的墙面上砌毛石。side=-1 外侧(-Y)，+1 内侧。skip(x,z)→True 则不砌（门洞）。"""
    z = z0
    row = 0
    while z < z1 - 0.05:
        h = min(rng.uniform(*course), z1 - z)
        x = x0 - (rng.uniform(0.1, 0.4) if row % 2 else 0.0)
        while x < x1 - 0.05:
            L = rng.uniform(*blen)
            if quoin and (x <= x0 + 0.01 or x + L >= x1 - 0.3):
                L = rng.uniform(0.9, 1.3)
            a, b = max(x, x0), min(x + L, x1)
            if b - a > 0.12:
                pieces = [(a, b)]
                if b - a > 0.6 and rng.random() < 0.3:      # 偶尔拆成两块小石
                    m = rng.uniform(a + 0.25, b - 0.25); pieces = [(a, m), (m, b)]
                for (pa, pb) in pieces:
                    cx = (pa+pb)/2
                    hh = h * rng.uniform(0.72, 1.0)
                    cz = z + hh/2 + rng.uniform(0, h - hh)
                    if skip and skip(cx, cz):
                        continue
                    pro = rng.uniform(0.04, 0.15)
                    y = y_at(cz) + side*(pro/2 - 0.04)
                    rot = (rng.uniform(-5, 5), rng.uniform(-6, 6), rng.uniform(-4, 4))
                    r = rng.random()
                    mat = "石深" if r < 0.22 else ("石浅" if r > 0.85 else "石")
                    P.add(g, mat, box((cx, y, cz), ((pb-pa)*rng.uniform(0.86, 0.97), 0.16+pro, hh*rng.uniform(0.86, 0.96)), rot))
                    if rng.random() < 0.35:   # 缝隙里的小碎石
                        P.add(g, "石深", box((pb, y_at(z+0.05) + side*0.02, z + rng.uniform(0.05, h-0.05)),
                                             (0.12, 0.14, 0.1), (rng.uniform(0, 40), rng.uniform(0, 40), rng.uniform(0, 40))))
            x += L
        z += h; row += 1

def rubble_side(P, rng, y0, y1, z0, z1, x_at, side, g="毛石端面"):
    """端面（x=x_at 的面）砌石，沿 Y 方向"""
    z = z0; row = 0
    while z < z1 - 0.05:
        h = min(rng.uniform(0.30, 0.48), z1 - z)
        y = y0 - (0.25 if row % 2 else 0)
        while y < y1 - 0.05:
            L = rng.uniform(0.5, 1.0); a, b = max(y, y0), min(y+L, y1)
            if b - a > 0.12:
                pro = rng.uniform(0.03, 0.09)
                P.add(g, "石", box((x_at(z+h/2) + side*(pro/2-0.04), (a+b)/2, z+h/2), (0.16+pro, b-a-0.035, h-0.035),
                                  (rng.uniform(-2, 2), 0, rng.uniform(-2, 2))))
            y += L
        z += h; row += 1


def wall_core(P, L, H, T0, T1, rng, skip=None, ends=False):
    """收分墙体：夯土芯 + 内外毛石面 + 顶面压石 + 步道铺石"""
    P.add("墙芯", "夯土", frustum((0, 0, 0), (L, T0-0.2), (L, T1-0.2), H))
    yo = lambda z: -(T0/2 - (T0-T1)/2 * z/H)
    yi = lambda z: (T0/2 - (T0-T1)/2 * z/H)
    rubble_face(P, rng, -L/2, L/2, 0, H-0.25, yo, -1, skip=skip, quoin=ends)
    rubble_face(P, rng, -L/2, L/2, 0, H-0.25, yi, +1, g="毛石内", skip=skip, quoin=ends)
    if ends:
        for sx in (-1, 1):
            rubble_side(P, rng, -T0/2, T0/2, 0, H-0.25, lambda z: sx*L/2, sx)
    # 顶部压檐石
    x = -L/2
    while x < L/2 - 0.05:
        l = min(rng.uniform(0.8, 1.2), L/2 - x)
        for sy in (-1, 1):
            P.add("压檐石", "石", box((x+l/2, sy*(T1/2-0.18), H-0.12), (l-0.03, 0.5, 0.24), (0, rng.uniform(-1.5, 1.5), 0)))
        x += l
    # 步道铺石
    x = -L/2
    while x < L/2 - 0.05:
        l = min(rng.uniform(0.6, 0.9), L/2 - x)
        y = -(T1/2-0.43)
        while y < T1/2 - 0.43 - 0.05:
            w = min(rng.uniform(0.5, 0.8), T1/2-0.43-y)
            P.add("步道", "石深" if rng.random() < 0.2 else "石", box((x+l/2, y+w/2, H-0.03), (l-0.03, w-0.03, 0.07)))
            y += w
        x += l


def palisade_parapet(P, L, H, T1, rng, gap=None):
    """城墙外沿木栅女墙：立柱 + 竖板（顶部参差削尖）+ 两道横档"""
    y = -(T1/2 - 0.22)
    nposts = max(2, round(L/1.5)) + 1
    for i in range(nposts):
        x = -L/2 + 0.1 + (L-0.2)*i/(nposts-1)
        if gap and gap[0] < x < gap[1]:
            continue
        P.add("女墙_立柱", "木深", log((x, y+0.12, H-0.4), (x, y+0.12, H+PAL_H+0.25), 0.11, n=8, tip=0.0, rng=rng))
    for zr in (H+0.45, H+PAL_H-0.35):
        P.add("女墙_横档", "木深", box((0, y+0.12, zr), (L-0.1, 0.12, 0.14)))
    x = -L/2 + 0.12
    while x < L/2 - 0.1:
        w = rng.uniform(0.18, 0.26)
        if not (gap and gap[0] < x < gap[1]):
            h = PAL_H + rng.uniform(-0.15, 0.12)
            poly = [(x, H-0.05), (x+w, H-0.05), (x+w, H+h-0.12), (x+w/2, H+h+0.06), (x, H+h-0.12)]
            P.add("女墙_竖板", "木", prism_y(poly, y-0.03, y+0.04))
        x += w + rng.uniform(0.02, 0.05)


# ============================================================ 构件
def W01():
    P = Piece("W01", "城墙直段"); rng = random.Random(SEED)
    wall_core(P, SEG_L, WALL_H, WALL_T0, WALL_T1, rng)
    palisade_parapet(P, SEG_L, WALL_H, WALL_T1, rng)
    P.add("内侧护石", "石", box((0, WALL_T1/2-0.18, WALL_H+0.15), (SEG_L-0.02, 0.36, 0.3)))
    return P


def W02():
    P = Piece("W02", "城墙转角石台"); rng = random.Random(SEED+2)
    S0, S1, H = 4.6, 4.0, WALL_H + 1.6
    P.add("台芯", "夯土", frustum((0, 0, 0), (S0-0.2, S0-0.2), (S1-0.2, S1-0.2), H))
    for k, (ax, sd) in enumerate((("y", -1), ("y", 1), ("x", -1), ("x", 1))):
        def slit(c, z, ax=ax):
            return abs(c) < 0.25 and (2.4 < z < 3.4 or 4.2 < z < 5.2)
        if ax == "y":
            rubble_face(P, rng, -S0/2, S0/2, 0, H-0.25, lambda z, sd=sd: sd*(S0/2 - (S0-S1)/2*z/H), sd, g="毛石", skip=slit)
        else:
            rubble_side(P, rng, -S0/2, S0/2, 0, H-0.25, lambda z, sd=sd: sd*(S0/2 - (S0-S1)/2*z/H), sd, g="毛石")
    for sd in (-1, 1):   # 射孔（暗色凹槽）
        for z in (2.9, 4.7):
            yy = sd*(S0/2 - (S0-S1)/2*z/H)
            P.add("射孔", "孔", box((0, yy, z), (0.22, 0.25, 0.9)))
    # 顶部垛口：四边石垛
    top = H
    P.add("台顶", "石", box((0, 0, top-0.1), (S1+0.2, S1+0.2, 0.2)))
    n = 4
    for k in range(4):
        for i in range(n):
            t = -S1/2 + 0.35 + (S1-0.7)*i/(n-1)
            if k < 2:
                c = (t, (-1 if k == 0 else 1)*(S1/2-0.2), top+0.55)
                s = (0.7, 0.42, 0.9)
            else:
                c = ((-1 if k == 2 else 1)*(S1/2-0.2), t, top+0.55)
                s = (0.42, 0.7, 0.9)
            P.add("垛口", "石", box(c, s, (rng.uniform(-2, 2), rng.uniform(-2, 2), 0)))
    P.add("女墙基", "石", frustum((0, 0, top), (S1+0.1, S1+0.1), (S1, S1), 0.1))
    return P


def W03():
    P = Piece("W03", "城门段"); rng = random.Random(SEED+3)
    GW, GH = 3.0, 3.6
    skip = lambda x, z: abs(x) < GW/2 + 0.05 and z < GH + 0.2
    # 门洞两侧墙芯 + 上方墙芯
    for sx in (-1, 1):
        xm = sx*(GW/2 + (SEG_L/2 - GW/2)/2); lw = SEG_L/2 - GW/2
        P.add("墙芯", "夯土", frustum((xm, 0, 0), (lw, WALL_T0-0.2), (lw, WALL_T1-0.2), WALL_H))
    P.add("墙芯", "夯土", box((0, 0, (GH+0.6+WALL_H)/2), (GW+0.2, WALL_T1-0.1, WALL_H-GH-0.6)))
    yo = lambda z: -(WALL_T0/2 - (WALL_T0-WALL_T1)/2*z/WALL_H)
    yi = lambda z: (WALL_T0/2 - (WALL_T0-WALL_T1)/2*z/WALL_H)
    rubble_face(P, rng, -SEG_L/2, SEG_L/2, 0, WALL_H-0.25, yo, -1, skip=skip, quoin=False)
    rubble_face(P, rng, -SEG_L/2, SEG_L/2, 0, WALL_H-0.25, yi, +1, g="毛石内", skip=skip, quoin=False)
    # 门洞侧壁与过梁
    for sx in (-1, 1):
        rubble_side(P, rng, -WALL_T0/2+0.1, WALL_T0/2-0.1, 0, GH, lambda z, sx=sx: sx*GW/2, -sx, g="门洞侧壁")
        P.add("门柱", "木深", box((sx*(GW/2-0.12), -WALL_T0/2+0.45, GH/2), (0.26, 0.26, GH)))
        P.add("门柱", "木深", box((sx*(GW/2-0.12), WALL_T0/2-0.45, GH/2), (0.26, 0.26, GH)))
    for yy in (-WALL_T0/2+0.45, 0, WALL_T0/2-0.45):
        P.add("过梁", "木深", box((0, yy, GH+0.18), (GW+0.8, 0.32, 0.36)))
    for i in range(9):
        P.add("过梁_椽", "木", box((-GW/2+0.2+i*(GW-0.4)/8, 0, GH+0.42), (0.16, WALL_T0-0.6, 0.12)))
    # 双扇门（半开）
    for sx in (-1, 1):
        hinge = (sx*(GW/2-0.25), -WALL_T0/2+0.62)
        ang = sx*-28
        for j in range(6):
            t = 0.12 + j*0.24
            off = _rot((-sx*t, 0, 0), (0, 0, ang))
            P.add("门扇", "木", box((hinge[0]+off[0], hinge[1]+off[1], GH/2-0.05), (0.23, 0.1, GH-0.2), (0, 0, ang)))
        for zz in (0.6, GH/2, GH-0.6):
            off = _rot((-sx*0.75, 0.07, 0), (0, 0, ang))
            P.add("门扇_铁箍", "铁", box((hinge[0]+off[0], hinge[1]+off[1], zz), (1.45, 0.03, 0.12), (0, 0, ang)))
    wall_top = Piece("tmp", "")
    # 顶部：压檐、步道、木栅女墙
    x = -SEG_L/2
    while x < SEG_L/2 - 0.05:
        l = min(rng.uniform(0.8, 1.2), SEG_L/2 - x)
        for sy in (-1, 1):
            P.add("压檐石", "石", box((x+l/2, sy*(WALL_T1/2-0.18), WALL_H-0.12), (l-0.03, 0.5, 0.24)))
        x += l
    P.add("步道", "石", box((0, 0, WALL_H-0.03), (SEG_L-0.05, WALL_T1-0.86, 0.07)))
    palisade_parapet(P, SEG_L, WALL_H, WALL_T1, rng)
    return P


def W04():
    P = Piece("W04", "登城石阶"); rng = random.Random(SEED+4)
    n, rise, tread, W = 16, WALL_H/16, 0.5, 1.8
    L = n*tread
    for i in range(n):
        x = -L/2 + i*tread + tread/2
        h = (i+1)*rise
        P.add("台阶_芯", "夯土", box((x, W/2, h/2), (tread, W-0.1, h)))
        x0 = -L/2 + i*tread
        segs = 2
        for s in range(segs):
            P.add("台阶_踏步石", "石", box((x0+tread/2, 0.05 + W*(s+0.5)/segs, h-0.08),
                                            (tread+0.04, W/segs-0.04, 0.16), (rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), rng.uniform(-2, 2))))
    # 外侧护墙（三角）
    rubble_face(P, rng, -L/2, L/2, 0, WALL_H, lambda z: W+0.15, +1, g="护墙",
                skip=lambda x, z: z > (x + L/2)/L*WALL_H + 0.5, course=(0.3, 0.42), quoin=False)
    P.add("护墙_芯", "夯土", prism_y([(-L/2, 0), (L/2, 0), (L/2, WALL_H+0.4), (-L/2, 0.4)], W, W+0.25))
    P.add("护墙_压顶", "石", box((0, W+0.12, WALL_H/2+0.55), (math.hypot(L, WALL_H)+0.1, 0.4, 0.18),
                                (0, -math.degrees(math.atan2(WALL_H, L)), 0)))
    return P


def P01():
    P = Piece("P01", "木栅栏直段"); rng = random.Random(SEED+5)
    L, H = 4.0, 3.2
    x = -L/2 + 0.1
    while x < L/2 - 0.08:
        r = rng.uniform(0.085, 0.11)
        h = H + rng.uniform(-0.2, 0.15)
        lean = rng.uniform(-0.04, 0.04)
        P.add("栅木", "木", log((x+r, 0, -0.3), (x+r+lean, rng.uniform(-0.02, 0.02), h), r, n=8, tip=0.28, rng=rng))
        x += 2*r + rng.uniform(0.0, 0.025)
    for z in (0.7, 2.2):
        P.add("横档", "木深", log((-L/2, 0.2, z), (L/2, 0.2, z+rng.uniform(-0.05, 0.05)), 0.075, n=7, rng=rng))
        for xx in [(-L/2 + 0.3 + i*0.9) for i in range(5)]:
            P.add("绑绳", "绳", log((xx, 0.08, z-0.07), (xx, 0.08, z+0.07), 0.13, n=8))
    for sx in (-1, 1):
        P.add("斜撑", "木深", log((sx*1.2, 1.5, 0), (sx*1.2, 0.22, 2.1), 0.075, n=7, rng=rng))
        P.add("撑脚石", "石", box((sx*1.2, 1.55, 0.1), (0.4, 0.35, 0.22), (0, 0, rng.uniform(0, 30))))
    x = -L/2
    while x < L/2:
        l = rng.uniform(0.4, 0.7)
        P.add("基石", "石", box((x+l/2, rng.uniform(-0.25, -0.15), 0.12), (l, 0.35, 0.26), (rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(-8, 8))))
        x += l
    return P


def P02():
    P = Piece("P02", "栅栏门"); rng = random.Random(SEED+6)
    GW = 3.0
    for sx in (-1, 1):
        P.add("门柱", "木深", log((sx*(GW/2+0.18), 0, -0.4), (sx*(GW/2+0.18), 0, 4.0), 0.18, n=10, rng=rng))
        P.add("门柱_石础", "石", frustum((sx*(GW/2+0.18), 0, 0), (0.7, 0.7), (0.5, 0.5), 0.3))
    P.add("门楣", "木深", log((-GW/2-0.5, 0, 3.75), (GW/2+0.5, 0, 3.75), 0.16, n=10, rng=rng))
    P.add("门楣", "木深", log((-GW/2-0.3, 0, 3.4), (GW/2+0.3, 0, 3.4), 0.1, n=8, rng=rng))
    for sx in (-1, 1):
        ang = sx*-35
        hx = sx*(GW/2)
        x = 0.05
        while x < GW/2 - 0.08:
            r = rng.uniform(0.075, 0.09)
            off = _rot((-sx*(x+r), -0.05, 0), (0, 0, ang))
            p0 = (hx+off[0], off[1], 0.08); p1 = (hx+off[0], off[1], 2.9 + rng.uniform(-0.12, 0.1))
            P.add("门扇", "木", log(p0, p1, r, n=7, tip=0.22, rng=rng))
            x += 2*r + 0.01
        for z in (0.5, 2.3):
            a = _rot((-sx*0.05, -0.2, 0), (0, 0, ang)); b = _rot((-sx*(GW/2-0.1), -0.2, 0), (0, 0, ang))
            P.add("门扇_横档", "木深", log((hx+a[0], a[1], z), (hx+b[0], b[1], z), 0.06, n=6))
        a = _rot((-sx*0.1, -0.22, 0), (0, 0, ang)); b = _rot((-sx*(GW/2-0.15), -0.22, 0), (0, 0, ang))
        P.add("门扇_斜撑", "木深", log((hx+a[0], a[1], 0.55), (hx+b[0], b[1], 2.25), 0.055, n=6))
    return P


def P03():
    P = Piece("P03", "石柱墩"); rng = random.Random(SEED+7)
    S0, S1, H = 1.6, 1.35, 4.6
    P.add("墩芯", "夯土", frustum((0, 0, 0), (S0-0.2, S0-0.2), (S1-0.2, S1-0.2), H))
    for sd in (-1, 1):
        rubble_face(P, rng, -S0/2, S0/2, 0, H, lambda z, sd=sd: sd*(S0/2-(S0-S1)/2*z/H), sd, course=(0.28, 0.4), blen=(0.4, 0.8))
        rubble_side(P, rng, -S0/2, S0/2, 0, H, lambda z, sd=sd: sd*(S0/2-(S0-S1)/2*z/H), sd)
    P.add("墩顶", "石", box((0, 0, H+0.08), (S1+0.15, S1+0.15, 0.16)))
    for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        P.add("垛", "石", box((dx*(S1/2-0.2), dy*(S1/2-0.2), H+0.5), (0.42, 0.42, 0.7), (0, 0, rng.uniform(-6, 6))))
    P.add("射孔", "孔", box((0, -(S0/2-(S0-S1)/2*0.6), H*0.6), (0.14, 0.12, 0.6)))
    return P


def P04():
    P = Piece("P04", "拒马"); rng = random.Random(SEED+8)
    L = 3.0
    P.add("横木", "木深", log((-L/2, 0, 0.62), (L/2, 0, 0.62), 0.13, n=10, rng=rng))
    for i in range(6):
        x = -L/2 + 0.25 + i*(L-0.5)/5
        for s in (-1, 1):
            a = math.radians(45)*s
            d = (0, math.sin(a), math.cos(a))
            P.add("尖桩", "木", log((x, -d[1]*0.75, 0.62-d[2]*0.75), (x, d[1]*0.85, 0.62+d[2]*0.85), 0.055, n=6, tip=0.2, rng=rng))
        P.add("绑绳", "绳", log((x-0.08, 0, 0.62), (x+0.08, 0, 0.62), 0.15, n=8))
    return P


PIECES = [W01, W02, W03, W04, P01, P02, P03, P04]


# ============================================================ Blender
def run():
    import bpy, bmesh
    from mathutils import Vector

    T0 = time.time(); logl = []
    def L(s):
        logl.append("[%5.1fs] %s" % (time.time()-T0, s)); print(logl[-1])
    os.makedirs(OUT + "renders/", exist_ok=True)
    os.makedirs(OUT + "fbx/", exist_ok=True)

    sc = bpy.data.scenes.get("城墙与栅栏")
    if sc:
        for ob in list(sc.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(sc)
    for c in list(bpy.data.collections):
        if c.name.startswith("套件_") or c.name in ("展示", "组装演示"):
            for ob in list(c.all_objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    sc = bpy.data.scenes.new("城墙与栅栏")
    bpy.context.window.scene = sc
    root = sc.collection

    mats = {}
    for k, rgb in COL.items():
        m = bpy.data.materials.get("墙栅_" + k) or bpy.data.materials.new("墙栅_" + k)
        m.diffuse_color = (*rgb, 1)
        try:
            m.use_nodes = True
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.9
        except Exception:
            pass
        mats[k] = m

    kit = {}
    built = {}
    for fn in PIECES:
        P = fn(); built[P.pid] = P
        col = bpy.data.collections.new("套件_%s_%s" % (P.pid, P.name))
        root.children.link(col)
        for g, (mat, V, F) in P.groups.items():
            me = bpy.data.meshes.new("%s_%s" % (P.pid, g))
            me.from_pydata(V, [], F); me.validate()
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
            me.materials.append(mats[mat])
            ob = bpy.data.objects.new("%s_%s" % (P.pid, g), me)
            ob.color = (*COL[mat], 1)
            col.objects.link(ob)
            if mat in ("石", "石深", "石浅") and len(F) < 20000:
                bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = 0.025; bv.segments = 1; bv.limit_method = "ANGLE"
        kit[P.pid] = col
        lo, hi = P.bbox()
        L("%s %s  %.2f×%.2f×%.2f m  面数 %d" % (P.pid, P.name, hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2], P.nf()))

    # 人物比例参照
    fig_col = bpy.data.collections.new("套件_人物参照"); root.children.link(fig_col)
    fig = None
    if os.path.isfile(FBX_FIG):
        before = set(bpy.data.objects)
        try:
            bpy.ops.import_scene.fbx(filepath=FBX_FIG)
            new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
            for o in [o for o in bpy.data.objects if o not in before]:
                for c in list(o.users_collection):
                    c.objects.unlink(o)
                fig_col.objects.link(o)
            if new:
                fig = new[0]
                bpy.context.view_layer.update()
                zs = [(fig.matrix_world @ v.co).z for v in fig.data.vertices]
                k = 1.78/(max(zs)-min(zs)); fig.scale = [s*k for s in fig.scale]
                bpy.context.view_layer.update()
                ws = [fig.matrix_world @ v.co for v in fig.data.vertices]
                fig.location.x -= (max(w.x for w in ws)+min(w.x for w in ws))/2
                fig.location.y -= (max(w.y for w in ws)+min(w.y for w in ws))/2
                fig.location.z -= min(w.z for w in ws)
                L("人物参照已导入并缩放到 1.78 m")
        except Exception as e:
            L("人物导入失败 %r" % (e,))

    # 导出 FBX（每个构件单独一个，原点在构件底面中心）
    if EXPORT_FBX:
        for pid, col in kit.items():
            lc = sc.view_layers[0].layer_collection.children[col.name]
            sc.view_layers[0].active_layer_collection = lc
            try:
                bpy.ops.export_scene.fbx(filepath=OUT + "fbx/%s.fbx" % col.name.replace("套件_", ""),
                                         use_active_collection=True, apply_unit_scale=True, use_mesh_modifiers=True,
                                         axis_forward="-Z", axis_up="Y")
            except Exception as e:
                L("FBX %s 失败 %r" % (pid, e))
        L("FBX 导出完成")

    # 套件集合在视图层排除，展示与组装都用集合实例
    for col in list(kit.values()) + [fig_col]:
        sc.view_layers[0].layer_collection.children[col.name].exclude = True

    def inst(col, loc, rz=0, parent_col=None, name=None):
        e = bpy.data.objects.new(name or ("实例_" + col.name), None)
        e.instance_type = "COLLECTION"; e.instance_collection = col
        e.location = loc; e.rotation_euler = (0, 0, math.radians(rz))
        (parent_col or root).objects.link(e)
        return e

    # ---------------- 展示：一排构件，间隔 12 m，每个旁边一个人物
    show = bpy.data.collections.new("展示"); root.children.link(show)
    order = ["W01", "W02", "W03", "W04", "P01", "P02", "P03", "P04"]
    cams = []
    subs = []
    for i, pid in enumerate(order):
        x = i*13.0
        sub = bpy.data.collections.new("展示_" + pid); show.children.link(sub); subs.append(sub)
        inst(kit[pid], (x, 0, 0), parent_col=sub)
        lo, hi = built[pid].bbox()
        if fig:
            inst(fig_col, (x + hi[0] + 1.0, lo[1] - 0.6, 0), parent_col=sub, name="人物_" + pid)
        cx, cz = x + (lo[0]+hi[0])/2 + 0.6, (lo[2]+hi[2])/2
        span = max(hi[0]-lo[0]+2.6, hi[2]-lo[2], hi[1]-lo[1]) * 1.2
        for vn, loc, rot in (("正视", (cx, -60, cz), (90, 0, 0)), ("侧视", (x+hi[0]+60, (lo[1]+hi[1])/2, cz), (90, 0, 90)),
                             ("顶视", (cx, (lo[1]+hi[1])/2, 80), (0, 0, 0))):
            cd = bpy.data.cameras.new("CAM_%s_%s" % (pid, vn)); cd.type = "ORTHO"; cd.ortho_scale = span; cd.clip_end = 300
            co = bpy.data.objects.new(cd.name, cd); show.objects.link(co); co.location = loc
            co.rotation_euler = tuple(math.radians(a) for a in rot)
            cams.append(("%s_%s_%s" % (pid, built[pid].name, vn), co, (1400, 1100), [sub]))
        cd = bpy.data.cameras.new("CAM_%s_透视" % pid); cd.lens = 40; cd.clip_end = 300
        co = bpy.data.objects.new(cd.name, cd); show.objects.link(co)
        tgt = Vector(((lo[0]+hi[0])/2 + x, (lo[1]+hi[1])/2, (hi[2])*0.4))
        R = max(hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2])
        co.location = tgt + Vector((-0.55, -1.0, 0.45)).normalized()*R*2.1
        co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()
        cams.append(("%s_%s_透视" % (pid, built[pid].name), co, (1500, 1100), [sub]))

    # ---------------- 组装演示：L 形城墙 + 角台 + 城门 + 登城阶 + 石墩 + 木栅 + 栅门 + 拒马
    demo = bpy.data.collections.new("组装演示"); root.children.link(demo)
    oy = 60.0   # 与展示行错开
    D = lambda x, y: (x, y + oy, 0)
    inst(kit["W02"], D(0, 0), parent_col=demo)
    h = 2.3   # 角台半宽，墙段从角台边缘起
    xs = [h + 3, h + 9, h + 15]
    inst(kit["W01"], D(xs[0], 0), parent_col=demo)
    inst(kit["W03"], D(xs[1], 0), parent_col=demo)
    inst(kit["W01"], D(xs[2], 0), parent_col=demo)
    inst(kit["P03"], D(h + 18 + 0.8, 0), parent_col=demo)
    px = h + 18 + 1.6
    inst(kit["P01"], D(px + 2, -0.6), parent_col=demo)
    inst(kit["P02"], D(px + 6.1, -0.6), parent_col=demo)
    inst(kit["P01"], D(px + 10.2, -0.6), parent_col=demo)
    inst(kit["P03"], D(px + 13.0, -0.6), parent_col=demo)
    for k in range(3):   # 沿 +Y 的城墙（外侧朝 -X）
        inst(kit["W01"], D(0, h + 3 + 6*k), rz=-90, parent_col=demo)
    inst(kit["W04"], D(xs[2] - 0.2, WALL_T0/2), parent_col=demo)
    for k, (x, y) in enumerate(((xs[1]-1.6, -7.5), (xs[1]+2.2, -8.2), (px + 6.1 - 3.6, -5.0), (px + 6.1 + 3.4, -5.3))):
        inst(kit["P04"], D(x, y), rz=[0, 12, -8, 6][k], parent_col=demo)
    if fig:
        for x, y, rz in ((xs[1], -2.6, 0), (xs[1] + 1.2, -3.1, 20), (xs[0], 0.2, 0), (px + 6.1, -2.2, 0)):
            e = inst(fig_col, D(x, y), rz=rz, parent_col=demo, name="人物_演示")
            if y > 0:
                e.location.z = WALL_H
    gd = bpy.data.meshes.new("地面"); gd.from_pydata([(-30, -30+oy-20, 0), (60, -30+oy-20, 0), (60, 40+oy, 0), (-30, 40+oy, 0)], [], [(0, 1, 2, 3)])
    gm = bpy.data.materials.get("墙栅_地面") or bpy.data.materials.new("墙栅_地面"); gm.diffuse_color = (0.55, 0.52, 0.46, 1)
    gd.materials.append(gm); g = bpy.data.objects.new("地面", gd); g.color = (0.55, 0.52, 0.46, 1); demo.objects.link(g)
    for nm, loc, tgt, lens in (("组装_鸟瞰", (-14, oy - 30, 22), (16, oy + 2, 1.5), 32),
                               ("组装_城门近景", (xs[1] - 9, oy - 17, 4.0), (xs[1], oy, 2.6), 35)):
        cd = bpy.data.cameras.new("CAM_" + nm); cd.lens = lens; cd.clip_end = 400
        co = bpy.data.objects.new(cd.name, cd); demo.objects.link(co); co.location = loc
        co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        cams.append((nm, co, (1800, 1100), [demo]))

    # ---------------- 渲染
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
    sc.camera = cams[-2][1]
    bpy.ops.wm.save_as_mainfile(filepath=OUT + "城墙与栅栏_套件.blend")
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
