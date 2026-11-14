# -*- coding: utf-8 -*-
"""
《楼·溯》第1章·巴丘瞭望（约210—214年） —— 白模（Greybox）生成脚本

生成内容（单位：米，Z 轴向上，正面朝 -Y，即 Blender 的 Front 视图方向）：
  1. 谯楼_废墟（建立前）
  2. 谯楼_建立中（含竹脚手架、未覆瓦的屋架、三脚吊架）
  3. 谯楼_建成后（台基 + 一层 + 腰檐 + 平座 + 二层 + 歇山顶）
  4. 鲁肃（A-Pose，身高约 1.78 m，含冠 1.86 m）+ 随身物品（佩剑、东吴军旗）

用法：
  · Blender 3.6 / 4.x：打开 Scripting 工作区 → 打开本文件 → Run Script。
    会生成集合「楼溯_第1章_白模」，每个资产一个子集合 + 一个根 Empty，
    并为每个资产创建 正视 / 侧视 / 后视 / 顶视 四台正交相机。重复运行会先清掉旧白模。
  · 无 Blender：python3 lousu_ch1_greybox.py --obj 输出目录   → 导出四个 OBJ（Y-up）。

所有尺寸都在下方 PARAMS 区，改数字后重新运行即可。
"""
import math
import random
import sys

# ============================================================ PARAMS
SEED = 7                      # 废墟碎石随机种子，改它可换一种坍塌形态
ASSET_SPACING = 30.0          # 场景中资产之间的横向间距（米）
WORK_DIR = "C:/Users/pjwly/3D Objects/lousu_ch1/"   # 渲染图、.blend、日志的输出目录
RENDER_VIEWS = True           # True = 运行后自动渲染所有三视图 PNG（Workbench，几秒钟）
RENDER_DIR = WORK_DIR + "renders/"
SAVE_BLEND = WORK_DIR + "lousu_ch1_greybox.blend"   # None = 不保存
LOG_PATH = WORK_DIR + "build_log.txt"
EXPORT_GLB_DIR = None         # 例如 WORK_DIR + "export/"：每个资产导出一个 .glb；None 不导出

# 台基
BASE_W = 12.0                 # 台基顶面边长
BASE_H = 2.4                  # 台基高度
STAIR_W = 3.0                 # 正面踏道宽
STAIR_N = 12                  # 踏步数（BASE_H / STAIR_N = 每级高度）
STAIR_TREAD = 0.30            # 每级进深
# 楼身
G_COL = 3.6                   # 一层外圈柱中心到楼心距离（柱网 7.2 m 见方）
G_H = 3.6                     # 一层柱高
U_COL = 2.6                   # 二层柱中心距离（5.2 m 见方）
U_H = 3.0                     # 二层柱高
ROOF_RIDGE_Z = 12.6           # 正脊高度（台基地面起算）

# 白模分色（灰阶区分材质类别，方便读图）
MATS = {
    "石": (0.55, 0.55, 0.53), "夯土": (0.62, 0.58, 0.52), "木": (0.45, 0.42, 0.39),
    "竹": (0.66, 0.64, 0.55), "瓦": (0.30, 0.31, 0.33), "布": (0.70, 0.70, 0.70),
    "皮肤": (0.80, 0.78, 0.76), "金属": (0.36, 0.37, 0.40), "旗": (0.58, 0.48, 0.46),
}


# ============================================================ 纯 Python 几何核心
def _sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def _mul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def _dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def _norm(a):
    l = math.sqrt(_dot(a, a)) or 1.0
    return (a[0]/l, a[1]/l, a[2]/l)


def _rot(v, r):
    """Euler XYZ（度）"""
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
    """收分方台：底 bw×bd，顶 tw×td，高 h；shift 为顶面平移（做歪斜断柱用）"""
    b = [(-bw/2, -bd/2, 0), (bw/2, -bd/2, 0), (bw/2, bd/2, 0), (-bw/2, bd/2, 0)]
    t = [(-tw/2+shift[0], -td/2+shift[1], h), (tw/2+shift[0], -td/2+shift[1], h),
         (tw/2+shift[0], td/2+shift[1], h), (-tw/2+shift[0], td/2+shift[1], h)]
    v = [_add((cx, cy, z0), _rot(p, (0, 0, rz))) for p in b + t]
    return v, list(_BOX_FACES)


