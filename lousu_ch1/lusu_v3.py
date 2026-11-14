# -*- coding: utf-8 -*-
"""
《楼·溯》第1章 · 鲁肃 角色模型 v3（布料模拟 + 程序化雕刻）

和 v2 的区别：
  · 衣服不再是硬壳：下裳、外袍（交领右衽、下摆前开）、大袖、蔽膝、绅都在 Blender 里做布料模拟，
    按「下裳 → 外袍 → 大袖/蔽膝/绅」三轮依次垂落到身体上，褶皱由重力与碰撞自然形成；
    模拟完成后加厚（Solidify）+ 细分（Subdivision），衣缘 / 中衣领用面材质区分。
  · 身体用 Skin 修改器 + 细分生成连续的有机体（含五指），同时作为布料碰撞体。
  · 头部：高分辨率头模 + 程序化雕刻（眉弓、眼窝、鼻梁鼻翼、颧骨、唇、下巴、下颌角、颞窝），
    眼球 + 上下眼睑、耳廓、眉、八字须与山羊须。
  · 头发：贴头的发壳带梳理发丝沟、发髻（缠绕发束）、发带、小冠 + 簪。
  · 鞋：细分平滑的翘头履 + 鞋底；佩剑、大带、带銙、玉佩为静态件。
  · 渲染：Cycles 灰模（clay）材质 + 三点布光 + 阴影捕捉地面；另出一张色块版透视图。

运行：Blender 4.2+ / 5.x，Scripting 中运行，或  blender -b -P lusu_v3.py
脚本会新建独立场景「鲁肃_v3」，不影响谯楼场景。布料模拟需 1–3 分钟。
"""
import math
import sys
import time

WORK_DIR = "C:/Users/pjwly/3D Objects/lousu_ch1/"
OUT_DIR = WORK_DIR + "renders_lusu_v3/"
SAVE_BLEND = WORK_DIR + "lusu_v3.blend"
LOG_PATH = WORK_DIR + "lusu_v3_log.txt"
SIM_FRAMES = 90
RENDER = True
SAMPLES = 96

CLAY = {
    "皮肤": (0.80, 0.74, 0.69), "发": (0.30, 0.30, 0.31), "外袍": (0.62, 0.62, 0.63),
    "衣缘": (0.50, 0.46, 0.45), "中衣": (0.82, 0.82, 0.80), "下裳": (0.56, 0.56, 0.57),
    "金属": (0.55, 0.53, 0.50), "玉": (0.75, 0.78, 0.74), "鞋": (0.35, 0.35, 0.36), "鞋底": (0.75, 0.74, 0.72),
    "眼": (0.88, 0.88, 0.86), "身体": (0.80, 0.74, 0.69), "木": (0.45, 0.42, 0.40),
}
PALETTE = {  # 色块版（接近概念图配色，仅作读图参考）
    "皮肤": (0.62, 0.45, 0.35), "发": (0.03, 0.03, 0.03), "外袍": (0.05, 0.045, 0.045),
    "衣缘": (0.32, 0.03, 0.03), "中衣": (0.75, 0.72, 0.66), "下裳": (0.20, 0.03, 0.03),
    "金属": (0.55, 0.40, 0.18), "玉": (0.55, 0.65, 0.55), "鞋": (0.03, 0.03, 0.03), "鞋底": (0.7, 0.68, 0.62),
    "眼": (0.8, 0.8, 0.78), "身体": (0.62, 0.45, 0.35), "木": (0.15, 0.06, 0.04),
}


# ============================================================ 向量工具
def _sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def _mul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def _dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def _norm(a):
    l = math.sqrt(_dot(a, a)) or 1.0
    return (a[0]/l, a[1]/l, a[2]/l)
def _lerp(a, b, t): return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t)
def _smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x-e0)/(e1-e0)))
    return t*t*(3-2*t)


def _rot(v, r):
    x, y, z = v
    rx, ry, rz = (math.radians(a) for a in r)
    y, z = y*math.cos(rx)-z*math.sin(rx), y*math.sin(rx)+z*math.cos(rx)
    x, z = x*math.cos(ry)+z*math.sin(ry), -x*math.sin(ry)+z*math.cos(ry)
    x, y = x*math.cos(rz)-y*math.sin(rz), x*math.sin(rz)+y*math.cos(rz)
    return (x, y, z)


def _ring_faces(m, n, cap=True, closed=True):
    f = []
    cols = n if closed else n-1
    for k in range(m-1):
        a, b = k*n, (k+1)*n
        f += [(a+i, a+(i+1) % n, b+(i+1) % n, b+i) for i in range(cols)]
    if cap and closed:
        f.append(tuple(reversed(range(n))))
        f.append(tuple(range((m-1)*n, m*n)))
    return f


def sweep(pts, ru, rw=None, n=10, cap=True, ref=(0, 0, 1)):
    m = len(pts)
    ru = ru if isinstance(ru, (list, tuple)) else [ru]*m
    rw = ru if rw is None else (rw if isinstance(rw, (list, tuple)) else [rw]*m)
    v = []
    for k, p in enumerate(pts):
        t = _norm(_sub(pts[min(k+1, m-1)], pts[max(k-1, 0)]))
        a = ref if abs(_dot(t, ref)) < 0.99 else ((1, 0, 0) if abs(t[0]) < 0.9 else (0, 1, 0))
        u = _norm(_cross(t, a)); w = _cross(t, u)
        for i in range(n):
            th = 2*math.pi*i/n
            v.append(_add(p, _add(_mul(u, ru[k]*math.cos(th)), _mul(w, rw[k]*math.sin(th)))))
    return v, _ring_faces(m, n, cap)


