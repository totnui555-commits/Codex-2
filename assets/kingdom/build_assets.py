"""Original Kingdom Edition art. Run: blender -b -t 2 --python assets/kingdom/build_assets.py"""

import bpy, bmesh, math, random
from pathlib import Path
from mathutils import Vector

random.seed(73)
bpy.context.preferences.filepaths.save_version = 0
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "apps/web/public/kingdom"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
M = {}
for name, color in {
    "stone": "c8ba97",
    "stone_dark": "9f9987",
    "cream": "f5e7bf",
    "wood": "73533d",
    "wood_light": "ad8156",
    "roof": "b66149",
    "roof_light": "cb7754",
    "teal": "477e80",
    "green": "658457",
    "gold": "e8b84e",
    "glass": "ffd68b",
    "ink": "303c3b",
    "grass": "87ad68",
    "grass_light": "a0bc75",
    "sand": "e3c995",
    "cliff": "b3a88c",
    "leaf": "497c59",
    "leaf_light": "70945c",
    "flower": "dd9e9e",
    "white": "f1e6d0",
    "blue": "69879e",
    "purple": "8d7096",
    "water": "75c5b9",
}.items():
    mat = bpy.data.materials.new(name)
    srgb = [int(color[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    mat.diffuse_color = tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in srgb) + (
        1,
    )
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = mat.diffuse_color
    bs.inputs["Roughness"].default_value = 0.7
    if name == "gold":
        bs.inputs["Metallic"].default_value = 0.45
    if name == "glass":
        bs.inputs["Emission Color"].default_value = mat.diffuse_color
        bs.inputs["Emission Strength"].default_value = 0.32
    M[name] = mat
parent = None


def finish(o, mat, bevel=0):
    if mat:
        o.data.materials.append(M[mat])
    if parent:
        o.parent = parent
    if bevel:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=2, affect="EDGES")
        bm.to_mesh(o.data)
        bm.free()
    return o


def box(p, s, mat, bevel=0.035):
    mesh = bpy.data.meshes.new("Soft timber and stone")
    verts = [
        (a * s[0] / 2, b * s[1] / 2, c * s[2] / 2)
        for a, b, c in [
            (-1, -1, -1),
            (-1, -1, 1),
            (-1, 1, -1),
            (-1, 1, 1),
            (1, -1, -1),
            (1, -1, 1),
            (1, 1, -1),
            (1, 1, 1),
        ]
    ]
    mesh.from_pydata(
        verts, [], [(0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4), (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6)]
    )
    mesh.update()
    o = bpy.data.objects.new("Block", mesh)
    bpy.context.collection.objects.link(o)
    o.location = p
    return finish(o, mat, bevel)


def cyl(p, r, depth, mat, vertices=24, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=vertices,
        radius1=r,
        radius2=r if r2 is None else r2,
        depth=depth,
    )
    mesh = bpy.data.meshes.new("Turned stone")
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new("Round", mesh)
    bpy.context.collection.objects.link(o)
    o.location = p
    return finish(o, mat, 0.018)


def ball(p, s, mat):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1)
    for v in bm.verts:
        v.co.x *= s[0]
        v.co.y *= s[1]
        v.co.z *= s[2]
    mesh = bpy.data.meshes.new("Sculpted foliage")
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new("Organic", mesh)
    bpy.context.collection.objects.link(o)
    o.location = p
    for f in mesh.polygons:
        f.use_smooth = True
    return finish(o, mat)


def beam(a, b, width, mat):
    d = Vector(b) - Vector(a)
    o = box((Vector(a) + Vector(b)) / 2, (width, width, d.length), mat, 0.012)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return o


def root(name, x, z, y):
    global parent
    parent = None
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = (x, -z, y)
    o["landmark_id"] = name
    parent = o
    return o


# Local model coordinates are translated into root space at the end.
def localize(root):
    for o in list(root.children):
        o.location -= root.location
    # All constructors use local coords; restore these rather than bake root translation.
    for o in list(root.children):
        o.location += root.location


