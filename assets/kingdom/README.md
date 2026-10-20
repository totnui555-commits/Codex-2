# Original Kingdom art kit

All models and materials here were authored for this repository; no downloaded game models, proprietary character designs or external textures are used. Rebuild with Blender 4.3+:

```bash
blender -b -t 2 --python assets/kingdom/build_assets.py
python scripts/validate_kingdom_assets.py
```

`island.blend` contains the high-detail island and individually named landmark roots. `citizen.blend` contains an original villager with named face, tunic, hat, pouch and separate limbs. Client transforms animate the named limbs; this is not a motion-captured or skeletal animation library. Original modular architecture includes softened timber frames, tiled pitched roofs, inset windows, flower boxes, stone bands, terraces, castle turrets/banners, workshop gears, alchemy props, harbor stalls, a pier/boat, garden plots, fences, foliage and cobblestone roads.

GLB packs live in `apps/web/public/kingdom/`: high-detail island, balanced/low decimated LODs and the reusable citizen. Geometry is batched by landmark/material; citizens use per-part GPU instancing across the configured cast. All files are self-contained and carry no operational records or credentials. World placement is x/z, with one model unit representing eight fictitious world units (~224 units across). The twelve-landmark registry lives in `apps/web/src/lib/kingdom.ts`.

The high source/export stays intact when generating lighter runtime LODs. Materials are authored in linear color space from the specified sRGB palette. Runtime water/shore foam is an original shader. Static contact shadows are computed at scene load; moving citizens use small selection/status footprints rather than rebuilding all island shadows each frame. Quality tiers control LOD, pixel ratio, antialiasing and shadow resolution. Hardware GPU/frame-time certification and further bespoke character/foliage detail remain separate acceptance work; software-renderer evidence is not a hardware performance guarantee.
