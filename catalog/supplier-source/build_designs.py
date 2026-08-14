import json
from collections import OrderedDict

d = json.load(open('/tmp/products_classified.json'))

buckets = OrderedDict()
for it in d:
    key = (it['page'], it['row'], it['weight'], it['type'], it['mm'])
    buckets.setdefault(key, []).append(it)

GAP_THRESHOLD = 75
designs = []
did = 0
for key, items in buckets.items():
    items_sorted = sorted(items, key=lambda x: x['cx'])
    cur = [items_sorted[0]]
    for prev, it in zip(items_sorted, items_sorted[1:]):
        if it['cx'] - prev['cx'] > GAP_THRESHOLD:
            designs.append(cur)
            cur = []
        cur.append(it)
    designs.append(cur)

print('total designs:', len(designs))
sizes = {}
for g in designs:
    sizes[len(g)] = sizes.get(len(g),0)+1
print('size distribution:', sizes)

# sanity: total items across designs must equal 640
total_items = sum(len(g) for g in designs)
print('total items check:', total_items)

# Build final design records
out = []
for i, g in enumerate(designs):
    variants = []
    for it in g:
        variants.append({
            "sku": it['sku'],
            "color": it['color'],
            "has_diamond": it['has_diamond'],
            "extras": it['extras'],
            "file": it['file']
        })
    rep = g[0]
    out.append({
        "design_id": f"d{i+1:04d}",
        "page": rep['page'],
        "type": rep['type'],
        "mm": rep['mm'],
        "weight": rep['weight'],
        "category": "silver" if rep['page'] >= 36 else "gold",
        "variants": variants
    })

with open('/tmp/designs.json','w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

print('sample design with 8 raw items (should now be split to 2):')
for g in designs:
    if any(x['sku']=='60425' for x in g):
        print([ (x['sku'],x['color']) for x in g])
