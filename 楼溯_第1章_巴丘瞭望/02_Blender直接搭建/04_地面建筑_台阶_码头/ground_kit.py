# -*- coding: utf-8 -*-
"""
《楼·溯》第1章·巴丘瞭望 —— 地面建筑 / 台阶 / 码头 模块化套件（Blender 直接搭建）

地面（原点在底面中心，z=0 为所在地面）：
  G01 石砌台地      8×8 m、高 1.2 m，层叠条石护面 + 压阑石 + 石板铺面，可叠两层
  G02 石阶          宽 3 m，7 级升 1.2 m（对齐台地高度），两侧垂带；原点在顶沿中心，向 -Y 下行
  G03 挡土矮墙      6 m 长、1.0 m 高，双面条石 + 压顶
  G04 石板路        6×2.4 m 铺地 + 边石
  G05 马道坡道      宽 3 m，6 m 长升 1.2 m，横向防滑条石 + 侧墙；原点在顶沿中心
码头（原点 z=0 为水面；岸面/桥面高 1.2 m）：
  D01 石砌岸壁      6 m 长，水下 1.6 m 至岸面，护舷木、系缆石墩、下水踏步
  D02 木栈桥段      6 m 长 × 3 m 宽，成对木桩、剪刀撑、纵横梁、桥板、两侧栏杆；原点在靠岸端中心，向 -Y 延伸
  D03 栈桥端头平台  7×7 m，下水木阶、系船柱、吊杆
  D04 系船桩群      三根斜木桩捆扎
"""
import math, os, random, time

OUT = "C:/Users/pjwly/3D Objects/楼溯_资产库/第1章_巴丘瞭望/07_Blender搭建/地面建筑与码头/"
BLD = "C:/Users/pjwly/3D Objects/楼溯_资产库/第1章_巴丘瞭望/07_Blender搭建/"
FBX_FIG = "D:/Caroline Elvira/ancient chinese robe 3d model/ancient_chinese_robe_3d_model.fbx"
SEED = 31
RENDER = True
EXPORT_FBX = True
H = 1.2   # 台地 / 岸面 / 桥面统一高度

COL = {"石": (0.50, 0.47, 0.42), "石深": (0.38, 0.36, 0.33), "石浅": (0.60, 0.57, 0.51), "夯土": (0.50, 0.44, 0.36),
       "木": (0.42, 0.29, 0.17), "木深": (0.28, 0.19, 0.12), "木湿": (0.20, 0.16, 0.12), "绳": (0.62, 0.54, 0.40),
       "铁": (0.20, 0.20, 0.22), "水": (0.30, 0.42, 0.47), "地": (0.52, 0.49, 0.40)}


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

def log(p0, p1, r, n=8, tip=0.0, rng=None, r1=None):
    d = [p1[i]-p0[i] for i in range(3)]; L = math.sqrt(sum(a*a for a in d)) or 1e-6; d = [a/L for a in d]
    a = (1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0)
    u = [d[1]*a[2]-d[2]*a[1], d[2]*a[0]-d[0]*a[2], d[0]*a[1]-d[1]*a[0]]
    ul = math.sqrt(sum(x*x for x in u)); u = [x/ul for x in u]
    w = [d[1]*u[2]-d[2]*u[1], d[2]*u[0]-d[0]*u[2], d[0]*u[1]-d[1]*u[0]]
    r1 = r*0.96 if r1 is None else r1
    V = []
    for t, rr in ((0.0, r), (1.0 - (tip/L if tip else 0), r1)):
        for i in range(n):
            th = 2*math.pi*i/n
            j = 1 + (rng.uniform(-0.05, 0.05) if rng else 0)
            V.append(tuple(p0[k] + d[k]*L*t + (u[k]*math.cos(th) + w[k]*math.sin(th))*rr*j for k in range(3)))
    F = [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)] + [tuple(reversed(range(n)))]
    if tip:
        V.append(tuple(p1)); c = len(V)-1; F += [(n+i, n+(i+1) % n, c) for i in range(n)]
    else:
        F.append(tuple(range(n, 2*n)))
    return V, F

