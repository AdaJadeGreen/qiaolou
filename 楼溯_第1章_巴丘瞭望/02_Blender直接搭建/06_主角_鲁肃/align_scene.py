# -*- coding: utf-8 -*-
"""
《楼·溯》第1章 —— 场景尺寸测量 + 外部人物模型比例对齐

做三件事：
  1. 从 lousu_ch1_greybox_v2.blend 追加（append）三个谯楼资产，量出精确尺寸并写报告。
  2. 导入 D:/Caroline Elvira/ancient chinese robe 3d model/ancient_chinese_robe_3d_model.fbx，
     量出原始尺寸，按真人身高 1.78 m 等比缩放，并把朝向转正（脸朝 -Y）。
  3. 在「建成后」谯楼上放三个人物实例（台阶下 / 门口 / 平座上），渲染正视与透视对照图，
     另存为 场景_比例对齐.blend。

在 Blender 的 Scripting 控制台里 exec 本文件即可；不会改动原有的 .blend。
"""
import math
import os
import time

WORK = "C:/Users/pjwly/3D Objects/lousu_ch1/"
SRC_BLEND = WORK + "lousu_ch1_greybox_v2.blend"
FBX = "D:/Caroline Elvira/ancient chinese robe 3d model/ancient_chinese_robe_3d_model.fbx"
OUT_DIR = WORK + "renders_align/"
SAVE_BLEND = WORK + "场景_比例对齐.blend"
REPORT = WORK + "尺寸报告.txt"

TARGET_H = 1.78          # 人物目标身高（米）
FACE_ROT_Z = 0.0         # 人物绕 Z 轴补偿旋转（度）；看过渲染图后再调
ASSETS = ["谯楼_废墟", "谯楼_建立中", "谯楼_建成后"]
RENDER = True
SAMPLES = 64


