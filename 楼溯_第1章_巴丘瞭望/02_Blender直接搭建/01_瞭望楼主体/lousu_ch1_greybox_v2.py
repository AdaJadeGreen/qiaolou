# -*- coding: utf-8 -*-
"""
《楼·溯》第1章·巴丘瞭望（约210—214年） —— 白模生成脚本 v2（细化版）

v2 相比 v1 的颗粒度提升：
  · 屋顶：凹曲面坡 + 四角起翘出冲、筒瓦垄、戗脊走兽、鸱吻、博风板、山花、檐椽
  · 斗拱：栌斗 + 两跳华拱 + 泥道拱/慢拱 + 散斗 + 昂，柱头与补间都有
  · 台基：分层条石砌筑、压阑石、铺地方砖、踏步分块 + 垂带 + 象眼
  · 门窗：格扇门（格心 + 裙板）、槛墙槛窗；栏杆：望柱 + 寻杖 + 盆唇 + 华板 + 蜀柱
  · 建立中：穿透柱身的榫头与木销、竹脚手架绑扎节点、檩条、吊架滑轮、瓦堆竹捆、工匠比例人
  · 废墟：条石残墙参差断口、半倒的木构残架、倒塌屋面残片、碎瓦
  · 鲁肃：带褶皱的袍身、交领与衣缘、大袖与袖缘、大带与绅、带銙、玉佩、进贤冠、
          五官体块、须髯、歧头履、环首剑；随身物品单独成资产
每个资产：正视 / 侧视 / 后视 / 顶视四台正交相机 + 一台 3/4 透视相机（对照概念图首行）。

用法：Blender 4.x / 5.x → Scripting → 运行；或命令行：
  blender -b -P lousu_ch1_greybox.py
无 Blender：python3 lousu_ch1_greybox.py --obj 输出目录
"""
import math
import random
import sys

# ============================================================ PARAMS
SEED = 7
ASSET_SPACING = 30.0
WORK_DIR = "C:/Users/pjwly/3D Objects/lousu_ch1/"
RENDER_VIEWS = True
RENDER_DIR = WORK_DIR + "renders_v2/"
SAVE_BLEND = WORK_DIR + "lousu_ch1_greybox_v2.blend"
LOG_PATH = WORK_DIR + "build_log_v2.txt"
EXPORT_GLB_DIR = None

BASE_W = 12.0
BASE_H = 2.4
STAIR_W = 3.0
STAIR_N = 12
STAIR_TREAD = 0.30
G_COL = 3.6
G_H = 3.6
U_COL = 2.6
U_H = 3.0
ROOF_RIDGE_Z = 12.8

MATS = {
    "石": (0.56, 0.56, 0.54), "夯土": (0.62, 0.58, 0.52), "木": (0.47, 0.43, 0.40),
    "竹": (0.68, 0.66, 0.56), "瓦": (0.30, 0.31, 0.33), "布": (0.66, 0.66, 0.67),
    "衣缘": (0.50, 0.42, 0.42), "皮肤": (0.80, 0.77, 0.74), "发": (0.25, 0.25, 0.26),
    "金属": (0.38, 0.39, 0.42), "玉": (0.72, 0.76, 0.72), "旗": (0.58, 0.47, 0.45),
}
SMOOTH_ANGLE = 40.0  # 大于此角度的边保持硬边


# ============================================================ 向量与基础几何
def _sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def _mul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def _dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def _norm(a):
    l = math.sqrt(_dot(a, a)) or 1.0
    return (a[0]/l, a[1]/l, a[2]/l)
def _lerp(a, b, t): return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t)


def _rot(v, r):
    x, y, z = v
    rx, ry, rz = (math.radians(a) for a in r)
    y, z = y*math.cos(rx)-z*math.sin(rx), y*math.sin(rx)+z*math.cos(rx)
    x, z = x*math.cos(ry)+z*math.sin(ry), -x*math.sin(ry)+z*math.cos(ry)
    x, y = x*math.cos(rz)-y*math.sin(rz), x*math.sin(rz)+y*math.cos(rz)
    return (x, y, z)


_BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def box(c, s, rot=(0, 0, 0)):
    hx, hy, hz = s[0]/2, s[1]/2, s[2]/2
    loc = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
           (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    return [_add(c, _rot(p, rot)) for p in loc], list(_BOX_FACES)


def tbox(cx, cy, z0, bw, bd, tw, td, h, rz=0, shift=(0, 0)):
    b = [(-bw/2, -bd/2, 0), (bw/2, -bd/2, 0), (bw/2, bd/2, 0), (-bw/2, bd/2, 0)]
    t = [(-tw/2+shift[0], -td/2+shift[1], h), (tw/2+shift[0], -td/2+shift[1], h),
         (tw/2+shift[0], td/2+shift[1], h), (-tw/2+shift[0], td/2+shift[1], h)]
    return [_add((cx, cy, z0), _rot(p, (0, 0, rz))) for p in b + t], list(_BOX_FACES)


def seg_box(p0, p1, w, h):
    """沿 p0→p1 的方木（截面 w×h，h 为接近竖直方向）"""
    d = _sub(p1, p0); L = math.sqrt(_dot(d, d))
    rz = math.degrees(math.atan2(d[1], d[0]))
    ry = -math.degrees(math.atan2(d[2], math.hypot(d[0], d[1])))
    return box(_mul(_add(p0, p1), 0.5), (L, w, h), (0, ry, rz))


def _ring_faces(m, n, cap=True):
    f = []
    for k in range(m-1):
        a, b = k*n, (k+1)*n
        f += [(a+i, a+(i+1) % n, b+(i+1) % n, b+i) for i in range(n)]
    if cap:
        f.append(tuple(reversed(range(n))))
        f.append(tuple(range((m-1)*n, m*n)))
    return f


def sweep(pts, ru, rw=None, n=8, cap=True, phase=0.0, ref=(0, 0, 1)):
    """沿折线扫掠椭圆截面。ru/rw 可为数或逐点列表。"""
    m = len(pts)
    ru = ru if isinstance(ru, (list, tuple)) else [ru]*m
    rw = ru if rw is None else (rw if isinstance(rw, (list, tuple)) else [rw]*m)
    v = []
    for k, p in enumerate(pts):
        t = _sub(pts[min(k+1, m-1)], pts[max(k-1, 0)])
        t = _norm(t)
        a = ref if abs(_dot(t, ref)) < 0.99 else ((1, 0, 0) if abs(t[0]) < 0.9 else (0, 1, 0))
        u = _norm(_cross(t, a)); w = _cross(t, u)
        for i in range(n):
            th = 2*math.pi*i/n + phase
            v.append(_add(p, _add(_mul(u, ru[k]*math.cos(th)), _mul(w, rw[k]*math.sin(th)))))
    return v, _ring_faces(m, n, cap)


def cyl(p0, p1, r0, r1=None, n=10):
    return sweep([p0, p1], [r0, r0 if r1 is None else max(r1, 1e-4)], n=n)


def lathe(rings, n=24, cx=0.0, cy=0.0, folds=0, phase=0.0, cap=True):
    """rings: [(z, rx, ry, dy, fold_amp)]"""
    v = []
    for (z, rx, ry, dy, amp) in rings:
        for i in range(n):
            th = 2*math.pi*i/n
            f = 1+amp*math.sin(folds*th+phase)
            v.append((cx+rx*f*math.cos(th), cy+dy+ry*f*math.sin(th), z))
    return v, _ring_faces(len(rings), n, cap)


def sphere(c, r, scale=(1, 1, 1), nu=14, nv=9):
    v = [(c[0], c[1], c[2]-r*scale[2])]
    for j in range(1, nv):
        ph = -math.pi/2 + math.pi*j/nv
        for i in range(nu):
            t = 2*math.pi*i/nu
            v.append((c[0]+r*scale[0]*math.cos(ph)*math.cos(t),
                      c[1]+r*scale[1]*math.cos(ph)*math.sin(t),
                      c[2]+r*scale[2]*math.sin(ph)))
    v.append((c[0], c[1], c[2]+r*scale[2]))
    top = len(v)-1
    f = [(0, 1+(i+1) % nu, 1+i) for i in range(nu)]
    for j in range(nv-2):
        a, b = 1+j*nu, 1+(j+1)*nu
        f += [(a+i, a+(i+1) % nu, b+(i+1) % nu, b+i) for i in range(nu)]
    last = 1+(nv-2)*nu
    f += [(last+i, last+(i+1) % nu, top) for i in range(nu)]
    return v, f


def ribbon(pts, normals, width, thick):
    v = []
    m = len(pts)
    for k, p in enumerate(pts):
        t = _norm(_sub(pts[min(k+1, m-1)], pts[max(k-1, 0)]))
        nrm = _norm(normals[k]) if isinstance(normals, list) else _norm(normals)
        s = _norm(_cross(t, nrm))
        for a, b in ((-1, 0), (1, 0), (1, 1), (-1, 1)):
            v.append(_add(p, _add(_mul(s, a*width/2), _mul(nrm, b*thick))))
    return v, _ring_faces(m, 4, True)


def slab(grid, t):
    """grid: 行×列的顶面点阵，向下加厚 t，封闭边界"""
    R, C = len(grid), len(grid[0])
    v = [p for row in grid for p in row] + [(p[0], p[1], p[2]-t) for row in grid for p in row]
    off = R*C
    def I(i, j, b=0): return b*off + i*C + j
    f = []
    for i in range(R-1):
        for j in range(C-1):
            f.append((I(i, j), I(i, j+1), I(i+1, j+1), I(i+1, j)))
            f.append((I(i+1, j, 1), I(i+1, j+1, 1), I(i, j+1, 1), I(i, j, 1)))
    for j in range(C-1):
        f.append((I(0, j, 1), I(0, j+1, 1), I(0, j+1), I(0, j)))
        f.append((I(R-1, j), I(R-1, j+1), I(R-1, j+1, 1), I(R-1, j, 1)))
    for i in range(R-1):
        f.append((I(i, 0), I(i+1, 0), I(i+1, 0, 1), I(i, 0, 1)))
        f.append((I(i, C-1, 1), I(i+1, C-1, 1), I(i+1, C-1), I(i, C-1)))
    return v, f


def prism(poly2d, axis, a0, a1):
    """平面多边形沿轴挤出。axis='x'：poly 为 (y,z)；'y'：poly 为 (x,z)"""
    n = len(poly2d)
    def P(q, a): return (a, q[0], q[1]) if axis == "x" else (q[0], a, q[1])
    v = [P(q, a0) for q in poly2d] + [P(q, a1) for q in poly2d]
    f = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    f += [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
    return v, f


def wavy_panel(x0, x1, ztop, zbot, y, amp, waves, thick, nx=14, nz=6):
    grid = []
    for i in range(nz+1):
        z = ztop + (zbot-ztop)*i/nz
        row = []
        for j in range(nx+1):
            u = j/nx
            row.append((x0+(x1-x0)*u, y+amp*u*math.sin(2*math.pi*waves*u + i*0.25), z))
        grid.append(row)
    # slab 沿 z 加厚不合适，这里改成沿 y 加厚
    R, C = len(grid), len(grid[0])
    v = [p for row in grid for p in row] + [(p[0], p[1]+thick, p[2]) for row in grid for p in row]
    off = R*C
    def I(i, j, b=0): return b*off+i*C+j
    f = []
    for i in range(R-1):
        for j in range(C-1):
            f.append((I(i, j), I(i, j+1), I(i+1, j+1), I(i+1, j)))
            f.append((I(i+1, j, 1), I(i+1, j+1, 1), I(i, j+1, 1), I(i, j, 1)))
    for j in range(C-1):
        f.append((I(0, j, 1), I(0, j+1, 1), I(0, j+1), I(0, j)))
        f.append((I(R-1, j), I(R-1, j+1), I(R-1, j+1, 1), I(R-1, j, 1)))
    for i in range(R-1):
        f.append((I(i, 0), I(i+1, 0), I(i+1, 0, 1), I(i, 0, 1)))
        f.append((I(i, C-1, 1), I(i+1, C-1, 1), I(i+1, C-1), I(i, C-1)))
    return v, f


class Asset:
    def __init__(self, label, smooth=False):
        self.label = label
        self.smooth = smooth
        self.groups = {}

    def add(self, group, mat, geo):
        g = self.groups.setdefault(group, [mat, [], []])
        off = len(g[1])
        g[1].extend(geo[0])
        g[2].extend(tuple(i+off for i in fc) for fc in geo[1])

    def bbox(self, skip_prefix=None):
        vs = [p for k, g in self.groups.items() if not (skip_prefix and k.startswith(skip_prefix)) for p in g[1]]
        return ([min(p[k] for p in vs) for k in range(3)], [max(p[k] for p in vs) for k in range(3)])

    def nfaces(self):
        return sum(len(g[2]) for g in self.groups.values())


_SIDE_N = [(0, -1), (1, 0), (0, 1), (-1, 0)]   # 四面外法线：前、右、后、左


# ============================================================ 建筑构件
def roof_sampler(W, D, z0, w, d, z1, lift=0.7, cf=0.32, flare=0.07, c=(0, 0)):
    H = z1 - z0
    def P(k, s, v):
        Wv = W+(w-W)*v; Dv = D+(d-D)*v
        cs = [(-Wv/2, -Dv/2), (Wv/2, -Dv/2), (Wv/2, Dv/2), (-Wv/2, Dv/2)]
        a = cs[k % 4]; b = cs[(k+1) % 4]
        x = a[0]+s*(b[0]-a[0]); y = a[1]+s*(b[1]-a[1])
        e = min(s, 1-s); cc = max(0.0, 1-e/cf); cc = cc*cc
        g = (1-v)**1.6
        fl = 1+flare*cc*g
        return (c[0]+x*fl, c[1]+y*fl, z0 + H*(0.32*v + 0.68*v**2.1) + lift*cc*g)
    return P


def curved_skirt(P, nside=28, nv=7, t=0.28):
    M = 4*nside
    rows = [[P(j//nside, (j % nside)/nside, i/nv) for j in range(M)] for i in range(nv+1)]
    v = [p for r in rows for p in r] + [(p[0], p[1], p[2]-t) for r in rows for p in r]
    off = (nv+1)*M
    def I(i, j, b=0): return b*off + i*M + j % M
    f = []
    for i in range(nv):
        for j in range(M):
            f.append((I(i, j), I(i, j+1), I(i+1, j+1), I(i+1, j)))
            f.append((I(i+1, j, 1), I(i+1, j+1, 1), I(i, j+1, 1), I(i, j, 1)))
    for j in range(M):
        f.append((I(0, j, 1), I(0, j+1, 1), I(0, j+1), I(0, j)))
        f.append((I(nv, j), I(nv, j+1), I(nv, j+1, 1), I(nv, j, 1)))
    return v, f


def roof_details(A, P, nside, t, tiles=True, rafters=True, beasts=True, tag=""):
    """筒瓦垄、戗脊（含起翘端头与走兽）、檐椽"""
    if tiles:
        for j in range(4*nside):
            k, s = j//nside, (j % nside)/nside
            if j % nside == 0 or j % 2:
                continue
            pts = [_add(P(k, s, v/6), (0, 0, 0.07)) for v in range(7)]
            A.add("屋面_筒瓦"+tag, "瓦", sweep(pts, 0.075, 0.06, n=6))
            o = _SIDE_N[k]; p0 = pts[0]
            A.add("屋面_瓦当"+tag, "瓦", cyl(_add(p0, (-o[0]*0.05, -o[1]*0.05, 0)), _add(p0, (o[0]*0.06, o[1]*0.06, 0)), 0.09, n=8))
    for k in range(4):
        pts = [_add(P(k, 0, v/7), (0, 0, 0.16)) for v in range(8)]
        p0 = pts[0]; od = _norm((p0[0], p0[1], 0))
        tip = _add(p0, (od[0]*0.45, od[1]*0.45, 0.32))
        A.add("屋脊_戗脊"+tag, "瓦", sweep([tip] + pts, 0.15, 0.17, n=6))
        if beasts:
            for q in (0.10, 0.17, 0.24):
                b = _add(P(k, 0, q), (0, 0, 0.42))
                A.add("屋脊_走兽"+tag, "瓦", box(b, (0.16, 0.16, 0.22), (0, 0, math.degrees(math.atan2(od[1], od[0])))))
    if rafters:
        for j in range(4*nside):
            k, s = j//nside, (j % nside)/nside
            if min(s, 1-s) < 0.12 or j % 2:
                continue
            o = _SIDE_N[k]; p = P(k, s, 0)
            a = _sub(p, (o[0]*1.0, o[1]*1.0, t+0.22)); b = _sub(p, (o[0]*0.12, o[1]*0.12, t+0.06))
            A.add("檐椽"+tag, "木", cyl(a, b, 0.06, n=6))
            A.add("檐椽"+tag, "木", seg_box(_sub(p, (o[0]*0.5, o[1]*0.5, t+0.02)), _add(p, (o[0]*0.08, o[1]*0.08, -t+0.02)), 0.09, 0.08))


def xieshan_top(A, w, d, z1, zr, oh_x=0.45, oh_y=0.35, t=0.24, nq=8):
    """歇山顶上段：凹曲两坡 + 筒瓦 + 山花 + 博风板 + 正脊鸱吻 + 垂脊"""
    hy = d/2 + oh_y; hx = w/2 + oh_x
    def prof(q): return (hy*(1-q), z1 + (zr-z1)*(0.3*q + 0.7*q**1.8))
    for sg in (-1, 1):
        grid = []
        for i in range(nq+1):
            y, z = prof(i/nq)
            grid.append([(-hx, sg*y, z), (hx, sg*y, z)])
        A.add("屋面_歇山坡", "瓦", slab(grid, t))
        nx = int(2*hx/0.34)
        for j in range(1, nx):
            x = -hx + j*2*hx/nx
            if j % 2:
                continue
            pts = []
            for i in range(nq+1):
                y, z = prof(i/nq)
                pts.append((x, sg*y, z+0.07))
            A.add("屋面_筒瓦", "瓦", sweep(pts, 0.075, 0.06, n=6))
    for sx in (-1, 1):
        q0 = oh_y/hy
        poly = []
        for i in range(nq+1):
            q = q0 + (1-q0)*i/nq
            y, z = prof(q); poly.append((-y, z-t))
        for i in range(nq, -1, -1):
            q = q0 + (1-q0)*i/nq
            y, z = prof(q); poly.append((y, z-t))
        poly = [(y, max(z, z1-0.05)) for y, z in poly]
        xw = sx*(w/2-0.1)
        A.add("山花板", "木", prism(poly, "x", xw-0.05, xw+0.05))
        bp = [(sx*(hx-0.05), sg*y, z-0.05) for sg in (-1,) for y, z in (prof(i/nq) for i in range(nq+1))]
        bp += [(sx*(hx-0.05), y, z-0.05) for y, z in (prof(1-i/nq) for i in range(1, nq+1))]
        A.add("博风板", "木", ribbon(bp, (sx, 0, 0), 0.30, 0.06))
        gp = [(sx*(hx-0.18), -y, z+0.12) for y, z in (prof(i/nq) for i in range(nq+1))]
        gp += [(sx*(hx-0.18), y, z+0.12) for y, z in (prof(1-i/nq) for i in range(1, nq+1))]
        A.add("屋脊_垂脊", "瓦", sweep(gp, 0.12, 0.15, n=6))
        xe = sx*(hx-0.15)
        A.add("屋脊_鸱吻", "瓦", sweep([(xe, 0, zr+0.25), (xe, 0, zr+0.75), (xe-sx*0.12, 0, zr+1.05), (xe-sx*0.38, 0, zr+1.12)],
                                     [0.22, 0.2, 0.14, 0.07], [0.14, 0.13, 0.1, 0.05], n=8))
        A.add("屋脊_鸱吻", "瓦", box((xe+sx*0.05, 0, zr+0.45), (0.28, 0.36, 0.5)))
    A.add("屋脊_正脊", "瓦", box((0, 0, zr+0.22), (2*hx-0.2, 0.32, 0.42)))
    A.add("屋脊_正脊", "瓦", box((0, 0, zr+0.47), (2*hx-0.3, 0.22, 0.08)))


def dougong(A, x, y, z, o, s=1.0, g="斗拱"):
    """简化宋式斗拱：栌斗 + 泥道拱/慢拱 + 两跳华拱 + 散斗 + 昂。o=外法线(ox,oy)"""
    ox, oy = o
    ax, ay = -oy, ox   # 沿墙方向
    def P(a, n, h): return (x+ax*a*s+ox*n*s, y+ay*a*s+oy*n*s, z+h*s)
    def B(c, la, ln, h):  # la 沿墙长, ln 出跳长
        sx = abs(ax)*la + abs(ox)*ln; sy = abs(ay)*la + abs(oy)*ln
        return box(c, (sx*s, sy*s, h*s))
    A.add(g, "木", tbox(x, y, z, 0.30*s, 0.30*s, 0.40*s, 0.40*s, 0.22*s))
    A.add(g, "木", B(P(0, 0, 0.31), 1.0, 0.13, 0.18))            # 泥道拱
    A.add(g, "木", B(P(0, 0.22, 0.31), 0.13, 0.85, 0.18))        # 一跳华拱
    for a, n in ((-0.45, 0), (0.45, 0), (0, 0.6)):
        A.add(g, "木", box(P(a, n, 0.48), (0.2*s, 0.2*s, 0.14*s)))  # 散斗
    A.add(g, "木", B(P(0, 0, 0.64), 1.5, 0.13, 0.18))            # 慢拱
    A.add(g, "木", B(P(0, 0.45, 0.64), 0.13, 1.35, 0.18))        # 二跳华拱
    for a, n in ((-0.7, 0), (0.7, 0), (0, 1.05)):
        A.add(g, "木", box(P(a, n, 0.80), (0.2*s, 0.2*s, 0.14*s)))
    A.add(g, "木", B(P(0, 1.05, 0.95), 0.9, 0.13, 0.16))          # 令拱
    A.add(g, "木", seg_box(P(0, -0.2, 1.0), P(0, 1.45, 0.58), 0.13*s, 0.16*s))  # 昂


def balustrade(A, g, mat, p0, p1, z, h=1.0, post_sp=1.8):
    """寻杖栏杆"""
    dx, dy = p1[0]-p0[0], p1[1]-p0[1]
    L = math.hypot(dx, dy); ang = math.degrees(math.atan2(dy, dx))
    mid = ((p0[0]+p1[0])/2, (p0[1]+p1[1])/2)
    n = max(1, round(L/post_sp))
    for k in range(n+1):
        t = k/n; px, py = p0[0]+dx*t, p0[1]+dy*t
        A.add(g, mat, box((px, py, z+(h+0.15)/2), (0.13, 0.13, h+0.15)))
        A.add(g, mat, sphere((px, py, z+h+0.2), 0.085, (1, 1, 1.3), nu=8, nv=5))
    A.add(g, mat, box((mid[0], mid[1], z+0.06), (L, 0.14, 0.12), (0, 0, ang)))           # 地栿
    A.add(g, mat, box((mid[0], mid[1], z+0.48), (L, 0.12, 0.07), (0, 0, ang)))           # 盆唇
    A.add(g, mat, box((mid[0], mid[1], z+0.29), (L, 0.04, 0.30), (0, 0, ang)))           # 华板
    ux, uy = dx/L, dy/L
    A.add(g, mat, cyl((p0[0], p0[1], z+h-0.06), (p1[0], p1[1], z+h-0.06), 0.04, n=8))    # 寻杖
    m = max(2, int(L/0.55))
    for k in range(1, m):
        t = k/m; px, py = p0[0]+dx*t, p0[1]+dy*t
        A.add(g, mat, box((px, py, z+0.5+(h-0.6)/2), (0.05, 0.05, h-0.6)))               # 蜀柱
        A.add(g, mat, box((px, py, z+h-0.13), (0.18, 0.06, 0.07), (0, 0, ang)))          # 云拱


def ring_balustrade(A, g, mat, half, z, h=1.0, gap=None, post_sp=1.8):
    c = [(-half, -half), (half, -half), (half, half), (-half, half)]
    for k in range(4):
        a, b = c[k], c[(k+1) % 4]
        if k == 0 and gap:
            balustrade(A, g, mat, a, (-gap, -half), z, h, post_sp)
            balustrade(A, g, mat, (gap, -half), b, z, h, post_sp)
        else:
            balustrade(A, g, mat, a, b, z, h, post_sp)


def lattice(A, g, mat, axis, a0, a1, perp, z0, z1, nv=4, nh=6, skirt=0.0, frame=0.08, bar=0.035, thick=0.08):
    """格心窗/格扇：axis='x' 墙沿 X（位于 y=perp），'y' 墙沿 Y（位于 x=perp）"""
    def B(a, z, la, lz, th=thick):
        c = (a, perp, z) if axis == "x" else (perp, a, z)
        s = (la, th, lz) if axis == "x" else (th, la, lz)
        return box(c, s)
    W = a1-a0; am = (a0+a1)/2
    A.add(g, mat, B(am, z1-frame/2, W, frame)); A.add(g, mat, B(am, z0+frame/2, W, frame))
    A.add(g, mat, B(a0+frame/2, (z0+z1)/2, frame, z1-z0)); A.add(g, mat, B(a1-frame/2, (z0+z1)/2, frame, z1-z0))
    zs = z0 + frame
    if skirt > 0:
        zk = z0 + (z1-z0)*skirt
        A.add(g, mat, B(am, (z0+zk)/2, W-2*frame, zk-z0-frame, thick*0.6))
        A.add(g, mat, B(am, zk, W, frame))
        zs = zk + frame/2
    ze = z1 - frame
    for i in range(1, nv):
        A.add(g, mat, B(a0+W*i/nv, (zs+ze)/2, bar, ze-zs, thick*0.7))
    for i in range(1, nh):
        A.add(g, mat, B(am, zs+(ze-zs)*i/nh, W-2*frame, bar, thick*0.7))
    A.add(g, mat, B(am, (zs+ze)/2, W-2*frame, ze-zs, 0.02))  # 窗纸/背板


def stone_base(A, W, H, rng, mat="石", ruin=0.0, g="台基"):
    """条石砌筑台基。ruin>0 时随机缺块、错位。"""
    plinth = 0.22; cap = 0.24
    body = H - plinth - cap
    nc = max(2, round(body/0.42)); ch = body/nc
    A.add(g+"_芯", mat, box((0, 0, H/2), (W-0.5, W-0.5, H-0.05 if not ruin else H*0.7)))
    A.add(g+"_土衬", mat, tbox(0, 0, 0, W+0.7, W+0.7, W+0.55, W+0.55, plinth))
    for k in range(4):
        o = _SIDE_N[k]; ax, ay = -o[1], o[0]
        for i in range(nc):
            inset = 0.02*i
            pos = -W/2 + (0.35 if i % 2 else 0.0)
            while pos < W/2-0.05:
                L = min(rng.uniform(0.75, 1.35), W/2-pos)
                if L < 0.25:
                    break
                if ruin and (rng.random() < ruin*(0.4+i/nc)):
                    pos += L; continue
                mid = pos + L/2; d = W/2 - 0.16 - inset + rng.uniform(0, 0.025)
                c = (ax*mid + o[0]*d, ay*mid + o[1]*d, plinth + ch*(i+0.5))
                rz = 0 if not ruin else rng.uniform(-3, 3)
                sz = (L-0.035, 0.32, ch-0.035) if k % 2 == 0 else (0.32, L-0.035, ch-0.035)
                A.add(g+"_条石", mat, box(c, sz, (0, 0, rz)))
                pos += L
        # 压阑石
        pos = -W/2-0.1
        while pos < W/2+0.1:
            L = min(1.25, W/2+0.1-pos)
            if not (ruin and rng.random() < ruin*1.4):
                mid = pos+L/2; d = W/2-0.22
                c = (ax*mid + o[0]*d, ay*mid + o[1]*d, plinth+body+cap/2 - (rng.uniform(0, 0.3) if ruin else 0))
                sz = (L-0.03, 0.75, cap) if k % 2 == 0 else (0.75, L-0.03, cap)
                rot = (rng.uniform(-6, 6), rng.uniform(-6, 6), 0) if ruin else (0, 0, 0)
                A.add(g+"_压阑石", mat, box(c, sz, rot))
            pos += L
    # 铺地方砖
    n = int((W-1.6)/1.0)
    for i in range(n):
        for j in range(n):
            if ruin and rng.random() < ruin*1.2:
                continue
            x = -(n-1)/2 + i; y = -(n-1)/2 + j
            rot = (rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(-6, 6)) if ruin else (0, 0, 0)
            zt = H if not ruin else H*0.7 + rng.uniform(0, 0.08)
            A.add(g+"_铺地", mat, box((x, y, zt-0.03), (0.96, 0.96, 0.06), rot))


def stone_stairs(A, y_edge, width, n, rise, tread, rng, skip=(), ruin=0.0, mat="石"):
    run = n*tread
    for i in range(1, n+1):
        if i in skip:
            continue
        y0 = y_edge-(n-i+1)*tread
        segs = 3
        for s in range(segs):
            if ruin and rng.random() < ruin:
                continue
            x = -width/2 + width*(s+0.5)/segs
            rot = (rng.uniform(-5, 5), rng.uniform(-5, 5), rng.uniform(-8, 8)) if ruin else (0, 0, 0)
            A.add("踏道_踏步", mat, box((x, y0+tread/2, i*rise-0.09), (width/segs-0.03, tread+0.04, 0.18), rot))
        A.add("踏道_踏步", mat, box((0, y0+tread/2, (i*rise-0.18)/2), (width-0.1, tread, max(0.02, i*rise-0.18))))
    for sx in (-1, 1):
        x0 = sx*(width/2+0.25)
        A.add("踏道_垂带", mat, prism([(y_edge-run-0.2, 0), (y_edge, 0), (y_edge, n*rise+0.12), (y_edge-run-0.2, 0.15)], "x", x0-0.25, x0+0.25))


def mannequin(A, x, y, z, rz=0, s=1.0, pose="stand", g="比例人"):
    """简易人形（比例参照，约 1.72 m）"""
    def T(p):
        q = _rot(p, (0, 0, rz))
        return (x+q[0]*s, y+q[1]*s, z+q[2]*s)
    A.add(g, "布", lathe([(T((0, 0, 0))[2], 0.30*s, 0.25*s, 0, 0), (T((0, 0, 0.9))[2], 0.18*s, 0.13*s, 0, 0)], n=12, cx=x, cy=y))
    A.add(g, "布", lathe([(z+0.9*s, 0.18*s, 0.13*s, 0, 0), (z+1.35*s, 0.21*s, 0.13*s, 0, 0), (z+1.45*s, 0.1*s, 0.08*s, 0, 0)], n=12, cx=x, cy=y))
    A.add(g, "皮肤", sphere((x, y, z+1.58*s), 0.11*s, (0.9, 1, 1.1), nu=10, nv=7))
    A.add(g, "发", sphere((x, y, z+1.71*s), 0.045*s, nu=8, nv=5))
    for sx in (-1, 1):
        if pose == "carry":
            A.add(g, "布", sweep([T((sx*0.2, 0, 1.38)), T((sx*0.22, -0.2, 1.25)), T((sx*0.12, -0.38, 1.35))], 0.06*s, n=8))
        else:
            A.add(g, "布", sweep([T((sx*0.2, 0, 1.38)), T((sx*0.27, 0, 1.08)), T((sx*0.3, -0.06, 0.82))], [0.06*s, 0.07*s, 0.09*s], n=8))


def ring_beams(A, g, mat, half, z, s=(0.24, 0.32), tenon=0.0):
    ext = 0.3 + 2*tenon
    for sgn in (-1, 1):
        A.add(g, mat, box((0, sgn*half, z), (2*half+ext, s[0], s[1])))
        A.add(g, mat, box((sgn*half, 0, z+0.001), (s[0], 2*half+ext, s[1])))


def perimeter_cols(half, step_n):
    pts = []
    for i in range(step_n+1):
        t = -half+2*half*i/step_n
        pts += [(t, -half), (t, half)]
        if 0 < i < step_n:
            pts += [(-half, t), (half, t)]
    return pts


def col_normal(x, y, half):
    if abs(abs(x)-half) < 1e-6 and abs(abs(y)-half) < 1e-6:
        return None
    if abs(y+half) < 1e-6: return (0, -1)
    if abs(y-half) < 1e-6: return (0, 1)
    if abs(x-half) < 1e-6: return (1, 0)
    return (-1, 0)


def column(A, x, y, z0, h, r=0.2, g="柱", base=True):
    if base:
        A.add("柱础", "石", lathe([(z0, 0.38, 0.38, 0, 0), (z0+0.08, 0.38, 0.38, 0, 0), (z0+0.14, 0.32, 0.32, 0, 0),
                                   (z0+0.2, 0.25, 0.25, 0, 0)], n=12, cx=x, cy=y))
        z0 += 0.2
    A.add(g, "木", lathe([(z0, r, r, 0, 0), (z0+h*0.7, r*0.97, r*0.97, 0, 0), (z0+h-0.1, r*0.9, r*0.9, 0, 0), (z0+h, r*0.8, r*0.8, 0, 0)],
                        n=12, cx=x, cy=y))


def queti(A, x, y, z, o, g="雀替"):
    """柱头两侧雀替"""
    ax, ay = -o[1], o[0]
    for sg in (-1, 1):
        cx, cy = x+ax*sg*0.4, y+ay*sg*0.4
        poly = [(-0.45, 0), (0.45, 0), (0.45, -0.12), (-0.05, -0.32), (-0.45, -0.32)] if sg > 0 else \
               [(-0.45, 0), (0.45, 0), (0.45, -0.32), (0.05, -0.32), (-0.45, -0.12)]
        if abs(ax) > 0.5:
            A.add(g, "木", prism([(cx+p[0], z+p[1]) for p in poly], "y", y-0.06, y+0.06))
        else:
            A.add(g, "木", prism([(cy+p[0], z+p[1]) for p in poly], "x", x-0.06, x+0.06))


def flag(A, x, y, z, pole_h=5.0, banner=(0.95, 1.7), g="旗"):
    A.add(g+"_杆", "木", cyl((x, y, z), (x, y, z+pole_h), 0.06, 0.045))
    A.add(g+"_杆", "金属", sweep([(x, y, z+pole_h), (x, y, z+pole_h+0.12), (x, y, z+pole_h+0.42)], [0.05, 0.08, 0.005], n=8))
    A.add(g+"_杆", "木", cyl((x, y, z+pole_h-0.1), (x+banner[0]+0.08, y, z+pole_h-0.1), 0.03, n=6))
    top = z+pole_h-0.14
    A.add(g+"_幡", "旗", wavy_panel(x+0.06, x+banner[0], top, top-banner[1], y, 0.08, 1.2, 0.025))
    for k in range(3):
        xx = x+0.15+k*(banner[0]-0.2)/2
        A.add(g+"_幡", "旗", wavy_panel(xx-0.08, xx+0.08, top-banner[1], top-banner[1]-0.45, y+0.02, 0.03, 0.5, 0.02, nx=3, nz=4))
    A.add(g+"_幡", "衣缘", box((x+banner[0]/2+0.03, y-0.02, top-0.05), (banner[0], 0.04, 0.1)))


# ============================================================ 1. 废墟
def build_ruin():
    A = Asset("谯楼_废墟")
    rng = random.Random(SEED)
    H = 1.6
    stone_base(A, BASE_W, H, rng, ruin=0.22, g="残台")
    zt = H*0.7
    # 断墙：条石堆砌、断口参差
    half = BASE_W/2-0.7
    cs = [(-half, -half), (half, -half), (half, half), (-half, half)]
    for k in range(4):
        a, b = cs[k], cs[(k+1) % 4]
        L = math.hypot(b[0]-a[0], b[1]-a[1]); ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L
        t = 0.0
        base_h = rng.uniform(0.6, 1.6)
        while t < L:
            bl = rng.uniform(0.55, 0.95)
            px, py = a[0]+ux*(t+bl/2), a[1]+uy*(t+bl/2)
            gap = (k == 0 and abs(px) < STAIR_W/2+0.4)
            base_h = max(0.0, min(2.2, base_h + rng.uniform(-0.45, 0.45)))
            if rng.random() < 0.12:
                base_h = rng.uniform(0, 0.3)
            if not gap:
                nb = int(base_h/0.36)
                for i in range(nb):
                    off = 0.18 if i % 2 else 0.0
                    jit = (rng.uniform(-0.05, 0.05), rng.uniform(-0.04, 0.04))
                    rz = math.degrees(math.atan2(uy, ux)) + rng.uniform(-3, 3)
                    A.add("断墙", "石", box((px+ux*off*0.3+jit[0], py+uy*off*0.3+jit[1], zt+0.18+i*0.36),
                                           (bl-0.04, 0.55, 0.33), (rng.uniform(-2, 2), rng.uniform(-2, 2), rz)))
                if nb and rng.random() < 0.35:   # 顶部松动的残块
                    A.add("断墙", "石", box((px+rng.uniform(-0.2, 0.2), py+rng.uniform(-0.2, 0.2), zt+0.18+nb*0.36),
                                           (bl*0.6, 0.4, 0.28), (rng.uniform(-15, 15), rng.uniform(-15, 15), rng.uniform(0, 60))))
            t += bl
    # 柱础与残木柱
    for (x, y) in perimeter_cols(G_COL, 3):
        A.add("柱础", "石", lathe([(zt, 0.38, 0.38, 0, 0), (zt+0.1, 0.36, 0.36, 0, 0), (zt+0.2, 0.26, 0.26, 0, 0)], n=12, cx=x, cy=y))
        if rng.random() < 0.5 and not (x > 0 and y > 0):
            h = rng.uniform(0.4, 2.0)
            top = (x+rng.uniform(-0.3, 0.3), y+rng.uniform(-0.3, 0.3), zt+0.2+h)
            A.add("残柱_木", "木", sweep([(x, y, zt+0.2), _lerp((x, y, zt+0.2), top, 0.85), top], [0.2, 0.19, 0.12], n=10))
            A.add("残柱_木", "木", box(_add(top, (0, 0, 0.05)), (0.18, 0.12, 0.25), (rng.uniform(-30, 30), rng.uniform(-30, 30), rng.uniform(0, 90))))
    # 半倒木构残架（右后角）
    posts = [((1.2, 1.2), 3.9), ((3.6, 1.2), 4.6), ((3.6, 3.6), 4.4), ((1.2, 3.6), 2.1)]
    for (x, y), h in posts:
        tilt = (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25))
        A.add("残架_木", "木", sweep([(x, y, zt+0.2), (x+tilt[0], y+tilt[1], zt+0.2+h)], [0.2, 0.17], n=10))
    A.add("残架_木", "木", seg_box((1.0, 1.2, zt+4.0), (3.9, 1.25, zt+4.4), 0.24, 0.32))
    A.add("残架_木", "木", seg_box((3.6, 1.0, zt+4.6), (3.65, 3.9, zt+4.3), 0.24, 0.32))
    A.add("残架_木", "木", seg_box((1.3, 3.5, zt+0.4), (3.5, 3.7, zt+4.1), 0.22, 0.28))     # 斜挂的额枋
    A.add("残架_木", "木", seg_box((3.3, 3.6, zt+3.2), (5.2, 4.8, zt+0.3), 0.2, 0.26))
    for (x, y), h in posts[:3]:
        dougong(A, x, y, zt+0.2+h-0.05 if h > 4 else zt+h, (1, 0) if x > 3 else (0, -1), s=0.75, g="残架_斗拱")
    # 坍落屋面残片：带筒瓦的斜板
    sl = []
    for i in range(6):
        row = []
        for j in range(2):
            x = 1.4 + j*3.0; y = 4.9 - i*0.55
            row.append((x, y, zt+0.3 + i*0.42 + (0.25 if j else 0)))
        sl.append(row)
    A.add("坍落屋面", "瓦", slab(sl, 0.2))
    for j in range(1, 9):
        x = 1.4 + j*3.0/9
        pts = [(x, 4.9-i*0.55, zt+0.37+i*0.42+0.25*j/9) for i in range(6)]
        A.add("坍落屋面", "瓦", sweep(pts, 0.07, 0.055, n=6))
    # 两根高大残石柱 + 斜搭额枋
    for x, h in ((-1.4, 3.6), (1.0, 2.8)):
        z = zt
        for i in range(int(h/0.6)):
            jit = 0.03*i
            A.add("残柱_石", "石", box((x+rng.uniform(-jit, jit), -0.6+rng.uniform(-jit, jit), z+0.3), (0.62, 0.62, 0.58),
                                      (rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(-5, 5))))
            z += 0.6
        A.add("残柱_石", "石", box((x+0.1, -0.6, z+0.12), (0.55, 0.45, 0.3), (8, -14, 20)))
    A.add("残柱_石", "石", seg_box((-1.6, -0.6, zt+3.55), (1.4, -0.6, zt+2.75), 0.45, 0.42))
    # 倒伏梁木
    for p0, p1, r in (((-4.2, -1.5, zt+0.25), (-0.6, 0.6, zt+0.15), 0.19),
                      ((1.5, -3.8, zt+0.2), (4.9, -2.2, zt+0.55), 0.17),
                      ((-6.9, 2.5, 0.2), (-4.8, 5.5, zt+0.45), 0.16),
                      ((-3.0, 2.0, zt+0.2), (-1.0, 4.4, zt+0.25), 0.14)):
        A.add("倒梁", "木", sweep([p0, _lerp(p0, p1, 0.5), p1], [r, r*1.02, r*0.85], n=10))
    # 残破踏道
    stone_stairs(A, -BASE_W/2-0.3, STAIR_W, 5, H*0.7/5, 0.42, rng, skip=(3,), ruin=0.3)
    # 碎石、碎瓦
    for _ in range(110):
        if rng.random() < 0.6:
            side = rng.randint(0, 3); t = rng.uniform(-half, half); off = rng.uniform(-1.8, 1.8)
            x, y = [(t, -half+off), (half+off, t), (t, half+off), (-half+off, t)][side]
        else:
            x, y = rng.uniform(-half, half), rng.uniform(-half, half)
        z = zt if (abs(x) < BASE_W/2-0.4 and abs(y) < BASE_W/2-0.4) else 0.0
        if rng.random() < 0.35:
            A.add("碎瓦", "瓦", box((x, y, z+0.03), (0.3, 0.18, 0.04), (rng.uniform(-20, 20), rng.uniform(-20, 20), rng.uniform(0, 180))))
        else:
            s = rng.uniform(0.15, 0.55)
            A.add("碎石", "石", box((x, y, z+s*0.25), (s, s*rng.uniform(0.6, 1.4), s*rng.uniform(0.35, 0.8)),
                                   (rng.uniform(-25, 25), rng.uniform(-25, 25), rng.uniform(0, 90))))
    mannequin(A, -5.0, -BASE_W/2-3.0, 0, rz=20)
    return A


# ============================================================ 2. 建立中
def build_construction():
    A = Asset("谯楼_建立中")
    rng = random.Random(SEED+1)
    stone_base(A, BASE_W, BASE_H, rng)
    run = STAIR_N*STAIR_TREAD
    stone_stairs(A, -BASE_W/2-0.3, STAIR_W, STAIR_N, BASE_H/STAIR_N, STAIR_TREAD, rng, skip=range(8, 13))
    A.add("跳板", "木", seg_box((0, -BASE_W/2-0.3-run*0.33, BASE_H*0.62), (0, -BASE_W/2-0.1, BASE_H+0.02), 1.2, 0.08))
    z0 = BASE_H
    for (x, y) in perimeter_cols(G_COL, 3):
        column(A, x, y, z0, G_H-0.2, 0.2, g="一层柱")
    ring_beams(A, "一层额枋", "木", G_COL, z0+G_H-0.25, tenon=0.25)
    ring_beams(A, "一层额枋", "木", G_COL, z0+G_H-0.75, s=(0.18, 0.22), tenon=0.2)
    for (x, y) in perimeter_cols(G_COL, 3):    # 榫头木销
        for zz in (z0+G_H-0.25, z0+G_H-0.75):
            A.add("榫卯_木销", "木", cyl((x, y, zz+0.2), (x, y, zz+0.32), 0.045, n=6))
    for x, y in [(x, y) for (x, y) in perimeter_cols(G_COL, 3) if col_normal(x, y, G_COL)]:
        o = col_normal(x, y, G_COL)
        if o[1] >= 0:   # 只装了后、左右面的斗拱，前面尚未安装
            dougong(A, x, y, z0+G_H, o, s=0.85)
    zf = z0+G_H+0.75
    for k in range(-4, 5):
        A.add("平座_搁栅", "木", box((k*0.9, 0, zf), (0.16, 2*G_COL+1.2, 0.24)))
    for k in range(0, 10):
        A.add("平座_楼板", "木", box((0, 0.4+k*0.42, zf+0.15), (2*G_COL+1.0, 0.40, 0.06), (0, rng.uniform(-1, 1), 0)))
    z1 = zf+0.18
    for (x, y) in perimeter_cols(U_COL, 2):
        column(A, x, y, z1, U_H, 0.17, g="二层柱", base=False)
    ring_beams(A, "二层额枋", "木", U_COL, z1+U_H-0.15, tenon=0.25)
    ring_beams(A, "二层额枋", "木", U_COL, z1+1.1, s=(0.16, 0.2), tenon=0.2)
    # 屋架：檩条、椽子、角梁、脊檩
    ze = z1+U_H+0.6; zi = ze+1.6
    P = roof_sampler(9.8, 9.8, ze, 5.6, 4.0, zi, lift=0.7)
    for j in range(0, 4*20):
        k, s = j//20, (j % 20)/20
        if j % 20 == 0:
            continue
        pts = [P(k, s, v/5) for v in range(6)]
        A.add("屋架_椽", "木", sweep(pts, 0.055, n=6))
    for k in range(4):
        A.add("屋架_角梁", "木", sweep([P(k, 0, v/5) for v in range(6)], 0.12, 0.15, n=6))
    for v in (0.0, 0.35, 0.7, 1.0):
        ring = [P(k, s/8, v) for k in range(4) for s in range(8)]
        for i in range(len(ring)):
            A.add("屋架_檩", "木", seg_box(_sub(ring[i], (0, 0, 0.1)), _sub(ring[(i+1) % len(ring)], (0, 0, 0.1)), 0.16, 0.18))
    for sgn in (-1, 1):
        for q in (0.0, 0.5):
            y = sgn*(2.0+0.35)*(1-q); z = zi + (ROOF_RIDGE_Z-zi)*(0.3*q+0.7*q**1.8)
            A.add("屋架_檩", "木", box((0, y, z-0.1), (6.4, 0.16, 0.18)))
        for xi in range(-7, 8):
            x = xi*0.42
            A.add("屋架_椽", "木", cyl((x, sgn*2.35, zi-0.1), (x, 0, ROOF_RIDGE_Z-0.05), 0.05, n=6))
    A.add("屋架_脊檩", "木", box((0, 0, ROOF_RIDGE_Z), (6.6, 0.24, 0.28)))
    for sx in (-1, 1):   # 山面梁架
        A.add("屋架_梁", "木", box((sx*2.8, 0, zi), (0.24, 4.8, 0.3)))
        A.add("屋架_梁", "木", box((sx*2.8, 0, (zi+ROOF_RIDGE_Z)/2), (0.18, 0.18, ROOF_RIDGE_Z-zi)))
    # 腰檐：只装了后半的椽子
    for k in range(-7, 8):
        x = k*0.75
        A.add("腰檐_椽", "木", cyl((x, 5.6, z0+3.1), (max(-G_COL, min(G_COL, x)), G_COL+0.2, zf-0.3), 0.055, n=6))
    # 竹脚手架 + 绑扎
    S = G_COL+1.25
    top = z0+11.6
    xs = [-S, -S/2, 0, S/2, S]
    posts = set()
    for t in xs:
        posts |= {(t, -S), (t, S), (-S, t), (S, t)}
    for (x, y) in posts:
        A.add("脚手架_立杆", "竹", cyl((x, y, z0), (x+rng.uniform(-0.05, 0.05), y+rng.uniform(-0.05, 0.05), top+rng.uniform(-0.8, 0.3)), 0.06, 0.05, n=7))
    levels = [z0+lv*1.6 for lv in range(1, 8)]
    for z in levels:
        for sgn in (-1, 1):
            A.add("脚手架_横杆", "竹", cyl((-S-0.4, sgn*S+0.07*sgn, z), (S+0.4, sgn*S+0.07*sgn, z), 0.05, n=6))
            A.add("脚手架_横杆", "竹", cyl((sgn*S+0.07*sgn, -S-0.4, z+0.1), (sgn*S+0.07*sgn, S+0.4, z+0.1), 0.05, n=6))
        for (x, y) in posts:
            A.add("脚手架_绑扎", "竹", cyl((x, y, z-0.09), (x, y, z+0.19), 0.085, n=8))
    for sgn in (-1, 1):
        for d in (-1, 1):
            A.add("脚手架_剪刀撑", "竹", cyl((d*S, sgn*(S+0.14), z0), (-d*S, sgn*(S+0.14), top-1.4), 0.045, n=6))
            A.add("脚手架_剪刀撑", "竹", cyl((sgn*(S+0.14), d*S, z0), (sgn*(S+0.14), -d*S, top-1.4), 0.045, n=6))
    for lv in (2, 4, 6):
        z = z0+lv*1.6+0.08
        for sgn in (-1, 1):
            for p in range(3):
                A.add("脚手架_走道板", "木", box((0, sgn*(S-0.25-p*0.27), z), (2*S, 0.25, 0.05)))
                A.add("脚手架_走道板", "木", box((sgn*(S-0.25-p*0.27), 0, z), (0.25, 2*S-1.6, 0.05)))
    def ladder(x, y0, y1, za, zb, g):
        for sx in (-0.25, 0.25):
            A.add(g, "竹", cyl((x+sx, y0, za), (x+sx, y1, zb), 0.04, n=6))
        n = int((zb-za)/0.32)
        for k in range(1, n):
            t = k/n
            A.add(g, "竹", cyl((x-0.27, y0+(y1-y0)*t, za+(zb-za)*t), (x+0.27, y0+(y1-y0)*t, za+(zb-za)*t), 0.025, n=5))
    ladder(S/2+0.45, -S-1.0, -S-0.1, z0, z0+6.5, "竹梯")
    ladder(-1.8, -1.2, -0.4, z0, zf+0.1, "竹梯_内")
    # 地面：三脚吊架、滑轮、木料、竹捆、石料、瓦堆
    apex = (BASE_W/2+2.5, -BASE_W/2-1.5, 7.8)
    for gpt in ((BASE_W/2+0.8, -BASE_W/2-3.8, 0), (BASE_W/2+4.8, -BASE_W/2-2.6, 0), (BASE_W/2+2.2, -BASE_W/2+1.2, 0)):
        A.add("吊架", "木", cyl(gpt, apex, 0.1, 0.08, n=8))
    A.add("吊架", "木", cyl(_add(apex, (-0.12, 0, -0.35)), _add(apex, (0.12, 0, -0.35)), 0.2, n=12))
    A.add("吊架_绳", "竹", cyl(_add(apex, (0, 0, -0.5)), (apex[0], apex[1], 2.6), 0.02, n=4))
    A.add("吊架_绳", "竹", cyl(_add(apex, (0.18, 0, -0.4)), (BASE_W/2+3.6, -BASE_W/2-3.2, 0.9), 0.02, n=4))
    A.add("吊架", "木", box((apex[0], apex[1], 2.4), (2.6, 0.22, 0.28), (0, 6, 30)))
    for k in range(10):
        r = 0.17; row = 0 if k < 4 else (1 if k < 7 else (2 if k < 9 else 3)); col = [0, 1, 2, 3, 0.5, 1.5, 2.5, 1, 2, 1.5][k]
        A.add("木料堆", "木", cyl((-BASE_W/2-4.0+col*0.35, -3.0, r+row*0.3), (-BASE_W/2-4.0+col*0.35, 2.4, r+row*0.3), r, n=8))
    for k in range(14):
        A.add("竹捆", "竹", cyl((-BASE_W/2-2.0+(k % 5)*0.11, 3.0+(k//5)*0.1, 0.05+(k//5)*0.09), (-BASE_W/2-2.0+(k % 5)*0.11, 8.5, 0.05+(k//5)*0.09), 0.05, n=6))
    for k in range(6):
        A.add("石料", "石", box((-BASE_W/2-2.0+(k % 3)*0.78, -BASE_W/2-3.2, 0.25+(k//3)*0.5), (0.72, 0.56, 0.48)))
    for i in range(3):
        for j in range(2):
            A.add("瓦堆", "瓦", box((2.5+i*0.7, -4.6+j*0.6, z0+0.3), (0.55, 0.45, 0.6)))
    mannequin(A, S/2+0.2, -S+0.1, z0+4*1.6+0.1, rz=180, pose="carry")
    mannequin(A, -2.4, -4.8, z0, rz=30, pose="carry")
    mannequin(A, BASE_W/2+3.4, -BASE_W/2-3.0, 0, rz=-60)
    mannequin(A, -1.2, -BASE_W/2-4.6, 0, rz=10, s=1.03)
    flag(A, -BASE_W/2+0.6, -BASE_W/2+0.6, BASE_H, 5.4)
    return A


# ============================================================ 3. 建成后
def build_complete():
    A = Asset("谯楼_建成后")
    rng = random.Random(SEED+2)
    stone_base(A, BASE_W, BASE_H, rng)
    stone_stairs(A, -BASE_W/2-0.3, STAIR_W, STAIR_N, BASE_H/STAIR_N, STAIR_TREAD, rng)
    z0 = BASE_H
    ring_balustrade(A, "台基栏杆", "木", BASE_W/2-0.3, z0, 1.0, gap=STAIR_W/2+0.2, post_sp=2.0)
    # 一层
    cols = perimeter_cols(G_COL, 3)
    for (x, y) in cols:
        column(A, x, y, z0, G_H-0.2, 0.2, g="一层柱")
    ring_beams(A, "一层额枋", "木", G_COL, z0+G_H-0.25)
    ring_beams(A, "一层额枋", "木", G_COL, z0+G_H-0.8, s=(0.16, 0.22))
    A.add("一层普拍枋", "木", box((0, 0, z0+G_H-0.02), (2*G_COL+0.5, 2*G_COL+0.5, 0.06)))
    for (x, y) in cols:
        o = col_normal(x, y, G_COL)
        if o:
            queti(A, x, y, z0+G_H-0.92, o)
    sp = 2*G_COL/3
    zlo, zhi = z0+0.15, z0+G_H-0.92
    for b in range(3):
        a0 = -G_COL + b*sp + 0.2; a1 = a0 + sp - 0.4
        if b == 1:   # 正面明间：四扇格扇门
            for leaf in range(4):
                l0 = a0 + (a1-a0)*leaf/4
                lattice(A, "门窗_格扇", "木", "x", l0, l0+(a1-a0)/4, -G_COL, zlo, zhi, nv=3, nh=7, skirt=0.33)
        else:        # 次间：槛墙 + 槛窗
            A.add("槛墙", "石", box(((a0+a1)/2, -G_COL, (zlo+z0+1.0)/2), (a1-a0+0.2, 0.3, z0+1.0-zlo)))
            lattice(A, "门窗_槛窗", "木", "x", a0, a1, -G_COL, z0+1.0, zhi, nv=4, nh=5)
        # 后墙与两山
        A.add("墙体", "夯土", box(((a0+a1)/2, G_COL, (zlo+zhi)/2), (a1-a0+0.4, 0.32, zhi-zlo)))
        for sx in (-1, 1):
            if b == 1:
                A.add("墙体", "夯土", box((sx*G_COL, (a0+a1)/2, (zlo+z0+1.0)/2), (0.32, a1-a0+0.4, z0+1.0-zlo)))
                lattice(A, "门窗_槛窗", "木", "y", a0, a1, sx*G_COL, z0+1.0, zhi, nv=4, nh=5)
            else:
                A.add("墙体", "夯土", box((sx*G_COL, (a0+a1)/2, (zlo+zhi)/2), (0.32, a1-a0+0.4, zhi-zlo)))
    for (x, y) in cols:
        o = col_normal(x, y, G_COL)
        if o:
            dougong(A, x, y, z0+G_H, o, s=0.8)
    for k in range(4):   # 补间铺作（每开间正中一朵）
        o = _SIDE_N[k]
        for a in (-2.4, 0.0, 2.4):
            x = -o[1]*a + o[0]*G_COL; y = o[0]*a + o[1]*G_COL
            dougong(A, x, y, z0+G_H, o, s=0.65, g="斗拱_补间")
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (sx*G_COL, sy*G_COL)
            dougong(A, c[0], c[1], z0+G_H, (sx, 0), s=0.8, g="斗拱_转角")
            dougong(A, c[0], c[1], z0+G_H+0.01, (0, sy), s=0.8, g="斗拱_转角")
    # 腰檐
    zw = z0+G_H+0.85
    Pw = roof_sampler(12.0, 12.0, zw, 7.9, 7.9, zw+1.0, lift=0.5, cf=0.3)
    A.add("腰檐", "瓦", curved_skirt(Pw, nside=32, nv=5, t=0.24))
    roof_details(A, Pw, 32, 0.24, beasts=False, tag="_腰檐")
    # 平座
    zf = zw+1.05
    A.add("平座", "木", box((0, 0, zf+0.12), (8.8, 8.8, 0.25)))
    for k in range(4):
        o = _SIDE_N[k]
        for a in [i*0.6-4.2 for i in range(15)]:
            x = -o[1]*a + o[0]*4.25; y = o[0]*a + o[1]*4.25
            A.add("平座_出挑", "木", box((x, y, zf-0.08), (0.14 if o[0] == 0 else 0.5, 0.5 if o[0] == 0 else 0.14, 0.16)))
    ring_balustrade(A, "平座栏杆", "木", 4.2, zf+0.25, 1.05, post_sp=1.4)
    # 二层
    z1 = zf+0.25
    ucols = perimeter_cols(U_COL, 2)
    for (x, y) in ucols:
        column(A, x, y, z1, U_H, 0.17, g="二层柱", base=False)
    ring_beams(A, "二层额枋", "木", U_COL, z1+U_H-0.2)
    ring_beams(A, "二层额枋", "木", U_COL, z1+U_H-0.7, s=(0.14, 0.2))
    for (x, y) in ucols:
        o = col_normal(x, y, U_COL)
        if o:
            queti(A, x, y, z1+U_H-0.8, o)
    for k in range(4):
        o = _SIDE_N[k]
        for b in range(2):
            a0 = -U_COL + b*U_COL + 0.17; a1 = a0 + U_COL - 0.34
            axis = "x" if o[0] == 0 else "y"
            perp = o[1]*U_COL if axis == "x" else o[0]*U_COL
            c = ((a0+a1)/2, perp) if axis == "x" else (perp, (a0+a1)/2)
            if k == 0:
                for leaf in range(2):
                    l0 = a0 + (a1-a0)*leaf/2
                    lattice(A, "门窗_格扇", "木", axis, l0, l0+(a1-a0)/2, perp, z1+0.05, z1+U_H-0.8, nv=3, nh=7, skirt=0.33)
            else:
                A.add("槛墙", "木", box((c[0], c[1], z1+0.45), (a1-a0+0.1 if axis == "x" else 0.2, 0.2 if axis == "x" else a1-a0+0.1, 0.9)))
                lattice(A, "门窗_槛窗", "木", axis, a0, a1, perp, z1+0.9, z1+U_H-0.8, nv=4, nh=5)
    A.add("匾额", "木", box((0, -U_COL-0.22, z1+U_H-0.45), (1.5, 0.1, 0.55), (-8, 0, 0)))
    A.add("匾额", "衣缘", box((0, -U_COL-0.28, z1+U_H-0.45), (1.25, 0.04, 0.38), (-8, 0, 0)))
    for (x, y) in ucols:
        o = col_normal(x, y, U_COL)
        if o:
            dougong(A, x, y, z1+U_H, o, s=0.8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            dougong(A, sx*U_COL, sy*U_COL, z1+U_H, (sx, 0), s=0.8, g="斗拱_转角")
            dougong(A, sx*U_COL, sy*U_COL, z1+U_H+0.01, (0, sy), s=0.8, g="斗拱_转角")
    # 歇山顶
    ze = z1+U_H+0.75
    zi = ze+1.6
    P = roof_sampler(10.2, 10.2, ze, 5.6, 4.0, zi, lift=0.75, cf=0.33, flare=0.08)
    A.add("屋面", "瓦", curved_skirt(P, nside=30, nv=7, t=0.3))
    roof_details(A, P, 30, 0.3)
    xieshan_top(A, 5.6, 4.0, zi-0.05, ROOF_RIDGE_Z)
    flag(A, -BASE_W/2+0.6, -BASE_W/2+0.6, BASE_H, 5.4)
    flag(A, BASE_W/2-0.6, -BASE_W/2+0.6, BASE_H, 5.4)
    mannequin(A, -0.9, -BASE_W/2-1.6, BASE_H*0.42, rz=0)
    return A


# ============================================================ 4. 鲁肃
FOLDS, FPHASE = 11, 0.4


def _robe_r(z):
    """袍身（下裳）轮廓：返回 rx, ry, dy, fold_amp"""
    prof = [(0.03, 0.44, 0.37, 0.03, 0.075), (0.15, 0.415, 0.345, 0.025, 0.065), (0.38, 0.355, 0.29, 0.015, 0.05),
            (0.62, 0.285, 0.225, 0.0, 0.032), (0.86, 0.215, 0.16, -0.01, 0.015), (1.0, 0.19, 0.14, -0.01, 0.0)]
    for a, b in zip(prof, prof[1:]):
        if a[0] <= z <= b[0]:
            t = (z-a[0])/(b[0]-a[0])
            return tuple(a[i]+(b[i]-a[i])*t for i in range(1, 5))
    return prof[-1][1:] if z > 1 else prof[0][1:]


def _robe_front(x, z, out=0.012):
    rx, ry, dy, amp = _robe_r(z)
    th = -math.acos(max(-1, min(1, x/rx)))
    f = 1+amp*math.sin(FOLDS*th+FPHASE)
    return (rx*f*math.cos(th), dy+ry*(1+amp)*math.sin(th)-out, z)


def _torso_r(z):
    prof = [(1.0, 0.19, 0.14), (1.15, 0.195, 0.14), (1.28, 0.21, 0.14), (1.38, 0.225, 0.135), (1.45, 0.21, 0.12), (1.49, 0.13, 0.09)]
    for a, b in zip(prof, prof[1:]):
        if a[0] <= z <= b[0]:
            t = (z-a[0])/(b[0]-a[0])
            return a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t
    return prof[-1][1:]


def _torso_front(x, z, out=0.008):
    rx, ry = _torso_r(z)
    xx = max(-rx*0.98, min(rx*0.98, x))
    y = -ry*math.sqrt(max(0.0, 1-(xx/rx)**2)) - out
    n = (xx/rx**2, y/ry**2, 0)
    return (xx, y, z), n


def build_lusu():
    A = Asset("鲁肃", smooth=True)
    # ---- 足
    for sx in (-1, 1):
        x = sx*0.11
        A.add("履", "布", sweep([(x, 0.03, 0.045), (x, -0.08, 0.045), (x, -0.19, 0.05), (x, -0.25, 0.08), (x, -0.255, 0.13)],
                               [0.05, 0.052, 0.045, 0.03, 0.012], [0.04, 0.042, 0.035, 0.025, 0.012], n=10))
    # ---- 下裳（带褶）+ 下摆衣缘
    rings = [(z,) + _robe_r(z) for z in (0.03, 0.15, 0.27, 0.38, 0.5, 0.62, 0.74, 0.86, 1.0)]
    A.add("袍_下裳", "布", lathe(rings, n=44, folds=FOLDS, phase=FPHASE))
    hem = [(z, rx+0.008, ry+0.008, dy, amp) for (z, rx, ry, dy, amp) in [(0.015,) + _robe_r(0.03), (0.11,) + _robe_r(0.11)]]
    A.add("衣缘_下摆", "衣缘", lathe(hem, n=44, folds=FOLDS, phase=FPHASE))
    # ---- 上衣躯干
    trings = [(z,) + _torso_r(z) + (0, 0) for z in (1.0, 1.15, 1.28, 1.38, 1.45, 1.49)]
    A.add("袍_上衣", "布", lathe(trings, n=28))
    for sx in (-1, 1):
        A.add("袍_上衣", "布", sphere((sx*0.205, 0.0, 1.425), 0.085, (1.0, 1.0, 0.8), nu=12, nv=7))
    # ---- 交领右衽 + 衣襟缘（延续到下摆）
    lap = []
    for i in range(10):
        t = i/9
        x = 0.065 + (-0.16-0.065)*t
        z = 1.47 + (1.1-1.47)*t
        lap.append(_torso_front(x, z, 0.012))
    A.add("衣缘_交领", "衣缘", ribbon([p for p, n in lap], [n for p, n in lap], 0.055, 0.012))
    lap2 = []
    for i in range(6):
        t = i/5
        x = -0.065 + (0.06+0.065)*t
        z = 1.47 + (1.33-1.47)*t
        lap2.append(_torso_front(x, z, 0.006))
    A.add("衣缘_交领", "衣缘", ribbon([p for p, n in lap2], [n for p, n in lap2], 0.05, 0.01))
    neck = []
    for i in range(13):
        th = math.pi + math.pi*i/12
        neck.append(((0.075*math.cos(th)), 0.065*math.sin(th) - 0.004, 1.49 + 0.012*math.sin(th)))
    A.add("衣缘_交领", "衣缘", sweep(neck, 0.018, 0.012, n=6))
    front_edge = [_robe_front(-0.15 + 0.02*(1-z), z, 0.014) for z in (1.0, 0.86, 0.74, 0.62, 0.5, 0.38, 0.27, 0.15, 0.06)]
    A.add("衣缘_衣襟", "衣缘", ribbon(front_edge, [_norm((p[0], p[1]-0.0, 0)) for p in front_edge], 0.05, 0.01))
    # ---- 大带、革带、带銙、绅、蔽膝、玉佩
    A.add("大带", "衣缘", lathe([(0.965, 0.2, 0.15, -0.005, 0), (1.085, 0.2, 0.15, -0.005, 0)], n=28))
    A.add("革带", "布", lathe([(1.03, 0.207, 0.157, -0.005, 0), (1.06, 0.207, 0.157, -0.005, 0)], n=28))
    for i in range(9):
        th = math.pi + math.pi*(i+0.5)/9
        p = (0.207*math.cos(th), -0.005+0.157*math.sin(th), 1.045)
        A.add("带銙", "金属", box(p, (0.028, 0.012, 0.035), (0, 0, math.degrees(th)+90)))
    A.add("带銙", "金属", box((0, -0.165, 1.045), (0.06, 0.02, 0.05)))
    A.add("大带_结", "衣缘", sphere((0.03, -0.158, 1.02), 0.028, (1.2, 0.6, 0.9), nu=10, nv=6))
    for sx, L in ((-0.015, 0.47), (0.045, 0.42)):
        pts = [(_robe_front(sx, z, 0.03)[0], _robe_front(sx, z, 0.03)[1], z) for z in [1.0 - L*i/5 for i in range(6)]]
        A.add("绅", "衣缘", ribbon(pts, (0, -1, 0), 0.045, 0.008))
    bx = [(_robe_front(0.0, z, 0.02)) for z in (0.97, 0.86, 0.74, 0.62, 0.52)]
    A.add("蔽膝", "布", ribbon(bx, (0, -1, 0), 0.2, 0.012))
    px = -0.17
    pz0 = _robe_front(px, 1.0, 0.03)
    A.add("玉佩", "衣缘", cyl((px, pz0[1], 1.0), (px-0.01, pz0[1]-0.01, 0.82), 0.006, n=5))
    A.add("玉佩", "玉", cyl((px-0.01, pz0[1]-0.02, 0.83), (px-0.01, pz0[1]-0.035, 0.83), 0.032, n=14))
    A.add("玉佩", "玉", box((px-0.012, pz0[1]-0.02, 0.77), (0.07, 0.012, 0.02)))
    A.add("玉佩", "衣缘", sweep([(px-0.012, pz0[1]-0.02, 0.76), (px-0.012, pz0[1]-0.022, 0.62)], [0.012, 0.03], n=8))
    # ---- 颈、头、五官、须髯、发
    A.add("颈", "皮肤", lathe([(1.47, 0.056, 0.056, 0, 0), (1.53, 0.053, 0.053, 0.0, 0), (1.58, 0.05, 0.05, 0.005, 0)], n=12))
    A.add("头", "皮肤", sphere((0, 0.005, 1.672), 0.1, (0.9, 1.0, 1.1), nu=16, nv=10))
    A.add("头", "皮肤", sphere((0, -0.025, 1.598), 0.068, (1.0, 0.95, 0.85), nu=14, nv=8))
    A.add("头", "皮肤", sweep([(0, -0.092, 1.692), (0, -0.104, 1.66), (0, -0.112, 1.638)], [0.011, 0.015, 0.02], [0.008, 0.012, 0.014], n=8))
    A.add("头", "皮肤", box((0, -0.087, 1.705), (0.13, 0.025, 0.022), (-12, 0, 0)))
    for sx in (-1, 1):
        A.add("头", "皮肤", sphere((sx*0.091, 0.005, 1.665), 0.03, (0.35, 0.6, 1.0), nu=8, nv=6))
        A.add("头", "发", box((sx*0.035, -0.098, 1.718), (0.045, 0.012, 0.01), (0, sx*-10, 0)))
        A.add("须髯", "发", sweep([(0, -0.106, 1.622), (sx*0.03, -0.1, 1.615), (sx*0.05, -0.088, 1.593)], [0.009, 0.008, 0.004], n=6))
    A.add("须髯", "发", sweep([(0, -0.092, 1.578), (0, -0.098, 1.54), (0, -0.09, 1.49)], [0.03, 0.022, 0.006], [0.018, 0.016, 0.006], n=8))
    A.add("发", "发", sphere((0, 0.018, 1.695), 0.104, (0.92, 1.0, 1.08), nu=16, nv=10))
    A.add("发", "发", sphere((0, 0.01, 1.795), 0.042, (1.0, 1.0, 1.15), nu=10, nv=7))
    # ---- 进贤冠
    A.add("冠", "布", lathe([(1.765, 0.06, 0.07, 0.005, 0), (1.79, 0.058, 0.068, 0.005, 0)], n=16))
    A.add("冠", "布", box((0, -0.02, 1.835), (0.075, 0.13, 0.012), (-38, 0, 0)))
    for sx in (-1, 1):
        A.add("冠", "布", prism([(-0.06, 1.785), (0.07, 1.785), (0.045, 1.88), (-0.03, 1.87)], "x", sx*0.037-0.004, sx*0.037+0.004))
    A.add("冠", "金属", cyl((-0.09, 0.012, 1.82), (0.09, 0.012, 1.82), 0.006, n=6))
    A.add("冠", "衣缘", sweep([(0.06, 0.0, 1.775), (0.07, -0.01, 1.68), (0.06, -0.03, 1.56)], 0.004, n=4))
    A.add("冠", "衣缘", sweep([(-0.06, 0.0, 1.775), (-0.07, -0.01, 1.68), (-0.06, -0.03, 1.56)], 0.004, n=4))
    # ---- 大袖 + 袖缘 + 手
    for sx in (-1, 1):
        sh = (sx*0.215, 0, 1.43)
        d1 = (sx*math.sin(math.radians(17)), 0, -math.cos(math.radians(17)))
        el = _add(sh, _mul(d1, 0.30))
        d2 = _norm((sx*math.sin(math.radians(11)), -0.28, -math.cos(math.radians(11))))
        wr = _add(el, _mul(d2, 0.25))
        path = [sh, _lerp(sh, el, 0.5), el, _lerp(el, wr, 0.5), wr]
        ru = [0.08, 0.095, 0.115, 0.135, 0.15]   # 前后方向
        rw = [0.075, 0.08, 0.085, 0.09, 0.095]
        A.add("大袖", "布", sweep(path, ru, rw, n=16))
        drop = [_add(_lerp(el, wr, 0.2), (sx*-0.01, 0.01, -0.03)), _add(wr, (sx*-0.02, 0.02, -0.12)), _add(wr, (sx*-0.025, 0.03, -0.25))]
        A.add("大袖_袂", "布", sweep(drop, [0.1, 0.135, 0.145], [0.045, 0.055, 0.05], n=12))
        cuff = [wr, _add(wr, _mul(d2, 0.035))]
        A.add("衣缘_袖缘", "衣缘", sweep(cuff, 0.16, 0.105, n=16, cap=False))
        A.add("衣缘_袖缘", "衣缘", sweep(cuff, 0.15, 0.095, n=16))
        hp = _add(wr, _mul(d2, 0.03))
        A.add("手", "皮肤", sweep([hp, _add(hp, _mul(d2, 0.085))], [0.045, 0.048], [0.02, 0.018], n=10))
        f0 = _add(hp, _mul(d2, 0.085))
        A.add("手", "皮肤", sweep([f0, _add(f0, _mul(d2, 0.05)), _add(f0, (sx*0.005, -0.02, -0.075))], [0.044, 0.04, 0.036], [0.015, 0.014, 0.012], n=10))
        A.add("手", "皮肤", sweep([_add(hp, (0, -0.03, -0.02)), _add(hp, (sx*-0.01, -0.065, -0.07))], [0.013, 0.011], n=6))
    # ---- 环首佩剑（左胯，角色左 = +X）
    top = (0.235, -0.13, 1.0); tip = (0.28, 0.33, 0.24)
    dr = _norm(_sub(tip, top))
    A.add("佩剑_鞘", "木", sweep([top, _lerp(top, tip, 0.5), tip], [0.028, 0.026, 0.02], [0.012, 0.011, 0.009], n=8))
    A.add("佩剑_鞘", "金属", sweep([_lerp(top, tip, 0.15), _lerp(top, tip, 0.2)], 0.034, 0.018, n=8))
    A.add("佩剑_鞘", "金属", sweep([_lerp(top, tip, 0.95), tip], [0.024, 0.026], [0.012, 0.012], n=8))
    A.add("佩剑_格", "金属", box(top, (0.045, 0.03, 0.035), (0, 0, 0)))
    gp = _sub(top, _mul(dr, 0.2))
    A.add("佩剑_柄", "衣缘", sweep([_sub(top, _mul(dr, 0.02)), gp], 0.016, n=8))
    c = _sub(gp, _mul(dr, 0.035))                 # 环首：在剑轴所在竖直面内画环
    side = _norm(_cross(dr, (1, 0, 0)))
    ring = [_add(c, _add(_mul(dr, -0.035*math.cos(a)), _mul(side, 0.035*math.sin(a)))) for a in [2*math.pi*i/16 for i in range(17)]]
    A.add("佩剑_环首", "金属", sweep(ring, 0.008, n=6, cap=False))
    A.add("佩剑_带", "衣缘", ribbon([(0.2, -0.1, 1.04), (0.25, -0.05, 0.98), (0.255, 0.02, 0.86)], (1, 0, 0), 0.025, 0.006))
    return A


def build_props():
    A = Asset("鲁肃_随身物品", smooth=True)
    # 环首剑：剑身（菱形截面）+ 剑鞘，并排立放
    x = 0.0
    A.add("剑身", "金属", sweep([(x, 0, 0.02), (x, 0, 0.1), (x, 0, 0.75)], [0.002, 0.018, 0.022], [0.001, 0.005, 0.006], n=4))
    A.add("剑_格", "金属", box((x, 0, 0.77), (0.08, 0.035, 0.035)))
    A.add("剑_柄", "衣缘", sweep([(x, 0, 0.785), (x, 0, 0.98)], 0.017, n=8))
    for i in range(6):
        A.add("剑_缠绳", "布", cyl((x, 0, 0.80+i*0.03), (x, 0, 0.812+i*0.03), 0.02, n=8))
    pts = [(x+0.04*math.sin(a), 0, 1.035+0.045*math.cos(a)) for a in [math.pi + 2*math.pi*i/16 for i in range(17)]]
    A.add("剑_环首", "金属", sweep(pts, 0.009, n=6, cap=False))
    x2 = 0.25
    A.add("剑鞘", "木", sweep([(x2, 0, 0.0), (x2, 0, 0.4), (x2, 0, 0.78)], [0.022, 0.026, 0.03], [0.011, 0.012, 0.013], n=8))
    A.add("剑鞘", "金属", sweep([(x2, 0, 0.0), (x2, 0, 0.06)], [0.026, 0.024], [0.014, 0.013], n=8))
    A.add("剑鞘", "金属", sweep([(x2, 0, 0.56), (x2, 0, 0.6)], 0.034, 0.016, n=8))
    A.add("剑鞘", "金属", sweep([(x2, 0, 0.75), (x2, 0, 0.785)], 0.034, 0.016, n=8))
    A.add("剑鞘", "玉", box((x2, -0.016, 0.62), (0.03, 0.012, 0.09)))
    # 东吴军旗
    fx = 0.8
    A.add("旗_杆", "木", sweep([(fx, 0, 0), (fx, 0, 1.4), (fx, 0, 2.8)], [0.03, 0.027, 0.024], n=10))
    A.add("旗_杆", "金属", sweep([(fx, 0, 2.8), (fx, 0, 2.88), (fx, 0, 3.15)], [0.035, 0.045, 0.002], [0.035, 0.012, 0.002], n=8))
    A.add("旗_杆", "衣缘", sweep([(fx, 0, 2.8), (fx+0.03, -0.03, 2.72), (fx+0.02, -0.05, 2.55)], 0.012, n=6))
    A.add("旗_杆", "木", cyl((fx, 0, 2.68), (fx+0.88, 0, 2.68), 0.016, n=6))
    A.add("旗_幡", "旗", wavy_panel(fx+0.06, fx+0.84, 2.66, 1.4, 0.0, 0.05, 1.0, 0.02, nx=14, nz=10))
    for (a0, a1, z0, z1) in ((fx+0.06, fx+0.84, 2.66, 2.58), (fx+0.06, fx+0.84, 1.48, 1.4), (fx+0.06, fx+0.14, 2.66, 1.4), (fx+0.76, fx+0.84, 2.66, 1.4)):
        A.add("旗_缘", "衣缘", wavy_panel(a0, a1, z0, z1, -0.012, 0.05*(a1-fx-0.06)/0.78, 1.0, 0.012, nx=3, nz=2))
    for k in range(3):
        xx = fx+0.14+k*0.31
        A.add("旗_幡", "旗", wavy_panel(xx-0.07, xx+0.07, 1.4, 1.05, 0.0, 0.03, 0.6, 0.015, nx=3, nz=5))
    A.add("旗_徽", "衣缘", cyl((fx+0.45, -0.03, 2.03), (fx+0.45, -0.045, 2.03), 0.18, n=24))
    return A


def build_all():
    return [build_ruin(), build_construction(), build_complete(), build_lusu(), build_props()]


# ============================================================ OBJ 导出
def export_obj(assets, out_dir):
    import os
    os.makedirs(out_dir, exist_ok=True)
    for A in assets:
        path = os.path.join(out_dir, A.label + ".obj")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# 楼溯 第1章 白模 v2 %s  单位 m，Y-up\n" % A.label)
            base = 1
            for gname, (mat, vs, fs) in A.groups.items():
                fh.write("o %s\nusemtl %s\n" % (gname, mat))
                for x, y, z in vs:
                    fh.write("v %.4f %.4f %.4f\n" % (x, z, -y))
                for f in fs:
                    fh.write("f " + " ".join(str(i+base) for i in f) + "\n")
                base += len(vs)
        print("写出", path)


# ============================================================ Blender 构建
ROOT = "楼溯_第1章_白模"


def build_blender(assets):
    import bpy
    import bmesh
    from mathutils import Vector

    scene = bpy.context.scene
    for name in (ROOT,):
        old = bpy.data.collections.get(name)
        if old:
            for ob in list(old.all_objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            for c in list(old.children_recursive):
                bpy.data.collections.remove(c)
            bpy.data.collections.remove(old)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)
    root = bpy.data.collections.new(ROOT)
    scene.collection.children.link(root)

    mats = {}
    for k, rgb in MATS.items():
        m = bpy.data.materials.get("白模_" + k) or bpy.data.materials.new("白模_" + k)
        m.diffuse_color = (*rgb, 1.0)
        try:
            m.use_nodes = True
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
                bsdf.inputs["Roughness"].default_value = 0.85
        except Exception:
            pass
        mats[k] = m

    sharp = math.radians(SMOOTH_ANGLE)
    cams = []
    log = ["Blender %s" % bpy.app.version_string]
    for idx, A in enumerate(assets):
        col = bpy.data.collections.new(A.label)
        root.children.link(col)
        empty = bpy.data.objects.new(A.label + "_根", None)
        empty.empty_display_size = 2.0
        empty.location = (idx * ASSET_SPACING, 0, 0)
        col.objects.link(empty)
        for gname, (mat, vs, fs) in A.groups.items():
            me = bpy.data.meshes.new(A.label + "_" + gname)
            me.from_pydata(vs, [], fs)
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            for f in bm.faces:
                f.smooth = True
            for e in bm.edges:
                if not e.is_manifold or e.calc_face_angle(math.pi) > sharp:
                    e.smooth = False
            bm.to_mesh(me); bm.free()
            me.update()
            me.materials.append(mats[mat])
            ob = bpy.data.objects.new(A.label + "_" + gname, me)
            ob.color = (*MATS[mat], 1.0)
            col.objects.link(ob)
            ob.parent = empty

        (x0, y0, z0), (x1, y1, z1) = A.bbox()
        cx, cy, cz = (x0+x1)/2, (y0+y1)/2, (z0+z1)/2
        span = max(x1-x0, y1-y0, z1-z0) * 1.1
        dist = span * 2 + 10
        views = {
            "正视": ((cx, y0-dist, cz), (90, 0, 0)),
            "侧视": ((x1+dist, cy, cz), (90, 0, 90)),
            "后视": ((cx, y1+dist, cz), (90, 0, 180)),
            "顶视": ((cx, cy, z1+dist), (0, 0, 0)),
        }
        for vname, (loc, rot) in views.items():
            cd = bpy.data.cameras.new("CAM_%s_%s" % (A.label, vname))
            cd.type = "ORTHO"; cd.ortho_scale = span; cd.clip_end = dist * 3
            co = bpy.data.objects.new(cd.name, cd)
            col.objects.link(co); co.parent = empty
            co.location = loc
            co.rotation_euler = tuple(math.radians(a) for a in rot)
            cams.append((A.label, vname, co, "ortho"))
        # 3/4 透视（对照概念图首行）
        R = max(x1-x0, y1-y0, z1-z0)
        tgt = Vector((cx, cy, z0 + (z1-z0)*0.42))
        loc = tgt + Vector((-0.62, -1.0, 0.42)).normalized() * R * 2.9
        cd = bpy.data.cameras.new("CAM_%s_透视" % A.label)
        cd.lens = 50; cd.clip_end = R * 20
        co = bpy.data.objects.new(cd.name, cd)
        col.objects.link(co); co.parent = empty
        co.location = loc
        co.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
        cams.append((A.label, "透视", co, "persp"))
        meshes = [o for o in col.all_objects if o.type == "MESH"]
        log.append("%s: %d mesh objects, %d faces" % (A.label, len(meshes), sum(len(o.data.polygons) for o in meshes)))

    try:
        scene.render.engine = "BLENDER_WORKBENCH"
        sh = scene.display.shading
        sh.light = "STUDIO"; sh.color_type = "MATERIAL"
        sh.show_cavity = True; sh.cavity_type = "BOTH"
        sh.show_object_outline = True
        sh.show_shadows = True
        scene.display.shadow_focus = 0.2
        scene.render.film_transparent = True
        scene.display.render_aa = "16"
    except Exception as e:
        log.append("shading setup partial: %r" % (e,))

    if cams:
        scene.camera = cams[0][2]

    if RENDER_VIEWS:
        import os
        os.makedirs(RENDER_DIR, exist_ok=True)
        prev = scene.camera
        for i, (label, vname, co, kind) in enumerate(cams):
            scene.camera = co
            if kind == "persp":
                scene.render.resolution_x, scene.render.resolution_y = 1800, 1100
            else:
                scene.render.resolution_x = scene.render.resolution_y = 1400
            for c in root.children:
                c.hide_render = (c.name != label)
            scene.render.filepath = RENDER_DIR + "%02d_%s_%s.png" % (i, label, vname)
            bpy.ops.render.render(write_still=True)
            log.append("rendered " + scene.render.filepath)
        for c in root.children:
            c.hide_render = False
        scene.camera = prev

    if EXPORT_GLB_DIR:
        import os
        out = EXPORT_GLB_DIR
        os.makedirs(out, exist_ok=True)
        for c in root.children:
            bpy.ops.object.select_all(action="DESELECT")
            for ob in c.objects:
                if ob.type == "MESH":
                    ob.select_set(True)
            bpy.ops.export_scene.gltf(filepath=os.path.join(out, c.name + ".glb"), use_selection=True, export_format="GLB")

    if SAVE_BLEND:
        import os
        os.makedirs(os.path.dirname(SAVE_BLEND), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=SAVE_BLEND)
        log.append("saved " + SAVE_BLEND)
    if LOG_PATH:
        import os
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "w", encoding="utf-8") as fh:
            fh.write("\n".join(log) + "\nOK\n")
    print("《楼·溯》第1章白模 v2 已生成")


if __name__ == "__main__":
    assets = build_all()
    try:
        import bpy  # noqa: F401
    except ImportError:
        bpy = None
    if bpy is not None:
        try:
            build_blender(assets)
        except Exception:
            import os, traceback
            tb = traceback.format_exc()
            print(tb)
            if LOG_PATH:
                os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
                with open(LOG_PATH, "w", encoding="utf-8") as fh:
                    fh.write("FAILED\n" + tb)
            raise
    elif "--obj" in sys.argv:
        export_obj(assets, sys.argv[sys.argv.index("--obj") + 1])
    else:
        for A in assets:
            (a, b) = A.bbox()
            print("%-12s 尺寸 %.1f × %.1f × %.2f m   面数 %d   部件组 %d" %
                  (A.label, b[0]-a[0], b[1]-a[1], b[2]-a[2], A.nfaces(), len(A.groups)))
