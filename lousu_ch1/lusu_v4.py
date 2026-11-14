# -*- coding: utf-8 -*-
"""
《楼·溯》第1章 · 鲁肃 v4 —— MPFB(MakeHuman) 写实底模 + 布料模拟

流程：
  1. MPFB 生成写实人体底模：男性、约 40 岁、东亚、偏结实；叠加脸部细节 target
     （下颌、下巴、颧骨、头部年龄感、眉位等）。
  2. 加 MPFB 内置 default 骨骼，把双臂摆成自然下垂（约 20°），烘焙为静态身体网格；
     原始 MPFB 人体与骨骼保留在隐藏集合「鲁肃_v4_MPFB源」里，可回去改参数 / 重新摆姿势。
  3. 服装按身体逐层截面自动放量（不与身体初始相交），三轮布料模拟：下裳 → 外袍 → 大袖/蔽膝/绅；
     交领用 Shrinkwrap 贴合模拟后的外袍。
  4. 头发：从底模头部取发区生成发壳（细分 + 发丝沟置换 + 加厚），发髻、发带、小冠、簪；
     眉、八字须、山羊须用射线投射贴到脸上；眼球放在 eye 骨骼位置。
  5. 鞋按脚的实际包围盒生成；大带、带銙、玉佩、佩剑按腰围定位。
  6. Cycles 灰模渲染 + 色块版。

依赖：Blender 4.2+，已安装 MPFB 扩展（extensions.blender.org）。同目录需有 lusu_v3.py（复用几何函数）。
"""
import math
import os
import sys
import time
import importlib.util

WORK_DIR = "C:/Users/pjwly/3D Objects/lousu_ch1/"
OUT_DIR = WORK_DIR + "renders_lusu_v4/"
SAVE_BLEND = WORK_DIR + "lusu_v4.blend"
LOG_PATH = WORK_DIR + "lusu_v4_log.txt"
SIM_FRAMES = 90
SAMPLES = 96
ARM_ANGLE = 20.0      # 上臂与竖直方向夹角（度）