def run():
    import bpy
    from mathutils import Vector

    T0 = time.time()
    lines = ["《楼·溯》第1章 场景尺寸报告   Blender %s" % bpy.app.version_string, ""]
    def L(s):
        lines.append(s); print(s)

    # ---------------------------------------------------------------- 新场景
    sc = bpy.data.scenes.get("比例对齐")
    if sc:
        for ob in list(sc.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(sc)
    sc = bpy.data.scenes.new("比例对齐")
    bpy.context.window.scene = sc
    coll = sc.collection

    def dims(objs, label=""):
        """返回 (minv, maxv, size) —— 计算所有网格对象（含修改器）的世界包围盒"""
        dg = bpy.context.evaluated_depsgraph_get()
        lo = [1e9]*3; hi = [-1e9]*3; nf = 0
        for o in objs:
            if o.type != "MESH" or o.hide_render:
                continue
            eo = o.evaluated_get(dg)
            me = eo.to_mesh()
            nf += len(me.polygons)
            mw = o.matrix_world
            for v in me.vertices:
                w = mw @ v.co
                for k in range(3):
                    lo[k] = min(lo[k], w[k]); hi[k] = max(hi[k], w[k])
            eo.to_mesh_clear()
        if nf == 0:
            return None
        return Vector(lo), Vector(hi), Vector((hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2])), nf

    # ---------------------------------------------------------------- 1. 追加谯楼
    L("=== 一、谯楼资产（来自 %s）===" % os.path.basename(SRC_BLEND))
    towers = {}
    for name in ASSETS:
        if bpy.data.collections.get(name):
            # 同名集合已存在（重复运行），先清掉
            c = bpy.data.collections[name]
            for ob in list(c.all_objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
        d_ = SRC_BLEND + "/Collection/"
        bpy.ops.wm.append(filepath=d_ + name, directory=d_, filename=name)
        c = bpy.data.collections.get(name)
        if c is None:
            L("  !! 追加失败：%s" % name)
            continue
        if c.name not in [x.name for x in coll.children]:
            try:
                coll.children.link(c)
            except Exception:
                pass
        # 相机不参与渲染与测量
        for ob in list(c.all_objects):
            if ob.type == "CAMERA":
                bpy.data.objects.remove(ob, do_unlink=True)
        towers[name] = c

    # 把三座楼重新排列：原本每个资产间隔 30 m，这里保留，方便单独看
    for i, name in enumerate(ASSETS):
        c = towers.get(name)
        if not c:
            continue
        root = next((o for o in c.objects if o.type == "EMPTY"), None)
        if root:
            root.location = (i * 30.0, 0, 0)
    bpy.context.view_layer.update()

    tower_info = {}
    for name in ASSETS:
        c = towers.get(name)
        if not c:
            continue
        d = dims(c.all_objects)
        if not d:
            continue
        lo, hi, sz, nf = d
        tower_info[name] = (lo, hi, sz)
        L("  %-12s 宽(X) %5.2f m   深(Y) %5.2f m   高(Z) %5.2f m   地面高程 %.2f→%.2f   面数 %d"
          % (name, sz.x, sz.y, sz.z, lo.z, hi.z, nf))

    # ---------------------------------------------------------------- 2. 导入 FBX
    L("")
    L("=== 二、外部人物模型 ===")
    L("  文件：%s" % FBX)
    before = set(bpy.data.objects)
    if not os.path.isfile(FBX):
        L("  !! 找不到 FBX 文件")
        new = []
    else:
        try:
            bpy.ops.import_scene.fbx(filepath=FBX)
        except Exception as e:
            L("  !! 导入失败：%r" % (e,))
        new = [o for o in bpy.data.objects if o not in before]
    char_objs = [o for o in new]
    if char_objs:
        for o in char_objs:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            coll.objects.link(o)
        bpy.context.view_layer.update()
        d = dims(char_objs)
        if d:
            lo, hi, sz, nf = d
            L("  导入后原始尺寸：宽 %.3f  深 %.3f  高 %.3f （单位：米）  面数 %d" % (sz.x, sz.y, sz.z, nf))
            L("  对象：%s" % ", ".join(o.name + "[" + o.type + "]" for o in char_objs))

            # 建一个父 Empty，统一缩放旋转
            root = bpy.data.objects.new("人物_根", None)
            root.empty_display_size = 0.5
            coll.objects.link(root)
            for o in char_objs:
                if o.parent is None:
                    o.parent = root
                    o.matrix_parent_inverse = root.matrix_world.inverted()

            k = TARGET_H / sz.z if sz.z > 1e-6 else 1.0
            root.scale = (k, k, k)
            root.rotation_euler = (0, 0, math.radians(FACE_ROT_Z))
            bpy.context.view_layer.update()
            d2 = dims(char_objs)
            lo2, hi2, sz2, _ = d2
            # 落到地面、居中
            root.location = (root.location.x - (lo2.x+hi2.x)/2,
                             root.location.y - (lo2.y+hi2.y)/2,
                             root.location.z - lo2.z)
            bpy.context.view_layer.update()
            lo3, hi3, sz3, _ = dims(char_objs)
            L("  缩放系数 %.4f  →  缩放后：宽 %.3f  深 %.3f  高 %.3f m" % (k, sz3.x, sz3.y, sz3.z))
            L("  （脚底已落到 Z=0，水平居中到原点）")
            char_root = root
        else:
            char_root = None
    else:
        char_root = None

    # ---------------------------------------------------------------- 3. 放到谯楼上
    L("")
    L("=== 三、人物与谯楼的比例关系 ===")
    placements = []
    if char_root and "谯楼_建成后" in tower_info:
        lo, hi, sz = tower_info["谯楼_建成后"]
        cx = (lo.x + hi.x) / 2
        L("  建成后谯楼：总高 %.2f m，台基占地约 %.1f×%.1f m" % (sz.z, 12.6, 12.6))
        L("  人物身高 %.2f m，约为楼总高的 1/%.1f" % (TARGET_H, sz.z/TARGET_H))
        # 三个位置：台阶下 / 台基门口 / 平座上
        spots = [("台阶下", (cx, lo.y - 1.2, 0.0)),
                 ("台基门口", (cx - 2.2, -6.0 + 2.6, 2.40)),
                 ("平座上", (cx + 2.6, -4.0, 8.35))]
        base_loc = char_root.location.copy()
        for nm, loc in spots:
            bpy.ops.object.select_all(action="DESELECT")
            for o in [char_root] + char_objs:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            bpy.context.view_layer.objects.active = char_root
            bpy.ops.object.duplicate(linked=True)
            dups = [o for o in bpy.context.selected_objects]
            newroot = next((o for o in dups if o.parent not in dups), dups[0])
            newroot.name = "人物_" + nm
            newroot.location = (base_loc.x + loc[0], base_loc.y + loc[1], base_loc.z + loc[2])
            placements.append((nm, newroot, loc))
            L("  放置「%s」于 (%.1f, %.1f, %.1f)" % (nm, *loc))
        # 原始那个移到一边当参考
        char_root.location = (char_root.location.x + cx - 9.5, char_root.location.y - 9.0, char_root.location.z)
        char_root.name = "人物_参考"
    bpy.context.view_layer.update()

    # ---------------------------------------------------------------- 渲染
    if RENDER:
        os.makedirs(OUT_DIR, exist_ok=True)
        world = bpy.data.worlds.new("对齐_world"); sc.world = world
        try:
            world.use_nodes = True
            world.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.45, 0.46, 1)
            world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
        except Exception:
            pass
        for nm, loc, en, size in (("主光", (-14, -22, 24), 9000, 12), ("补光", (18, -14, 10), 2600, 16)):
            ld = bpy.data.lights.new(nm, "AREA"); ld.energy = en; ld.size = size
            lo_ = bpy.data.objects.new(nm, ld); coll.objects.link(lo_); lo_.location = loc
            lo_.rotation_euler = (Vector((60, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

        cams = []
        if "谯楼_建成后" in tower_info:
            lo, hi, sz = tower_info["谯楼_建成后"]
            cx = (lo.x+hi.x)/2
            span = max(sz.x, sz.z) * 1.25
            cd = bpy.data.cameras.new("CAM_对照_正视"); cd.type = "ORTHO"; cd.ortho_scale = span; cd.clip_end = 400
            co = bpy.data.objects.new("CAM_对照_正视", cd); coll.objects.link(co)
            co.location = (cx, -120, sz.z/2); co.rotation_euler = (math.radians(90), 0, 0)
            cams.append(("建成后_正视对照", co, (1500, 1500)))

            cd = bpy.data.cameras.new("CAM_对照_透视"); cd.lens = 45; cd.clip_end = 500
            co = bpy.data.objects.new("CAM_对照_透视", cd); coll.objects.link(co)
            co.location = (cx - 20, -26, 11)
            co.rotation_euler = (Vector((cx, 0, 5.5)) - co.location).to_track_quat("-Z", "Y").to_euler()
            cams.append(("建成后_透视对照", co, (1700, 1300)))

            # 人物单体正视（检查朝向与比例）
            cd = bpy.data.cameras.new("CAM_人物"); cd.type = "ORTHO"; cd.ortho_scale = 2.4; cd.clip_end = 400
            co = bpy.data.objects.new("CAM_人物", cd); coll.objects.link(co)
            px = char_root.location.x if char_root else 0
            py = char_root.location.y if char_root else 0
            co.location = (px, py - 40, 0.9); co.rotation_euler = (math.radians(90), 0, 0)
            cams.append(("人物_正视", co, (900, 1500)))
            cd = bpy.data.cameras.new("CAM_人物侧"); cd.type = "ORTHO"; cd.ortho_scale = 2.4; cd.clip_end = 400
            co = bpy.data.objects.new("CAM_人物侧", cd); coll.objects.link(co)
            co.location = (px - 40, py, 0.9); co.rotation_euler = (math.radians(90), 0, math.radians(-90))
            cams.append(("人物_侧视", co, (900, 1500)))

        # 三座楼全景
        if tower_info:
            allo = Vector((min(v[0].x for v in tower_info.values()), 0, 0))
            ahi = Vector((max(v[1].x for v in tower_info.values()), 0, 0))
            cd = bpy.data.cameras.new("CAM_全景"); cd.type = "ORTHO"
            cd.ortho_scale = (ahi.x - allo.x) * 1.08; cd.clip_end = 500
            co = bpy.data.objects.new("CAM_全景", cd); coll.objects.link(co)
            co.location = ((allo.x+ahi.x)/2, -150, 7); co.rotation_euler = (math.radians(90), 0, 0)
            cams.append(("三座楼_全景", co, (2400, 800)))

        sc.render.engine = "BLENDER_WORKBENCH"
        try:
            sh = sc.display.shading
            sh.light = "STUDIO"; sh.color_type = "MATERIAL"
            sh.show_cavity = True; sh.show_object_outline = True; sh.show_shadows = True
            sc.display.render_aa = "16"
        except Exception:
            pass
        sc.render.film_transparent = True
        for nm, co, (rx, ry) in cams:
            sc.camera = co
            sc.render.resolution_x, sc.render.resolution_y = rx, ry
            sc.render.filepath = OUT_DIR + "对齐_%s.png" % nm
            bpy.ops.render.render(write_still=True)
            L("  渲染 " + nm)

    L("")
    L("用时 %.1f s" % (time.time()-T0))
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_BLEND)
    print("saved", SAVE_BLEND)


if __name__ == "__main__":
    try:
        run()
    except Exception:
        import traceback
        tb = traceback.format_exc(); print(tb)
        with open(REPORT, "w", encoding="utf-8") as fh:
            fh.write("FAILED\n" + tb)
        raise
