# -*- coding: utf-8 -*-
"""
《楼·溯》第1章·巴丘瞭望 —— 总场景整合（master_scene.py）

按概念图《巴丘瞭望 - 资产制作方式建议》的层级与位置，把已完成的 Blender 搭建资产
（瞭望楼主体三态 / 城墙与栅栏 / 营地建筑 / 地面建筑·台阶·码头 / 水域与港口结构）
整合进一个总场景，并为尚未生成的 Tripo 资产放置按资产编号命名的占位体。

坐标约定：米；+Z 向上；湖在 -Y 方向（概念图的“远处”），概念图机位在 +Y 侧俯看。
         画面左 = +X（营地、港口），画面右 = -X（城墙与栅栏）。
         湖面 z=0，岸面 1.2，营地/城墙台地 4.0，瞭望楼台地 8.8。

用法（Blender 5.x Python 控制台）：
  exec(compile(open(r'<本文件>', encoding='utf-8').read(), 'master_scene', 'exec'), {'__name__': '__main__'})
"""
import math, os, random, time

BASE = "C:/Users/pjwly/3D Objects/楼溯_资产库/第1章_巴丘瞭望/"
BLD = BASE + "07_Blender搭建/"
OUT = BASE + "08_总场景/"
TOWER_BLEND = "C:/Users/pjwly/3D Objects/lousu_ch1/lousu_ch1_greybox_v2.blend"
LUSU_BLEND = "C:/Users/pjwly/3D Objects/lousu_ch1/lusu_v3.blend"
RENDER = True
SEED = 1101

SRC = {
    "wall": (BLD + "城墙与栅栏/城墙与栅栏_套件.blend",
             ["套件_W01_城墙直段", "套件_W02_城墙转角石台", "套件_W03_城门段", "套件_W04_登城石阶",
              "套件_P01_木栅栏直段", "套件_P02_栅栏门", "套件_P03_石柱墩", "套件_P04_拒马", "套件_人物参照"]),
    "camp": (BLD + "营地建筑/营地建筑_套件.blend",
             ["营地套件_C01_主帅指挥帐", "营地套件_C02_营房长帐", "营地套件_C03_圆帐", "营地套件_C04_军需敞棚",
              "营地套件_C05_旗杆", "营地套件_C06_篝火灶"]),
    "ground": (BLD + "地面建筑与码头/地面建筑与码头_套件.blend",
               ["地码套件_G01_石砌台地", "地码套件_G02_石阶", "地码套件_G03_挡土矮墙", "地码套件_G04_石板路",
                "地码套件_G05_马道坡道", "地码套件_D01_石砌岸壁", "地码套件_D02_木栈桥段", "地码套件_D03_栈桥端头平台",
                "地码套件_D04_系船桩群"]),
    "harbor": (BLD + "水域与港口结构/水域与港口结构_套件.blend",
               ["港口套件_H01_石砌防波堤段", "港口套件_H02_防波堤端头烽火台", "港口套件_H03_水寨木栅", "港口套件_H04_水门",
                "港口套件_H05_修船滑道", "港口套件_H06_浮台", "港口套件_H07_浅滩岸坡", "港口套件_H08_水面块"]),
    "tower": (TOWER_BLEND, ["谯楼_废墟", "谯楼_建立中", "谯楼_建成后"]),
}

# ------------------------------------------------------------------ 地形
TOWER = (0.0, -14.0)
Z_SHORE, Z_CAMP, Z_TOWER = 1.2, 4.0, 8.8
SHORE_Y = -30.0


def ss(t):
    t = max(0.0, min(1.0, t))
    return t*t*(3-2*t)


def _n(x, y):
    return (math.sin(x*0.11 + 1.3)*math.cos(y*0.093 - 0.7) + 0.5*math.sin(x*0.23 - y*0.19 + 2.1))


def base_h(x, y):
    s = y - SHORE_Y
    if s < 0:
        return max(-3.0, -0.4 + 0.35*s)
    if s < 14:
        v = Z_SHORE
    elif s < 20:
        v = Z_SHORE + (Z_CAMP - Z_SHORE)*ss((s-14)/6)
    else:
        v = Z_CAMP
        if y > 34:
            v += (y-34)*0.10 + 0.6*ss((y-34)/10)*_n(x, y)
    if abs(x) > 85 and s > 0:
        v += (abs(x)-85)*0.35*ss(s/20) + 1.5*ss((abs(x)-85)/20)*_n(x, y)
    return v


def terrain_h(x, y):
    h = base_h(x, y)
    r = math.hypot(x-TOWER[0], y-TOWER[1])
    if r < 24:
        p = Z_TOWER if r < 14 else Z_TOWER - (Z_TOWER + 2.0)*ss((r-14)/10)
        h = max(h, p)
    if abs(x) < 8.0 and -1.0 < y < 10.6:          # 登楼石阶下的夯土坡（石阶坐在其上）
        emb = Z_TOWER - 1.2*max(y, 0)/2.52 - 0.6
        w = 1.0 if abs(x) < 2.6 else 1.0 - ss((abs(x)-2.6)/5.4)
        h = max(h, h + (emb - h)*w) if emb > h else h
    return h


# ------------------------------------------------------------------ 几何工具
def box(c, s):
    cx, cy, cz = c; sx, sy, sz = s[0]/2, s[1]/2, s[2]/2
    V = [(cx+a*sx, cy+b*sy, cz+d*sz) for d in (-1, 1) for b in (-1, 1) for a in (-1, 1)]
    F = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return V, F


def cyl(c, r, h, seg=8, r2=None):
    r2 = r if r2 is None else r2
    cx, cy, cz = c
    V = [(cx+r*math.cos(2*math.pi*i/seg), cy+r*math.sin(2*math.pi*i/seg), cz) for i in range(seg)]
    if r2 > 1e-4:
        V += [(cx+r2*math.cos(2*math.pi*i/seg), cy+r2*math.sin(2*math.pi*i/seg), cz+h) for i in range(seg)]
        F = [(i, (i+1) % seg, seg+(i+1) % seg, seg+i) for i in range(seg)]
        F += [tuple(range(seg))[::-1], tuple(range(seg, 2*seg))]
    else:
        V.append((cx, cy, cz+h))
        F = [(i, (i+1) % seg, seg) for i in range(seg)] + [tuple(range(seg))[::-1]]
    return V, F