MACRO = {"gender": 1.0, "age": 0.62, "muscle": 0.62, "weight": 0.55, "proportions": 0.65, "height": 0.62,
         "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 1.0, "caucasian": 0.0, "african": 0.0}}
FACE_TARGETS = [("chin-prominent-incr", 0.35), ("chin-width-incr", 0.25), ("head-age-incr", 0.45),
                ("l-cheek-bones-incr", 0.35), ("r-cheek-bones-incr", 0.35), ("head-rectangular", 0.30),
                ("eyebrows-trans-down", 0.20), ("nose-hump-incr", 0.15), ("neck-scale-horiz-incr", 0.25)]

spec = importlib.util.spec_from_file_location("lusu_v3_base", WORK_DIR + "lusu_v3.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
_sub, _add, _mul, _dot, _cross, _norm, _lerp = B._sub, B._add, B._mul, B._dot, B._cross, B._norm, B._lerp
sweep, ellipsoid, lathe, box, merge, flat_strip, garment_tube = B.sweep, B.ellipsoid, B.lathe, B.box, B.merge, B.flat_strip, B.garment_tube
CLAY, PALETTE = B.CLAY, B.PALETTE


def run():
    import bpy
    import bmesh
    from mathutils import Vector, Matrix
    from mathutils.bvhtree import BVHTree

    T0 = time.time()
    log = ["Blender %s" % bpy.app.version_string]
    def L(s):
        log.append("[%6.1fs] %s" % (time.time()-T0, s)); print(log[-1])
    def flush(ok=True):
        with open(LOG_PATH, "w", encoding="utf-8") as fh:
            fh.write("\n".join(log) + ("\nOK\n" if ok else "\n"))

    mp = None
    for name in ("bl_ext.blender_org.mpfb", "bl_ext.user_default.mpfb", "mpfb"):
        try:
            mp = importlib.import_module(name); break
        except Exception:
            continue
    if mp is None:
        raise RuntimeError("找不到 MPFB 扩展，请先从 extensions.blender.org 安装 MPFB")
    HS = importlib.import_module(mp.__name__ + ".services.humanservice").HumanService
    TS = importlib.import_module(mp.__name__ + ".services.targetservice").TargetService

    # ---------------------------------------------------------------- 场景
    sc = bpy.data.scenes.get("鲁肃_v4")
    if sc:
        for ob in list(sc.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(sc)
    sc = bpy.data.scenes.new("鲁肃_v4")
    bpy.context.window.scene = sc
    sc.frame_start = 1; sc.frame_end = SIM_FRAMES
    coll = sc.collection
    src = bpy.data.collections.new("鲁肃_v4_MPFB源")
    coll.children.link(src)

    # ---------------------------------------------------------------- 1. MPFB 人体
    basemesh = HS.create_human(mask_helpers=True, detailed_helpers=False, extra_vertex_groups=True,
                               feet_on_ground=True, scale=0.1, macro_detail_dict=MACRO)
    for t, w in FACE_TARGETS:
        p = TS.target_full_path(t)
        if p:
            try:
                TS.load_target(basemesh, p, weight=w)
            except Exception as e:
                L("target %s: %r" % (t, e))
        else:
            L("target missing " + t)
    basemesh.name = "鲁肃_MPFB人体"
    bpy.context.view_layer.update()
    L("mpfb human created")

    dg = bpy.context.evaluated_depsgraph_get()
    apose = bpy.data.meshes.new_from_object(basemesh.evaluated_get(dg), depsgraph=dg)
    AV = [basemesh.matrix_world @ v.co for v in apose.vertices]
    bpy.data.meshes.remove(apose)

    rig = HS.add_builtin_rig(basemesh, "default")
    bpy.context.view_layer.update()
    for o in (basemesh, rig):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        src.objects.link(o)

    def pb(name):
        b = rig.pose.bones.get(name)
        if b is None:
            for k in rig.pose.bones.keys():
                if k.lower().startswith(name.split(".")[0].lower()) and k.endswith(name[-2:]):
                    return rig.pose.bones[k]
        return b

    def aim(bone, tgt):
        cur = (bone.tail - bone.head).normalized()
        q = cur.rotation_difference(tgt.normalized())
        h = bone.head.copy()
        bone.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ bone.matrix
        bpy.context.view_layer.update()

    a = math.radians(ARM_ANGLE)
    for side, sx in (("L", 1), ("R", -1)):
        up = pb("upperarm01." + side)
        aim(up, Vector((sx*math.sin(a), 0.02, -math.cos(a))))
        lo = pb("lowerarm01." + side)
        if lo:
            aim(lo, Vector((sx*math.sin(a-0.06), -0.30, -math.cos(a-0.06))))
        for k in rig.pose.bones.keys():   # 手指微屈
            if k.startswith("finger") and k.endswith(side) and not k.startswith("finger1"):
                rb = rig.pose.bones[k]
                rb.rotation_mode = "XYZ"; rb.rotation_euler[0] += math.radians(12)
    bpy.context.view_layer.update()
    W = rig.matrix_world
    def J(name, end="head"):
        b = pb(name)
        return tuple(W @ (b.head if end == "head" else b.tail))
    joints = {}
    for side in ("L", "R"):
        joints["sh"+side] = J("upperarm01." + side)
        joints["el"+side] = J("lowerarm01." + side)
        wb = pb("wrist." + side)
        joints["wr"+side] = J("wrist." + side) if wb else J("lowerarm02." + side, "tail")
        joints["eye"+side] = J("eye." + side)
    L("posed; joints " + ", ".join("%s=(%.3f,%.3f,%.3f)" % (k, *v) for k, v in joints.items()))

    dg = bpy.context.evaluated_depsgraph_get()
    bme = bpy.data.meshes.new_from_object(basemesh.evaluated_get(dg), depsgraph=dg)
    bme.name = "鲁肃_身体"
    body = bpy.data.objects.new("鲁肃_身体", bme)
    coll.objects.link(body)
    body.matrix_world = basemesh.matrix_world.copy()
    for p in bme.polygons:
        p.use_smooth = True
    bme.materials.clear()
    src.hide_render = True
    src.hide_viewport = True
    BV = [body.matrix_world @ v.co for v in bme.vertices]
    H = max(v.z for v in BV)
    L("body baked: %d verts, height %.3f" % (len(BV), H))
    sm = body.modifiers.new("Subdivision", "SUBSURF"); sm.levels = 1; sm.render_levels = 2

    # ---------------------------------------------------------------- 身体测量
    sz = H / 1.775
    shx = abs(joints["shL"][0])
    def slice_ext(z, band=0.012, arms_out=True):
        xl = None
        if arms_out and z < joints["shL"][2] - 0.03*sz:
            xl = shx + 0.03 if z > 0.95*sz else 0.32
        pts = [v for v in AV if abs(v.z - z) < band and (xl is None or abs(v.x) < xl)]
        if not pts:
            return None
        return (max(abs(v.x) for v in pts), min(v.y for v in pts), max(v.y for v in pts))

    def fit(z, rx, ry, dy, margin):
        e = slice_ext(z)
        if e is None:
            return rx, ry, dy
        hx, y0, y1 = e
        ryb = (y1-y0)/2 + margin; dyb = (y0+y1)/2
        return max(rx, hx + margin), max(ry, ryb), (dyb if ryb >= ry else dy)

    # ---------------------------------------------------------------- 材质与建对象
    mats = {}
    def get_mat(key):
        if key in mats:
            return mats[key]
        m = bpy.data.materials.get("鲁肃v4_" + key) or bpy.data.materials.new("鲁肃v4_" + key)
        rgb = CLAY[key]; m.diffuse_color = (*rgb, 1)
        try:
            m.use_nodes = True
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = (*rgb, 1)
            b.inputs["Roughness"].default_value = 0.5 if key in ("皮肤", "身体") else (0.3 if key in ("金属", "玉", "眼") else 0.75)
            if key == "金属":
                b.inputs["Metallic"].default_value = 0.8
            if key in ("外袍", "衣缘", "中衣", "下裳"):
                for nm in ("Sheen Weight", "Sheen"):
                    if nm in b.inputs:
                        b.inputs[nm].default_value = 0.4; break
            if key in ("皮肤", "身体"):
                for nm in ("Subsurface Weight", "Subsurface"):
                    if nm in b.inputs:
                        b.inputs[nm].default_value = 0.15; break
        except Exception as e:
            L("mat %s %r" % (key, e))
        mats[key] = m
        return m
    bme.materials.append(get_mat("皮肤"))

    def make_obj(name, geo, mat_keys, subsurf=1, pin=None):
        V, F = geo
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in V], [], F)
        me.validate()
        keys = mat_keys if isinstance(mat_keys, list) else [mat_keys]*len(me.polygons)
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
            p.use_smooth = True
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        if pin is not None:
            vg = ob.vertex_groups.new(name="pin"); vg.add(pin, 1.0, "REPLACE")
        if subsurf:
            m = ob.modifiers.new("Subdivision", "SUBSURF"); m.levels = subsurf; m.render_levels = subsurf+1
        return ob

    # ---------------------------------------------------------------- 脸部射线投射
    bm = bmesh.new(); bm.from_mesh(bme); bm.transform(body.matrix_world)
    bvh = BVHTree.FromBMesh(bm)
    eL, eR = Vector(joints["eyeL"]), Vector(joints["eyeR"])
    em = (eL + eR) / 2
    fs = abs(eL.x - eR.x) / 2 / 0.031
    def face_pt(x, z, out=0.0):
        X = em.x + x*fs; Z = em.z + (z - 0.004)*fs
        hit = bvh.ray_cast(Vector((X, em.y - 0.4, Z)), Vector((0, 1, 0)), 1.0)
        if hit[0] is None:
            return (X, em.y - 0.02, Z)
        return (hit[0].x, hit[0].y - out, hit[0].z)
    hit = bvh.ray_cast(Vector((em.x, em.y + 0.07, H + 0.3)), Vector((0, 0, -1)), 1.0)
    head_top = hit[0] if hit[0] is not None else Vector((em.x, em.y + 0.07, H))
    L("eyes mid (%.3f,%.3f,%.3f) scale %.3f head_top %.3f" % (em.x, em.y, em.z, fs, head_top.z))

    # 眼球
    eyes = []
    er = 0.0118*fs
    for e in (eL, eR):
        c = (e.x, e.y, e.z)
        eyes.append(ellipsoid(c, (er, er, er), 18, 12))
        eyes.append(ellipsoid(_add(c, (0, -er*0.84, 0.0004)), (0.0062*fs, 0.0034*fs, 0.0062*fs), 14, 8))
    make_obj("鲁肃_眼球", merge(*eyes), "眼", 1)

    # 眉、须
    brows = []
    for sx in (-1, 1):
        pts = [face_pt(sx*(0.012 + 0.040*t), 0.026 + 0.006*math.sin(math.pi*t*0.9) - 0.002*t, 0.0022) for t in [k/6 for k in range(7)]]
        brows.append(sweep(pts, [0.0045, 0.006, 0.0062, 0.0058, 0.005, 0.004, 0.0025], [0.0025]*7, n=6))
    make_obj("鲁肃_眉", merge(*brows), "发", 1)
    beard = []
    for sx in (-1, 1):
        pts = [face_pt(sx*0.004, -0.0445, 0.0022), face_pt(sx*0.016, -0.0475, 0.0026), face_pt(sx*0.026, -0.056, 0.0024), face_pt(sx*0.030, -0.069, 0.002)]
        beard.append(sweep(pts, [0.0035, 0.0048, 0.0042, 0.0018], [0.0022, 0.003, 0.0026, 0.0012], n=8))
    g = [face_pt(0, -0.072, 0.002), face_pt(0, -0.088, 0.004), face_pt(0, -0.100, 0.005)]
    g += [_add(g[-1], (0, 0.007, -0.018)), _add(g[-1], (0, 0.012, -0.036))]
    beard.append(sweep(g, [0.0085, 0.011, 0.0105, 0.0065, 0.0012], [0.0035, 0.005, 0.0055, 0.004, 0.001], n=12))
    beard.append(sweep([face_pt(0, -0.0645, 0.002), face_pt(0, -0.0705, 0.0035)], [0.004, 0.006], [0.0015, 0.002], n=6))
    make_obj("鲁肃_须髯", merge(*beard), "发", 1)

    # ---------------------------------------------------------------- 头发：从头部取发区
    hc = Vector((em.x, em.y + 0.085*fs, em.z + 0.01))
    def hairline_z(v):
        d = v - hc
        th = math.atan2(d.y, d.x)
        F = max(0.0, -math.sin(th)); Bk = max(0.0, math.sin(th))
        return em.z + (0.022 + 0.040*F**1.4 - 0.095*Bk**1.25)*fs
    hb = bmesh.new(); hb.from_mesh(bme); hb.transform(body.matrix_world)
    keep = set()
    for v in hb.verts:
        if v.co.z > hairline_z(v.co) and v.co.z > em.z - 0.12 and (v.co - hc).length < 0.17*fs:
            keep.add(v.index)
    hb.verts.ensure_lookup_table()
    kill = [f for f in hb.faces if not all(v.index in keep for v in f.verts)]
    bmesh.ops.delete(hb, geom=kill, context="FACES")
    loose = [v for v in hb.verts if not v.link_faces]
    bmesh.ops.delete(hb, geom=loose, context="VERTS")
    hme = bpy.data.meshes.new("鲁肃_头发")
    hb.to_mesh(hme); hb.free()
    for p in hme.polygons:
        p.use_smooth = True
    hair = bpy.data.objects.new("鲁肃_头发", hme); coll.objects.link(hair)
    hme.materials.append(get_mat("发"))
    m = hair.modifiers.new("Subdivision", "SUBSURF"); m.levels = 2; m.render_levels = 2
    tex = bpy.data.textures.get("鲁肃v4_发丝") or bpy.data.textures.new("鲁肃v4_发丝", "WOOD")
    try:
        tex.wood_type = "BANDS"; tex.noise_basis_2 = "SIN"; tex.turbulence = 2.0; tex.noise_scale = 0.08
    except Exception:
        pass
    dsp = hair.modifiers.new("发丝沟", "DISPLACE"); dsp.texture = tex; dsp.texture_coords = "LOCAL"; dsp.strength = 0.0018; dsp.mid_level = 0.3
    so = hair.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = 0.0045; so.offset = 1.0
    L("hair shell: %d faces" % len(hme.polygons))

    bc = (head_top.x, head_top.y - 0.004, head_top.z + 0.018)
    bun = [ellipsoid(bc, (0.031, 0.031, 0.027), 16, 10)]
    for k in range(6):
        a0 = 2*math.pi*k/6
        pts = [_add(bc, ((0.029 - 0.006*abs(s-6.5)/6.5)*math.cos(a0+s*0.42), (0.029 - 0.006*abs(s-6.5)/6.5)*math.sin(a0+s*0.42), -0.016 + 0.034*s/13)) for s in range(14)]
        bun.append(sweep(pts, 0.0085, 0.0065, n=8))
    make_obj("鲁肃_发髻", merge(*bun), "发", 1)
    make_obj("鲁肃_发带", lathe([(bc[2]-0.026, 0.026, 0.026, 0.0), (bc[2]-0.016, 0.031, 0.031, 0.0)], n=20, cx=bc[0], cy=bc[1]), "衣缘", 1)
    crown = [lathe([(bc[2]-0.004, 0.035, 0.044, -0.002), (bc[2]+0.012, 0.037, 0.046, -0.002), (bc[2]+0.02, 0.033, 0.042, -0.002)], n=20, cx=bc[0], cy=bc[1]),
             box(_add(bc, (0, -0.030, 0.040)), (0.046, 0.005, 0.052), (-24, 0, 0)),
             box(_add(bc, (0, 0.030, 0.046)), (0.046, 0.005, 0.066), (14, 0, 0))]
    for sx in (-1, 1):
        crown.append(sweep([_add(bc, (sx*0.023, -0.036, 0.018)), _add(bc, (sx*0.023, -0.012, 0.062)), _add(bc, (sx*0.023, 0.026, 0.075)), _add(bc, (sx*0.023, 0.040, 0.018))], 0.004, 0.0025, n=6))
    make_obj("鲁肃_冠", merge(*crown), "发", 1)
    make_obj("鲁肃_簪", sweep([_add(bc, (-0.075, 0, 0.03)), _add(bc, (0, 0, 0.03)), _add(bc, (0.08, 0, 0.03))], [0.0045, 0.0035, 0.0018], n=8), "金属", 1)
    L("head parts ok")

    # ---------------------------------------------------------------- 鞋（按脚包围盒）
    shoes, soles = [], []
    for sx in (-1, 1):
        fv = [v for v in BV if v.z < 0.10*sz and v.x*sx > 0.02]
        x0, x1 = min(v.x for v in fv), max(v.x for v in fv)
        y0, y1 = min(v.y for v in fv), max(v.y for v in fv)
        xc = (x0+x1)/2; wd = (x1-x0)/2 + 0.010
        yh = y1 + 0.012; yt = y0 - 0.022; Lf = yh - yt
        def P(t, z): return (xc, yh - Lf*t, z)
        path = [P(0.0, 0.052), P(0.1, 0.058), P(0.32, 0.056), P(0.55, 0.050), P(0.75, 0.046), P(0.9, 0.048), P(0.98, 0.064), P(1.01, 0.087), P(1.0, 0.102)]
        ru = [wd*0.80, wd*0.95, wd, wd, wd*0.9, wd*0.68, wd*0.42, wd*0.25, wd*0.12]
        rw = [0.042, 0.046, 0.042, 0.036, 0.030, 0.023, 0.016, 0.010, 0.006]
        shoes.append(sweep(path, ru, rw, n=14))
        ol = [(p[0]+ru[k]*1.04, p[1]) for k, p in enumerate(path[:7])] + [(path[k][0]-ru[k]*1.04, path[k][1]) for k in range(6, -1, -1)]
        n = len(ol)
        soles.append(([(a, b, 0.0) for a, b in ol] + [(a, b, 0.017) for a, b in ol],
                      [tuple(reversed(range(n))), tuple(range(n, 2*n))] + [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]))
    shoe_obj = make_obj("鲁肃_履", merge(*shoes), "鞋", 2)
    sole_obj = make_obj("鲁肃_履底", merge(*soles), "鞋底", 1)

    # ---------------------------------------------------------------- 服装（按身体截面放量）
    def rows_fit(design, margin, pin_fn):
        rows = []
        for (z, rx, ry, dy, amp) in design:
            zz = z*sz
            rx2, ry2, dy2 = fit(zz, rx*sz**0.5, ry*sz**0.5, dy, margin)
            rows.append((zz, rx2, ry2, dy2, amp, pin_fn(z)))
        return rows

    skirt_design = [(1.00, 0.196, 0.146, -0.004, 0), (0.965, 0.198, 0.148, -0.004, 0)]
    for k in range(1, 23):
        t = k/22; z = 0.965 + (0.045-0.965)*t
        skirt_design.append((z, 0.20+0.12*t**0.9, 0.15+0.115*t**0.9, 0.012*t, 0.05*t))
    srows = rows_fit(skirt_design, 0.014, lambda z: z >= 0.96)
    # 下摆以下的截面可以比上一行收（双腿之间），保证单调外扩
    for i in range(2, len(srows)):
        z, rx, ry, dy, amp, pn = srows[i]
        srows[i] = (z, max(rx, srows[i-1][1]), max(ry, srows[i-1][2]), dy, amp, pn)
    V, F, pin, meta = garment_tube(srows, 80, folds=14, phase=0.7)
    last = len(srows)-2
    smats = ["衣缘" if (j >= last-2 or abs(thd+90) < 13) else "下裳" for (j, i, thd, z) in meta]
    skirt = make_obj("鲁肃_下裳", (V, F), smats, 0, pin)
    def skirt_at(z):
        for a, b in zip(srows, srows[1:]):
            if b[0] <= z <= a[0]:
                t = (a[0]-z)/(a[0]-b[0])
                return tuple(a[i]+(b[i]-a[i])*t for i in (1, 2, 3))
        return srows[-1][1:4] if z < srows[-1][0] else srows[0][1:4]

    robe_design = []
    zs = [1.508, 1.492, 1.468, 1.452, 1.440] + [1.42 - 0.022*k for k in range(17)] + [1.060, 1.022, 0.985]
    zs = sorted(set(round(z, 4) for z in zs), reverse=True)
    for z in zs:
        rx, ry, dy = B.robe_profile(z)
        robe_design.append((z, rx, ry, dy, 0))
    rrows = rows_fit(robe_design, 0.016, lambda z: z >= 1.395 or z <= 1.061)
    waist_row = len(rrows)-1
    wz, wrx, wry, wdy = rrows[-1][0], rrows[-1][1], rrows[-1][2], rrows[-1][3]
    for k in range(1, 23):
        t = k/22; z = wz + (0.085*sz - wz)*t
        rx = wrx + 0.20*t**0.85; ry = wry + 0.165*t**0.85
        s = skirt_at(z)
        rx = max(rx, s[0] + 0.03); ry = max(ry, s[1] + 0.03)
        rrows.append((z, rx, ry, 0.02*t, 0.075*t, False))
    V, F, pin, meta = garment_tube(rrows, 128, folds=9, phase=0.25)
    keepF, rmats = [], []
    lastr = len(rrows)-2
    for f, (j, i, thd, z) in zip(F, meta):
        if j >= waist_row and -113 < thd < -67:
            continue
        mk = "外袍"
        if j <= 1 or j >= lastr-2 or (j >= waist_row and (-121 < thd <= -113 or -67 <= thd < -59)):
            mk = "衣缘"
        keepF.append(f); rmats.append(mk)
    robe = make_obj("鲁肃_外袍", (V, keepF), rmats, 0, pin)
    def robe_at(z):
        for a, b in zip(rrows, rrows[1:]):
            if b[0] <= z <= a[0]:
                t = (a[0]-z)/(a[0]-b[0])
                return tuple(a[i]+(b[i]-a[i])*t for i in (1, 2, 3))
        return rrows[-1][1:4] if z < rrows[-1][0] else rrows[0][1:4]
    L("garments built: skirt %d, robe %d faces" % (len(F) if False else len(skirt.data.polygons), len(robe.data.polygons)))

    def sleeve(side, sx):
        S = Vector(joints["sh"+side]) + Vector((sx*0.005, 0, 0.03)); E = Vector(joints["el"+side]); Wr = Vector(joints["wr"+side])
        d = (Wr - E).normalized(); End = Wr + d*0.10
        n, nu = 30, 44
        path = [(S.lerp(E, (k/n)/0.5) if k/n < 0.5 else E.lerp(End, (k/n-0.5)/0.5)) for k in range(n+1)]
        Vv, pinv, cents = [], [], []
        for k, p in enumerate(path):
            t = k/n
            rl = 0.074 + (0.105-0.074)*t
            rf = 0.082 + (0.215-0.082)*t**1.05
            c = p + Vector((sx*(0.014 + 0.028*t), 0.105*t**1.3, 0.0)); cents.append(c)
            tg = (path[min(k+1, n)] - path[max(k-1, 0)]).normalized()
            u = tg.cross(Vector((0, 1, 0))).normalized(); w = tg.cross(u)
            for i in range(nu):
                th = 2*math.pi*i/nu; wob = 1 + 0.03*math.sin(6*th)
                Vv.append(tuple(c + u*(rl*wob*math.cos(th)) + w*(rf*wob*math.sin(th))))
                if k <= 1:
                    pinv.append(k*nu+i)
        Ff = B._ring_faces(n+1, nu, cap=False)
        mk = ["衣缘" if k >= n-2 else "外袍" for k in range(n) for i in range(nu)]
        ce = cents[-1]; Vv.append(tuple(ce)); ci = len(Vv)-1; base = n*nu
        for i in range(nu):
            a_, b_ = base+i, base+(i+1) % nu
            if Vv[a_][1]-ce.y > -0.06 and Vv[b_][1]-ce.y > -0.06:
                Ff.append((a_, ci, b_)); mk.append("外袍")
        return make_obj("鲁肃_大袖_" + ("左" if sx > 0 else "右"), (Vv, Ff), mk, 0, pinv)
    sleeves = [sleeve("L", 1), sleeve("R", -1)]

    zb0, zb1 = 0.982*sz, 1.078*sz
    zbm = (zb0+zb1)/2
    brx, bry, bdy = robe_at(zbm)
    brx += 0.012; bry += 0.012
    def bixi_geo():
        nx, nz = 10, 18
        Vv, pinv = [], []
        for j in range(nz+1):
            z = zb0+0.008 - 0.50*sz*j/nz
            s = skirt_at(z)
            yf = s[2] - s[1] - 0.045
            for i in range(nx+1):
                Vv.append((-0.115 + 0.23*i/nx, yf, z))
                if j == 0:
                    pinv.append(i)
        Ff = [(j*(nx+1)+i, j*(nx+1)+i+1, (j+1)*(nx+1)+i+1, (j+1)*(nx+1)+i) for j in range(nz) for i in range(nx)]
        mk = ["衣缘" if (i in (0, nx-1) or j >= nz-2) else "下裳" for j in range(nz) for i in range(nx)]
        return Vv, Ff, pinv, mk
    Vv, Ff, pv, mk = bixi_geo()
    bixi = make_obj("鲁肃_蔽膝", (Vv, Ff), mk, 0, pv)
    Vs, Fs, ps, ms = [], [], [], []
    for x0, Ln in ((0.075, 0.46), (0.118, 0.40)):
        base = len(Vs); nz = 14
        for j in range(nz+1):
            z = zb0+0.012 - Ln*sz*j/nz
            s = skirt_at(z); yf = s[2] - s[1] - 0.065
            for i in range(2):
                Vs.append((x0 - 0.02 + 0.04*i, yf, z))
                if j == 0:
                    ps.append(base+i)
        for j in range(nz):
            a_ = base + j*2; Fs.append((a_, a_+1, a_+3, a_+2)); ms.append("衣缘")
    shen = make_obj("鲁肃_绅", (Vs, Fs), ms, 0, ps)

    # 大带、带銙、玉佩、佩剑
    make_obj("鲁肃_大带", lathe([(zb0, brx-0.003, bry-0.003, bdy), (zb0+0.008, brx, bry, bdy), (zb1-0.008, brx, bry, bdy), (zb1, brx-0.003, bry-0.003, bdy)], n=40), "衣缘", 1)
    kua = []
    for i in range(11):
        th = math.pi + math.pi*(i+0.5)/11
        p = ((brx+0.006)*math.cos(th), bdy+(bry+0.006)*math.sin(th), zbm-0.004)
        kua.append(box(p, (0.026, 0.008, 0.034), (0, 0, math.degrees(th)+90)))
    kua.append(box((0, bdy-bry-0.008, zbm), (0.07, 0.012, 0.055)))
    kua.append(ellipsoid((0, bdy-bry-0.015, zbm), (0.018, 0.006, 0.018), 12, 8))
    make_obj("鲁肃_带銙", merge(*kua), "金属", 1)
    th = math.radians(-125)
    px, py = brx*math.cos(th), bdy+bry*math.sin(th) - 0.01
    make_obj("鲁肃_玉佩", merge(sweep([(px, py, zb0), (px-0.01, py-0.01, zb0-0.09), (px-0.012, py-0.012, zb0-0.16)], 0.003, n=6),
                              ellipsoid((px-0.012, py-0.016, zb0-0.175), (0.026, 0.006, 0.026), 16, 8),
                              box((px-0.012, py-0.016, zb0-0.225), (0.06, 0.008, 0.016)),
                              sweep([(px-0.012, py-0.016, zb0-0.235), (px-0.012, py-0.018, zb0-0.30), (px-0.012, py-0.02, zb0-0.37)], [0.006, 0.014, 0.022], [0.006, 0.012, 0.016], n=10)), "玉", 1)
    th = math.radians(-50)
    top = (brx*math.cos(th)+0.02, bdy+bry*math.sin(th)-0.02, zb0+0.02)
    tip = (top[0]+0.12, top[1]+0.37, top[2]-0.68*sz)
    dr = _norm(_sub(tip, top))
    sword = [make_obj("鲁肃_佩剑_鞘", sweep([top, _lerp(top, tip, 0.5), tip], [0.026, 0.024, 0.019], [0.011, 0.010, 0.009], n=10), "木", 1)]
    gp = _sub(top, _mul(dr, 0.19)); cc = _sub(gp, _mul(dr, 0.032)); side = _norm(_cross(dr, (1, 0, 0)))
    ring = [_add(cc, _add(_mul(dr, -0.032*math.cos(q)), _mul(side, 0.032*math.sin(q)))) for q in [2*math.pi*i/20 for i in range(21)]]
    sword.append(make_obj("鲁肃_佩剑_饰件", merge(sweep([_lerp(top, tip, 0.18), _lerp(top, tip, 0.22)], 0.032, 0.016, n=10),
                                               sweep([_lerp(top, tip, 0.94), tip], [0.022, 0.023], [0.012, 0.012], n=10),
                                               box(top, (0.06, 0.03, 0.03), (0, 0, math.degrees(math.atan2(dr[1], dr[0]))+90)),
                                               sweep([_sub(top, _mul(dr, 0.015)), gp], 0.015, n=10),
                                               sweep(ring, 0.0065, n=6, cap=False)), "金属", 1))
    L("accessories ok")

    floor = make_obj("碰撞_地面", ([(-2, -2, 0), (2, -2, 0), (2, 2, 0), (-2, 2, 0)], [(0, 1, 2, 3)]), "鞋底", 0)
    floor.hide_render = True; floor.hide_viewport = True

    # ---------------------------------------------------------------- 布料模拟
    def add_collision(objs):
        for o in objs:
            if "Collision" not in o.modifiers:
                o.modifiers.new("Collision", "COLLISION")
            o.collision.thickness_outer = 0.004; o.collision.thickness_inner = 0.01; o.collision.cloth_friction = 8.0
    def remove_collision(objs):
        for o in objs:
            mm = o.modifiers.get("Collision")
            if mm:
                o.modifiers.remove(mm)
    cfg = {"default": dict(quality=7, mass=0.3, air=2.0, tension=15, shear=8, bend=0.5),
           "鲁肃_下裳": dict(quality=7, mass=0.25, air=3.0, tension=15, shear=8, bend=0.4),
           "鲁肃_外袍": dict(quality=8, mass=0.4, air=3.0, tension=20, shear=10, bend=0.9),
           "鲁肃_大袖_左": dict(quality=9, mass=0.22, air=3.0, tension=40, shear=12, bend=0.4, self=True),
           "鲁肃_大袖_右": dict(quality=9, mass=0.22, air=3.0, tension=40, shear=12, bend=0.4, self=True),
           "鲁肃_蔽膝": dict(quality=6, mass=0.4, air=2.0, tension=25, shear=12, bend=2.0),
           "鲁肃_绅": dict(quality=6, mass=0.2, air=2.0, tension=25, shear=12, bend=0.5)}
    def simulate(cloths, colliders, label):
        add_collision(colliders)
        for o in cloths:
            for mm in list(o.modifiers):
                o.modifiers.remove(mm)
            cm = o.modifiers.new("Cloth", "CLOTH"); s = cm.settings; st = cfg.get(o.name, cfg["default"])
            s.quality = st["quality"]; s.mass = st["mass"]; s.air_damping = st["air"]
            s.tension_stiffness = s.compression_stiffness = st["tension"]; s.shear_stiffness = st["shear"]; s.bending_stiffness = st["bend"]
            s.vertex_group_mass = "pin"; s.pin_stiffness = 1.0
            c = cm.collision_settings; c.collision_quality = 4; c.distance_min = 0.0035
            c.use_self_collision = st.get("self", False)
            if c.use_self_collision:
                c.self_distance_min = 0.0025
            cm.point_cache.frame_start = 1; cm.point_cache.frame_end = SIM_FRAMES
        sc.frame_set(1)
        for f in range(1, SIM_FRAMES+1):
            sc.frame_set(f)
        dgx = bpy.context.evaluated_depsgraph_get()
        for o in cloths:
            nm = bpy.data.meshes.new_from_object(o.evaluated_get(dgx), preserve_all_data_layers=True, depsgraph=dgx)
            old = o.data; o.modifiers.clear(); o.data = nm; nm.name = o.name; bpy.data.meshes.remove(old)
        sc.frame_set(1)
        remove_collision(colliders)
        L("sim %s done" % label)

    try:
        simulate([skirt], [body, floor, shoe_obj], "下裳")
        simulate([robe], [body, skirt, floor, shoe_obj], "外袍")
        lap = lambda z: B._lapel(z/sz)
        def robe_pt(z, thd, out=0.006):
            rx, ry, dy = robe_at(z); t = math.radians(thd)
            p = (rx*math.cos(t), dy+ry*math.sin(t), z); nn = _norm((math.cos(t)/rx, math.sin(t)/ry, 0))
            return _add(p, _mul(nn, out)), nn
        def line(z0, z1, f, n=36):
            P_, N_ = [], []
            for k in range(n+1):
                z = z0+(z1-z0)*k/n; p, nn = robe_pt(z, f(z)); P_.append(p); N_.append(nn)
            return P_, N_
        strips = {"衣缘_交领": ("衣缘", line(1.50*sz, 1.11*sz, lap), 0.058, 4),
                  "中衣_领": ("中衣", line(1.50*sz, 1.34*sz, lambda z: lap(z)+10.5, 20), 0.030, 3),
                  "衣缘_内襟": ("衣缘", line(1.50*sz, 1.36*sz, lambda z: -128 + 36*max(0.0, min(1.0, (1.50*sz-z)/(0.14*sz))), 18), 0.045, 3)}
        for nm, (mk, (P_, N_), wdt, na) in strips.items():
            co = make_obj("鲁肃_" + nm, flat_strip(P_, N_, wdt, na), mk, 0)
            sw = co.modifiers.new("Shrinkwrap", "SHRINKWRAP"); sw.target = robe
            sw.wrap_method = "NEAREST_SURFACEPOINT"; sw.wrap_mode = "OUTSIDE_SURFACE"; sw.offset = 0.0045
            so = co.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = 0.003
            su = co.modifiers.new("Subdivision", "SUBSURF"); su.levels = 1; su.render_levels = 2
        simulate(sleeves + [bixi, shen], [body, robe, skirt, floor] + sword, "大袖/蔽膝/绅")
        sim_ok = True
    except Exception:
        import traceback
        sim_ok = False
        L("SIM FAILED: " + traceback.format_exc())
    for o in [skirt, robe, bixi, shen] + sleeves:
        so = o.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = 0.005 if o not in (bixi, shen) else 0.004; so.offset = 0.0; so.use_rim = True
        su = o.modifiers.new("Subdivision", "SUBSURF"); su.levels = 1; su.render_levels = 2
        for p in o.data.polygons:
            p.use_smooth = True
    L("garments finalized sim_ok=%s" % sim_ok)
    flush(False)

    # ---------------------------------------------------------------- 灯光、相机、渲染
    def look(ob, target):
        ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()
    def add_light(name, loc, energy, size, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; ld.color = color
        lo = bpy.data.objects.new(name, ld); coll.objects.link(lo); lo.location = loc; look(lo, (0, 0, 1.0))
    add_light("主光", (-2.2, -3.0, 3.2), 260, 1.6)
    add_light("补光", (2.8, -2.2, 1.6), 60, 3.0, (0.9, 0.95, 1.0))
    add_light("轮廓光", (1.2, 3.2, 2.8), 280, 1.2)
    world = bpy.data.worlds.new("鲁肃v4_world"); sc.world = world
    try:
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.42, 0.43, 1)
        world.node_tree.nodes["Background"].inputs[1].default_value = 0.25
    except Exception:
        pass
    ground = make_obj("地面_阴影", ([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [(0, 1, 2, 3)]), "中衣", 0)
    try:
        ground.is_shadow_catcher = True
    except Exception:
        pass
    cams = []
    def ortho(name, loc, rot):
        cd = bpy.data.cameras.new(name); cd.type = "ORTHO"; cd.ortho_scale = 2.1*sz; cd.clip_end = 100
        co = bpy.data.objects.new(name, cd); coll.objects.link(co); co.location = loc
        co.rotation_euler = tuple(math.radians(v) for v in rot); return co
    def persp(name, loc, tgt, lens):
        cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 100
        co = bpy.data.objects.new(name, cd); coll.objects.link(co); co.location = loc; look(co, tgt); return co
    zc = 0.94*sz
    cams.append(("正视", ortho("CAM_正视", (0, -10, zc), (90, 0, 0)), (1000, 1900)))
    cams.append(("侧视", ortho("CAM_侧视", (-10, 0, zc), (90, 0, -90)), (1000, 1900)))
    cams.append(("后视", ortho("CAM_后视", (0, 10, zc), (90, 0, 180)), (1000, 1900)))
    cams.append(("透视", persp("CAM_透视", (-1.25, -3.05, 1.40*sz), (0, 0, zc), 50), (1200, 1700)))
    fc = (em.x, em.y + 0.02, em.z - 0.02)
    cams.append(("面部特写", persp("CAM_面部", (fc[0]-0.26, fc[1]-0.62, fc[2]+0.04), fc, 85), (1200, 1200)))
    cams.append(("面部正面", persp("CAM_面部正面", (fc[0], fc[1]-0.75, fc[2]+0.01), fc, 85), (1200, 1200)))
    cams.append(("手袖特写", persp("CAM_手袖", (1.1, -1.6, 1.2*sz), (0.28, 0.0, 0.95*sz), 50), (1200, 1200)))

    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = t; prefs.get_devices()
                devs = [d for d in prefs.devices if d.type == t]
                if devs:
                    for d in devs:
                        d.use = True
                    sc.cycles.device = "GPU"; break
            except Exception:
                continue
    except Exception:
        pass
    sc.cycles.samples = SAMPLES
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass
    sc.render.film_transparent = True
    try:
        sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = -0.9
    except Exception:
        pass
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, co, (rx, ry) in cams:
        sc.camera = co; sc.render.resolution_x, sc.render.resolution_y = rx, ry
        sc.render.filepath = OUT_DIR + "鲁肃_v4_%s.png" % name
        bpy.ops.render.render(write_still=True); L("rendered " + name)
    for k, m in mats.items():
        try:
            m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (*PALETTE[k], 1)
        except Exception:
            pass
    for name in ("透视", "正视", "面部特写"):
        co = [c for c in cams if c[0] == name][0]
        sc.camera = co[1]; sc.render.resolution_x, sc.render.resolution_y = co[2]
        sc.render.filepath = OUT_DIR + "鲁肃_v4_%s_色块.png" % name
        bpy.ops.render.render(write_still=True); L("rendered %s 色块" % name)
    for k, m in mats.items():
        try:
            m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (*CLAY[k], 1)
        except Exception:
            pass
    sc.camera = cams[3][1]
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_BLEND)
    L("saved " + SAVE_BLEND)
    flush(True)


if __name__ == "__main__":
    try:
        run()
    except Exception:
        import traceback
        tb = traceback.format_exc(); print(tb)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write("\nFAILED\n" + tb)
        raise
