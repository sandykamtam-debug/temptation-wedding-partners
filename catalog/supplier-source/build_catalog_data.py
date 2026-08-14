# Converts designs.json (full/verbose format) into the compact JSON array that gets
# embedded directly into catalog/index.html as `var DESIGNS = [...]`.
#
# Usage: python3 build_catalog_data.py designs.json catalog_data.json

import json, re, sys

src = sys.argv[1] if len(sys.argv) > 1 else "designs.json"
dst = sys.argv[2] if len(sys.argv) > 2 else "catalog_data.json"

d = json.load(open(src))

def parse_mm(mm):
    if not mm:
        return None
    m = re.match(r'([\d,]+)', mm)
    if not m:
        return None
    return float(m.group(1).replace(',', '.'))

out = []
for des in d:
    typ = des["type"]
    style = "flat" if typ in ("PLANA", "PLANO") else "comfort"
    variants = []
    has_diamond_any = False
    for v in des["variants"]:
        variants.append({
            "sku": v["sku"],
            "c": v["color"][0],       # 'y' / 'w' / 'r'
            "d": 1 if v["has_diamond"] else 0,
            "img": v["img"],          # filename in catalog/rings-images/
        })
        if v["has_diamond"]:
            has_diamond_any = True
    out.append({
        "id": des["design_id"],
        "cat": "silver" if des["category"] == "silver" else "gold",
        "style": style,
        "mm": parse_mm(des["mm"]),
        "wt": des["weight"],
        "hasDia": has_diamond_any,
        "v": variants,
    })

with open(dst, "w") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

print(f"designs: {len(out)} -> {dst}")