def lathe(rings, n=14, cx=0.0, cy=0.0):
    V = [(cx+r*math.cos(2*math.pi*i/n), cy+r*math.sin(2*math.pi*i/n), z) for z, r in rings for i in range(n)]
    m = len(rings)
    F = [(k*n+i, k*n+(i+1) % n, (k+1)*n+(i+1) % n, (k+1)*n+i) for k in range(m-1) for i in range(n)]
    return V, F + [tuple(reversed(range(n))), tuple(range((m-1)*n, m*n))]

def prism_x(poly, x0, x1):
    """YZ 平面多边形沿 X 挤出"""
    n = len(poly)
    V = [(x0, y, z) for y, z in poly] + [(x1, y, z) for y, z in poly]
    return V, [tuple(reversed(range(n))), tuple(range(n, 2*n))] + [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]


class Piece:
    def __init__(self, pid, name, fig=None):
        self.pid, self.name, self.groups, self.fig = pid, name, {}, fig
    def add(self, g, mat, geo):
        e = self.groups.setdefault(g, [mat, [], []]); o = len(e[1])
        e[1].extend(geo[0]); e[2].extend(tuple(i+o for i in f) for f in geo[1])
    def bbox(self):
        vs = [p for g in self.groups.values() for p in g[1]]
        return [min(p[k] for p in vs) for k in range(3)], [max(p[k] for p in vs) for k in range(3)]
    def nf(self):
        return sum(len(g[2]) for g in self.groups.values())


def _mat(rng):
    r = rng.random()
    return "石深" if r < 0.2 else ("石浅" if r > 0.86 else "石")


def ashlar(P, rng, o, d, n, L, z0, z1, batter=0.0, course=(0.2, 0.34), blen=(0.6, 1.5), g="条石", skip=None):
    """层叠条石护面：o 起点(x,y)，d 沿墙单位向量，n 外法线，向上每米内收 batter"""
    yaw = math.degrees(math.atan2(d[1], d[0]))
    z = z0; row = 0
    while z < z1 - 0.04:
        h = min(rng.uniform(*course), z1 - z)
        a = -(rng.uniform(0.2, 0.6) if row % 2 else 0.0)
        while a < L - 0.04:
            l = rng.uniform(*blen)
            s0, s1 = max(a, 0), min(a+l, L)
            if s1 - s0 > 0.15:
                hh = h*rng.uniform(0.8, 1.0); zc = z + hh/2 + rng.uniform(0, h-hh)
                ac = (s0+s1)/2
                if not (skip and skip(ac, zc)):
                    pro = rng.uniform(0.03, 0.10)
                    off = -batter*(zc - z0) + pro/2 - 0.04
                    c = (o[0] + d[0]*ac + n[0]*off, o[1] + d[1]*ac + n[1]*off, zc)
                    P.add(g, _mat(rng), box(c, ((s1-s0)*rng.uniform(0.9, 0.98), 0.2+pro, hh*rng.uniform(0.86, 0.96)),
                                             (rng.uniform(-2, 2), rng.uniform(-3, 3), yaw + rng.uniform(-1.5, 1.5))))
            a += l
        z += h; row += 1


def coping(P, rng, o, d, n, L, z, depth=0.45, g="压阑石"):
    yaw = math.degrees(math.atan2(d[1], d[0]))
    a = 0.0
    while a < L - 0.04:
        l = min(rng.uniform(0.8, 1.3), L - a)
        c = (o[0] + d[0]*(a+l/2) - n[0]*(depth/2-0.05), o[1] + d[1]*(a+l/2) - n[1]*(depth/2-0.05), z - 0.1)
        P.add(g, _mat(rng), box(c, (l-0.03, depth, 0.2), (rng.uniform(-1, 1), rng.uniform(-1, 1), yaw)))
        a += l


def flagstones(P, rng, x0, x1, y0, y1, z, size=(0.45, 0.9), missing=0.0, g="石板"):
    y = y0
    while y < y1 - 0.04:
        w = min(rng.uniform(*size), y1 - y)
        x = x0 - rng.uniform(0, 0.4)
        while x < x1 - 0.04:
            l = rng.uniform(size[0], size[1]*1.3)
            a, b = max(x, x0), min(x+l, x1)
            if b - a > 0.12 and rng.random() >= missing:
                P.add(g, _mat(rng), box(((a+b)/2, y+w/2, z - 0.04 + rng.uniform(-0.01, 0.015)), (b-a-0.03, w-0.03, 0.08),
                                         (rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2), rng.uniform(-1.5, 1.5))))
            x += l
        y += w