def roof(w, d, h, mat="roof", base=1.7):
    vertices = [
        (-w / 2, -d / 2, base),
        (w / 2, -d / 2, base),
        (0, -d / 2, base + h),
        (-w / 2, d / 2, base),
        (w / 2, d / 2, base),
        (0, d / 2, base + h),
    ]
    mesh = bpy.data.meshes.new("Pitched roof")
    mesh.from_pydata(vertices, [], [(0, 1, 2), (3, 5, 4), (0, 2, 5, 3), (2, 1, 4, 5), (0, 3, 4, 1)])
    mesh.update()
    o = bpy.data.objects.new("Roof", mesh)
    bpy.context.collection.objects.link(o)
    finish(o, mat, 0.04)
    # Layered tile courses on both slopes, each tile has a softened lip.
    for side in (-1, 1):
        angle = math.atan2(h, w / 2)
        for row in range(5):
            t = (row + 0.5) / 5
            x = side * w / 2 * (1 - t)
            z = base + h * t + 0.035
            for col in range(7):
                tile = box(
                    (x, -d / 2 + (col + 0.5) * d / 7, z),
                    (math.hypot(w / 2, h) / 5 * 0.99, d / 7 * 0.96, 0.055),
                    "roof_light" if (row + col) % 4 == 0 else mat,
                    0.018,
                )
                tile.rotation_euler[1] = -side * angle
    beam((0, -d / 2 - 0.04, base + h + 0.07), (0, d / 2 + 0.04, base + h + 0.07), 0.12, "wood")


def window(x, y, z):
    box((x, y, z), (0.38, 0.08, 0.49), "wood")
    box((x, y - 0.052, z), (0.29, 0.045, 0.39), "glass", 0.02)
    box((x, y - 0.08, z), (0.035, 0.035, 0.43), "wood", 0.005)
    box((x, y - 0.08, z), (0.31, 0.035, 0.035), "wood", 0.005)
    box((x, y - 0.12, z - 0.27), (0.48, 0.24, 0.1), "wood_light")


def house(name, x, z, y, w=2, d=1.7, h=1.6, roofmat="roof"):
    r = root(name, x, z, y)
    box((0, 0, 0.12), (w + 0.25, d + 0.25, 0.24), "stone")
    box((0, 0, h / 2 + 0.15), (w, d, h), "cream", 0.07)
    for a in (-1, 1):
        for b in (-1, 1):
            box((a * (w / 2 - 0.06), b * (d / 2 - 0.03), h / 2 + 0.15), (0.12, 0.12, h), "wood")
    for level in (0.3, h + 0.08):
        box((0, -d / 2 - 0.025, level), (w + 0.04, 0.09, 0.12), "wood")
    box((0, -d / 2 - 0.06, 0.66), (0.48, 0.1, 1.03), "wood")
    box((0, -d / 2 - 0.12, 0.66), (0.35, 0.025, 0.86), "wood_light")
    ball((0.13, -d / 2 - 0.16, 0.65), (0.035, 0.035, 0.035), "gold")
    for a in (-1, 1):
        window(a * w * 0.31, -d / 2 - 0.05, 1.05)
    roof(w + 0.4, d + 0.38, 0.95, roofmat, h + 0.12)
    box((w * 0.28, 0.2, h + 0.7), (0.3, 0.35, 1), "stone")
    box((w * 0.28, 0.2, h + 1.23), (0.4, 0.43, 0.13), "stone_dark")
    for a in (-1, 1):
        box((a * w * 0.36, -d / 2 - 0.3, 0.18), (0.5, 0.35, 0.28), "wood_light")
        for j in range(3):
            ball((a * w * 0.36 + (j - 1) * 0.13, -d / 2 - 0.3, 0.4), (0.12, 0.13, 0.16), "leaf_light")
            ball((a * w * 0.36 + (j - 1) * 0.13, -d / 2 - 0.3, 0.52), (0.07, 0.07, 0.07), "flower")
    return r