def cyl(p0, p1, r0, r1=None, n=10):
    """两点间圆柱/圆台"""
    r1 = r0 if r1 is None else r1
    d = _norm(_sub(p1, p0))
    a = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
    u = _norm(_cross(d, a)); w = _cross(d, u)
    v = []
    for p, r in ((p0, r0), (p1, r1)):
        for i in range(n):
            t = 2*math.pi*i/n
            v.append(_add(p, _add(_mul(u, r*math.cos(t)), _mul(w, r*math.sin(t)))))
    f = [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
    f.append(tuple(reversed(range(n)))); f.append(tuple(range(n, 2*n)))
    return v, f


def vfrustum(cx, cy, z0, z1, rx0, ry0, rx1, ry1, n=16, top_shift=(0, 0)):
    """竖直椭圆台（袍身、躯干）"""
    v = []
    for z, rx, ry, (sx, sy) in ((z0, rx0, ry0, (0, 0)), (z1, rx1, ry1, top_shift)):
        for i in range(n):
            t = 2*math.pi*i/n
            v.append((cx+sx+rx*math.cos(t), cy+sy+ry*math.sin(t), z))
    f = [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
    f.append(tuple(reversed(range(n)))); f.append(tuple(range(n, 2*n)))
    return v, f


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


def wedge(x0, x1, y_far, y_near, h):
    """三角棱柱：踏道两侧的垂带石"""
    v = [(x0, y_far, 0), (x1, y_far, 0), (x1, y_near, 0), (x0, y_near, 0), (x0, y_near, h), (x1, y_near, h)]
    return v, [(0, 3, 2, 1), (3, 2, 5, 4), (0, 1, 5, 4), (0, 4, 3), (1, 2, 5)]


def _rect_ring(W, D, f):
    cs = [(-W/2, -D/2), (W/2, -D/2), (W/2, D/2), (-W/2, D/2)]
    ring = []
    for k in range(4):
        a, b = cs[k], cs[(k+1) % 4]
        ring += [a, (a[0]+f*(b[0]-a[0]), a[1]+f*(b[1]-a[1])),
                 (a[0]+(1-f)*(b[0]-a[0]), a[1]+(1-f)*(b[1]-a[1]))]
    return ring  # 12 点，角点索引 0,3,6,9


def roof_skirt(W, D, z0, w, d, z1, t=0.25, lift=0.45, f=0.28, c=(0, 0)):
    """带起翘的檐面（腰檐 / 歇山顶下段）。外沿 W×D@z0，内沿 w×d@z1，厚度 t，四角起翘 lift。"""
    o, i = _rect_ring(W, D, f), _rect_ring(w, d, f)
    n = 12
    def L(k): return lift if k % 3 == 0 else 0.0
    v = [(c[0]+o[k][0], c[1]+o[k][1], z0+L(k)) for k in range(n)]          # 0  外上
    v += [(c[0]+i[k][0], c[1]+i[k][1], z1) for k in range(n)]              # 12 内上
    v += [(c[0]+o[k][0], c[1]+o[k][1], z0+L(k)-t) for k in range(n)]      # 24 外下
    v += [(c[0]+i[k][0], c[1]+i[k][1], z1-t) for k in range(n)]            # 36 内下
    fs = []
    for k in range(n):
        m = (k+1) % n
        fs += [(k, m, 12+m, 12+k), (36+k, 36+m, 24+m, 24+k),
               (24+k, 24+m, m, k), (12+k, 12+m, 36+m, 36+k)]
    return v, fs


def gable(w, d, z1, h, c=(0, 0)):
    """歇山顶上段：沿 X 向的两坡 + 山花三角"""
    x, y = c
    v = [(x-w/2, y-d/2, z1), (x+w/2, y-d/2, z1), (x+w/2, y+d/2, z1), (x-w/2, y+d/2, z1),
         (x-w/2, y, z1+h), (x+w/2, y, z1+h)]
    return v, [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 4, 5), (3, 0, 4), (1, 2, 5)]


class Asset:
    def __init__(self, label):
        self.label = label
        self.groups = {}  # 组名 -> [mat, verts, faces]

    def add(self, group, mat, geo):
        g = self.groups.setdefault(group, [mat, [], []])
        off = len(g[1])
        g[1].extend(geo[0])
        g[2].extend(tuple(i+off for i in fc) for fc in geo[1])

    def bbox(self):
        vs = [p for g in self.groups.values() for p in g[1]]
        return ([min(p[k] for p in vs) for k in range(3)], [max(p[k] for p in vs) for k in range(3)])


# ------------------------------------------------------------ 通用构件
def railing(A, g, mat, p0, p1, z, h=1.0, spacing=1.0, post=0.09):
    dx, dy = p1[0]-p0[0], p1[1]-p0[1]
    Lg = math.hypot(dx, dy); ang = math.degrees(math.atan2(dy, dx))
    n = max(1, round(Lg/spacing))
    for k in range(n+1):
        t = k/n
        A.add(g, mat, box((p0[0]+dx*t, p0[1]+dy*t, z+h/2), (post, post, h)))
    mid = ((p0[0]+p1[0])/2, (p0[1]+p1[1])/2)
    A.add(g, mat, box((mid[0], mid[1], z+h-0.04), (Lg, 0.10, 0.08), (0, 0, ang)))
    A.add(g, mat, box((mid[0], mid[1], z+h*0.45), (Lg, 0.06, 0.06), (0, 0, ang)))
    A.add(g, mat, box((mid[0], mid[1], z+0.08), (Lg, 0.08, 0.10), (0, 0, ang)))


def ring_railing(A, g, mat, half, z, h=1.0, gap=None, spacing=1.0):
    """方形一圈栏杆；gap=正面(-Y)开口半宽"""
    c = [(-half, -half), (half, -half), (half, half), (-half, half)]
    for k in range(4):
        a, b = c[k], c[(k+1) % 4]
        if k == 0 and gap:
            railing(A, g, mat, a, (-gap, -half), z, h, spacing)
            railing(A, g, mat, (gap, -half), b, z, h, spacing)
        else:
            railing(A, g, mat, a, b, z, h, spacing)


def stairs(A, g, mat, y_edge, width, n, rise, tread, skip=()):
    for i in range(1, n+1):
        if i in skip:
            continue
        y0 = y_edge-(n-i+1)*tread
        A.add(g, mat, box((0, y0+tread/2, i*rise/2), (width, tread, i*rise)))
    run = n*tread
    for sx in (-1, 1):
        x0 = sx*width/2
        A.add("踏道_垂带", mat, wedge(x0, x0+sx*0.45, y_edge-run, y_edge, n*rise))


def perimeter_cols(half, step_n):
    pts = []
    for i in range(step_n+1):
        t = -half+2*half*i/step_n
        pts += [(t, -half), (t, half)]
        if 0 < i < step_n:
            pts += [(-half, t), (half, t)]
    return pts


def ring_beams(A, g, mat, half, z, s=(0.24, 0.30)):
    for sgn in (-1, 1):
        A.add(g, mat, box((0, sgn*half, z), (2*half+0.3, s[0], s[1])))
        A.add(g, mat, box((sgn*half, 0, z), (s[0], 2*half+0.3, s[1])))


def base_platform(A, mat="石"):
    run = STAIR_N*STAIR_TREAD
    A.add("台基", mat, tbox(0, 0, 0, BASE_W+0.6, BASE_W+0.6, BASE_W, BASE_W, BASE_H))
    A.add("台基", mat, box((0, 0, BASE_H-0.12), (BASE_W+0.2, BASE_W+0.2, 0.24)))   # 压阑石
    return run


def roof_rafters(A, g, mat, eave_half, z_eave, inner_w, inner_d, z_inner, ridge_z, spacing=0.6):
    """建造中：只有椽子与脊檩、没有瓦面"""
    n = int(2*eave_half/spacing)
    for k in range(n+1):
        x = -eave_half+k*spacing
        xi = max(-inner_w/2, min(inner_w/2, x))
        for sgn in (-1, 1):
            A.add(g, mat, cyl((x, sgn*eave_half, z_eave), (xi, sgn*inner_d/2, z_inner), 0.05, n=6))
            if abs(x) <= inner_w/2+1e-6:
                A.add(g, mat, cyl((xi, sgn*inner_d/2, z_inner), (xi, 0, ridge_z), 0.05, n=6))
    for sx in (-1, 1):
        for sy in (-1, 1):  # 角梁
            A.add(g, mat, cyl((sx*(eave_half+0.3), sy*(eave_half+0.3), z_eave+0.35),
                              (sx*inner_w/2, sy*inner_d/2, z_inner), 0.09, n=8))
    A.add(g, mat, box((0, 0, ridge_z), (inner_w+0.4, 0.22, 0.26)))                 # 脊檩
    for sgn in (-1, 1):
        A.add(g, mat, box((0, sgn*inner_d/2, z_inner), (inner_w, 0.2, 0.22)))
        A.add(g, mat, box((sgn*inner_w/2, 0, z_inner), (0.2, inner_d, 0.22)))


def flag(A, x, y, z, pole_h=4.5, banner=(0.9, 1.6)):
    A.add("旗杆", "木", cyl((x, y, z), (x, y, z+pole_h), 0.05, 0.04))
    A.add("旗杆", "金属", cyl((x, y, z+pole_h), (x, y, z+pole_h+0.25), 0.06, 0.0, n=8))
    A.add("旗杆", "木", box((x+banner[0]/2, y, z+pole_h-0.1), (banner[0]+0.1, 0.05, 0.05)))
    A.add("旗幡", "旗", box((x+banner[0]/2+0.03, y, z+pole_h-0.15-banner[1]/2), (banner[0], 0.03, banner[1]), (0, 4, 0)))


# ============================================================ 1. 废墟
def build_ruin():
    A = Asset("谯楼_废墟")
    rng = random.Random(SEED)
    H = 1.1  # 残存台基高度
    # 残台：4×4 块，高低错落，西北角塌落一块
    cell = BASE_W/4
    for i in range(4):
        for j in range(4):
            if (i, j) == (0, 3):
                continue
            cx, cy = -BASE_W/2+cell*(i+0.5), -BASE_W/2+cell*(j+0.5)
            edge = i in (0, 3) or j in (0, 3)
            h = H*rng.uniform(0.6, 0.85 if edge else 1.0)
            A.add("残台", "夯土", tbox(cx, cy, 0, cell+0.15, cell+0.15, cell-(0.35 if edge else 0.02),
                                       cell-(0.35 if edge else 0.02), h, rz=rng.uniform(-2, 2)))
    # 断墙：沿外圈分段，随机高低与缺口；正面中间留出原踏道口
    half = BASE_W/2-0.5
    corners = [(-half, -half), (half, -half), (half, half), (-half, half)]
    for k in range(4):
        a, b = corners[k], corners[(k+1) % 4]
        Lg = math.hypot(b[0]-a[0], b[1]-a[1]); ang = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
        t = 0.0
        while t < Lg:
            seg = rng.uniform(0.9, 1.8); seg = min(seg, Lg-t)
            mid = t+seg/2
            px, py = a[0]+(b[0]-a[0])*mid/Lg, a[1]+(b[1]-a[1])*mid/Lg
            if not (k == 0 and abs(px) < STAIR_W/2+0.3) and rng.random() > 0.22:
                h = rng.choice([0.3, 0.5, 0.7, 0.9, 1.2, 1.5]) * rng.uniform(0.8, 1.1)
                A.add("断墙", "石", tbox(px, py, H*0.7, seg, 0.55, seg*rng.uniform(0.7, 0.95), 0.45, h,
                                         rz=ang+rng.uniform(-3, 3)))
            t += seg
    # 柱础 + 残木柱
    for (x, y) in perimeter_cols(G_COL, 3):
        A.add("柱础", "石", cyl((x, y, H*0.8), (x, y, H*0.8+0.22), 0.34, 0.30, n=10))
        r = rng.random()
        if r < 0.55:
            h = rng.uniform(0.4, 2.2)
            top = (x+rng.uniform(-0.25, 0.25), y+rng.uniform(-0.25, 0.25), H*0.8+0.22+h)
            A.add("残柱_木", "木", cyl((x, y, H*0.8+0.22), top, 0.19, 0.16, n=10))
    # 两根高大的残石柱（概念图中央的双柱）
    for x, h in ((-1.2, 3.4), (1.2, 2.7)):
        A.add("残柱_石", "石", tbox(x, 1.8, H*0.9, 0.75, 0.75, 0.6, 0.6, h, rz=rng.uniform(-4, 4)))
        A.add("残柱_石", "石", box((x+0.1, 1.8, H*0.9+h+0.12), (0.62, 0.5, 0.25), (8, -12, 20)))
    A.add("残柱_石", "石", box((0, 1.8, H*0.9+2.5), (3.0, 0.45, 0.4), (0, 14, 0)))  # 斜搭的残额枋
    # 倒伏的梁木
    for p0, p1, r in (((-4.2, -1.5, H+0.2), (-0.5, 0.8, H+0.1), 0.18),
                      ((2.0, -3.6, H+0.15), (5.2, -2.0, H+0.6), 0.16),
                      ((3.0, 3.8, H+0.2), (6.6, 6.2, 0.3), 0.2),
                      ((-6.8, 2.5, 0.2), (-5.0, 5.5, H+0.4), 0.15)):
        A.add("倒梁", "木", cyl(p0, p1, r, n=8))
    # 残破踏道：缺级、错位
    run = STAIR_N*STAIR_TREAD*(H/BASE_H)
    n = 5
    for i in range(1, n+1):
        if i == 3:
            continue
        y0 = -BASE_W/2-(n-i+1)*run/n
        A.add("残踏道", "石", box((rng.uniform(-0.15, 0.15), y0+run/n/2, i*H/n/2),
                                  (STAIR_W*rng.uniform(0.6, 1.0), run/n, i*H/n), (0, 0, rng.uniform(-6, 6))))
    # 碎石
    for _ in range(70):
        if rng.random() < 0.6:   # 散落在墙脚
            side = rng.randint(0, 3); t = rng.uniform(-half, half); off = rng.uniform(-1.6, 1.6)
            x, y = [(t, -half+off), (half+off, t), (t, half+off), (-half+off, t)][side]
        else:
            x, y = rng.uniform(-half, half), rng.uniform(-half, half)
        z = H*0.75 if (abs(x) < BASE_W/2-0.3 and abs(y) < BASE_W/2-0.3) else 0.0
        s = rng.uniform(0.18, 0.6)
        A.add("碎石", "石", box((x, y, z+s*0.3), (s, s*rng.uniform(0.6, 1.3), s*rng.uniform(0.4, 0.8)),
                               (rng.uniform(-25, 25), rng.uniform(-25, 25), rng.uniform(0, 90))))
    return A


# ============================================================ 2. 建立中
def build_construction():
    A = Asset("谯楼_建立中")
    rng = random.Random(SEED+1)
    run = base_platform(A)
    stairs(A, "踏道", "石", -BASE_W/2-0.3, STAIR_W, STAIR_N, BASE_H/STAIR_N, STAIR_TREAD, skip=range(8, 13))
    # 未完工的踏道上段：搭一块木跳板
    A.add("跳板", "木", box((0, -BASE_W/2-0.3-run*0.18, BASE_H*0.83), (1.2, run*0.45, 0.08), (-28, 0, 0)))
    z0 = BASE_H
    # 一层柱网 + 额枋
    for (x, y) in perimeter_cols(G_COL, 3):
        A.add("柱础", "石", cyl((x, y, z0), (x, y, z0+0.2), 0.32, 0.28))
        A.add("一层柱", "木", cyl((x, y, z0+0.2), (x, y, z0+G_H), 0.2, 0.18, n=12))
    ring_beams(A, "一层额枋", "木", G_COL, z0+G_H-0.2)
    # 平座楼板：只铺了后半
    zf = z0+G_H+0.2
    for k in range(-4, 5):
        A.add("平座搁栅", "木", box((k*0.9, 0, zf), (0.16, 2*G_COL+0.8, 0.22)))
    for k in range(0, 9):
        A.add("楼板", "木", box((0, 0.5+k*0.42, zf+0.15), (2*G_COL+0.6, 0.4, 0.06)))
    # 二层柱 + 额枋
    z1 = zf+0.18
    for (x, y) in perimeter_cols(U_COL, 2):
        A.add("二层柱", "木", cyl((x, y, z1), (x, y, z1+U_H), 0.17, 0.15, n=12))
    ring_beams(A, "二层额枋", "木", U_COL, z1+U_H-0.15)
    ring_beams(A, "二层额枋", "木", U_COL, z1+1.1, s=(0.18, 0.2))
    # 屋架：椽子 + 角梁 + 脊檩，未铺瓦
    roof_rafters(A, "屋架_椽", "木", 4.9, z1+U_H, 5.6, 4.0, z1+U_H+1.5, ROOF_RIDGE_Z)
    # 一层腰檐：只装了后半的椽子
    for k in range(-6, 7):
        x = k*0.8
        A.add("腰檐_椽", "木", cyl((x, 5.5, z0+3.0), (max(-G_COL, min(G_COL, x)), G_COL+0.2, zf-0.1), 0.05, n=6))
    # ---- 竹脚手架
    S = G_COL+1.2
    top = z0+11.0
    xs = [-S, -S/2, 0, S/2, S]
    posts = set()
    for t in xs:
        posts |= {(t, -S), (t, S), (-S, t), (S, t)}
    for (x, y) in posts:
        A.add("脚手架_立杆", "竹", cyl((x, y, z0), (x, y, top+rng.uniform(-0.6, 0.3)), 0.055, n=6))
    for lv in range(1, 7):
        z = z0+lv*1.6
        for sgn in (-1, 1):
            A.add("脚手架_横杆", "竹", cyl((-S-0.3, sgn*S, z), (S+0.3, sgn*S, z), 0.045, n=6))
            A.add("脚手架_横杆", "竹", cyl((sgn*S, -S-0.3, z), (sgn*S, S+0.3, z), 0.045, n=6))
    for sgn in (-1, 1):   # 剪刀撑
        A.add("脚手架_斜撑", "竹", cyl((-S, sgn*S, z0), (S, sgn*S, top-1.0), 0.045, n=6))
        A.add("脚手架_斜撑", "竹", cyl((sgn*S, -S, z0), (sgn*S, S, top-1.0), 0.045, n=6))
    for lv in (2, 4, 6):  # 走道板
        z = z0+lv*1.6+0.06
        for sgn in (-1, 1):
            A.add("脚手架_跳板", "木", box((0, sgn*(S-0.45), z), (2*S, 0.8, 0.05)))
            A.add("脚手架_跳板", "木", box((sgn*(S-0.45), 0, z), (0.8, 2*S-1.6, 0.05)))
    # 正面竹梯
    lx = S/2+0.45
    for sx in (-0.25, 0.25):
        A.add("竹梯", "竹", cyl((lx+sx, -S-1.0, z0), (lx+sx, -S-0.1, z0+6.6), 0.04, n=6))
    for k in range(1, 22):
        t = k/22
        A.add("竹梯", "竹", cyl((lx-0.25, -S-1.0+0.9*t, z0+6.6*t), (lx+0.25, -S-1.0+0.9*t, z0+6.6*t), 0.025, n=5))
    # 地面：三脚吊架 + 木料堆 + 石料
    apex = (BASE_W/2+2.5, -BASE_W/2-1.5, 7.5)
    for g in ((BASE_W/2+0.8, -BASE_W/2-3.8, 0), (BASE_W/2+4.8, -BASE_W/2-2.6, 0), (BASE_W/2+2.2, -BASE_W/2+1.2, 0)):
        A.add("三脚吊架", "木", cyl(g, apex, 0.09, 0.07, n=8))
    A.add("三脚吊架", "木", cyl(apex, (apex[0], apex[1], 2.2), 0.02, n=4))  # 吊绳
    A.add("三脚吊架", "石", box((apex[0], apex[1], 1.9), (0.7, 0.5, 0.5)))
    for k in range(9):
        r = 0.16; row = k//4; col = k % 4 - row*0.5
        A.add("木料堆", "木", cyl((-BASE_W/2-3.8+col*0.34, -3.0, r+row*0.3), (-BASE_W/2-3.8+col*0.34, 2.0, r+row*0.3), r, n=8))
    for k in range(6):
        A.add("石料", "石", box((-BASE_W/2-2.0+(k % 3)*0.75, -BASE_W/2-3.2, 0.25+(k//3)*0.5), (0.7, 0.55, 0.48)))
    flag(A, -BASE_W/2+0.6, -BASE_W/2+0.6, BASE_H, 5.0)
    return A


# ============================================================ 3. 建成后
def build_complete():
    A = Asset("谯楼_建成后")
    run = base_platform(A)
    stairs(A, "踏道", "石", -BASE_W/2-0.3, STAIR_W, STAIR_N, BASE_H/STAIR_N, STAIR_TREAD)
    z0 = BASE_H
    ring_railing(A, "台基栏杆", "木", BASE_W/2-0.25, z0, 0.9, gap=STAIR_W/2)
    # 一层
    for (x, y) in perimeter_cols(G_COL, 3):
        A.add("柱础", "石", cyl((x, y, z0), (x, y, z0+0.2), 0.32, 0.28))
        A.add("一层柱", "木", cyl((x, y, z0+0.2), (x, y, z0+G_H), 0.2, 0.18, n=12))
    ring_beams(A, "一层额枋", "木", G_COL, z0+G_H-0.2)
    sp = 2*G_COL/3
    for sgn in (-1, 1):   # 墙板：两侧、背面封闭；正面中间开门
        A.add("一层墙板", "木", box((sgn*G_COL, 0, z0+G_H/2), (0.14, 2*G_COL, G_H-0.4)))
    A.add("一层墙板", "木", box((0, G_COL, z0+G_H/2), (2*G_COL, 0.14, G_H-0.4)))
    for sgn in (-1, 1):
        A.add("一层墙板", "木", box((sgn*sp, -G_COL, z0+G_H/2), (sp, 0.14, G_H-0.4)))
    A.add("门", "木", box((0, -G_COL+0.08, z0+1.3), (sp-0.4, 0.1, 2.6)))
    A.add("门", "木", box((0, -G_COL+0.08, z0+3.0), (sp-0.4, 0.1, 0.5)))  # 横披窗
    for (x, y) in perimeter_cols(G_COL, 3):  # 斗拱（简化方块）
        A.add("斗拱", "木", box((x, y, z0+G_H+0.05), (0.5, 0.5, 0.3)))
        A.add("斗拱", "木", box((x*1.04, y*1.04, z0+G_H+0.3), (0.7, 0.7, 0.2)))
    # 腰檐
    zw = z0+G_H-0.4
    A.add("腰檐", "瓦", roof_skirt(11.4, 11.4, zw, 7.6, 7.6, zw+0.9, t=0.22, lift=0.4))
    # 平座 + 栏杆
    zf = zw+0.9
    A.add("平座", "木", box((0, 0, zf+0.12), (8.6, 8.6, 0.25)))
    ring_railing(A, "平座栏杆", "木", 4.15, zf+0.25, 1.05, spacing=0.9)
    # 二层
    z1 = zf+0.25
    for (x, y) in perimeter_cols(U_COL, 2):
        A.add("二层柱", "木", cyl((x, y, z1), (x, y, z1+U_H), 0.17, 0.15, n=12))
    ring_beams(A, "二层额枋", "木", U_COL, z1+U_H-0.15)
    for sgn in (-1, 1):
        A.add("二层墙板", "木", box((sgn*U_COL, 0, z1+U_H/2), (0.12, 2*U_COL, U_H-0.3)))
        A.add("二层墙板", "木", box((0, sgn*U_COL, z1+0.55), (2*U_COL, 0.12, 1.1)))       # 槛墙
        A.add("二层窗", "木", box((0, sgn*U_COL, z1+1.1+0.8), (2*U_COL-0.4, 0.08, 1.4)))  # 槛窗
    for (x, y) in perimeter_cols(U_COL, 2):
        A.add("斗拱", "木", box((x, y, z1+U_H+0.05), (0.42, 0.42, 0.26)))
        A.add("斗拱", "木", box((x*1.05, y*1.05, z1+U_H+0.25), (0.6, 0.6, 0.18)))
    # 歇山顶
    ze = z1+U_H+0.25
    zi = ze+1.5
    A.add("屋顶", "瓦", roof_skirt(9.8, 9.8, ze, 5.6, 4.0, zi, t=0.3, lift=0.55))
    A.add("屋顶", "瓦", gable(5.9, 4.3, zi-0.15, ROOF_RIDGE_Z-zi+0.15))
    A.add("屋脊", "瓦", box((0, 0, ROOF_RIDGE_Z+0.12), (6.2, 0.32, 0.36)))
    for sx in (-1, 1):
        A.add("屋脊", "瓦", box((sx*3.0, 0, ROOF_RIDGE_Z+0.5), (0.35, 0.4, 0.9)))   # 鸱吻（占位）
        for sy in (-1, 1):  # 戗脊
            A.add("屋脊", "瓦", cyl((sx*2.9, sy*2.05, zi), (sx*4.95, sy*4.95, ze+0.55+0.15), 0.12, n=6))
    # 旗
    flag(A, -BASE_W/2+0.6, -BASE_W/2+0.6, BASE_H, 5.0)
    flag(A, BASE_W/2-0.6, -BASE_W/2+0.6, BASE_H, 5.0)
    return A


# ============================================================ 4. 鲁肃
def build_lusu():
    A = Asset("鲁肃")
    # 足与袍
    for sx in (-1, 1):
        A.add("鞋", "布", box((sx*0.11, -0.10, 0.045), (0.10, 0.28, 0.09)))
        A.add("鞋", "布", box((sx*0.11, -0.235, 0.09), (0.08, 0.04, 0.05), (20, 0, 0)))  # 翘头
    A.add("袍_下裳", "布", vfrustum(0, 0.02, 0.04, 1.0, 0.40, 0.33, 0.18, 0.13, n=20, top_shift=(0, -0.02)))
    A.add("袍_下裳", "布", vfrustum(0, 0.03, 0.02, 0.06, 0.42, 0.35, 0.41, 0.34, n=20))      # 下摆
    A.add("躯干", "布", vfrustum(0, 0, 1.0, 1.28, 0.18, 0.13, 0.21, 0.135))
    A.add("躯干", "布", vfrustum(0, 0, 1.28, 1.42, 0.21, 0.135, 0.23, 0.13))
    A.add("躯干", "布", vfrustum(0, 0, 1.42, 1.48, 0.23, 0.13, 0.10, 0.08))
    A.add("交领", "布", box((0.03, -0.132, 1.31), (0.05, 0.015, 0.30), (0, 35, 0)))
    A.add("交领", "布", box((-0.03, -0.128, 1.36), (0.04, 0.012, 0.20), (0, -35, 0)))
    A.add("腰带", "布", vfrustum(0, -0.005, 0.97, 1.08, 0.195, 0.145, 0.195, 0.145))
    A.add("腰带", "金属", box((0, -0.15, 1.025), (0.09, 0.02, 0.07)))
    A.add("蔽膝", "布", box((0, -0.16, 0.72), (0.18, 0.02, 0.48), (-6, 0, 0)))
    # 头颈
    A.add("颈", "皮肤", vfrustum(0, 0, 1.46, 1.57, 0.055, 0.055, 0.05, 0.05, n=10))
    A.add("头", "皮肤", sphere((0, 0, 1.665), 0.1, (0.92, 1.0, 1.18)))
    A.add("头", "皮肤", box((0, -0.097, 1.655), (0.026, 0.03, 0.045)))   # 鼻
    A.add("胡须", "布", sphere((0, -0.07, 1.555), 0.042, (0.9, 0.6, 1.4)))
    A.add("发髻", "布", sphere((0, 0.01, 1.795), 0.048))
    A.add("冠", "布", box((0, 0.0, 1.815), (0.065, 0.13, 0.085), (-8, 0, 0)))
    A.add("冠", "金属", cyl((-0.085, 0, 1.82), (0.085, 0, 1.82), 0.007, n=6))      # 簪
    # 手臂（A-pose）+ 大袖
    for sx in (-1, 1):
        sh = (sx*0.21, 0, 1.42)
        d1 = (sx*math.sin(math.radians(18)), 0, -math.cos(math.radians(18)))
        el = _add(sh, _mul(d1, 0.30))
        d2 = _norm((sx*math.sin(math.radians(12)), -0.3, -math.cos(math.radians(12))))
        wr = _add(el, _mul(d2, 0.26))
        A.add("大袖", "布", cyl(sh, wr, 0.075, 0.15, n=12))
        mid = _mul(_add(el, wr), 0.5)
        A.add("大袖", "布", box((mid[0]+sx*0.01, mid[1]+0.02, mid[2]-0.17), (0.09, 0.30, 0.36), (8, sx*-12, 0)))
        A.add("手", "皮肤", sphere(_add(wr, _mul(d2, 0.07)), 0.045, (0.8, 1.0, 1.25)))
    # 佩剑：挂于左胯（角色左侧 = +X）
    top = (0.23, -0.12, 1.0); tip = (0.27, 0.32, 0.22)
    dr = _norm(_sub(tip, top))
    A.add("佩剑", "木", cyl(top, tip, 0.026, 0.02, n=8))                        # 鞘
    A.add("佩剑", "金属", box(top, (0.03, 0.03, 0.11), (60, 0, 0)))            # 格
    A.add("佩剑", "布", cyl(top, _sub(top, _mul(dr, 0.2)), 0.016, n=8))         # 柄
    A.add("佩剑", "金属", sphere(_sub(top, _mul(dr, 0.21)), 0.025))             # 首
    # ---- 随身物品（独立摆放在人物右侧，便于单独出图 / 导出）
    px = 0.9
    A.add("道具_佩剑", "木", cyl((px, 0, 0.0), (px, 0, 0.78), 0.026, 0.02, n=8))
    A.add("道具_佩剑", "金属", box((px, 0, 0.81), (0.11, 0.03, 0.03)))
    A.add("道具_佩剑", "布", cyl((px, 0, 0.82), (px, 0, 1.02), 0.016, n=8))
    A.add("道具_佩剑", "金属", sphere((px, 0, 1.04), 0.025))
    fx = 1.5
    A.add("道具_军旗", "木", cyl((fx, 0, 0), (fx, 0, 2.8), 0.025, n=8))
    A.add("道具_军旗", "金属", cyl((fx, 0, 2.8), (fx, 0, 2.98), 0.035, 0.0, n=8))
    A.add("道具_军旗", "木", box((fx+0.4, 0, 2.68), (0.85, 0.03, 0.03)))
    A.add("道具_军旗", "旗", box((fx+0.42, 0, 2.06), (0.76, 0.02, 1.2)))
    for k in range(3):
        A.add("道具_军旗", "旗", box((fx+0.12+k*0.3, 0, 1.33), (0.12, 0.015, 0.26)))  # 旗尾飘带
    return A


def build_all():
    return [build_ruin(), build_construction(), build_complete(), build_lusu()]


# ============================================================ OBJ 导出（无 Blender 时用）
def export_obj(assets, out_dir):
    import os
    os.makedirs(out_dir, exist_ok=True)
    for A in assets:
        path = os.path.join(out_dir, A.label + ".obj")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# 楼溯 第1章 白模 %s  单位 m，Y-up\n" % A.label)
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

    scene = bpy.context.scene
    old = bpy.data.collections.get(ROOT)
    if old:
        for ob in list(old.all_objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        for c in list(old.children_recursive):
            bpy.data.collections.remove(c)
        bpy.data.collections.remove(old)
    root = bpy.data.collections.new(ROOT)
    scene.collection.children.link(root)

    mats = {}
    for k, rgb in MATS.items():
        m = bpy.data.materials.get("白模_" + k) or bpy.data.materials.new("白模_" + k)
        m.diffuse_color = (*rgb, 1.0)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.8
        mats[k] = m

    cams = []
    for idx, A in enumerate(assets):
        col = bpy.data.collections.new(A.label)
        root.children.link(col)
        empty = bpy.data.objects.new(A.label + "_根", None)
        empty.empty_display_type = "PLAIN_AXES"
        empty.empty_display_size = 2.0
        empty.location = (idx * ASSET_SPACING, 0, 0)
        col.objects.link(empty)
        for gname, (mat, vs, fs) in A.groups.items():
            me = bpy.data.meshes.new(A.label + "_" + gname)
            me.from_pydata(vs, [], fs)
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me); bm.free()
            me.update()
            me.materials.append(mats[mat])
            ob = bpy.data.objects.new(A.label + "_" + gname, me)
            ob.color = (*MATS[mat], 1.0)
            col.objects.link(ob)
            ob.parent = empty

        (x0, y0, z0), (x1, y1, z1) = A.bbox()
        cx, cy, cz = (x0+x1)/2, (y0+y1)/2, (z0+z1)/2
        span = max(x1-x0, y1-y0, z1-z0) * 1.12
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
            col.objects.link(co)
            co.parent = empty
            co.location = loc
            co.rotation_euler = tuple(math.radians(a) for a in rot)
            cams.append((A.label, vname, co))

    # 白模出图设置：Workbench + 物体色 + 描边/腔隙，接近概念图的三视图读感
    try:
        scene.render.engine = "BLENDER_WORKBENCH"
        sh = scene.display.shading
        sh.light = "STUDIO"; sh.color_type = "MATERIAL"
        sh.show_cavity = True; sh.show_object_outline = True
        scene.render.resolution_x = scene.render.resolution_y = 1600
        scene.render.film_transparent = True
    except Exception as e:
        print("出图设置跳过：", e)

    if cams:
        scene.camera = cams[0][2]

    log = ["Blender %s" % bpy.app.version_string]
    for c in root.children:
        meshes = [o for o in c.all_objects if o.type == "MESH"]
        nf = sum(len(o.data.polygons) for o in meshes)
        bad = [o.name for o in meshes if len(o.data.polygons) == 0]
        log.append("%s: %d mesh objects, %d faces, empty=%s" % (c.name, len(meshes), nf, bad))

    if RENDER_VIEWS:
        import os
        os.makedirs(RENDER_DIR, exist_ok=True)
        prev = scene.camera
        for i, (label, vname, co) in enumerate(cams):
            scene.camera = co
            # 渲染时只显示当前资产的集合，避免相邻资产入镜
            for c in root.children:
                c.hide_render = (c.name != label)
            scene.render.filepath = RENDER_DIR + "%02d_%s_%s.png" % (i, label, vname)
            bpy.ops.render.render(write_still=True)
            log.append("rendered " + scene.render.filepath)
        for c in root.children:
            c.hide_render = False
        scene.camera = prev

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

    if EXPORT_GLB_DIR:
        import os
        out = bpy.path.abspath(EXPORT_GLB_DIR)
        os.makedirs(out, exist_ok=True)
        for c in root.children:
            bpy.ops.object.select_all(action="DESELECT")
            for ob in c.objects:
                if ob.type == "MESH":
                    ob.select_set(True)
            bpy.ops.export_scene.gltf(filepath=os.path.join(out, c.name + ".glb"),
                                      use_selection=True, export_format="GLB")

    print("《楼·溯》第1章白模已生成：", [A.label for A in assets])


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
    else:
        if "--obj" in sys.argv:
            export_obj(assets, sys.argv[sys.argv.index("--obj") + 1])
        else:
            for A in assets:
                (a, b) = A.bbox()
                nf = sum(len(g[2]) for g in A.groups.values())
                print("%-10s 尺寸 %.1f × %.1f × %.2f m   面数 %d   部件组 %d" %
                      (A.label, b[0]-a[0], b[1]-a[1], b[2]-a[2], nf, len(A.groups)))