_FACES = lambda W, D: [((-W/2, -D/2), (1, 0), (0, -1), W), ((W/2, -D/2), (0, 1), (1, 0), D),
                       ((W/2, D/2), (-1, 0), (0, 1), W), ((-W/2, D/2), (0, -1), (-1, 0), D)]


# ============================================================ 地面构件
def G01():
    P = Piece("G01", "石砌台地", fig=(2.5, -1.5, H)); rng = random.Random(SEED)
    W = D = 8.0
    P.add("台芯", "夯土", box((0, 0, H/2-0.02), (W-0.3, D-0.3, H-0.06)))
    for o, d, n, L in _FACES(W, D):
        ashlar(P, rng, o, d, n, L, 0, H-0.2, batter=0.05)
        coping(P, rng, o, d, n, L, H)
    flagstones(P, rng, -W/2+0.42, W/2-0.42, -D/2+0.42, D/2-0.42, H, size=(0.5, 1.0), missing=0.03)
    return P


def G02():
    P = Piece("G02", "石阶"); rng = random.Random(SEED+1)
    Wd, rise, tread, n = 3.0, 0.15, 0.36, 7
    run = n*tread
    for i in range(1, n+1):
        y1 = -(n+1-i)*tread + tread; y0 = y1 - tread
        top = i*rise
        P.add("台阶芯", "夯土", box((0, (y0+y1)/2, (top-0.08)/2), (Wd-0.1, tread, top-0.08)))
        segs = rng.choice((2, 3))
        for s in range(segs):
            x0 = -Wd/2 + Wd*s/segs
            P.add("踏步石", _mat(rng), box((x0 + Wd/segs/2, (y0+y1)/2 - 0.02, top-0.08), (Wd/segs-0.03, tread+0.05, 0.16),
                                         (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1.5, 1.5))))
    for sx in (-1, 1):
        x = sx*(Wd/2 + 0.25)
        P.add("垂带", "石", prism_x([(0.0, 0.0), (0.0, H+0.15), (-run, 0.28), (-run, 0.0)], x-0.25, x+0.25))
        L = math.hypot(run, H-0.13)
        P.add("垂带_压顶", "石浅", box((x, -run/2, (H+0.15+0.28)/2+0.07), (0.56, L+0.05, 0.12), (math.degrees(math.atan2(H-0.13, run)), 0, 0)))
    return P


def G03():
    P = Piece("G03", "挡土矮墙"); rng = random.Random(SEED+2)
    L, T, Hh = 6.0, 0.6, 1.0
    P.add("墙芯", "夯土", box((0, 0, (Hh-0.15)/2), (L-0.1, T-0.2, Hh-0.15)))
    ashlar(P, rng, (-L/2, -T/2), (1, 0), (0, -1), L, 0, Hh-0.16, course=(0.2, 0.3))
    ashlar(P, rng, (L/2, T/2), (-1, 0), (0, 1), L, 0, Hh-0.16, course=(0.2, 0.3))
    for sx in (-1, 1):
        ashlar(P, rng, (sx*L/2, -sx*T/2), (0, sx), (sx, 0), T, 0, Hh-0.16, blen=(0.6, 0.7))
    a = -L/2
    while a < L/2 - 0.04:
        l = min(rng.uniform(0.7, 1.2), L/2 - a)
        P.add("压顶石", _mat(rng), box((a+l/2, 0, Hh-0.08), (l-0.03, T+0.14, 0.16), (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))))
        a += l
    return P


def G04():
    P = Piece("G04", "石板路"); rng = random.Random(SEED+3)
    L, Wd = 6.0, 2.4
    flagstones(P, rng, -L/2, L/2, -Wd/2+0.2, Wd/2-0.2, 0.07, size=(0.4, 0.8))
    for sy in (-1, 1):
        a = -L/2
        while a < L/2 - 0.04:
            l = min(rng.uniform(0.7, 1.2), L/2 - a)
            P.add("边石", _mat(rng), box((a+l/2, sy*(Wd/2-0.1), 0.04), (l-0.03, 0.22, 0.22), (rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(-1, 1))))
            a += l
    return P