# Terrain. A continuous smooth multi-ring shoreline, not a rectangular platform.
root("landscape", 0, 0, 0)
N = 160
verts = []
for radius, height in [(1.02, -0.85), (1.05, -0.15), (1, 0.1), (0.955, 0.47), (0.88, 0.52), (0, 0.52)]:
    for i in range(N):
        a = i * math.tau / N
        r = 1 + 0.045 * math.sin(5 * a) + 0.025 * math.cos(9 * a)
        verts.append((14 * radius * r * math.cos(a), 10 * radius * r * math.sin(a), height))
faces = []
for ring in range(5):
    for i in range(N):
        faces.append((ring * N + i, ring * N + (i + 1) % N, (ring + 1) * N + (i + 1) % N, (ring + 1) * N + i))
mesh = bpy.data.meshes.new("Sculpted continuous island")
mesh.from_pydata(verts, [], faces)
mesh.update()
o = bpy.data.objects.new("Island", mesh)
bpy.context.collection.objects.link(o)
for mat in ("cliff", "sand", "grass", "grass_light"):
    o.data.materials.append(M[mat])
for f in o.data.polygons:
    f.material_index = 0 if f.index // N < 1 else 1 if f.index // N < 3 else 2
    f.use_smooth = True
o.parent = parent
# Keep terraces and western ridge.
for x, y, s in [
    (0, 5, (3.1, 2.5, 0.85)),
    (-10, 2.5, (2.1, 2.1, 1.3)),
    (-3.5, 5, (1.7, 1.9, 0.3)),
    (3.5, 4.5, (1.9, 1.7, 0.3)),
]:
    ball((x, y, 0.45), s, "grass")
for i in range(42):
    a = i * math.tau / 42
    rr = 1 + 0.04 * math.sin(a * 5)
    ball(
        (13.4 * rr * math.cos(a), 9.4 * rr * math.sin(a), 0.04),
        (random.uniform(0.25, 0.6), random.uniform(0.25, 0.55), random.uniform(0.2, 0.45)),
        "stone_dark" if i % 3 else "stone",
    )
# Roads, timber borders and stepping stones.
paths = [
    [(0, -3), (0, 1.4), (0, 3.1), (0, 3.6)],
    [(0, 1.4), (-6, 1.4), (-8, 1.4), (-9, 1)],
    [(0, 1.4), (5, 0.1), (7.8, 0.1)],
    [(0, -3), (4, -4.4), (7, -5.1)],
    [(-3, -3.5), (0, -3)],
]
for path in paths:
    for a, b in zip(path, path[1:]):
        distance = math.dist(a, b)
        steps = max(1, int(distance / 0.3))
        for i in range(steps):
            t = i / steps
            for side in (-1, 1):
                px = a[0] * (1 - t) + b[0] * t
                py = a[1] * (1 - t) + b[1] * t + side * 0.22
                height = 0.54
                for hx, hy, sx, sy, sz in [(0, 5, 3.1, 2.5, 0.85), (-10, 2.5, 2.1, 2.1, 1.3)]:
                    q = ((px - hx) / sx) ** 2 + ((py - hy) / sy) ** 2
                    if q < 1:
                        height = max(height, 0.48 + sz * math.sqrt(1 - q))
                p = (px, py, height)
                stone = box(p, (0.29, 0.32, 0.055), "stone" if i % 3 else "sand", 0.05)
                stone.rotation_euler[2] = random.uniform(-0.12, 0.12)
# Trees: smooth clustered crowns, roots and layered foliage.
for x, y, scale in [
    (-11, -1, 0.9),
    (-11, 5, 1),
    (-8, 6, 1.1),
    (-6, 6, 0.85),
    (-6, 4, 1),
    (-8, -4, 1),
    (-10, -4, 0.8),
    (-7, -6, 0.85),
    (-5, -6, 0.7),
    (11, 2, 0.9),
    (11, -1, 0.7),
    (8, 6, 0.85),
    (5, 7, 0.7),
    (2, 8, 0.8),
    (-1, 8, 0.7),
    (-3, 7, 0.8),
    (-12, 2, 0.75),
]:
    cyl((x, y, 0.5 + 0.7 * scale), 0.16 * scale, 1.4 * scale, "wood", 12)
    for j in range(6):
        a = j * 2.4
        ball(
            (
                x + math.cos(a) * 0.4 * scale,
                y + math.sin(a) * 0.4 * scale,
                1.7 * scale + 0.5 + (j % 2) * 0.35,
            ),
            (0.7 * scale, 0.65 * scale, 0.72 * scale),
            "leaf" if j % 2 else "leaf_light",
        )