def blob(c, rx, rz, rng, seg=10, rings=6, jit=0.12):
    cx, cy, cz = c
    V = [(cx, cy, cz-rz)]
    for j in range(1, rings):
        ph = -math.pi/2 + math.pi*j/rings
        for i in range(seg):
            th = 2*math.pi*i/seg
            k = 1 + rng.uniform(-jit, jit)
            V.append((cx+rx*k*math.cos(ph)*math.cos(th), cy+rx*k*math.cos(ph)*math.sin(th), cz+rz*k*math.sin(ph)))
    V.append((cx, cy, cz+rz))
    F = [(0, 1+(i+1) % seg, 1+i) for i in range(seg)]
    for j in range(rings-2):
        a, b = 1+j*seg, 1+(j+1)*seg
        F += [(a+i, a+(i+1) % seg, b+(i+1) % seg, b+i) for i in range(seg)]
    top = len(V)-1; a = 1+(rings-2)*seg
    F += [(a+i, a+(i+1) % seg, top) for i in range(seg)]
    return V, F


def mountain(c, r, h, rng, seg=36, rings=9, rough=0.18):
    cx, cy, cz = c
    ph = [rng.uniform(0, 6.28) for _ in range(4)]
    V, F = [], []
    for j in range(rings):
        t = j/rings
        rr = r*(1-t)
        for i in range(seg):
            th = 2*math.pi*i/seg
            k = 1 + rough*(math.sin(3*th+ph[0])*0.6 + math.sin(5*th+ph[1])*0.4 + math.sin(9*th+ph[2])*0.25) + rng.uniform(-0.05, 0.05)
            z = h*(1-(1-t)**1.7)*(1 + 0.12*math.sin(4*th+ph[3])) if j else 0.0
            V.append((cx+rr*k*math.cos(th), cy+rr*k*math.sin(th), cz+z))
    V.append((cx, cy, cz+h))
    for j in range(rings-1):
        a, b = j*seg, (j+1)*seg
        F += [(a+i, a+(i+1) % seg, b+(i+1) % seg, b+i) for i in range(seg)]
    top = len(V)-1; a = (rings-1)*seg
    F += [(a+i, a+(i+1) % seg, top) for i in range(seg)]
    return V, F


def hull(L, B, D, rng):
    """木船船体：沿 X 的若干站位，每站 4 点（舷顶/舭/舭/舷顶）。"""
    n = 11; V, F = [], []
    for k in range(n):
        t = -1 + 2*k/(n-1)
        b = max(0.06, B/2*(1-abs(t)**2.4))
        zd = D + 0.35*D*abs(t)**2.2
        zb = -0.35*D*(1-abs(t)**3)
        x = L/2*t
        V += [(x, -b, zd), (x, -b*0.45, zb), (x, b*0.45, zb), (x, b, zd)]
    for k in range(n-1):
        a, b_ = 4*k, 4*(k+1)
        F += [(a, b_, b_+1, a+1), (a+1, b_+1, b_+2, a+2), (a+2, b_+2, b_+3, a+3), (a+3, b_+3, b_, a)]
    F += [(0, 1, 2, 3), (4*(n-1)+3, 4*(n-1)+2, 4*(n-1)+1, 4*(n-1))]
    return V, F


class Mesh:
    def __init__(self):
        self.g = {}

    def add(self, mat, VF):
        V, F = VF
        gv, gf = self.g.setdefault(mat, ([], []))
        o = len(gv); gv.extend(V); gf.extend(tuple(i+o for i in f) for f in F)
        return self


COLORS = {
    "草地": (0.36, 0.42, 0.24), "夯土地": (0.52, 0.45, 0.34), "岸泥": (0.45, 0.40, 0.31), "湖水": (0.22, 0.40, 0.50),
    "山近": (0.30, 0.38, 0.26), "山远": (0.42, 0.50, 0.58), "山最远": (0.58, 0.66, 0.74), "云": (0.95, 0.95, 0.96),
    "树冠": (0.24, 0.36, 0.18), "松冠": (0.17, 0.28, 0.17), "黄花": (0.72, 0.62, 0.20), "树干": (0.32, 0.23, 0.15),
    "山石": (0.52, 0.50, 0.46), "船木": (0.42, 0.29, 0.17), "船木深": (0.28, 0.19, 0.11), "帆": (0.72, 0.62, 0.45),
    "红布": (0.55, 0.10, 0.07), "黑布": (0.12, 0.11, 0.11), "木箱": (0.50, 0.36, 0.20), "铁": (0.25, 0.25, 0.26),
    "灰帐": (0.70, 0.68, 0.63), "马": (0.36, 0.24, 0.16), "陶": (0.55, 0.38, 0.25), "火": (1.0, 0.5, 0.15),
}


