# Catalog data pipeline

This folder holds the supplier PDF extraction pipeline and the resulting data used to
build `catalog/index.html` (the live filterable-grid catalog, 640 rings / 315 designs).
Kept here so a future session doesn't have to redo PDF extraction, color classification,
and design-grouping from scratch.

## Files

- `extract_products.py` — original extraction script (documented, no position data).
- `extract_products_v2.py` — **the one actually used for the current catalog.** Same
  extraction logic (position-based SKU-to-photo matching from the PDF) but also records
  each item's `row` (rounded y-position) and `cx` (x-center), needed for design-grouping.
  Run: `python3 extract_products_v2.py /path/to/supplier.pdf /path/to/output_dir`
  → `<output_dir>/images/*.png` (one crop per ring) + `<output_dir>/meta.json`.
- `classify_color.py` — classifies a cropped ring photo as `yellow` / `white` / `rose`
  gold by sampling pixel colors. Calibrated against known reference SKUs from the Aug
  2026 PDF (60425=yellow, 60426=white, 60427=rose, 65001=white+diamond) — re-validate
  against a few known examples if the supplier ever sends photos shot under different
  lighting.
- `build_designs.py` — groups the flat per-SKU item list into "designs" (same physical
  design, different gold colors / diamond options). Items on the same PDF page/row are
  sorted by `cx` (left-to-right) and split into separate designs wherever the gap
  between consecutive items exceeds 75pt — this threshold was picked by inspecting the
  actual gap distribution in the Aug 2026 PDF (intra-design gaps cluster at 56–68pt,
  inter-design gaps start at 83pt+). Re-check this threshold if a new PDF has different
  spacing.
- `make_squares.py` — auto-trims each ring photo to its content bounding box (removing
  excess white margin) and pads to a clean 500×500 square JPEG, ready for the catalog
  grid. Reads from an extraction output folder, writes to a flat folder of `.jpg` files.
- `designs.json` — **the actual dataset used to build the live catalog.** 315 designs,
  640 total variants. Each design: `design_id`, `page`, `type` (PLANA/CONFORT/PLANO),
  `mm` (width, often `null` — see Known limitations), `weight`, `category` (`gold` or
  `silver`), and a `variants` array of `{sku, color, has_diamond, extras, file, img}`.
  `img` is the filename in `catalog/rings-images/` (renamed to `<sku>.jpg` from the
  extraction's `p<page>_<sku>.png`).
- `all_640_products_by_category.json`, `currently_live_155.json` — **superseded.** These
  were from the earlier 16-category/155-curated-ring flipbook catalog (pre-Aug-14
  rebuild). Kept for reference only; `designs.json` is the current source of truth.

## Pipeline order (to rebuild from a new supplier PDF)

1. `python3 extract_products_v2.py new_catalog.pdf /tmp/extract_out`
2. For each item's `file`, run `classify_color.py` to get yellow/white/rose, and check
   `extras` (any entry starting with `Br.` means it has a diamond) — see
   `build_designs.py` for how this was scripted in bulk (`classify_color` imported and
   called per image, results merged into the meta.json item list before grouping).
3. `python3 build_designs.py` (edit the input/output paths at the top) → produces the
   grouped `designs.json`-equivalent.
4. `python3 make_squares.py` (edit the input/output paths at the top) → produces clean
   square thumbnails in a flat folder; copy into `catalog/rings-images/` named
   `<sku>.jpg`.
5. Build the compact JS-embeddable data array from `designs.json` (id, cat, style, mm,
   wt, hasDia, and a `v` array of `{sku, c, d, img}` — see the `var DESIGNS = [...]`
   block near the bottom of `catalog/index.html` for the exact shape expected by the
   page's JS) and splice it into the `catalog/index.html` template in place of the
   `DESIGNS` array.
6. **Before touching the live file: grep the whole output (HTML + JSON + image
   filenames) case-insensitively for `franco`, `alianzas ssf`, `simón franco` — the
   supplier's own branding must never appear on the site. This has been a hard,
   repeated requirement from Sandy.** The brand-safety check that's been used each time:
   `grep -rlia "franco\|alianzas ssf\|simón franco" <output dir>` should return nothing.

## Known limitations (as of the Aug 14, 2026 build)

- **Width (mm) is missing for ~178 of 315 gold designs.** The PDF only prints an
  explicit "`X mm`" label near some rows; where it's missing, `mm` is `null`. All 116
  silver ("Plata de Ley 925") designs have it. Because of this, width is shown on cards
  where known but is **not** used as a filter — showing an unreliable/incomplete filter
  would be worse than not having one.
- **Two-tone (e.g. white+yellow gold blend) designs are not detected.** A pixel-based
  two-tone heuristic (checking for two significant color clusters in one photo) was
  tried and rejected: it had a ~27% false-positive rate on the gold section (ordinary
  specular highlights on a solid-gold ring get misread as a second color) vs. ~8.5% on
  the silver section, where a hand-checked sample did confirm genuine two-tone (silver
  body + gold accent stripe) designs. If Sandy supplies reference SKUs/photos for the
  white+yellow blend line, those can be manually tagged rather than auto-detected.
- **"Plata de Ley 925" (sterling silver) section, pages 36–43 of the PDF, 129 items /
  116 designs, SKUs starting `90xxx`.** This is genuinely silver per the PDF's own page
  headers (confirmed by reading the raw PDF text, not inferred). Sandy's normal metal
  lineup is White/Yellow/Rose Gold + a two-tone blend — no silver — but she chose to
  keep this section on the site, correctly labeled "Sterling Silver" (see
  `catalog/index.html`'s `variantLabel()` / `metalLabel()` functions — silver-category
  items must never be labeled with a gold color name).