# Flower beds, grass tufts, fences, crates and garden plots.
for i in range(75):
    a = random.random() * math.tau
    rad = random.uniform(0.78, 0.92)
    x = 13 * rad * math.cos(a)
    y = 9 * rad * math.sin(a)
    for j in range(2):
        ball((x + j * 0.12, y, 0.6), (0.09, 0.09, 0.15), "leaf_light")
        ball((x + j * 0.12, y, 0.76), (0.07, 0.07, 0.06), "flower" if i % 3 else "gold")
for x, y in [(-5, -4.5), (-6, -3.5), (-8, -2.8)]:
    box((x, y, 0.55), (1.4, 0.9, 0.08), "wood")
    for i in range(5):
        for j in range(3):
            ball((x - 0.5 + i * 0.24, y - 0.3 + j * 0.28, 0.67), (0.11, 0.11, 0.1), "leaf_light")
for i in range(10):
    x = -6 + i * 0.38
    box((x, -5.3, 0.85), (0.1, 0.1, 0.7), "wood_light")
    box((x, -5.3, 1), (0.5, 0.06, 0.08), "wood_light")
# Hero keep with masonry bands, corner turrets and gold flags.
r = root("keep", 0, -5, 1.5)
box((0, 0, 0.12), (3.9, 2.8, 0.24), "stone_dark")
box((0, 0, 1.18), (2.9, 2, 2.15), "stone", 0.08)
roof(3.15, 2.3, 1.3, "teal", 2.28)
for x in (-1.65, 1.65):
    for y in (-1.1, 1.1):
        cyl((x, y, 1.45), 0.48, 2.9, "stone")
        cyl((x, y, 2.85), 0.57, 0.3, "stone_dark")
        cyl((x, y, 3.35), 0.68, 0.9, "teal", 32, r2=0.025)
        for level in (0.5, 1.4, 2.2):
            cyl((x, y, level), 0.495, 0.07, "stone_dark")
        beam((x, y, 3.8), (x, y, 4.45), 0.035, "gold")
        box((x + 0.19, y, 4.25), (0.4, 0.035, 0.23), "gold")
box((0, -1.035, 0.67), (0.73, 0.12, 1.3), "wood")
cyl((0, -1.11, 1.32), 0.36, 0.08, "wood", 24).rotation_euler[0] = math.pi / 2
for x in (-0.88, 0.88):
    window(x, -1.05, 1.55)
    box((x, -1.1, 2.18), (0.28, 0.045, 0.7), "gold")
for i in range(7):
    box((0, -1.7 - i * 0.22, -0.04 - i * 0.13), (1.3, 0.24, 0.18), "stone")
# Lighthouse is independent and visibly west of the keep.
r = root("lighthouse", -10, -2.5, 1.6)
cyl((0, 0, 1.65), 0.75, 3.3, "stone", 40, r2=0.54)
for z in (0.25, 1.1, 2, 2.9):
    cyl((0, 0, z), 0.77 - z * 0.06, 0.12, "stone_dark", 40)
cyl((0, 0, 3.35), 0.9, 0.15, "wood")
cyl((0, 0, 3.8), 0.64, 0.8, "glass")
cyl((0, 0, 4.3), 0.96, 0.55, "teal", 32, r2=0.03)
for i in range(8):
    a = i * math.tau / 8
    x = 0.69 * math.cos(a)
    y = 0.69 * math.sin(a)
    beam((x, y, 3.45), (x, y, 4.2), 0.065, "wood")