def G05():
    P = Piece("G05", "马道坡道"); rng = random.Random(SEED+4)
    Wd, run = 3.0, 6.0
    ang = math.degrees(math.atan2(H, run))
    P.add("坡芯", "夯土", prism_x([(0.0, 0.0), (0.0, H-0.1), (-run, 0.0)], -Wd/2, Wd/2))
    k = 0
    y = -run
    while y < -0.05:
        w = rng.uniform(0.35, 0.5)
        yc = y + w/2; zc = H*(1 + yc/run)
        P.add("坡面条石", _mat(rng), box((rng.uniform(-0.05, 0.05), yc, zc - 0.03), (Wd - 0.05, w - 0.04, 0.12), (ang + rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))))
        y += w; k += 1
    for sx in (-1, 1):
        x = sx*(Wd/2 + 0.25)
        P.add("侧墙", "石", prism_x([(0.0, 0.0), (0.0, H+0.45), (-run, 0.45), (-run, 0.0)], x-0.25, x+0.25))
        P.add("侧墙_压顶", "石浅", box((x, -run/2, (H+0.9)/2+0.06), (0.56, math.hypot(run, H)+0.05, 0.12), (ang, 0, 0)))
    return P


# ============================================================ 码头构件
def D01():
    P = Piece("D01", "石砌岸壁", fig=(-1.5, 1.0, H)); rng = random.Random(SEED+5)
    L, T, zb = 6.0, 2.0, -1.6
    P.add("岸芯", "夯土", box((0, T/2+0.1, (zb+H)/2), (L, T, H-zb-0.05)))
    ashlar(P, rng, (-L/2, 0), (1, 0), (0, -1), L, zb, H-0.2, batter=0.06, course=(0.24, 0.38), g="岸壁条石")
    coping(P, rng, (-L/2, 0), (1, 0), (0, -1), L, H, depth=0.7)
    flagstones(P, rng, -L/2, L/2, 0.68, T, H, size=(0.5, 1.0))
    for x in (-1.6, 1.6):
        P.add("系缆石", "石深", lathe([(H, 0.22), (H+0.35, 0.18), (H+0.42, 0.24), (H+0.55, 0.2)], n=12, cx=x, cy=0.45))
    for x in (-2.6, -0.6):
        P.add("护舷木", "木湿", log((x, -0.14, -0.6), (x, -0.14, H-0.05), 0.12, n=8, rng=rng))
    for j in range(6):
        x0 = 0.5 + j*0.32
        top = H - 0.18 - j*0.25
        P.add("下水踏步", _mat(rng), box((x0+0.16, -0.5, (zb+top)/2), (0.32, 0.95, top-zb), (0, 0, rng.uniform(-1, 1))))
    return P


def _deck(P, rng, x0, x1, y0, y1, z, plank=0.24):
    y = y0
    while y < y1 - 0.05:
        w = min(plank*rng.uniform(0.85, 1.1), y1 - y)
        P.add("桥板", "木" if rng.random() > 0.2 else "木深",
              box(((x0+x1)/2 + rng.uniform(-0.04, 0.04), y + w/2, z - 0.04 + rng.uniform(-0.012, 0.012)), (x1-x0 + rng.uniform(-0.1, 0.1), w-0.025, 0.07),
                  (rng.uniform(-0.6, 0.6), 0, rng.uniform(-0.6, 0.6))))
        y += w


def _railing(P, rng, x, y0, y1, z):
    n = max(2, round(abs(y1-y0)/1.5)) + 1
    for i in range(n):
        y = y0 + (y1-y0)*i/(n-1)
        P.add("栏杆柱", "木深", log((x, y, z-0.2), (x, y, z+1.05), 0.07, n=8, rng=rng))
        P.add("栏杆柱", "木深", box((x, y, z+1.1), (0.17, 0.17, 0.1)))
    for zz, r in ((z+0.95, 0.055), (z+0.5, 0.04)):
        P.add("扶手", "木", log((x, y0-0.05, zz), (x, y1+0.05, zz + rng.uniform(-0.02, 0.02)), r, n=7, rng=rng))


def _piles(P, rng, pts, zb, zt, r=0.17):
    for (x, y) in pts:
        lean = (rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04))
        P.add("木桩", "木湿", log((x+lean[0], y+lean[1], zb), (x, y, zt), r, n=10, rng=rng))
        P.add("木桩_箍", "铁", log((x, y, zt-0.32), (x, y, zt-0.22), r+0.015, n=10))


