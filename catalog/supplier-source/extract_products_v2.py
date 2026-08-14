# Extracts individual ring product photos + SKU/weight/type metadata from the
# Simon Franco (Alianzas SSF) wholesale supplier PDF catalog.
#
# Usage:
#   pip install pymupdf --break-system-packages
#   python3 extract_products.py /path/to/supplier_catalog.pdf /path/to/output_dir
#
# Output: <output_dir>/images/*.png (one crop per ring) + <output_dir>/meta.json
# (all extracted items, page order) which you then group/curate similar to
# all_640_products_by_category.json before building new REF_SECTIONS entries.
#
# Note: GOLD_PAGES / SILVER_PAGES below are the page ranges (1-indexed, PDF
# page numbers) that contained gold vs silver product grids in the Aug 2026
# PDF (catalogo_260813_175910.pdf). If the supplier sends a differently laid
# out PDF, re-check these ranges (pages 1-3, 34-35, 44-48 in that PDF were
# cover/branding/certification pages and were deliberately skipped so no
# Simon Franco / Alianzas SSF branding gets pulled in).

import sys, fitz, re, json, os

pdf_path = sys.argv[1] if len(sys.argv) > 1 else "/path/to/supplier_catalog.pdf"
out_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/extract"

doc = fitz.open(pdf_path)

GOLD_PAGES = list(range(4, 34))
SILVER_PAGES = list(range(36, 44))
ALL_PAGES = GOLD_PAGES + SILVER_PAGES

SKU_RE = re.compile(r'^\d{4,5}(_\d)?$')
WEIGHT_RE = re.compile(r'^[\d,]+\s*gr\.?$', re.I)
TYPE_RE = re.compile(r'^(PLANA|CONFORT|PLANO)$', re.I)
EXTRA_RE = re.compile(r'^(Br\.|Cz)', re.I)
MM_RE = re.compile(r'^\d[\d,]*\s*mm$')

os.makedirs(f"{out_dir}/images", exist_ok=True)
results = []
ZOOM = 5.0
mat = fitz.Matrix(ZOOM, ZOOM)

for pno in ALL_PAGES:
    page = doc[pno-1]
    d = page.get_text("dict")
    spans = []
    for block in d["blocks"]:
        if "lines" not in block: continue
        for line in block["lines"]:
            for span in line["spans"]:
                txt = span["text"].strip()
                if not txt: continue
                x0,y0,x1,y1 = span["bbox"]
                spans.append({"text": txt, "x0":x0,"y0":y0,"x1":x1,"y1":y1,"cx":(x0+x1)/2})

    skus = [s for s in spans if SKU_RE.match(s["text"])]
    mm_labels = sorted([s for s in spans if MM_RE.match(s["text"])], key=lambda s: s["y0"])
    title_candidates = [s for s in spans if s["y0"] < 90]
    title = title_candidates[0]["text"].strip() if title_candidates else None

    items = []
    for sku_span in skus:
        cx = sku_span["cx"]
        y0 = sku_span["y0"]
        # gather nearby texts below sku within same column, y0..y0+40
        nearby = [s for s in spans if s is not sku_span and abs(s["cx"]-cx) < 20 and s["y0"] > y0 - 2 and s["y0"] < y0 + 45]
        nearby.sort(key=lambda s: s["y0"])
        weight = next((s["text"] for s in nearby if WEIGHT_RE.match(s["text"])), None)
        typ = next((s["text"] for s in nearby if TYPE_RE.match(s["text"])), None)
        extras = [s["text"] for s in nearby if EXTRA_RE.match(s["text"])]
        # nearest mm label above this item
        mm = None
        for m in mm_labels:
            if m["y0"] < y0:
                mm = m["text"]
            else:
                break
        items.append({
            "sku": sku_span["text"], "cx": cx, "y0": y0,
            "weight": weight, "type": typ, "extras": extras, "mm": mm
        })

    items.sort(key=lambda it: (round(it["y0"]/10), it["cx"]))

    page_result = {"page": pno, "title": title, "items": []}
    for idx, it in enumerate(items):
        crop = fitz.Rect(it["cx"]-30, it["y0"]-98, it["cx"]+30, it["y0"]-3)
        crop = crop & page.rect
        fname = f"p{pno}_{it['sku']}.png"
        try:
            pix = page.get_pixmap(matrix=mat, clip=crop)
            pix.save(f"{out_dir}/images/{fname}")
        except Exception as e:
            fname = None
        page_result["items"].append({
            "sku": it["sku"], "weight": it["weight"], "type": it["type"],
            "extras": it["extras"], "mm": it["mm"], "file": fname,
            "row": round(it["y0"]/10), "cx": round(it["cx"],1)
        })
    results.append(page_result)

with open(f"{out_dir}/meta.json","w") as f:
    json.dump(results, f, indent=1, ensure_ascii=False)

total = sum(len(p["items"]) for p in results)
missing_weight = sum(1 for p in results for it in p["items"] if not it["weight"])
print("pages:", len(results), "total items:", total, "missing weight:", missing_weight)