box((0, -0.69, 0.65), (0.4, 0.1, 1.05), "wood")
for i in range(9):
    box((0.2, -1 - i * 0.2, 0.05 - i * 0.13), (1, 0.23, 0.16), "stone")
# Separate village landmarks.
house("guild", -3, -0.3, 0.55, 2.8, 2, 1.75, "green")
house("library", -3.5, -5, 0.7, 2, 1.65, 1.7, "teal")
house("treasury", 3.5, -4.5, 0.7, 2, 1.7, 1.65, "teal")
house("workshop", 6, -1.5, 0.55, 2.6, 2, 1.65, "roof")
# Workshop gear, copper boiler, workbench and stacked timber.
for i in range(10):
    a = i * math.tau / 10
    box((1.4 + math.cos(a) * 0.43, -1.05, 1.7 + math.sin(a) * 0.43), (0.13, 0.15, 0.19), "gold")
cyl((1.4, -1.05, 1.7), 0.35, 0.16, "wood", 24).rotation_euler[0] = math.pi / 2
cyl((-1.55, 0, 0.6), 0.4, 1.1, "gold")
cyl((-1.55, 0, 1.25), 0.12, 0.35, "wood")
box((0, -1.65, 0.58), (1.2, 0.5, 0.16), "wood_light")
beam((-0.5, -1.65, 0.12), (-0.5, -1.65, 0.52), 0.1, "wood")
beam((0.5, -1.65, 0.12), (0.5, -1.65, 0.52), 0.1, "wood")
house("atelier", 6, 2, 0.55, 2, 1.7, 1.6, "purple")
box((1.3, -0.5, 0.75), (0.07, 0.8, 1.2), "wood_light")
box((1.25, -0.55, 1), (0.07, 0.65, 0.6), "white")
ball((1.19, -0.6, 1), (0.05, 0.2, 0.19), "flower")
house("alchemy", 9, -3.3, 0.6, 1.9, 1.7, 1.8, "blue")
for i in range(3):
    ball((-0.4 + i * 0.35, -1.25, 0.85), (0.13, 0.13, 0.19), "teal" if i % 2 else "purple")
    cyl((-0.4 + i * 0.35, -1.25, 1.05), 0.055, 0.2, "glass")
house("post", 0, 1, 0.55, 1.8, 1.5, 1.35, "roof")
box((1.2, -0.6, 0.7), (0.4, 0.35, 0.6), "teal")
box((1.2, -0.79, 0.82), (0.26, 0.025, 0.04), "ink")
box((0, -0.82, 1.3), (0.46, 0.05, 0.3), "gold")
house("market", 2.8, 5, 0.55, 1.7, 1.4, 1.4, "green")
for x in (-1.6, 1.6):
    for a in (-1, 1):
        box((x + a * 0.48, -1.2, 0.65), (0.07, 0.07, 1.3), "wood")
    for i in range(5):
        box((x - 0.4 + i * 0.2, -1.2, 1.35), (0.2, 1, 0.08), "white" if i % 2 else "roof_light")
    box((x, -1.2, 0.55), (1.1, 0.7, 0.6), "wood_light")
    for i in range(4):
        ball((x - 0.35 + i * 0.23, -1.2, 0.95), (0.13, 0.13, 0.12), "gold" if i % 2 else "flower")
house("shipyard", 7, 6, 0.3, 1.7, 1.2, 1.1, "teal")
# Pier and moored boat with curved hull, ribs, mast and cream sail.
for i in range(22):
    box((0, -1.2 - i * 0.19, 0.06), (1.3, 0.17, 0.14), "wood_light")
for side in (-1, 1):
    for i in range(4):
        cyl((side * 0.58, -1.4 - i * 1.05, -0.25), 0.085, 0.9, "wood", 12)