def run():
    import bpy, bmesh
    from mathutils import Vector, Matrix

    T0 = time.time(); logl = []

    def L(s):
        logl.append("[%5.1fs] %s" % (time.time()-T0, s)); print(logl[-1])

    os.makedirs(OUT + "renders/", exist_ok=True)
    try:
        bpy.ops.wm.read_homefile(use_empty=True, load_ui=False)
    except Exception as e:
        L("read_homefile: %r" % (e,))
    sc = bpy.context.scene
    sc.name = "楼溯_第1章_巴丘瞭望_总场景"
    root = sc.collection
    rng = random.Random(SEED)

    def newcol(name, parent):
        c = bpy.data.collections.new(name); parent.children.link(c); return c

    mats = {}
    for k, rgb in COLORS.items():
        m = bpy.data.materials.new("总场景_" + k); m.diffuse_color = (*rgb, 1)
        try:
            m.use_nodes = True
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = (*rgb, 1)
            b.inputs["Roughness"].default_value = 0.08 if k == "湖水" else 0.9
            if k == "火":
                b.inputs["Emission Color"].default_value = (1.0, 0.45, 0.1, 1); b.inputs["Emission Strength"].default_value = 3.0
        except Exception:
            pass
        mats[k] = m

    def mkobj(name, M, col, smooth=False, loc=(0, 0, 0), rz=0.0):
        me = bpy.data.meshes.new(name); V, F, idx = [], [], []
        for mi, (mat, (gv, gf)) in enumerate(M.g.items()):
            o = len(V); V += gv; F += [tuple(i+o for i in f) for f in gf]; idx += [mi]*len(gf)
            me.materials.append(mats[mat])
        me.from_pydata(V, [], F); me.validate()
        for p, mi in zip(me.polygons, idx):
            p.material_index = mi; p.use_smooth = smooth
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name, me); col.objects.link(ob)
        ob.location = loc; ob.rotation_euler = (0, 0, math.radians(rz))
        return ob

    # ---------------- 层级
    C_ROOT = newcol("楼溯_第1章_巴丘瞭望", root)
    C_BL = newcol("01_Blender直接搭建", C_ROOT)
    C_TW = newcol("01_瞭望楼主体", C_BL)
    C_WL = newcol("02_城墙与栅栏", C_BL)
    C_CP = newcol("03_营地建筑", C_BL)
    C_GD = newcol("04_地面建筑_台阶_码头", C_BL)
    C_HB = newcol("05_水域与港口结构", C_BL)
    C_LS = newcol("06_主角_鲁肃", C_BL)
    C_TR = newcol("02_Tripo生成_占位", C_ROOT)
    C_T = {k: newcol(n, C_TR) for k, n in (("SHP", "01_船只"), ("TNT", "02_营地帐篷_货物"), ("ENV", "03_远景山脉_云层"),
                                           ("VEG", "04_自然植被"), ("CHR", "05_人物_士兵工匠百姓"), ("FLG", "06_旗帜_布幔_木架"),
                                           ("ANM", "07_动物"), ("PRP", "08_场景小道具"))}
    C_TE = newcol("03_地形与水面", C_ROOT)
    C_CAM = newcol("04_相机", C_ROOT)
    C_SRC = newcol("_资产源_套件(不渲染)", root)
    C_SRC_BL = newcol("_源_Blender套件", C_SRC)
    C_SRC_TR = newcol("_源_Tripo占位原型", C_SRC)

    # ---------------- 载入套件集合
    kit = {}
    for key, (blend, names) in SRC.items():
        if not os.path.isfile(blend):
            L("缺少文件 %s" % blend); continue
        with bpy.data.libraries.load(blend, link=False) as (df, dt):
            want = [n for n in names if n in df.collections]
            miss = [n for n in names if n not in df.collections]
            dt.collections = want
        for c in dt.collections:
            if c is None:
                continue
            short = c.name.split("_", 1)[1] if "_" in c.name else c.name
            pid = short.split("_")[0] if key != "tower" else c.name
            if c.name.endswith("人物参照"):
                pid = "FIG"
            kit[pid] = c
            C_SRC_BL.children.link(c)
        L("载入 %-6s %d 个集合%s" % (key, len(want), ("，缺 %s" % miss) if miss else ""))

    # 鲁肃 v3（布料已定型）：取 lusu_v3.blend 中所有“鲁肃_”网格，收进一个集合
    if os.path.isfile(LUSU_BLEND):
        with bpy.data.libraries.load(LUSU_BLEND, link=False) as (df, dt):
            dt.objects = [n for n in df.objects if n.startswith("鲁肃_")]
        cl = bpy.data.collections.new("鲁肃_v3"); C_SRC_BL.children.link(cl)

        def wbox(o):
            mw = o.matrix_basis.copy(); p = o
            while p.parent:
                mw = p.parent.matrix_basis @ p.matrix_parent_inverse @ mw; p = p.parent
            ws = [mw @ Vector(v) for v in o.bound_box]
            return (Vector((min(w.x for w in ws), min(w.y for w in ws), min(w.z for w in ws))),
                                                         Vector((max(w.x for w in ws), max(w.y for w in ws), max(w.z for w in ws))))
        objs = [o for o in dt.objects if o is not None and o.type == "MESH"]
        body = [o for o in objs if "身体" in o.name] or objs
        b0, b1 = wbox(body[0]); bc = (b0 + b1)/2
        for o in objs:
            lo_, hi_ = wbox(o)
            c_ = (lo_ + hi_)/2
            if (Vector((c_.x, c_.y)) - Vector((bc.x, bc.y))).length < 1.5 and abs(c_.z - bc.z) < 1.6 and (hi_ - lo_).length < 3.5:
                cl.objects.link(o)
            else:   # 布料模拟残留的飞点：删掉身体包围盒（外扩 0.6m）以外的顶点后再收入
                bm = bmesh.new(); bm.from_mesh(o.data)
                mw = o.matrix_basis
                lo2, hi2 = b0 - Vector((0.6, 0.6, 0.15)), b1 + Vector((0.6, 0.6, 0.6))
                bad = [v for v in bm.verts if not all(lo2[i] <= (mw @ v.co)[i] <= hi2[i] for i in range(3))]
                bmesh.ops.delete(bm, geom=bad, context="VERTS"); bm.to_mesh(o.data); bm.free()
                cl.objects.link(o)
                L("鲁肃_v3 %s 清理飞点 %d 个" % (o.name, len(bad)))
        kit["鲁肃_v3"] = cl
        L("载入 鲁肃_v3 %d 个网格" % len(cl.objects))

    # 瞭望楼三态 / 鲁肃：以网格包围盒底面中心作为实例原点
    for nm in ("谯楼_废墟", "谯楼_建立中", "谯楼_建成后", "鲁肃_v3"):
        c = kit.get(nm)
        if not c:
            continue
        lo = Vector((1e9, 1e9, 1e9)); hi = -lo
        for o in c.all_objects:
            if o.type != "MESH":
                continue
            mw = o.matrix_basis.copy(); p = o
            while p.parent:                      # 未进场景的对象 matrix_world 未求值，手动沿父链求世界矩阵
                mw = p.parent.matrix_basis @ p.matrix_parent_inverse @ mw; p = p.parent
            for v in o.bound_box:
                w = mw @ Vector(v)
                lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
        c.instance_offset = ((lo.x+hi.x)/2, (lo.y+hi.y)/2, lo.z)
        L("%s 包围盒 %.1f×%.1f×%.1f m" % (nm, hi.x-lo.x, hi.y-lo.y, hi.z-lo.z))

    placed = []

    def inst(pid, loc, rz=0.0, col=None, name=None, z=None, scale=1.0, hide=False):
        c = kit.get(pid) if isinstance(pid, str) else pid
        if c is None:
            return None
        x, y = loc[0], loc[1]
        zz = loc[2] if len(loc) > 2 else (terrain_h(x, y) if z is None else z)
        e = bpy.data.objects.new(name or (pid if isinstance(pid, str) else c.name), None)
        e.instance_type = "COLLECTION"; e.instance_collection = c
        e.location = (x, y, zz); e.rotation_euler = (0, 0, math.radians(rz)); e.scale = (scale,)*3
        e.empty_display_size = 1.0
        (col or C_ROOT).objects.link(e)
        if hide:
            e.hide_viewport = True; e.hide_render = True
        placed.append(((col or C_ROOT).name, e.name, c.name, x, y, zz, rz))
        return e

    # ================================================================ 01 Blender 直接搭建
    # ---- 瞭望楼主体（三态同位，默认显示“建成后”）
    for nm, hide in (("谯楼_建成后", False), ("谯楼_建立中", True), ("谯楼_废墟", True)):
        inst(nm, (TOWER[0], TOWER[1], Z_TOWER), rz=180, col=C_TW, name="瞭望楼_" + nm.split("_")[1], hide=hide)

    # ---- 城墙与栅栏（画面右侧 = -X）
    WY = -6.0
    inst("W02", (-22.0, WY, Z_CAMP), col=C_WL)
    inst("W01", (-27.3, WY, Z_CAMP), col=C_WL)
    inst("W03", (-33.3, WY, Z_CAMP), col=C_WL)
    inst("W01", (-39.3, WY, Z_CAMP), col=C_WL)
    inst("W02", (-44.6, WY, Z_CAMP), col=C_WL)
    inst("W04", (-39.3, WY + 1.7, Z_CAMP), col=C_WL)
    for yy in (-0.7, 5.3, 11.3, 17.3):
        inst("W01", (-44.6, yy, Z_CAMP), rz=-90, col=C_WL)
    inst("W02", (-44.6, 22.6, Z_CAMP), col=C_WL)
    for xx, pid in ((-40.3, "P01"), (-36.3, "P01"), (-32.3, "P01"), (-28.3, "P02"), (-24.3, "P01"), (-20.3, "P01"), (-16.3, "P01")):
        inst(pid, (xx, 22.6, Z_CAMP), col=C_WL)
    inst("P03", (-14.0, 22.6, Z_CAMP), col=C_WL)
    inst("P03", (-19.4, WY, Z_CAMP), col=C_WL)
    for p, r in (((-33.3, -11.5), 0), ((-28.8, -12.2), 8), ((-37.8, -12.2), -8)):
        inst("P04", p, rz=r, col=C_WL)

    # ---- 营地建筑（画面左前 = +X, +Y）
    inst("C01", (30.0, 12.0, Z_CAMP), rz=180, col=C_CP)
    inst("C02", (17.0, 22.0, Z_CAMP), rz=180, col=C_CP)
    inst("C03", (14.5, 8.5, Z_CAMP), col=C_CP)
    inst("C03", (42.0, 4.0, Z_CAMP), rz=30, col=C_CP)
    inst("C04", (30.5, 25.0, Z_CAMP), rz=180, col=C_CP)
    inst("C06", (22.5, 3.5, Z_CAMP), col=C_CP)
    for p in ((24.0, 5.0), (36.5, 5.0), (7.0, 13.0), (-5.5, 1.0), (5.5, 1.0)):
        inst("C05", (p[0], p[1], Z_CAMP if abs(p[0]) > 5 else Z_TOWER), col=C_CP)

    # ---- 地面建筑 / 台阶 / 码头
    for k in range(4):                         # 楼台北侧四跑石阶下到营地
        inst("G02", (0.0, 2.52*k, Z_TOWER - 1.2*(k+1)), rz=180, col=C_GD)
    for xx in (-4.4, 4.4):                     # 石阶两侧挡土矮墙（台地边）
        inst("G03", (xx, 0.4, Z_TOWER - 0.2), col=C_GD)
    for yy in (13.0, 19.0, 25.0):              # 石阶下的营中石板路
        inst("G04", (0.0, yy, Z_CAMP), rz=90, col=C_GD)
    for xx in (6.0, 12.0, 18.0):
        inst("G04", (xx, 16.0, Z_CAMP), col=C_GD)
    inst("G01", (-12.0, 12.0, Z_CAMP), col=C_GD)          # 营前石砌台地（点将台）
    inst("G05", (36.0, -10.0, Z_CAMP), rz=0, col=C_GD)    # 营地→码头马道
    for xx in (24.0, 30.0, 36.0, 42.0, 48.0):
        inst("D01", (xx, SHORE_Y, 0.0), col=C_GD)
    inst("D02", (34.5, SHORE_Y, 0.0), col=C_GD)
    inst("D02", (34.5, SHORE_Y - 6, 0.0), col=C_GD)
    inst("D03", (34.5, SHORE_Y - 12, 0.0), col=C_GD)
    for p in ((27.0, -44.0), (49.5, -50.0), (20.0, -48.0)):
        inst("D04", (p[0], p[1], 0.0), col=C_GD)
    for yy in (-27.0, -21.0):
        inst("G04", (34.5, yy, Z_SHORE), rz=90, col=C_GD)

    # ---- 水域与港口结构（画面左后 = +X, -Y）
    for xx in (54.0, 60.0, 66.0, 72.0, 78.0):
        inst("H07", (xx, SHORE_Y, 0.0), col=C_HB)
    inst("H05", (17.0, SHORE_Y, 0.0), col=C_HB)
    for k in range(4):
        inst("H01", (62.0, SHORE_Y - 3 - 6*k, 0.0), rz=90, col=C_HB)
    inst("H02", (62.0, SHORE_Y - 27.5, 0.0), col=C_HB)
    GX, GY = 44.0, SHORE_Y - 30
    inst("H04", (GX, GY, 0.0), col=C_HB)
    for xx in (GX - 8.6, GX - 14.6, GX - 20.6):
        inst("H03", (xx, GY, 0.0), col=C_HB)
    for yy in (GY + 3.1, GY + 9.1, GY + 15.1, GY + 21.1):
        inst("H03", (GX - 23.6, yy, 0.0), rz=90, col=C_HB)
    for xx in (GX + 8.6, GX + 13.6):
        inst("H03", (xx, GY, 0.0), col=C_HB)
    inst("H06", (48.0, -39.0, 0.0), rz=12, col=C_HB)
    inst("H06", (52.5, -44.0, 0.0), rz=-8, col=C_HB)
    for xx in (24.0, 48.0):
        for yy in (-42.0, -66.0):
            inst("H08", (xx, yy, 0.0), col=C_HB)
    inst("C04", (17.0, -21.5, Z_SHORE), rz=90, col=C_HB, name="岸上_C04_军需敞棚")
    inst("C02", (45.0, -21.0, Z_SHORE), col=C_HB, name="岸上_C02_营房长帐")
    for p in ((31.5, -27.5), (37.5, -27.5), (58.0, -36.0)):
        inst("C05", (p[0], p[1], Z_SHORE), col=C_HB, name="岸上_C05_旗杆")
    L("Blender 搭建实例：%d" % len(placed))

    # ================================================================ 03 地形与水面
    xs = [float(x) for x in range(-170, 171, 2)]
    ys = sorted(set([float(y) for y in range(-64, 98, 1)] + [SHORE_Y - 0.1]))
    nx = len(xs)
    V = [(x, y, terrain_h(x, y)) for y in ys for x in xs]
    F = [(j*nx+i, j*nx+i+1, (j+1)*nx+i+1, (j+1)*nx+i) for j in range(len(ys)-1) for i in range(nx-1)]
    me = bpy.data.meshes.new("地形_巴丘")
    me.from_pydata(V, [], F); me.validate()
    for nm in ("草地", "夯土地", "岸泥"):
        me.materials.append(mats[nm])
    for p in me.polygons:
        c = p.center
        if c.z < Z_SHORE + 0.3 or (c.y < -16 and c.z < 2.0):
            p.material_index = 2
        elif (abs(c.x) < 50 and -12 < c.y < 30 and abs(c.z - Z_CAMP) < 0.05) or math.hypot(c.x, c.y+14) < 14.5:
            p.material_index = 1
        p.use_smooth = True
    terr = bpy.data.objects.new("地形_巴丘", me); C_TE.objects.link(terr)
    wm = bpy.data.meshes.new("湖面_洞庭")
    wm.from_pydata([(-1800, -2200, -0.03), (1800, -2200, -0.03), (1800, 97, -0.03), (-1800, 97, -0.03)], [], [(0, 1, 2, 3)])
    wm.materials.append(mats["湖水"]); C_TE.objects.link(bpy.data.objects.new("湖面_洞庭", wm))
    L("地形 %d 顶点" % len(V))

    # ================================================================ 02 Tripo 占位原型
    proto = {}

    def make_proto(aid, name, M, smooth=False):
        c = bpy.data.collections.new("%s_%s_占位" % (aid, name)); C_SRC_TR.children.link(c)
        mkobj("%s_%s" % (aid, name), M, c, smooth=smooth)
        proto[aid] = c
        return c

    r0 = random.Random(SEED+7)
    # 船只
    M = Mesh().add("船木", hull(16, 4.2, 1.4, r0)).add("船木深", box((1.0, 0, 2.9), (7.5, 3.4, 2.6)))
    M.add("船木深", box((1.0, 0, 4.5), (8.2, 4.0, 0.25))).add("红布", box((1.0, 0, 5.3), (5.0, 3.0, 1.4)))
    M.add("船木深", box((1.0, 0, 6.15), (5.8, 3.6, 0.22)))
    make_proto("CH01-SHP-01", "画舫", M)
    M = Mesh().add("船木", hull(16, 4.4, 1.5, r0))
    for mx, mh in ((-2.5, 13.0), (3.5, 10.0)):
        M.add("船木深", cyl((mx, 0, 1.2), 0.16, mh, 6, 0.1)).add("帆", box((mx+0.6, 0, 1.2+mh*0.55), (3.6, 0.08, mh*0.6)))
    make_proto("CH01-SHP-02", "双桅大帆船", M)
    M = Mesh().add("船木", hull(10, 3.0, 1.1, r0)).add("船木深", cyl((0.5, 0, 0.9), 0.12, 8.5, 6, 0.08))
    M.add("帆", box((1.0, 0, 5.4), (2.6, 0.06, 4.8))).add("船木深", box((-2.6, 0, 1.6), (2.4, 2.2, 1.2)))
    make_proto("CH01-SHP-03", "单桅中帆船", M)
    M = Mesh().add("船木", hull(5, 1.5, 0.55, r0)).add("船木深", box((0, 0, 0.6), (1.2, 1.1, 0.06)))
    make_proto("CH01-SHP-04", "小木舟", M)
    # 帐篷/货物
    M = Mesh().add("红布", cyl((0, 0, 0), 3.2, 3.8, 8, 0.0)).add("灰帐", cyl((0, 0, 0), 3.0, 1.8, 8))
    make_proto("CH01-TNT-01", "红顶主帐", M)
    M = Mesh().add("灰帐", cyl((0, 0, 0), 2.0, 2.8, 4, 0.0))
    make_proto("CH01-TNT-02", "灰白小帐", M)
    M = Mesh().add("灰帐", cyl((-1.3, 0, 0), 1.9, 3.4, 6, 0.0)).add("灰帐", cyl((1.3, 0, 0), 1.9, 3.4, 6, 0.0))
    make_proto("CH01-TNT-03", "双尖顶军帐", M)
    M = Mesh()
    for px in (-1.4, 1.4):
        for py in (-0.6, 0.6):
            M.add("树干", box((px, py, 1.1), (0.14, 0.14, 2.2)))
    M.add("树干", box((0, 0, 0.9), (3.0, 1.4, 0.08))).add("树干", box((0, 0, 2.2), (3.1, 1.5, 0.1)))
    M.add("木箱", box((-0.7, 0, 1.25), (1.0, 0.9, 0.62))).add("木箱", box((0.6, 0, 1.2), (0.8, 0.8, 0.52)))
    make_proto("CH01-TNT-04", "营地货物木架", M)
    # 植被
    rr = random.Random(SEED+9)
    M = Mesh().add("树干", cyl((0, 0, 0), 0.28, 4.0, 6, 0.18)).add("树冠", blob((0, 0, 5.6), 3.0, 2.4, rr))
    M.add("树冠", blob((1.4, 0.6, 4.6), 1.9, 1.5, rr)).add("树冠", blob((-1.3, -0.5, 4.8), 1.8, 1.5, rr))
    make_proto("CH01-VEG-01", "阔叶乔木", M, smooth=True)
    M = Mesh().add("树干", cyl((0, 0, 0), 0.24, 2.5, 6, 0.15))
    for z, r in ((1.8, 2.4), (3.6, 1.9), (5.2, 1.4), (6.6, 0.9)):
        M.add("松冠", cyl((0, 0, z), r, 2.4, 8, 0.0))
    make_proto("CH01-VEG-02", "常绿乔木", M)
    M = Mesh().add("山石", blob((0, 0, 0.5), 1.6, 1.0, rr, jit=0.3)).add("山石", blob((1.3, 0.4, 0.3), 0.9, 0.6, rr, jit=0.3))
    make_proto("CH01-VEG-03", "景观山石", M, smooth=False)
    M = Mesh().add("树冠", blob((0, 0, 0.55), 1.1, 0.7, rr)).add("黄花", blob((0.2, 0.1, 0.95), 0.8, 0.35, rr))
    make_proto("CH01-VEG-04", "黄花灌木", M, smooth=True)
    # 旗帜/木架
    M = Mesh().add("树干", cyl((0, 0, 0), 0.09, 6.0, 6, 0.06)).add("树干", box((0.55, 0, 5.8), (1.2, 0.06, 0.06)))
    M.add("红布", box((0.6, 0, 4.6), (1.1, 0.04, 2.3)))
    make_proto("CH01-FLG-01", "东吴红色军旗", M)
    M = Mesh().add("树干", cyl((0, 0, 0), 0.08, 5.0, 6, 0.05)).add("黑布", box((0.45, 0, 3.7), (0.85, 0.04, 2.4)))
    make_proto("CH01-FLG-02", "黑色旗幡", M)
    M = Mesh()
    for px in (-1.6, 1.6):
        M.add("树干", box((px, 0, 1.2), (0.16, 0.5, 2.4)))
    for z in (0.6, 1.4, 2.2):
        M.add("树干", box((0, 0, z), (3.4, 0.12, 0.12)))
    for k in range(7):
        M.add("铁", box((-1.2 + 0.4*k, 0.12, 1.5), (0.04, 0.04, 2.6)))
    make_proto("CH01-FLG-03", "大型兵器木架", M)
    M = Mesh().add("树干", box((-0.6, 0, 0.7), (0.1, 0.4, 1.4))).add("树干", box((0.6, 0, 0.7), (0.1, 0.4, 1.4)))
    M.add("树干", box((0, 0, 1.0), (1.4, 0.1, 0.1)))
    for k in range(4):
        M.add("铁", box((-0.45 + 0.3*k, 0.1, 0.95), (0.03, 0.03, 1.8)))
    make_proto("CH01-FLG-04", "小型兵器木架", M)
    # 小道具
    make_proto("CH01-PRP-01", "大木箱", Mesh().add("木箱", box((0, 0, 0.45), (1.2, 0.9, 0.9))))
    make_proto("CH01-PRP-02", "铁箍木箱", Mesh().add("木箱", box((0, 0, 0.35), (0.9, 0.7, 0.7))).add("铁", box((0, 0, 0.35), (0.95, 0.06, 0.74))))
    make_proto("CH01-PRP-03", "小木箱", Mesh().add("木箱", box((0, 0, 0.25), (0.6, 0.5, 0.5))))
    make_proto("CH01-PRP-04", "木桶", Mesh().add("木箱", cyl((0, 0, 0), 0.38, 0.95, 10, 0.34)).add("铁", cyl((0, 0, 0.42), 0.4, 0.08, 10)), smooth=True)
    M = Mesh().add("树干", box((-0.9, 0, 1.4), (0.14, 0.14, 2.8))).add("树干", box((0.9, 0, 1.4), (0.14, 0.14, 2.8)))
    M.add("树干", box((0, 0, 2.8), (2.1, 0.16, 0.16))).add("铁", box((0, 0, 2.0), (0.04, 0.04, 1.4))).add("木箱", box((0, 0, 1.1), (0.6, 0.6, 0.5)))
    make_proto("CH01-PRP-05", "木吊架", M)
    make_proto("CH01-PRP-06", "金属罐", Mesh().add("铁", cyl((0, 0, 0), 0.25, 0.55, 10, 0.18)), smooth=True)
    make_proto("CH01-PRP-07", "营地火盆", Mesh().add("铁", cyl((0, 0, 0), 0.12, 0.6, 6, 0.12)).add("铁", cyl((0, 0, 0.6), 0.25, 0.25, 10, 0.5)).add("火", blob((0, 0, 0.9), 0.32, 0.25, rr)))
    # 马
    M = Mesh().add("马", blob((0, 0, 1.35), 0.95, 0.45, rr, jit=0.03)).add("马", box((1.05, 0, 1.75), (0.35, 0.3, 0.8)))
    M.add("马", box((1.35, 0, 2.1), (0.6, 0.26, 0.28)))
    for px in (-0.65, 0.6):
        for py in (-0.2, 0.2):
            M.add("马", box((px, py, 0.5), (0.14, 0.14, 1.0)))
    M.add("红布", box((-0.05, 0, 1.78), (0.6, 0.9, 0.12)))
    make_proto("CH01-ANM-01", "鞍马", M, smooth=False)
    # 人物：用人物参照（1.78m 汉服模型）
    if "FIG" in kit:
        proto["CHR"] = kit["FIG"]

    # ---- 远景山脉 / 近岸山丘 / 湖心岛 / 云层（直接建在场景中）
    rm = random.Random(SEED+3)
    M_far, M_mid, M_isl, M_hill, M_cld = Mesh(), Mesh(), Mesh(), Mesh(), Mesh()
    for k in range(16):
        x = -1100 + k*145 + rm.uniform(-40, 40); y = -1300 + rm.uniform(-150, 150)
        M_far.add("山最远", mountain((x, y, -2), rm.uniform(170, 260), rm.uniform(110, 190), rm))
    for k in range(13):
        x = -700 + k*115 + rm.uniform(-35, 35); y = -720 + rm.uniform(-90, 90)
        M_mid.add("山远", mountain((x, y, -2), rm.uniform(110, 170), rm.uniform(45, 90), rm))
    for k in range(9):
        x = rm.uniform(-320, 360); y = rm.uniform(-420, -170)
        M_isl.add("山近", mountain((x, y, -2), rm.uniform(25, 60), rm.uniform(10, 32), rm, rough=0.25))
    for sx in (-1, 1):
        for k in range(4):
            M_hill.add("山近", mountain((sx*rm.uniform(210, 290), rm.uniform(-60, 110), -1), rm.uniform(70, 110), rm.uniform(30, 60), rm))
    M_hill.add("山近", mountain((-180, -140, -2), 70, 40, rm))
    for k in range(14):
        x = rm.uniform(-1100, 1100); y = rm.uniform(-1400, -700)
        M_cld.add("云", blob((x, y, rm.uniform(180, 300)), rm.uniform(60, 120), rm.uniform(10, 20), rm, seg=12, rings=5, jit=0.25))
    for aid, nm, M, col in (("CH01-ENV-01", "远景主峰山脉", M_far, None), ("CH01-ENV-01", "远景山脉_中景", M_mid, None),
                            ("CH01-ENV-02", "近岸山丘", M_hill, None), ("CH01-ENV-03", "湖心岛群", M_isl, None),
                            ("CH01-ENV-04", "云层", M_cld, None)):
        ob = mkobj("%s_%s_占位" % (aid, nm), M, C_T["ENV"], smooth=True)
        if nm == "云层":
            ob.hide_render = True                # 云层占位只在视口显示，避免灰底与投影条纹

    # ---- Tripo 占位实例布置
    def tp(aid, loc, rz=0.0, cat=None, scale=1.0, z=None):
        c = proto.get(aid if aid in proto else aid[:9])
        return inst(c, loc, rz=rz, col=C_T[cat or aid.split("-")[1]], name=aid + "_占位", z=z, scale=scale)

    # 船只：港内 + 湖面
    for aid, p, r in (("CH01-SHP-04", (40.0, -41.0), 80), ("CH01-SHP-04", (29.0, -39.0), 100), ("CH01-SHP-04", (52.0, -50.0), 20),
                      ("CH01-SHP-03", (27.0, -51.0), 75), ("CH01-SHP-03", (55.0, -38.0), 100), ("CH01-SHP-01", (39.0, -52.5), 0),
                      ("CH01-SHP-04", (18.0, -38.0), 95)):
        tp(aid, p, r, z=0.0)
    rb = random.Random(SEED+5)
    n = 0
    while n < 34:
        x, y = rb.uniform(-260, 330), rb.uniform(-330, -72)
        if -40 < x < 90 and y > -80:
            continue
        aid = rb.choice(("CH01-SHP-02", "CH01-SHP-03", "CH01-SHP-03", "CH01-SHP-04", "CH01-SHP-04", "CH01-SHP-01"))
        tp(aid, (x, y), rb.uniform(0, 360), z=0.0); n += 1

    # 植被：散布在陆地上，避开建筑区
    def free(x, y):
        if math.hypot(x-TOWER[0], y-TOWER[1]) < 17:
            return False
        if -48 < x < -12 and -9 < y < 26:     # 城墙围合
            return False
        if 8 < x < 46 and -4 < y < 30:        # 营地
            return False
        if -4 < x < 22 and -2 < y < 30:
            return False
        if 10 < x < 82 and -34 < y < -12:     # 码头岸
            return False
        if -16 < x < -8 and 6 < y < 18:
            return False
        return terrain_h(x, y) > 1.0
    rv = random.Random(SEED+11); n = 0; tries = 0
    while n < 260 and tries < 6000:
        tries += 1
        x, y = rv.uniform(-160, 160), rv.uniform(-36, 92)
        if not free(x, y):
            continue
        aid = rv.choice(("CH01-VEG-01", "CH01-VEG-01", "CH01-VEG-02", "CH01-VEG-02", "CH01-VEG-04", "CH01-VEG-04", "CH01-VEG-03"))
        tp(aid, (x, y), rv.uniform(0, 360), scale=rv.uniform(0.75, 1.3), z=terrain_h(x, y) - 0.1); n += 1
    for k in range(18):                                       # 楼台崖边的树与山石
        a = rv.uniform(math.radians(200), math.radians(340)); r = rv.uniform(15.5, 19)
        x, y = TOWER[0] + r*math.cos(a), TOWER[1] + r*math.sin(a)
        tp(rv.choice(("CH01-VEG-02", "CH01-VEG-01", "CH01-VEG-03")), (x, y), rv.uniform(0, 360), scale=rv.uniform(0.7, 1.1), z=terrain_h(x, y) - 0.2)

    # 营地帐篷/货物（Tripo）
    for aid, p, r in (("CH01-TNT-02", (38.0, 18.0), 0), ("CH01-TNT-02", (41.0, 12.0), 20), ("CH01-TNT-03", (21.0, 12.0), 90),
                      ("CH01-TNT-01", (8.0, 24.0), 0), ("CH01-TNT-04", (25.0, 25.5), 0), ("CH01-TNT-04", (24.0, -21.0), 90),
                      ("CH01-TNT-02", (-30.0, 12.0), 0), ("CH01-TNT-03", (-22.0, 16.0), 0), ("CH01-TNT-02", (-36.0, 4.0), 30)):
        tp(aid, p, r, cat="TNT", z=Z_CAMP if p[1] > -12 else Z_SHORE)
    # 旗帜/木架
    for aid, p, r, z in (("CH01-FLG-01", (-3.0, -3.0), 0, Z_TOWER), ("CH01-FLG-01", (3.0, -3.0), 0, Z_TOWER),
                         ("CH01-FLG-01", (-22.0, -6.0), 0, Z_CAMP + 6.4), ("CH01-FLG-01", (-44.6, -6.0), 0, Z_CAMP + 6.4),
                         ("CH01-FLG-01", (-44.6, 22.6), 0, Z_CAMP + 6.4), ("CH01-FLG-02", (-30.0, -2.5), 0, Z_CAMP),
                         ("CH01-FLG-02", (26.0, 19.0), 0, Z_CAMP), ("CH01-FLG-03", (-27.0, 6.0), 0, Z_CAMP),
                         ("CH01-FLG-04", (-34.0, 8.0), 90, Z_CAMP), ("CH01-FLG-03", (36.0, 20.5), 0, Z_CAMP),
                         ("CH01-FLG-01", (-12.0, 7.5), 0, Z_CAMP), ("CH01-FLG-01", (-12.0, 16.5), 0, Z_CAMP)):
        tp(aid, p, r, cat="FLG", z=z)
    # 小道具
    rp = random.Random(SEED+13)
    for cx, cy, z0, k in ((27.0, 22.5, Z_CAMP, 8), (20.0, -24.5, Z_SHORE, 9), (40.0, -25.0, Z_SHORE, 7), (-32.0, 0.5, Z_CAMP, 5), (6.0, -4.0, Z_TOWER, 4)):
        for i in range(k):
            aid = rp.choice(("CH01-PRP-01", "CH01-PRP-02", "CH01-PRP-03", "CH01-PRP-04", "CH01-PRP-04", "CH01-PRP-06"))
            tp(aid, (cx + rp.uniform(-2.5, 2.5), cy + rp.uniform(-1.6, 1.6)), rp.uniform(0, 360), cat="PRP", z=z0)
    tp("CH01-PRP-05", (28.0, -24.0), 0, cat="PRP", z=Z_SHORE)
    tp("CH01-PRP-05", (8.0, 3.0), 90, cat="PRP", z=Z_CAMP)
    for p in ((-31.0, -3.5), (-35.6, -3.5), (33.0, 4.0), (6.0, -9.0)):
        tp("CH01-PRP-07", p, 0, cat="PRP", z=Z_CAMP if p[1] > -6 else Z_TOWER)
    # 马
    for p, r in (((44.0, 22.0), 90), ((42.0, 24.5), 100), ((-16.0, 3.0), 200), ((22.0, -18.0), 10)):
        tp("CH01-ANM-01", p, r, cat="ANM", z=Z_CAMP if p[1] > -12 else Z_SHORE)
    # 人物（1.78m 汉服人物参照代替各类人物）
    rc = random.Random(SEED+17)
    groups = (((-4.5, -3.5), Z_TOWER, 3), ((-33.3, -9.5), None, 4), ((-33.3, -2.0), Z_CAMP, 3), ((30.0, 4.0), Z_CAMP, 6),
              ((22.0, 6.0), Z_CAMP, 4), ((34.5, -38.0), 1.25, 4), ((30.0, -25.0), Z_SHORE, 6), ((18.0, -26.0), Z_SHORE, 3),
              ((0.0, 14.0), Z_CAMP, 3), ((-12.0, 12.0), Z_CAMP + 1.2, 2), ((62.0, -50.0), Z_SHORE, 2), ((-44.6, 10.0), Z_CAMP + 4.8, 2))
    for (cx, cy), z0, k in groups:
        for i in range(k):
            x, y = cx + rc.uniform(-2.2, 2.2), cy + rc.uniform(-1.6, 1.6)
            tp("CHR", (x, y), rc.uniform(0, 360), cat="CHR", z=z0 if z0 is not None else terrain_h(x, y))
    if "鲁肃_v3" in kit:
        inst("鲁肃_v3", (1.6, -3.2, Z_TOWER), rz=200, col=C_LS, name="鲁肃_v3_主角")
    else:
        inst(proto.get("CHR"), (1.6, -3.2, Z_TOWER), rz=200, col=C_LS, name="鲁肃_主角位(人物参照)")
    L("占位实例累计：%d" % len(placed))

    # ---- 源集合不参与渲染
    vl = sc.view_layers[0]
    vl.layer_collection.children[C_SRC.name].exclude = True

    # ================================================================ 04 相机 + 渲染
    W = bpy.data.worlds.new("总场景_天空"); W.color = (0.66, 0.76, 0.86); sc.world = W
    cams = []
    for nm, loc, tgt, lens in (("01_概念图视角_场景总览", (-30.0, 88.0, 46.0), (14.0, -22.0, 6.0), 24),
                               ("02_鸟瞰_布局总图", (14.0, 38.0, 128.0), (14.0, -10.0, 0.0), 28),
                               ("03_瞭望楼近景", (14.0, 22.0, 16.0), (0.0, -14.0, 17.0), 30),
                               ("04_远景视角_湖上望楼", (-48.0, -118.0, 16.0), (10.0, -14.0, 11.0), 38),
                               ("05_港口与码头", (8.0, -8.0, 22.0), (42.0, -45.0, 0.0), 26),
                               ("06_营地与城墙", (8.0, 52.0, 18.0), (-10.0, 6.0, 4.0), 26),
                               ("07_鲁肃与瞭望楼", (4.2, 4.2, 10.6), (0.8, -4.5, 11.6), 30)):
        cd = bpy.data.cameras.new("CAM_" + nm); cd.lens = lens; cd.clip_start = 0.5; cd.clip_end = 4000
        co = bpy.data.objects.new(cd.name, cd); C_CAM.objects.link(co); co.location = loc
        co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        cams.append((nm, co))

    sc.render.engine = "BLENDER_WORKBENCH"
    try:
        sh = sc.display.shading
        sh.light = "STUDIO"; sh.color_type = "MATERIAL"
        sh.show_cavity = True; sh.cavity_type = "BOTH"; sh.show_object_outline = True; sh.show_shadows = True
        sc.display.shadow_focus = 0.1; sc.display.light_direction = (0.35, 0.45, 0.82); sc.display.render_aa = "16"
        sh.background_type = "WORLD"
    except Exception as e:
        L("shading %r" % (e,))
    sc.render.film_transparent = False
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    if RENDER:
        for nm, co in cams:
            sc.camera = co
            sc.render.filepath = OUT + "renders/%s.png" % nm
            bpy.ops.render.render(write_still=True)
        L("渲染 %d 张" % len(cams))
    sc.camera = cams[0][1]

    # ---- 布局表
    with open(OUT + "布局表.csv", "w", encoding="utf-8-sig") as fh:
        fh.write("层级集合,实例名,源集合,x,y,z,rz\n")
        for row in placed:
            fh.write("%s,%s,%s,%.2f,%.2f,%.2f,%.0f\n" % row)
    try:
        bpy.ops.file.pack_all()
    except Exception as e:
        L("pack_all %r" % (e,))
    bpy.ops.wm.save_as_mainfile(filepath=OUT + "楼溯_第1章_巴丘瞭望_总场景.blend", compress=True)
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
        print("terrain sample", terrain_h(0, -14), terrain_h(0, 5), terrain_h(30, 12), terrain_h(40, -40), terrain_h(-33, -12))