def D02():
    P = Piece("D02", "木栈桥段", fig=(0.3, -3.0, H)); rng = random.Random(SEED+6)
    Lg, Wd, zb = 6.0, 3.0, -2.2
    xs = (-1.3, 1.3)
    ys = (-1.0, -3.0, -5.0)
    _piles(P, rng, [(x, y) for x in xs for y in ys], zb, H-0.25)
    for y in ys:
        P.add("横梁", "木深", box((0, y, H-0.32), (Wd+0.4, 0.24, 0.24)))
        P.add("剪刀撑", "木湿", log((xs[0], y, -0.3), (xs[1], y, H-0.45), 0.06, n=6))
        P.add("剪刀撑", "木湿", log((xs[1], y, -0.3), (xs[0], y, H-0.45), 0.06, n=6))
    for x in (-1.3, -0.45, 0.45, 1.3):
        P.add("纵梁", "木深", box((x, -Lg/2, H-0.15), (0.18, Lg, 0.2)))
    for sx in (-1, 1):
        P.add("纵向斜撑", "木湿", log((sx*1.3, -1.0, -0.2), (sx*1.3, -3.0, H-0.45), 0.055, n=6))
        P.add("纵向斜撑", "木湿", log((sx*1.3, -5.0, -0.2), (sx*1.3, -3.0, H-0.45), 0.055, n=6))
    _deck(P, rng, -Wd/2-0.1, Wd/2+0.1, -Lg, 0, H, plank=0.24)   # 木板沿 X 横铺，按 Y 排列
    for sx in (-1, 1):
        _railing(P, rng, sx*(Wd/2+0.02), -Lg+0.15, -0.15, H)
    return P


def D03():
    P = Piece("D03", "栈桥端头平台", fig=(-1.2, -3.0, H)); rng = random.Random(SEED+7)
    Wd, Lg, zb = 7.0, 7.0, -2.4
    xs = (-3.1, 0.0, 3.1); ys = (-0.8, -3.5, -6.2)
    _piles(P, rng, [(x, y) for x in xs for y in ys], zb, H-0.25, r=0.19)
    for y in ys:
        P.add("横梁", "木深", box((0, y, H-0.32), (Wd+0.3, 0.26, 0.26)))
        for a, b in ((xs[0], xs[1]), (xs[1], xs[2])):
            P.add("剪刀撑", "木湿", log((a, y, -0.4), (b, y, H-0.45), 0.06, n=6))
    for x in [-3.1 + i*6.2/7 for i in range(8)]:
        P.add("纵梁", "木深", box((x, -Lg/2, H-0.15), (0.18, Lg, 0.2)))
    _deck(P, rng, -Wd/2-0.05, Wd/2+0.05, -Lg, 0, H, plank=0.26)
    for sx in (-1, 1):
        _railing(P, rng, sx*(Wd/2), -Lg+0.15, -0.15, H)
    # 前沿下水木阶
    for k in range(4):
        y = -Lg - 0.3 - k*0.35; z = H - 0.28 - k*0.28
        P.add("下水木阶", "木", box((0, y, z), (2.4, 0.34, 0.07)))
        for sx in (-1, 1):
            P.add("下水木阶_梁", "木深", log((sx*1.15, -Lg, H-0.12), (sx*1.15, -Lg-1.6, -0.1), 0.07, n=6))
    for sx in (-1, 1):
        P.add("木阶桩", "木湿", log((sx*1.2, -Lg-1.55, zb), (sx*1.2, -Lg-1.55, 0.3), 0.12, n=8))
    # 系船柱
    for (x, y) in ((-3.2, -6.7), (3.2, -6.7), (-3.2, -0.6)):
        P.add("系船柱", "木深", log((x, y, H-0.1), (x, y, H+0.75), 0.16, n=10, r1=0.14))
        P.add("系船柱_帽", "木深", box((x, y, H+0.8), (0.42, 0.42, 0.1)))
        P.add("缆绳", "绳", log((x-0.17, y, H+0.4), (x+0.17, y, H+0.4), 0.18, n=10))
    # 吊杆
    mx, my = 2.4, -1.6
    P.add("吊杆_桅", "木深", log((mx, my, H), (mx, my, H+5.2), 0.14, n=10, r1=0.1))
    P.add("吊杆_底座", "木深", box((mx, my, H+0.15), (0.8, 0.8, 0.3)))
    for dx, dy in ((0.9, 0.9), (-0.9, 0.9), (0.9, -0.9)):
        P.add("吊杆_斜撑", "木湿", log((mx+dx, my+dy, H), (mx, my, H+1.8), 0.06, n=6))
    tip = (mx-1.6, my-4.3, H+4.0)
    P.add("吊杆_臂", "木", log((mx, my, H+1.2), tip, 0.09, n=8, r1=0.06))
    P.add("吊绳", "绳", log((mx, my, H+5.1), tip, 0.02, n=4))
    P.add("吊绳", "绳", log(tip, (tip[0], tip[1], H+1.6), 0.02, n=4))
    P.add("吊钩", "铁", box((tip[0], tip[1], H+1.55), (0.12, 0.04, 0.2)))
    P.add("吊物木箱", "木", box((tip[0], tip[1], H+1.15), (0.8, 0.6, 0.6), (0, 0, 12)))
    return P