root("harbor-boat", 9, 8, 0.05)
ball((0, 0, 0), (0.6, 1.3, 0.27), "wood")
box((0, 0, 0.2), (0.88, 2, 0.12), "wood_light")
beam((0, 0, 0.2), (0, 0, 2.1), 0.065, "wood")
mesh = bpy.data.meshes.new("Original canvas sail")
mesh.from_pydata([(0.05, 0, 0.6), (0.05, 0, 2), (0.05, -1.1, 0.6)], [], [(0, 1, 2)])
o = bpy.data.objects.new("Sail", mesh)
bpy.context.collection.objects.link(o)
finish(o, "white")
o.data.materials[0].use_backface_culling = False
# Commons fountain and cottages provide a village rather than a corporate campus.
root("commons", -3, 3.5, 0.5)
cyl((0, 0, 0.15), 1, 0.3, "stone")
cyl((0, 0, 0.32), 0.8, 0.08, "water")
cyl((0, 0, 0.65), 0.18, 0.8, "stone")
ball((0, 0, 1.12), (0.24, 0.24, 0.24), "gold")
for i, (x, z) in enumerate([(-7, 2), (-8, 4), (-5, 5.7), (0, 7.2)]):
    house("cottage-" + str(i), x, z, 0.53, 1.35, 1.2, 1.05, "roof" if i % 2 else "green")
# Convert root-local objects to intentional glTF hierarchy; merge material batches per root.
for r in [o for o in bpy.context.scene.objects if o.type == "EMPTY"]:
    children = [o for o in r.children if o.type == "MESH"]
    bymat = {}
    for o in children:
        key = tuple(m.name for m in o.data.materials)
        bymat.setdefault(key, []).append(o)
    for objects in bymat.values():
        bpy.ops.object.select_all(action="DESELECT")
        for o in objects:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        merged = bpy.context.object
        merged.name = r.name + "__" + (merged.data.materials[0].name if merged.data.materials else "terrain")
        merged["landmark_id"] = r.get("landmark_id", "")
# Ambient art is deterministic and original, licensed with the repository.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "assets/kingdom/island.blend"), compress=True)
bpy.ops.export_scene.gltf(
    filepath=str(OUT / "island.glb"), export_format="GLB", export_extras=True, export_yup=True
)
# Runtime LODs preserve the full-resolution Blender source and hero export.
for quality, ratio in [("balanced", 0.55), ("low", 0.25)]:
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            modifier = obj.modifiers.get("Runtime LOD") or obj.modifiers.new("Runtime LOD", "DECIMATE")
            modifier.ratio = ratio
    bpy.ops.export_scene.gltf(
        filepath=str(OUT / ("island-" + quality + ".glb")),
        export_format="GLB",
        export_extras=True,
        export_yup=True,
        export_apply=True,
    )
# Original villager model, separate source; named limbs support client animation.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
parent = None
body = box((0, 0, 0.39), (0.23, 0.15, 0.27), "teal", 0.06)
body.name = "Tunic"
head = ball((0, 0, 0.65), (0.14, 0.12, 0.15), "cream")
head.name = "Face"
for x in (-0.047, 0.047):
    ball((x, -0.11, 0.67), (0.018, 0.018, 0.022), "ink")
ball((0, -0.124, 0.62), (0.022, 0.023, 0.02), "roof_light")
hat = cyl((0, 0, 0.83), 0.18, 0.24, "teal", 20, r2=0.025)
hat.name = "Hat"
cyl((0, 0, 0.73), 0.19, 0.035, "wood_light")
for side in (-1, 1):
    leg = box((side * 0.065, 0, 0.15), (0.08, 0.1, 0.23), "wood", 0.03)
    leg.name = "LegLeft" if side < 0 else "LegRight"
    arm = box((side * 0.16, 0, 0.4), (0.07, 0.1, 0.22), "teal", 0.035)
    arm.name = "ArmLeft" if side < 0 else "ArmRight"
    ball((side * 0.16, -0.02, 0.28), (0.045, 0.05, 0.05), "cream")
box((0, -0.09, 0.38), (0.2, 0.025, 0.04), "wood_light")
box((0.12, 0.07, 0.45), (0.12, 0.1, 0.14), "wood_light")
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "assets/kingdom/citizen.blend"), compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT / "citizen.glb"), export_format="GLB", export_yup=True)
print("KINGDOM_ASSETS_COMPLETE", OUT)