def box(c, s, rot=(0, 0, 0)):
    hx, hy, hz = s[0]/2, s[1]/2, s[2]/2
    loc = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
           (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    return [_add(c, _rot(p, rot)) for p in loc], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def lathe(rings, n=24, cx=0.0, cy=0.0, cap=True):
    v = []
    for (z, rx, ry, dy) in rings:
        for i in range(n):
            th = 2*math.pi*i/n
            v.append((cx+rx*math.cos(th), cy+dy+ry*math.sin(th), z))
    return v, _ring_faces(len(rings), n, cap)


def ellipsoid(c, r, nu=16, nv=10):
    v = [(c[0], c[1], c[2]-r[2])]
    for j in range(1, nv):
        ph = -math.pi/2 + math.pi*j/nv
        for i in range(nu):
            t = 2*math.pi*i/nu
            v.append((c[0]+r[0]*math.cos(ph)*math.cos(t), c[1]+r[1]*math.cos(ph)*math.sin(t), c[2]+r[2]*math.sin(ph)))
    v.append((c[0], c[1], c[2]+r[2]))
    top = len(v)-1
    f = [(0, 1+(i+1) % nu, 1+i) for i in range(nu)]
    for j in range(nv-2):
        a, b = 1+j*nu, 1+(j+1)*nu
        f += [(a+i, a+(i+1) % nu, b+(i+1) % nu, b+i) for i in range(nu)]
    last = 1+(nv-2)*nu
    f += [(last+i, last+(i+1) % nu, top) for i in range(nu)]
    return v, f


def merge(*geos):
    V, F = [], []
    for v, f in geos:
        o = len(V); V += v; F += [tuple(i+o for i in fc) for fc in f]
    return V, F


# ============================================================ 头部：程序化雕刻
HEAD_C = (0.0, 0.004, 1.655)
HA, HB, HCZ = 0.074, 0.097, 0.116
# (x, z, 幅度, sx, sz)  头部局部坐标（米），正面朝 -Y
FEATS = [
    (0.031, 0.024, 0.0055, 0.022, 0.009), (-0.031, 0.024, 0.0055, 0.022, 0.009),     # 眉弓
    (0.0, 0.020, 0.0030, 0.012, 0.010),                                                 # 眉间
    (0.031, 0.003, -0.0135, 0.0165, 0.0115), (-0.031, 0.003, -0.0135, 0.0165, 0.0115),  # 眼窝
    (0.0, -0.004, 0.0105, 0.0075, 0.020),                                               # 鼻梁
    (0.0, -0.029, 0.0175, 0.0105, 0.0105),                                              # 鼻头
    (0.0135, -0.033, 0.0075, 0.0075, 0.0065), (-0.0135, -0.033, 0.0075, 0.0075, 0.0065),  # 鼻翼
    (0.0, -0.043, -0.0020, 0.006, 0.004),                                               # 人中
    (0.046, -0.010, 0.0075, 0.017, 0.013), (-0.046, -0.010, 0.0075, 0.017, 0.013),      # 颧骨
    (0.043, -0.042, -0.0045, 0.014, 0.016), (-0.043, -0.042, -0.0045, 0.014, 0.016),    # 面颊凹
    (0.0, -0.0495, 0.0060, 0.017, 0.0048),                                              # 上唇
    (0.0, -0.0555, -0.0040, 0.019, 0.0018),                                             # 口缝
    (0.0, -0.0615, 0.0058, 0.015, 0.0052),                                              # 下唇
    (0.0, -0.0705, -0.0030, 0.014, 0.0045),                                             # 颏唇沟
    (0.0, -0.088, 0.0175, 0.021, 0.013),                                                # 下巴
    (0.058, -0.072, 0.0065, 0.013, 0.016), (-0.058, -0.072, 0.0065, 0.013, 0.016),      # 下颌角
    (0.021, -0.041, -0.0022, 0.0045, 0.006), (-0.021, -0.041, -0.0022, 0.0045, 0.006),  # 法令纹
    (0.026, -0.053, -0.0018, 0.004, 0.005), (-0.026, -0.053, -0.0018, 0.004, 0.005),
    (0.060, 0.030, -0.0030, 0.012, 0.016), (-0.060, 0.030, -0.0030, 0.012, 0.016),      # 颞窝
]


def head_local(th, ph, extra=0.0):
    cph = math.cos(ph)
    x = HA*cph*math.cos(th); y = HB*cph*math.sin(th); z = HCZ*math.sin(ph)
    X, Y, Z = x/HA, y/HB, z/HCZ
    if Z < -0.1:
        t = min(1.0, (-0.1-Z)/0.9)
        x *= 1 - 0.32*t*t
        y *= (1 - 0.50*t) if Y > 0 else (1 - 0.06*t)
    if Y > 0 and Z > -0.25:
        y *= 1 + 0.07*(1-abs(Z))
    if Y < 0:
        y *= 0.965
    fr = max(0.0, min(1.0, (-Y-0.2)*1.7))
    d = 0.0
    if fr > 0:
        for (fx, fz, amp, sx, sz) in FEATS:
            d += amp*math.exp(-((x-fx)**2/sx**2 + (z-fz)**2/sz**2))
        d *= fr
    n = _norm((x/HA**2, y/HB**2, z/HCZ**2))
    d += extra
    return (x+n[0]*d, y+n[1]*d, z+n[2]*d), n


def head_mesh(nu=96, nv=72):
    v = []
    _, _ = head_local(0, -math.pi/2)
    p, _ = head_local(0, -math.pi/2); v.append(_add(HEAD_C, p))
    for j in range(1, nv):
        ph = -math.pi/2 + math.pi*j/nv
        for i in range(nu):
            th = 2*math.pi*i/nu
            p, _ = head_local(th, ph); v.append(_add(HEAD_C, p))
    p, _ = head_local(0, math.pi/2); v.append(_add(HEAD_C, p))
    top = len(v)-1
    f = [(0, 1+(i+1) % nu, 1+i) for i in range(nu)]
    for j in range(nv-2):
        a, b = 1+j*nu, 1+(j+1)*nu
        f += [(a+i, a+(i+1) % nu, b+(i+1) % nu, b+i) for i in range(nu)]
    last = 1+(nv-2)*nu
    f += [(last+i, last+(i+1) % nu, top) for i in range(nu)]
    return v, f


_FACE_CACHE = []


def face_pt(x, z, out=0.0):
    """头部正面在局部 (x,z) 处的世界坐标点（向外偏 out）"""
    if not _FACE_CACHE:
        for j in range(1, 160):
            ph = -math.pi/2 + math.pi*j/160
            for i in range(0, 160):
                th = -math.pi + math.pi*i/160   # 前半球
                p, n = head_local(th, ph)
                _FACE_CACHE.append((p, n))
    best = min(_FACE_CACHE, key=lambda q: (q[0][0]-x)**2 + (q[0][2]-z)**2 + (0 if q[0][1] < 0 else 1))
    p, n = best
    return _add(HEAD_C, (x, p[1]-out, z))


def build_head():
    parts = {}
    parts["头"] = ("皮肤", head_mesh(), 1)
    eyes, lids = [], []
    for sx in (-1, 1):
        x = sx*0.031; z = 0.004
        s = face_pt(x, z)
        c = (s[0], s[1]+0.0085, s[2])
        R = 0.0118
        eyes.append(ellipsoid(c, (R, R, R), 16, 12))
        eyes.append(ellipsoid(_add(c, (0, -R*0.82, 0.0005)), (0.0062, 0.0035, 0.0062), 14, 8))
        for e, rr, a0, a1 in ((22, 0.0036, -80, 80), (-24, 0.0022, -72, 72)):
            pts = []
            for k in range(13):
                a = math.radians(a0 + (a1-a0)*k/12)
                ee = math.radians(e) * (1 - 0.35*abs(math.sin(a)))
                pts.append(_add(c, ((R+0.0012)*math.sin(a)*math.cos(ee), -(R+0.0012)*math.cos(a)*math.cos(ee), (R+0.0012)*math.sin(ee))))
            lids.append(sweep(pts, rr, rr*0.8, n=8))
    parts["眼球"] = ("眼", merge(*eyes), 1)
    parts["眼睑"] = ("皮肤", merge(*lids), 1)
    ears = []
    for sx in (-1, 1):
        cy = HEAD_C[1]+0.010; cz = HEAD_C[2]-0.006
        best = None
        for jj in range(200):
            ph = -0.6 + 0.6*jj/200
            for ii in range(-30, 31):
                th = (0 if sx > 0 else math.pi) + math.radians(ii)
                p, _ = head_local(th, ph)
                d = (p[1]-(cy-HEAD_C[1]))**2 + (p[2]-(cz-HEAD_C[2]))**2
                if best is None or d < best[0]:
                    best = (d, p)
        x0 = best[1][0] - sx*0.002
        rim = [(-0.006, 0.027), (0.004, 0.031), (0.013, 0.024), (0.018, 0.008), (0.016, -0.008), (0.010, -0.021),
               (0.002, -0.031), (-0.005, -0.030), (-0.008, -0.022)]
        pts = [(x0 + sx*(0.006 + 0.28*max(0, oy) + 0.05*max(0, -oz)), cy+oy, cz+oz) for oy, oz in rim]
        ears.append(sweep(pts, [0.0035, 0.0045, 0.005, 0.005, 0.005, 0.0045, 0.006, 0.0065, 0.005], [0.006, 0.006, 0.006, 0.006, 0.006, 0.005, 0.006, 0.007, 0.006], n=8))
        ears.append(ellipsoid((x0+sx*0.004, cy+0.006, cz-0.002), (0.0055, 0.0145, 0.025), 12, 10))
    parts["耳"] = ("皮肤", merge(*ears), 1)
    parts["颈"] = ("皮肤", merge(
        lathe([(1.455, 0.060, 0.058, 0.010), (1.50, 0.056, 0.054, 0.010), (1.55, 0.052, 0.050, 0.012), (1.60, 0.048, 0.046, 0.014)], n=24),
        ellipsoid((0, -0.044, 1.52), (0.009, 0.006, 0.012), 10, 8)), 1)
    # 眉
    brows = []
    for sx in (-1, 1):
        pts = []
        for k in range(7):
            t = k/6
            x = sx*(0.012 + 0.040*t); z = 0.024 + 0.006*math.sin(math.pi*t*0.9) - 0.002*t
            pts.append(face_pt(x, z, 0.0025))
        brows.append(sweep(pts, [0.0045, 0.0058, 0.006, 0.0055, 0.0048, 0.004, 0.0025], [0.0026]*7, n=6))
    parts["眉"] = ("发", merge(*brows), 1)
    # 须髯：八字须 + 山羊须 + 唇下须
    beard = []
    for sx in (-1, 1):
        pts = [face_pt(sx*0.004, -0.0445, 0.0025), face_pt(sx*0.016, -0.0475, 0.0028), face_pt(sx*0.026, -0.056, 0.0025), face_pt(sx*0.030, -0.068, 0.002)]
        beard.append(sweep(pts, [0.0035, 0.0048, 0.0042, 0.0018], [0.0022, 0.003, 0.0026, 0.0012], n=8))
    g = [face_pt(0, -0.072, 0.002), face_pt(0, -0.088, 0.004), face_pt(0, -0.100, 0.005)]
    g += [_add(g[-1], (0, 0.007, -0.018)), _add(g[-1], (0, 0.012, -0.036))]
    beard.append(sweep(g, [0.0085, 0.011, 0.0105, 0.0065, 0.0012], [0.0035, 0.005, 0.0055, 0.004, 0.001], n=12))
    beard.append(sweep([face_pt(0, -0.0645, 0.002), face_pt(0, -0.0705, 0.0035)], [0.004, 0.006], [0.0015, 0.002], n=6))
    parts["须髯"] = ("发", merge(*beard), 1)
    return parts


def build_hair():
    parts = {}
    nu, nr = 128, 22
    def hairline(th):
        F = max(0.0, -math.sin(th)); B = max(0.0, math.sin(th))
        return 0.022 + 0.050*F**1.4 - 0.088*B**1.25
    outer, inner = [], []
    for j in range(nr+1):
        ro, ri = [], []
        for i in range(nu):
            th = 2*math.pi*i/nu
            zh = hairline(th)
            ph0 = math.asin(max(-0.99, min(0.99, zh/HCZ)))
            t = j/nr
            ph = ph0 + (math.pi/2*0.995 - ph0)*t
            Z = math.sin(ph)
            groove = 0.0011*(0.5+0.5*math.cos(64*th + 6*t))
            off = (0.0042 + 0.0035*max(0.0, Z) + groove) * _smooth(0.0, 0.22, t) + 0.0013
            po, _ = head_local(th, ph, off)
            pi, _ = head_local(th, ph, -0.0025)
            ro.append(_add(HEAD_C, po)); ri.append(_add(HEAD_C, pi))
        outer.append(ro); inner.append(ri)
    V = [p for r in outer for p in r] + [p for r in inner for p in r]
    off = (nr+1)*nu
    def I(j, i, b=0): return b*off + j*nu + i % nu
    F = []
    for j in range(nr):
        for i in range(nu):
            F.append((I(j, i), I(j, i+1), I(j+1, i+1), I(j+1, i)))
            F.append((I(j+1, i, 1), I(j+1, i+1, 1), I(j, i+1, 1), I(j, i, 1)))
    for i in range(nu):
        F.append((I(0, i, 1), I(0, i+1, 1), I(0, i+1), I(0, i)))
    parts["发_头发"] = ("发", (V, F), 1)
    # 发髻：缠绕的发束
    bc = _add(HEAD_C, (0, 0.016, HCZ+0.022))
    bun = [ellipsoid(bc, (0.031, 0.031, 0.027), 16, 10)]
    for k in range(6):
        a0 = 2*math.pi*k/6
        pts = []
        for s in range(14):
            a = a0 + s*0.42
            r = 0.029 - 0.006*abs(s-6.5)/6.5
            pts.append(_add(bc, (r*math.cos(a), r*math.sin(a), -0.016 + 0.034*s/13)))
        bun.append(sweep(pts, 0.0085, 0.0065, n=8))
    parts["发_发髻"] = ("发", merge(*bun), 1)
    parts["发_发带"] = ("衣缘", lathe([(bc[2]-0.026, 0.026, 0.026, 0.0), (bc[2]-0.016, 0.031, 0.031, 0.0)], n=20, cx=bc[0], cy=bc[1]), 1)
    # 小冠 + 簪
    crown = []
    crown.append(lathe([(bc[2]-0.004, 0.035, 0.044, -0.002), (bc[2]+0.012, 0.037, 0.046, -0.002), (bc[2]+0.02, 0.033, 0.042, -0.002)], n=20, cx=bc[0], cy=bc[1]))
    crown.append(box(_add(bc, (0, -0.030, 0.040)), (0.046, 0.005, 0.052), (-24, 0, 0)))
    crown.append(box(_add(bc, (0, 0.030, 0.046)), (0.046, 0.005, 0.066), (14, 0, 0)))
    for sx in (-1, 1):
        crown.append(sweep([_add(bc, (sx*0.023, -0.036, 0.018)), _add(bc, (sx*0.023, -0.012, 0.062)), _add(bc, (sx*0.023, 0.026, 0.075)), _add(bc, (sx*0.023, 0.040, 0.018))], 0.004, 0.0025, n=6))
    parts["冠"] = ("发", merge(*crown), 1)
    parts["冠_簪"] = ("金属", sweep([_add(bc, (-0.075, 0.0, 0.03)), _add(bc, (0.0, 0.0, 0.03)), _add(bc, (0.08, 0.0, 0.03))], [0.0045, 0.0035, 0.0018], n=8), 1)
    return parts


# ============================================================ 鞋、佩饰、剑
def build_shoes():
    parts = {}
    up, sole = [], []
    for sx in (-1, 1):
        x = sx*0.105
        path = [(x, 0.065, 0.052), (x, 0.035, 0.058), (x, -0.03, 0.054), (x, -0.10, 0.048), (x, -0.16, 0.044), (x, -0.205, 0.046),
                (x, -0.232, 0.062), (x, -0.240, 0.085), (x, -0.236, 0.10)]
        ru = [0.036, 0.044, 0.047, 0.047, 0.042, 0.032, 0.020, 0.012, 0.006]
        rw = [0.040, 0.044, 0.040, 0.034, 0.028, 0.022, 0.016, 0.010, 0.006]
        up.append(sweep(path, ru, rw, n=14))
        # 鞋底：沿足迹轮廓的扁平板
        outline = []
        for k, p in enumerate(path[:7]):
            outline.append((p[0]+ru[k]*1.04, p[1]))
        for k in range(6, -1, -1):
            outline.append((path[k][0]-ru[k]*1.04, path[k][1]))
        n = len(outline)
        V = [(a, b, 0.0) for a, b in outline] + [(a, b, 0.017) for a, b in outline]
        F = [tuple(reversed(range(n))), tuple(range(n, 2*n))] + [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
        sole.append((V, F))
    parts["履"] = ("鞋", merge(*up), 2)
    parts["履_底"] = ("鞋底", merge(*sole), 1)
    return parts


def build_accessories():
    parts = {}
    # 大带（红）+ 革带 + 带銙 + 带扣 + 结
    parts["大带"] = ("衣缘", lathe([(0.982, 0.214, 0.166, -0.006), (0.99, 0.217, 0.169, -0.006), (1.07, 0.217, 0.169, -0.006), (1.078, 0.214, 0.166, -0.006)], n=40), 1)
    kua = []
    for i in range(11):
        th = math.pi + math.pi*(i+0.5)/11
        p = (0.222*math.cos(th), -0.006+0.174*math.sin(th), 1.026)
        kua.append(box(p, (0.026, 0.008, 0.034), (0, 0, math.degrees(th)+90)))
    kua.append(box((0, -0.181, 1.026), (0.07, 0.012, 0.055)))
    kua.append(ellipsoid((0, -0.188, 1.026), (0.018, 0.006, 0.018), 12, 8))
    parts["带銙"] = ("金属", merge(*kua), 1)
    # 玉佩（右胯）
    px, py = -0.175, -0.13
    jade = [sweep([(px, py, 0.99), (px-0.01, py-0.01, 0.90), (px-0.012, py-0.012, 0.83)], 0.003, n=6),
            ellipsoid((px-0.012, py-0.016, 0.815), (0.026, 0.006, 0.026), 16, 8),
            box((px-0.012, py-0.016, 0.765), (0.06, 0.008, 0.016)),
            sweep([(px-0.012, py-0.016, 0.755), (px-0.012, py-0.018, 0.69), (px-0.012, py-0.02, 0.62)], [0.006, 0.014, 0.022], [0.006, 0.012, 0.016], n=10)]
    parts["玉佩"] = ("玉", merge(*jade), 1)
    # 佩剑（左胯，角色左 = +X）
    top = (0.215, -0.165, 1.005); tip = (0.33, 0.20, 0.33)
    dr = _norm(_sub(tip, top))
    sw = [sweep([top, _lerp(top, tip, 0.5), tip], [0.026, 0.024, 0.019], [0.011, 0.010, 0.009], n=10)]
    parts["佩剑_鞘"] = ("木", sw[0], 1)
    fit = [sweep([_lerp(top, tip, 0.18), _lerp(top, tip, 0.22)], 0.032, 0.016, n=10),
           sweep([_lerp(top, tip, 0.94), tip], [0.022, 0.023], [0.012, 0.012], n=10),
           box(top, (0.06, 0.03, 0.03), (0, 0, math.degrees(math.atan2(dr[1], dr[0]))+90))]
    gp = _sub(top, _mul(dr, 0.19))
    fit.append(sweep([_sub(top, _mul(dr, 0.015)), gp], 0.015, n=10))
    c = _sub(gp, _mul(dr, 0.032)); side = _norm(_cross(dr, (1, 0, 0)))
    ring = [_add(c, _add(_mul(dr, -0.032*math.cos(a)), _mul(side, 0.032*math.sin(a)))) for a in [2*math.pi*i/20 for i in range(21)]]
    fit.append(sweep(ring, 0.0065, n=6, cap=False))
    parts["佩剑_饰件"] = ("金属", merge(*fit), 1)
    return parts


# ============================================================ 身体骨架（Skin 修改器）
def body_skeleton():
    """返回 (verts, edges, radii)。手臂约 18° A-pose。"""
    V, R, E = [], [], []
    def add(p, r, parent=None):
        V.append(p); R.append(r)
        i = len(V)-1
        if parent is not None:
            E.append((parent, i))
        return i
    pel = add((0, 0.0, 0.97), (0.165, 0.115))
    sp1 = add((0, 0.0, 1.10), (0.150, 0.105), pel)
    ch = add((0, 0.0, 1.27), (0.165, 0.115), sp1)
    uch = add((0, 0.005, 1.38), (0.150, 0.105), ch)
    nb = add((0, 0.01, 1.45), (0.06, 0.055), uch)
    add((0, 0.012, 1.55), (0.05, 0.048), nb)
    for sx in (-1, 1):
        sh = add((sx*0.185, 0.0, 1.415), (0.06, 0.06), uch)
        el = add((sx*0.29, -0.012, 1.16), (0.045, 0.045), sh)
        wr = add((sx*0.33, -0.055, 0.935), (0.032, 0.026), el)
        palm = add((sx*0.338, -0.068, 0.875), (0.040, 0.016), wr)
        for k, fo in enumerate((-0.018, -0.006, 0.006, 0.018)):
            b = add((sx*(0.342+0.0), -0.07+fo, 0.835), (0.0085, 0.0085), palm)
            m = add((sx*0.344, -0.072+fo*1.05, 0.805 + (0.004 if k in (0, 3) else 0)), (0.0078, 0.0078), b)
            add((sx*0.341, -0.078+fo*1.08, 0.78 + (0.01 if k == 3 else 0)), (0.007, 0.007), m)
        t1 = add((sx*0.326, -0.09, 0.895), (0.011, 0.011), wr)
        add((sx*0.328, -0.103, 0.865), (0.009, 0.009), t1)
        hip = add((sx*0.095, 0.0, 0.93), (0.085, 0.085), pel)
        kn = add((sx*0.105, -0.01, 0.52), (0.058, 0.058), hip)
        an = add((sx*0.105, 0.02, 0.095), (0.04, 0.04), kn)
        add((sx*0.105, -0.11, 0.045), (0.035, 0.025), an)
    return V, E, R


# ============================================================ 服装网格（布料模拟前的初始形）
FRONT = -math.pi/2


def _deg(th):
    d = math.degrees(th)
    while d > 180: d -= 360
    while d <= -180: d += 360
    return d


def garment_tube(rows, nu, folds=0, phase=0.0):
    """rows: [(z, rx, ry, dy, pleat_amp, pinned)] → verts, faces, pin, 每面 (row, col, θ中心)"""
    V, pin = [], []
    for j, (z, rx, ry, dy, amp, pn) in enumerate(rows):
        for i in range(nu):
            th = -math.pi + 2*math.pi*i/nu
            f = 1 + amp*math.sin(folds*th + phase)
            V.append((rx*f*math.cos(th), dy + ry*f*math.sin(th), z))
            if pn:
                pin.append(j*nu+i)
    F, meta = [], []
    for j in range(len(rows)-1):
        for i in range(nu):
            a, b = j*nu, (j+1)*nu
            F.append((a+i, a+(i+1) % nu, b+(i+1) % nu, b+i))
            thc = -math.pi + 2*math.pi*(i+0.5)/nu
            meta.append((j, i, _deg(thc), (rows[j][0]+rows[j+1][0])/2))
    return V, F, pin, meta


def build_skirt():
    rows = [(1.00, 0.196, 0.146, -0.004, 0, True), (0.965, 0.198, 0.148, -0.004, 0, True)]
    n = 22
    for k in range(1, n+1):
        t = k/n
        z = 0.965 + (0.045-0.965)*t
        rows.append((z, 0.20+0.12*t**0.9, 0.15+0.115*t**0.9, 0.012*t, 0.05*t, False))
    V, F, pin, meta = garment_tube(rows, 80, folds=14, phase=0.7)
    mats = []
    last = len(rows)-2
    for (j, i, thd, z) in meta:
        if j >= last-2 or abs(thd+90) < 13:
            mats.append("衣缘")
        else:
            mats.append("下裳")
    return V, F, pin, mats


def _lapel(z):
    """交领右衽：外襟边线的角度（度），从左颈侧斜向右腋下"""
    t = _smooth(1.50, 1.12, z) if False else max(0.0, min(1.0, (1.50-z)/(1.50-1.13)))
    return -52 + (-150+52)*t


ROBE_KEYS = [(1.508, 0.080, 0.074, 0.014), (1.492, 0.125, 0.104, 0.010), (1.468, 0.190, 0.133, 0.004),
             (1.440, 0.245, 0.150, 0.0), (1.400, 0.258, 0.157, 0.0), (1.330, 0.238, 0.160, -0.004),
             (1.245, 0.222, 0.160, -0.005), (1.170, 0.212, 0.158, -0.005), (1.105, 0.207, 0.156, -0.005),
             (1.060, 0.203, 0.153, -0.005), (1.022, 0.201, 0.151, -0.005), (0.985, 0.206, 0.156, -0.005)]


def robe_profile(z):
    K = ROBE_KEYS
    if z >= K[0][0]:
        return K[0][1:]
    for a, b in zip(K, K[1:]):
        if b[0] <= z <= a[0]:
            t = (a[0]-z)/(a[0]-b[0])
            return tuple(a[i]+(b[i]-a[i])*t for i in range(1, 4))
    return K[-1][1:]


def build_robe():
    rows = []
    zs = [1.508, 1.492, 1.468, 1.452, 1.440] + [1.42 - 0.022*k for k in range(int((1.42-1.06)/0.022)+1)] + [1.060, 1.022, 0.985]
    zs = sorted(set(round(z, 4) for z in zs), reverse=True)
    for z in zs:
        rx, ry, dy = robe_profile(z)
        rows.append((z, rx, ry, dy, 0, z >= 1.395 or z <= 1.061))
    waist_row = len(rows)-1
    n = 22
    for k in range(1, n+1):
        t = k/n
        z = 0.985 + (0.085-0.985)*t
        rows.append((z, 0.212+0.20*t**0.85, 0.162+0.165*t**0.85, 0.02*t, 0.075*t, False))
    V, F, pin, meta = garment_tube(rows, 128, folds=9, phase=0.25)
    keepF, mats = [], []
    last = len(rows)-2
    for f, (j, i, thd, z) in zip(F, meta):
        if j >= waist_row and -113 < thd < -67:   # 下摆前开
            continue
        m = "外袍"
        if j <= 1:
            m = "衣缘"
        elif j >= last-2:
            m = "衣缘"
        elif j >= waist_row and (-121 < thd <= -113 or -67 <= thd < -59):
            m = "衣缘"
        keepF.append(f); mats.append(m)
    return V, keepF, pin, mats


def flat_strip(pts, normals, width, nacross=3):
    V, F = [], []
    m = len(pts)
    for k, p in enumerate(pts):
        t = _norm(_sub(pts[min(k+1, m-1)], pts[max(k-1, 0)]))
        s = _norm(_cross(t, normals[k]))
        for a in range(nacross):
            V.append(_add(p, _mul(s, width*(a/(nacross-1)-0.5))))
    for k in range(m-1):
        for a in range(nacross-1):
            i = k*nacross+a
            F.append((i, i+1, i+1+nacross, i+nacross))
    return V, F


def _robe_pt(z, thd, out=0.006):
    rx, ry, dy = robe_profile(z)
    th = math.radians(thd)
    p = (rx*math.cos(th), dy+ry*math.sin(th), z)
    n = _norm((math.cos(th)/rx, math.sin(th)/ry, 0))
    return _add(p, _mul(n, out)), n


def build_collar():
    out = {}
    def line(z0, z1, f, n=36):
        P, N = [], []
        for k in range(n+1):
            z = z0+(z1-z0)*k/n
            p, nn = _robe_pt(z, f(z)); P.append(p); N.append(nn)
        return P, N
    P, N = line(1.50, 1.11, _lapel)
    out["衣缘_交领"] = ("衣缘", flat_strip(P, N, 0.058, 4))
    P, N = line(1.50, 1.34, lambda z: _lapel(z) + 10.5, 20)
    out["中衣_领"] = ("中衣", flat_strip(P, N, 0.030, 3))
    P, N = line(1.50, 1.36, lambda z: -128 + 36*max(0.0, min(1.0, (1.50-z)/0.14)), 18)
    out["衣缘_内襟"] = ("衣缘", flat_strip(P, N, 0.045, 3))
    return out


def build_sleeve(sx):
    S = (sx*0.192, 0.0, 1.455); E = (sx*0.292, -0.012, 1.162); W = (sx*0.332, -0.055, 0.937)
    d = _norm(_sub(W, E))
    End = _add(W, _mul(d, 0.10))
    path = []
    n = 30
    for k in range(n+1):
        t = k/n
        p = _lerp(S, E, t/0.5) if t < 0.5 else _lerp(E, End, (t-0.5)/0.5)
        path.append(p)
    nu = 44
    V, pin, centers = [], [], []
    for k, p in enumerate(path):
        t = k/n
        rl = 0.072 + (0.105-0.072)*t                 # 左右方向（窄）
        rf = 0.080 + (0.215-0.080)*t**1.05           # 前后方向（宽）
        off = (sx*(0.012 + 0.028*t), 0.105*t**1.3, 0.0)   # 袖身向外、向后偏，手臂贴着前沿
        c = _add(p, off); centers.append(c)
        tg = _norm(_sub(path[min(k+1, n)], path[max(k-1, 0)]))
        u = _norm(_cross(tg, (0, 1, 0))); w = _cross(tg, u)
        for i in range(nu):
            th = 2*math.pi*i/nu
            wob = 1 + 0.03*math.sin(6*th)
            V.append(_add(c, _add(_mul(u, rl*wob*math.cos(th)), _mul(w, rf*wob*math.sin(th)))))
            if k <= 1:
                pin.append(k*nu+i)
    F = _ring_faces(n+1, nu, cap=False)
    mats = ["衣缘" if k >= n-2 else "外袍" for k in range(n) for i in range(nu)]
    # 袖口：后半缝合（袂），前半留开口（袪）
    ce = centers[-1]
    V.append(ce); ci = len(V)-1
    base = n*nu
    for i in range(nu):
        a, b = base+i, base+(i+1) % nu
        pa, pb = V[a], V[b]
        if pa[1]-ce[1] > -0.06 and pb[1]-ce[1] > -0.06:
            F.append((a, ci, b)); mats.append("外袍")
    return V, F, pin, mats


def build_bixi():
    """蔽膝：系于大带前、垂于前开处"""
    nx, nz = 10, 18
    V, pin = [], []
    for j in range(nz+1):
        z = 0.99 - 0.50*j/nz
        t = max(0.0, (0.965-z)/0.92)
        yf = -(0.15+0.115*t**0.9) - 0.012*t - 0.03
        for i in range(nx+1):
            x = -0.115 + 0.23*i/nx
            V.append((x, yf - 0.012, z))
            if j == 0:
                pin.append(j*(nx+1)+i)
    F = []
    for j in range(nz):
        for i in range(nx):
            a = j*(nx+1)+i
            F.append((a, a+1, a+nx+2, a+nx+1))
    mats = ["衣缘" if (i in (0, nx-1) or j >= nz-2) else "下裳" for j in range(nz) for i in range(nx)]
    return V, F, pin, mats


def build_shen():
    """绅：大带垂下的两条带端"""
    Vs, Fs, pins, mats = [], [], [], []
    for x0, L in ((0.075, 0.46), (0.118, 0.40)):
        nz = 14
        base = len(Vs)
        for j in range(nz+1):
            z = 0.995 - L*j/nz
            t = max(0.0, (0.965-z)/0.92)
            yf = -(0.15+0.115*t**0.9) - 0.012*t - 0.05
            for i in range(2):
                Vs.append((x0 - 0.02 + 0.04*i, yf - 0.02, z))
                if j == 0:
                    pins.append(base + i)
        for j in range(nz):
            a = base + j*2
            Fs.append((a, a+1, a+3, a+2)); mats.append("衣缘")
    return Vs, Fs, pins, mats


# ============================================================ Blender 部分
def run_blender():
    import bpy
    import bmesh
    from mathutils import Vector

    T0 = time.time()
    log = ["Blender %s" % bpy.app.version_string]
    def L(s):
        log.append("[%6.1fs] %s" % (time.time()-T0, s)); print(log[-1])

    # 独立场景
    sc = bpy.data.scenes.get("鲁肃_v3")
    if sc:
        for ob in list(sc.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(sc)
    sc = bpy.data.scenes.new("鲁肃_v3")
    bpy.context.window.scene = sc
    sc.frame_start = 1; sc.frame_end = SIM_FRAMES
    coll = sc.collection

    mats = {}
    def get_mat(key):
        if key in mats:
            return mats[key]
        m = bpy.data.materials.get("鲁肃v3_" + key) or bpy.data.materials.new("鲁肃v3_" + key)
        rgb = CLAY[key]
        m.diffuse_color = (*rgb, 1)
        try:
            m.use_nodes = True
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = (*rgb, 1)
            b.inputs["Roughness"].default_value = 0.55 if key in ("皮肤", "身体") else (0.35 if key in ("金属", "玉", "眼") else 0.75)
            if key in ("金属",):
                b.inputs["Metallic"].default_value = 0.8
            if key in ("外袍", "衣缘", "中衣", "下裳"):
                for nm in ("Sheen Weight", "Sheen"):
                    if nm in b.inputs:
                        b.inputs[nm].default_value = 0.4
                        break
            if key in ("皮肤", "身体"):
                for nm in ("Subsurface Weight", "Subsurface"):
                    if nm in b.inputs:
                        b.inputs[nm].default_value = 0.15
                        break
        except Exception as e:
            L("mat %s: %r" % (key, e))
        mats[key] = m
        return m

    def make_obj(name, geo, mat_keys, subsurf=1, smooth=True, pin=None):
        V, F = geo
        me = bpy.data.meshes.new(name)
        me.from_pydata(V, [], F)
        me.validate()
        keys = mat_keys if isinstance(mat_keys, list) else [mat_keys]*len(F)
        uniq = []
        for k in keys:
            if k not in uniq:
                uniq.append(k)
        for k in uniq:
            me.materials.append(get_mat(k))
        idx = {k: i for i, k in enumerate(uniq)}
        for p, k in zip(me.polygons, keys):
            p.material_index = idx[k]
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        for p in me.polygons:
            p.use_smooth = smooth
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        if pin is not None:
            vg = ob.vertex_groups.new(name="pin")
            vg.add(pin, 1.0, "REPLACE")
        if subsurf:
            m = ob.modifiers.new("Subdivision", "SUBSURF"); m.levels = subsurf; m.render_levels = subsurf+1 if subsurf < 2 else subsurf
        return ob

    # ---- 身体（Skin）
    V, E, R = body_skeleton()
    me = bpy.data.meshes.new("鲁肃_身体")
    me.from_pydata(V, E, [])
    body = bpy.data.objects.new("鲁肃_身体", me)
    coll.objects.link(body)
    sk = body.modifiers.new("Skin", "SKIN")
    try:
        if len(me.skin_vertices) == 0:
            me.skin_vertices.new()
    except Exception:
        pass
    for i, r in enumerate(R):
        me.skin_vertices[0].data[i].radius = r
    me.skin_vertices[0].data[0].use_root = True
    sk.branch_smoothing = 0.6
    sk.use_smooth_shade = True
    ss = body.modifiers.new("Subdivision", "SUBSURF"); ss.levels = 2; ss.render_levels = 2
    me.materials.append(get_mat("身体"))
    L("body ok")

    # ---- 静态件
    for parts in (build_head(), build_hair(), build_shoes(), build_accessories()):
        for name, (mk, geo, sub) in parts.items():
            make_obj("鲁肃_" + name, geo, mk, subsurf=sub)
    L("static parts ok")

    floor = make_obj("碰撞_地面", ([(-2, -2, 0), (2, -2, 0), (2, 2, 0), (-2, 2, 0)], [(0, 1, 2, 3)]), "鞋底", subsurf=0)
    floor.hide_render = True

    # ---- 布料模拟
    def add_collision(objs):
        for o in objs:
            if "Collision" not in o.modifiers:
                o.modifiers.new("Collision", "COLLISION")
            o.collision.thickness_outer = 0.004
            o.collision.thickness_inner = 0.01
            o.collision.cloth_friction = 8.0
            try:
                o.collision.damping = 0.4
            except Exception:
                pass

    def remove_collision(objs):
        for o in objs:
            m = o.modifiers.get("Collision")
            if m:
                o.modifiers.remove(m)

    def simulate(cloths, colliders, settings, label):
        add_collision(colliders)
        for o in cloths:
            for m in list(o.modifiers):
                o.modifiers.remove(m)
            cm = o.modifiers.new("Cloth", "CLOTH")
            s = cm.settings
            st = settings.get(o.name, settings["default"])
            s.quality = st.get("quality", 7)
            s.mass = st.get("mass", 0.3)
            s.air_damping = st.get("air", 2.0)
            s.tension_stiffness = s.compression_stiffness = st.get("tension", 15.0)
            s.shear_stiffness = st.get("shear", 8.0)
            s.bending_stiffness = st.get("bend", 0.5)
            s.vertex_group_mass = "pin"
            s.pin_stiffness = 1.0
            c = cm.collision_settings
            c.collision_quality = 4
            c.distance_min = st.get("dist", 0.0035)
            c.use_self_collision = st.get("self", False)
            if c.use_self_collision:
                c.self_distance_min = 0.0025
            cm.point_cache.frame_start = 1
            cm.point_cache.frame_end = SIM_FRAMES
        sc.frame_set(1)
        for f in range(1, SIM_FRAMES+1):
            sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        for o in cloths:
            eo = o.evaluated_get(dg)
            nm = bpy.data.meshes.new_from_object(eo, preserve_all_data_layers=True, depsgraph=dg)
            old = o.data
            o.modifiers.clear()
            o.data = nm
            nm.name = o.name
            bpy.data.meshes.remove(old)
        sc.frame_set(1)
        remove_collision(colliders)
        L("sim %s done" % label)

    gV, gF, gP, gM = build_skirt()
    skirt = make_obj("鲁肃_下裳", (gV, gF), gM, subsurf=0, pin=gP)
    gV, gF, gP, gM = build_robe()
    robe = make_obj("鲁肃_外袍", (gV, gF), gM, subsurf=0, pin=gP)
    sleeves = []
    for sx in (1, -1):
        gV, gF, gP, gM = build_sleeve(sx)
        sleeves.append(make_obj("鲁肃_大袖_" + ("左" if sx > 0 else "右"), (gV, gF), gM, subsurf=0, pin=gP))
    gV, gF, gP, gM = build_bixi()
    bixi = make_obj("鲁肃_蔽膝", (gV, gF), gM, subsurf=0, pin=gP)
    gV, gF, gP, gM = build_shen()
    shen = make_obj("鲁肃_绅", (gV, gF), gM, subsurf=0, pin=gP)
    shoes = [o for o in coll.objects if o.name.startswith("鲁肃_履")]

    cfg = {
        "default": dict(quality=7, mass=0.3, air=2.0, tension=15, shear=8, bend=0.5),
        "鲁肃_下裳": dict(quality=7, mass=0.25, air=3.0, tension=15, shear=8, bend=0.4),
        "鲁肃_外袍": dict(quality=8, mass=0.4, air=3.0, tension=20, shear=10, bend=0.9),
        "鲁肃_大袖_左": dict(quality=9, mass=0.22, air=3.0, tension=40, shear=12, bend=0.4, self=True),
        "鲁肃_大袖_右": dict(quality=9, mass=0.22, air=3.0, tension=40, shear=12, bend=0.4, self=True),
        "鲁肃_蔽膝": dict(quality=6, mass=0.4, air=2.0, tension=25, shear=12, bend=2.0),
        "鲁肃_绅": dict(quality=6, mass=0.2, air=2.0, tension=25, shear=12, bend=0.5),
    }
    sim_ok = True
    try:
        simulate([skirt], [body, floor] + shoes, cfg, "下裳")
        simulate([robe], [body, skirt, floor] + shoes, cfg, "外袍")
        for nm, (mk, geo) in build_collar().items():
            co = make_obj("鲁肃_" + nm, geo, mk, subsurf=0)
            sw = co.modifiers.new("Shrinkwrap", "SHRINKWRAP"); sw.target = robe
            sw.wrap_method = "NEAREST_SURFACEPOINT"; sw.wrap_mode = "OUTSIDE_SURFACE"; sw.offset = 0.0045
            so = co.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = 0.003
            su = co.modifiers.new("Subdivision", "SUBSURF"); su.levels = 1; su.render_levels = 2
        sword = [o for o in coll.objects if o.name.startswith("鲁肃_佩剑")]
        simulate(sleeves + [bixi, shen], [body, robe, skirt, floor] + sword, cfg, "大袖/蔽膝/绅")
    except Exception as e:
        import traceback
        sim_ok = False
        L("SIM FAILED: " + traceback.format_exc())

    for o in [skirt, robe, bixi, shen] + sleeves:
        so = o.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = 0.005 if o not in (bixi, shen) else 0.004; so.offset = 0.0
        so.use_rim = True
        su = o.modifiers.new("Subdivision", "SUBSURF"); su.levels = 1; su.render_levels = 2
        for p in o.data.polygons:
            p.use_smooth = True
    L("garments finalized, sim_ok=%s" % sim_ok)

    # ---- 灯光、地面、相机
    def look(ob, target):
        d = Vector(target) - ob.location
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    def add_light(name, loc, energy, size, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; ld.color = color
        lo = bpy.data.objects.new(name, ld); coll.objects.link(lo); lo.location = loc
        look(lo, (0, 0, 1.0))
        return lo
    add_light("主光", (-2.2, -3.0, 3.2), 260, 1.6)
    add_light("补光", (2.8, -2.2, 1.6), 60, 3.0, (0.9, 0.95, 1.0))
    add_light("轮廓光", (1.2, 3.2, 2.8), 280, 1.2)
    world = bpy.data.worlds.new("鲁肃v3_world"); sc.world = world
    try:
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.42, 0.43, 1)
        world.node_tree.nodes["Background"].inputs[1].default_value = 0.25
    except Exception:
        world.color = (0.42, 0.42, 0.43)
    ground = make_obj("地面_阴影", ([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [(0, 1, 2, 3)]), "中衣", subsurf=0)
    try:
        ground.is_shadow_catcher = True
    except Exception:
        pass

    cams = []
    def ortho_cam(name, loc, rot, scale=2.1):
        cd = bpy.data.cameras.new(name); cd.type = "ORTHO"; cd.ortho_scale = scale; cd.clip_end = 100
        co = bpy.data.objects.new(name, cd); coll.objects.link(co)
        co.location = loc; co.rotation_euler = tuple(math.radians(a) for a in rot)
        cd.shift_y = 0.0
        return co
    cams.append(("正视", ortho_cam("CAM_正视", (0, -10, 0.94), (90, 0, 0)), (1000, 1900)))
    cams.append(("侧视", ortho_cam("CAM_侧视", (-10, 0, 0.94), (90, 0, -90)), (1000, 1900)))
    cams.append(("后视", ortho_cam("CAM_后视", (0, 10, 0.94), (90, 0, 180)), (1000, 1900)))
    def persp(name, loc, tgt, lens):
        cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 100
        co = bpy.data.objects.new(name, cd); coll.objects.link(co); co.location = loc; look(co, tgt)
        return co
    cams.append(("透视", persp("CAM_透视", (-1.25, -3.05, 1.40), (0, 0, 0.94), 50), (1200, 1700)))
    cams.append(("面部特写", persp("CAM_面部", (-0.25, -0.62, 1.70), (0, 0, 1.665), 85), (1200, 1200)))
    cams.append(("手袖特写", persp("CAM_手袖", (1.1, -1.6, 1.2), (0.28, 0.0, 0.95), 50), (1200, 1200)))

    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = t
                prefs.get_devices()
                devs = [d for d in prefs.devices if d.type == t]
                if devs:
                    for d in devs:
                        d.use = True
                    sc.cycles.device = "GPU"
                    L("cycles device %s" % t)
                    break
            except Exception:
                continue
    except Exception as e:
        L("gpu setup: %r" % (e,))
    sc.cycles.samples = SAMPLES
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass
    sc.render.film_transparent = True
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
        sc.view_settings.exposure = -0.9
    except Exception:
        pass

    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    if RENDER:
        for name, co, (rx, ry) in cams:
            sc.camera = co
            sc.render.resolution_x, sc.render.resolution_y = rx, ry
            sc.render.filepath = OUT_DIR + "鲁肃_v3_%s.png" % name
            bpy.ops.render.render(write_still=True)
            L("rendered " + name)
        # 色块版
        for k, m in mats.items():
            try:
                m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (*PALETTE[k], 1)
            except Exception:
                pass
        for name in ("透视", "正视"):
            co = [c for c in cams if c[0] == name][0]
            sc.camera = co[1]; sc.render.resolution_x, sc.render.resolution_y = co[2]
            sc.render.filepath = OUT_DIR + "鲁肃_v3_%s_色块.png" % name
            bpy.ops.render.render(write_still=True)
            L("rendered %s 色块" % name)
        for k, m in mats.items():
            try:
                m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (*CLAY[k], 1)
            except Exception:
                pass
    sc.camera = cams[3][1]
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_BLEND)
    L("saved " + SAVE_BLEND)
    with open(LOG_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\nOK\n")


# ============================================================ 无 Blender：导出静态件供预览
def static_parts():
    out = {}
    for d in (build_head(), build_hair(), build_shoes(), build_accessories()):
        out.update(d)
    for name, fn in (("下裳", build_skirt), ("外袍", build_robe), ("蔽膝", build_bixi), ("绅", build_shen)):
        V, F, P, M = fn()
        out["布_" + name] = (M, (V, F), 0)
    for sx in (1, -1):
        V, F, P, M = build_sleeve(sx)
        out["布_大袖%d" % sx] = (M, (V, F), 0)
    return out


if __name__ == "__main__":
    try:
        import bpy  # noqa
        HAVE = True
    except ImportError:
        HAVE = False
    if HAVE:
        try:
            run_blender()
        except Exception:
            import os, traceback
            tb = traceback.format_exc(); print(tb)
            os.makedirs(WORK_DIR, exist_ok=True)
            with open(LOG_PATH, "w", encoding="utf-8") as fh:
                fh.write("FAILED\n" + tb)
            raise
    else:
        p = static_parts()
        print("parts:", len(p), "faces:", sum(len(g[1][1]) for g in p.values()))