def D04():
    P = Piece("D04", "系船桩群"); rng = random.Random(SEED+8)
    zb, zt = -2.0, 2.1
    for k in range(3):
        a = 2*math.pi*k/3
        base = (0.55*math.cos(a), 0.55*math.sin(a), zb)
        P.add("桩", "木湿", log(base, (0.12*math.cos(a), 0.12*math.sin(a), zt - 0.1*k), 0.16, n=10, rng=rng))
    for z in (1.3, 1.7):
        P.add("捆绳", "绳", lathe([(z, 0.42 - (z-1.3)*0.3), (z+0.12, 0.41 - (z-1.3)*0.3)], n=14))
    return P


PIECES = [G01, G02, G03, G04, G05, D01, D02, D03, D04]


# ============================================================ Blender
def run():
    import bpy, bmesh
    from mathutils import Vector

    T0 = time.time(); logl = []
    def L(s):
        logl.append("[%5.1fs] %s" % (time.time()-T0, s)); print(logl[-1])
    for d in ("renders/", "fbx/"):
        os.makedirs(OUT + d, exist_ok=True)

    sc = bpy.data.scenes.get("地面建筑与码头")
    if sc:
        for ob in list(sc.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(sc)
    for c in list(bpy.data.collections):
        if c.name.startswith("地码套件_") or c.name.startswith("地码展示") or c.name == "地码组装演示":
            for ob in list(c.all_objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    sc = bpy.data.scenes.new("地面建筑与码头")
    bpy.context.window.scene = sc
    root = sc.collection

    mats = {}
    for k, rgb in COL.items():
        m = bpy.data.materials.get("地码_" + k) or bpy.data.materials.new("地码_" + k)
        m.diffuse_color = (*rgb, 1)
        try:
            m.use_nodes = True
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.15 if k == "水" else 0.9
        except Exception:
            pass
        mats[k] = m

    kit, built = {}, {}
    for fn in PIECES:
        P = fn(); built[P.pid] = P
        col = bpy.data.collections.new("地码套件_%s_%s" % (P.pid, P.name)); root.children.link(col)
        for g, (mat, V, F) in P.groups.items():
            me = bpy.data.meshes.new("%s_%s" % (P.pid, g))
            me.from_pydata(V, [], F); me.validate()
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
            me.materials.append(mats[mat])
            ob = bpy.data.objects.new("%s_%s" % (P.pid, g), me); col.objects.link(ob)
            if mat in ("石", "石深", "石浅") and len(F) < 30000:
                bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = 0.02; bv.segments = 1; bv.limit_method = "ANGLE"
        kit[P.pid] = col
        lo, hi = P.bbox()
        L("%s %s  %.2f×%.2f×%.2f m  面数 %d" % (P.pid, P.name, hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2], P.nf()))

    # 人物
    fig_col = None
    for nm in ("套件_人物参照", "营地套件_人物参照", "地码套件_人物参照"):
        c = bpy.data.collections.get(nm)
        if c and [o for o in c.objects if o.type == "MESH"]:
            fig_col = c; break
    if fig_col is None:
        fig_col = bpy.data.collections.new("地码套件_人物参照"); root.children.link(fig_col)
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

    # 其他套件（演示用）
    ext = {}
    for blend, names in ((BLD + "营地建筑/营地建筑_套件.blend", ("营地套件_C03_圆帐", "营地套件_C04_军需敞棚", "营地套件_C05_旗杆", "营地套件_C06_篝火灶")),
                         (BLD + "城墙与栅栏/城墙与栅栏_套件.blend", ("套件_P01_木栅栏直段", "套件_P03_石柱墩"))):
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
                bpy.ops.export_scene.fbx(filepath=OUT + "fbx/%s.fbx" % col.name.replace("地码套件_", ""),
                                         use_active_collection=True, use_mesh_modifiers=True, axis_forward="-Z", axis_up="Y")
            except Exception as e:
                L("FBX %s 失败 %r" % (pid, e))
        L("FBX 导出完成")
    for col in kit.values():
        sc.view_layers[0].layer_collection.children[col.name].exclude = True
    lcf = sc.view_layers[0].layer_collection.children.get(fig_col.name)
    if lcf:
        lcf.exclude = True

    def inst(col, loc, rz=0, parent=None, name=None, scale=(1, 1, 1)):
        e = bpy.data.objects.new(name or ("实例_" + col.name), None)
        e.instance_type = "COLLECTION"; e.instance_collection = col
        e.location = loc; e.rotation_euler = (0, 0, math.radians(rz)); e.scale = scale
        (parent or root).objects.link(e)
        return e

    # ---------------- 展示
    show = bpy.data.collections.new("地码展示"); root.children.link(show)
    cams, subs = [], []
    x = 0.0
    for fn in PIECES:
        pid = fn.__name__
        P = built[pid]; lo, hi = P.bbox()
        x += -lo[0] + 2.5
        sub = bpy.data.collections.new("地码展示_" + pid); show.children.link(sub); subs.append(sub)
        inst(kit[pid], (x, 0, 0), parent=sub)
        if pid != "D04":
            fp = P.fig if P.fig else (hi[0] + 0.9, lo[1] + 0.5, 0)
            inst(fig_col, (x + fp[0], fp[1], fp[2]), parent=sub, name="人物_" + pid)
        cx, cz = x + (lo[0]+hi[0])/2 + (0.5 if not P.fig else 0), (lo[2]+hi[2])/2
        span = max(hi[0]-lo[0]+2.2, hi[2]-lo[2], hi[1]-lo[1]) * 1.15
        for vn, loc, rot in (("正视", (cx, -90, cz), (90, 0, 0)), ("侧视", (x+hi[0]+90, (lo[1]+hi[1])/2, cz), (90, 0, 90)),
                             ("顶视", (cx, (lo[1]+hi[1])/2, 90), (0, 0, 0))):
            cd = bpy.data.cameras.new("CAM_%s_%s" % (pid, vn)); cd.type = "ORTHO"; cd.ortho_scale = span; cd.clip_end = 400
            co = bpy.data.objects.new(cd.name, cd); sub.objects.link(co); co.location = loc
            co.rotation_euler = tuple(math.radians(a) for a in rot)
            cams.append(("%s_%s_%s" % (pid, P.name, vn), co, (1400, 1100), [sub]))
        cd = bpy.data.cameras.new("CAM_%s_透视" % pid); cd.lens = 40; cd.clip_end = 400
        co = bpy.data.objects.new(cd.name, cd); sub.objects.link(co)
        tgt = Vector((x + (lo[0]+hi[0])/2, (lo[1]+hi[1])/2, (lo[2]+hi[2])/2))
        R = max(hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2])
        co.location = tgt + Vector((-0.6, -1.0, 0.55)).normalized()*max(R*2.1, 7.0)
        co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()
        cams.append(("%s_%s_透视" % (pid, P.name), co, (1500, 1150), [sub]))
        x += hi[0] + 4

    # ---------------- 水岸组装演示：水面 z=0（-Y 侧），岸面 z=1.2（+Y 侧）
    demo = bpy.data.collections.new("地码组装演示"); root.children.link(demo)
    oy = 90.0
    D = lambda x, y, z=0.0: (x, y + oy, z)
    for k in range(-5, 6):
        inst(kit["D01"], D(6*k, 0), parent=demo)
    ax = -1.5                       # 主轴：主栈桥 → 石板路 → 石阶 → 台地
    inst(kit["D02"], D(ax, 0), parent=demo)
    inst(kit["D02"], D(ax, -6), parent=demo)
    inst(kit["D03"], D(ax, -12), parent=demo)
    inst(kit["D02"], D(10.5, 0), parent=demo)
    for p in ((-7.5, -8), (3.0, -15.5), (13.2, -6.5), (2.2, -3.0)):
        inst(kit["D04"], D(*p), parent=demo)
    inst(kit["G04"], D(ax, 4.4, H), rz=90, parent=demo)
    inst(kit["G04"], D(ax, 10.4, H), rz=90, parent=demo)
    run = 7*0.36
    ty = 13.4 + run + 4.0           # 台地中心
    inst(kit["G02"], D(ax, ty - 4.0, H), parent=demo)
    inst(kit["G01"], D(ax, ty, H), parent=demo)
    inst(kit["G01"], D(ax, ty + 1.2, H + 1.2), parent=demo, scale=(0.62, 0.62, 1.0))
    inst(kit["G02"], D(ax, ty + 1.2 - 2.48, H + 1.2), parent=demo)
    inst(kit["G05"], D(ax + 4.0, ty + 1.0, H), rz=90, parent=demo)
    for p, r in (((ax - 2.1, 9.4), 90), ((ax + 2.1, 9.4), 90), ((-10.5, 8.0), 0), ((-16.5, 8.0), 0)):
        inst(kit["G03"], D(p[0], p[1], H), rz=r, parent=demo)
    if "C04" in ext:
        inst(ext["C04"], D(10.5, 5.0, H), parent=demo)
    if "C06" in ext:
        inst(ext["C06"], D(-8.5, 3.6, H), parent=demo)
    if "C05" in ext:
        for p in ((ax - 2.6, ty - 4.6), (ax + 2.6, ty - 4.6), (ax + 1.6, ty + 2.2)):
            inst(ext["C05"], D(p[0], p[1], H if p[1] < ty - 4 else H + 2.4), parent=demo)
    if "C03" in ext:
        inst(ext["C03"], D(-12.5, ty, H), parent=demo)
    if "P01" in ext:
        for k in range(5):
            inst(ext["P01"], D(-18 + 4.1*k, ty + 6, H), parent=demo)
    for p, z, r in (((ax + 0.6, -3.0), H, 10), ((ax - 0.8, -9.5), H, 200), ((ax + 1.2, -15.0), H, 0), ((ax - 0.6, 6.0), H, 180),
                    ((ax + 0.9, ty - 5.3), H + 0.55, 0), ((ax + 1.8, ty - 2.6), H + 1.2, 30), ((10.2, -3.5), H, 150), ((9.4, 2.4), H, 260),
                    ((ax - 0.5, ty + 0.4), H + 2.4, 0)):
        inst(fig_col, D(p[0], p[1], z), rz=r, parent=demo, name="人物_演示")
    wm = bpy.data.meshes.new("水面"); wm.from_pydata([(-40, oy-45, 0), (40, oy-45, 0), (40, oy, 0), (-40, oy, 0)], [], [(0, 1, 2, 3)])
    wm.materials.append(mats["水"]); demo.objects.link(bpy.data.objects.new("水面", wm))
    gm = bpy.data.meshes.new("岸地"); gm.from_pydata([(-33, oy+1.9, H-0.01), (33, oy+1.9, H-0.01), (33, oy+45, H-0.01), (-33, oy+45, H-0.01)], [], [(0, 1, 2, 3)])
    gm.materials.append(mats["地"]); demo.objects.link(bpy.data.objects.new("岸地", gm))
    for nm, loc, tgt, lens in (("水岸_鸟瞰", (-28, oy-40, 26), (0, oy+2, 1), 30),
                               ("水岸_码头近景", (9, oy-22, 4.5), (-1.5, oy-9, 1.5), 30),
                               ("水岸_台阶近景", (-10.5, oy+5, 4.2), (-1.5, oy+ty-2, 2.4), 30)):
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
    bpy.ops.wm.save_as_mainfile(filepath=OUT + "地面建筑与码头_套件.blend")
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
            print("%s %-8s %.2f×%.2f×%.2f  z %.2f→%.2f  面数 %d" % (P.pid, P.name, hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2], lo[2], hi[2], P.nf()))
