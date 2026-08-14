# Project Log — Temptation Jewellery Wedding Site

Running record of work done on this repo, kept up to date so anyone (including future-you or a future Claude session) can see what's finished and exactly where to pick things up.

Live site: https://wedding.temptationjewellery.com/
Live catalog: https://wedding.temptationjewellery.com/catalog/
Repo: `sandykamtam-debug/temptation-wedding-partners` on GitHub

---

## 1. Git / GitHub access — DONE

**Problem found:** the git remote URL had a GitHub personal access token embedded in it in plain text (`https://ghp_xxx@github.com/...`), and pushes were sometimes typed with the token pasted directly into the command — both leave the token sitting in `.git/config` and shell history.

**Fixed:**
- Old token revoked and a new one generated on GitHub (done directly on github.com by Sandy).
- Remote URL cleaned to the plain form (no embedded credentials).
- Discovered the real intermittent-push-failure cause: the GitHub CLI (`gh`) is registered as this Mac's global git credential helper (overrides `osxkeychain`), and it had **two** logged-in accounts — `ksandeepsanjay-eng` and `sandykamtam-debug` — with the wrong one (`ksandeepsanjay-eng`) set active, causing `Permission denied (403)` pushes to this repo.
- **Permanent fix:** set up per-account SSH instead of relying on `gh`'s single "active account":
  - SSH keys: `~/.ssh/id_ed25519_sandykamtam` and `~/.ssh/id_ed25519_ksandeepsanjay` (already existed, registered to the matching GitHub accounts).
  - `~/.ssh/config` host aliases: `github-sandykamtam` and `github-ksandeepsanjay`.
  - This repo's remote is now: `git@github-sandykamtam:sandykamtam-debug/temptation-wedding-partners.git`
  - Verified with `ssh -T git@github-sandykamtam` → authenticates as `sandykamtam-debug`.

**Where to start if push ever fails again:**
1. `git remote -v` — confirm it's still the `github-sandykamtam` SSH alias, not `https://...` with a token, and not plain `github.com`.
2. `ssh -T git@github-sandykamtam` — should say "Hi sandykamtam-debug!". If it doesn't, the SSH key may have been removed from the GitHub account, or `~/.ssh/config` got edited.
3. For the OTHER project (`ksandeepsanjay-eng`'s repos), use the `github-ksandeepsanjay` alias the same way — don't rely on `gh auth switch`.

**Reminder:** Cloud Claude/Cowork sessions can read/clone this repo but cannot `git push` to it (403 from the session's git proxy — this repo isn't in its authorized set). All deploys go through Sandy running commands on her Mac, in the current clone (`~/Desktop/temptation-wedding-partners` — see §6).

---

## 2. Wedding catalog — current architecture (rebuilt Aug 14, 2026)

The catalog is now a normal static page + a folder of individual JPEG images — **not** a bundled/base64 flipbook. This replaced the earlier flipbook format entirely (see §5 for that old format, kept for historical reference only).

- **`catalog/index.html`** (~80KB) — the whole catalog page: markup, CSS, and a `var DESIGNS = [...]` JS array containing all product data inline. Loads product photos as plain `<img src="rings-images/<sku>.jpg">` tags (lazy-loaded), not embedded — much lighter than the old base64 bundle and lets the browser cache images normally.
- **`catalog/rings-images/`** — 640 individual JPEG photos (500×500, one per SKU/color/diamond variant), named `<sku>.jpg`. Auto-cropped from the supplier PDF, background-trimmed and padded to a clean square.
- **`catalog/supplier-source/`** — the extraction/classification/grouping pipeline and its output data (`designs.json`), so the whole thing can be rebuilt or extended without redoing PDF extraction from scratch. **See `catalog/supplier-source/README.md` for the full pipeline explanation** — order of scripts, data shapes, calibration notes, and known limitations (missing widths on ~178 designs, no two-tone detection, the Plata de Ley/silver section).

### How the page works (for whoever edits this next)

- `DESIGNS` is an array of **315 designs** (grouped from **640 individual SKUs** — a "design" is one physical ring shape available in multiple gold colors and/or with/without a diamond). Each design: `{id, cat, style, mm, wt, hasDia, v:[{sku,c,d,img}, ...]}` — `cat` is `"gold"` or `"silver"`, `c` is `"y"/"w"/"r"` (yellow/white/rose), `d` is `1`/`0` for diamond, `img` is the filename in `rings-images/`.
- Filters (Metal / Style / Stones) are plain JS array filtering — `designMatchesFilters()`. Width (mm) is deliberately **not** a filter (see supplier-source README — too much missing data).
- Each grid card shows color swatches; clicking one swaps the card's photo in place via `cardVariantIndex`, without needing a full re-render.
- Clicking a card image opens the lightbox (`openLightbox()`), which shows a bigger photo, its own swatch row, spec lines, an "Enquire about this ring" button, and a continuously-scrolling trust ticker that **restarts from position 0 every time the popup opens** (`restartTicker()` forces a reflow: `animation:none` → read `offsetWidth` → clear the inline style).
- **Metal labeling is category-aware, not just color-aware** — `variantLabel(design, variant)` returns `"Sterling Silver"` for any silver-category item regardless of its detected sub-tone, and only uses the gold color name (`"Yellow/White/Rose Gold"`) for gold-category items. Never hardcode a gold color name without checking `d.cat` first — this was a real bug (see §4).
- The "Enquire about this ring" button links to `https://wedding.temptationjewellery.com/#apply` (the homepage's partner application form) with `target="_top"`, so it correctly breaks out of the iframe when the catalog is viewed embedded on the homepage, and still works normally when the catalog page is opened directly.
- The homepage (`index.html`) embeds this same page in an iframe (`#catalog` section, `<iframe src="/catalog/index.html">`), fixed height (800px desktop / 640px / 540px on smaller breakpoints). The catalog page needs to look right both standalone and inside that iframe.

### Brand safety — hard requirement, verify on every change

**Zero Simón Franco / Alianzas SSF branding anywhere on the site — this was Sandy's explicit, repeated, "at any cost" requirement.** Before deploying any catalog change, grep the whole output case-insensitively:
```bash
grep -rlia "franco\|alianzas ssf\|simón franco" catalog/index.html catalog/rings-images/ catalog/supplier-source/designs.json
```
Should return nothing. (A generic Spanish word like "Alianzas" alone, meaning "wedding bands", is fine and appears in the footer text — only the supplier's actual name is the problem.)

---

## 3. Catalog history

**Aug 14, 2026 (morning) — expanded 8→24 pages, 73→228 products (curated).** Original flipbook-format catalog expanded from a curated selection of the 640-ring supplier PDF, capped at 155 total images to keep the base64-bundled file size mobile-safe (~17MB). Superseded by the same-day evening rebuild below.

**Aug 14, 2026 (evening) — rebuilt as a filterable grid, complete 640-ring collection.** Per Sandy's explicit instruction to use the *complete* supplier set (not a curated subset), and to make the catalog "more interactive and attractive": replaced the bundled flipbook with the current architecture (§2). All 640 rings, grouped into 315 designs, filterable by metal/style/stones, with color swatches and a click-to-view lightbox popup containing a continuously-scrolling trust-message ticker. Deployed and verified live — commit `e1d253b`.

**Aug 14, 2026 (evening, follow-up fix) — Sterling Silver labeling + enquiry button.** Sandy caught two real defects after using the new catalog live:
1. The 129-item "Plata de Ley 925" section (confirmed genuinely sterling silver via the supplier PDF's own page headers — not a data error) was displaying wrong labels like "White Gold" inherited from the generic gold-color lookup. Sandy's actual metal lineup is White/Yellow/Rose Gold plus a white-yellow two-tone blend — no silver — but she chose to **keep** this section, just labeled correctly, rather than remove it. Fixed (see §2, "Metal labeling is category-aware").
2. "Enquire about this ring" was a `mailto:` link, silently broken on devices with no email client configured. Changed to link to the homepage's partner application form instead.
Deployed and verified live — commit `e77ae20`.

**What's explicitly NOT done:** a white+yellow gold two-tone blend line, which Sandy confirmed is real but which isn't represented in the supplier PDF as its own section, and which an automated pixel-based two-tone detector couldn't reliably identify (too many false positives from ordinary photo highlights — see supplier-source README). Waiting on Sandy to supply reference SKUs or photos for that line.

---

## 4. Commission tiers, custom stones, and other site sections — DONE

- **Commission tiers** now consistently show `10% / 12.5% / 15%` (previously mixed € and % units on two of the three tier cards) — commit `f7e9b6a`. The homepage marquee's stale "8–15%" commission figure and "73 designs" catalog count were also corrected to "10–15%" and "315 designs / 640 rings" as part of the Aug 14 catalog rebuild.
- **Custom Stones section** — a 12-month birthstone chart after the catalog section (no astrology wording, only month + stone name). 4 stones marked "Available now" (Amethyst/Feb, Emerald/May, Blue Sapphire/Sep, Tanzanite/Dec) — the other 8 months are "On request", not confirmed sourceable. Request form posts to `functions/api/stone-request.js`, emails Sandy via Resend (mirrors `request-size.js` / `partner-application.js`).
- **Site redesign** (earlier work): cinematic hero with ring-union intro animation, ring size guide with interactive size picker, mobile responsiveness fixes, Google Analytics + Search Console verification, real logo in hero/nav, partner/size-request forms sending via Resend instead of `mailto:`.

---

## 5. OLD flipbook catalog format — superseded, kept for historical reference only

The pre-Aug-14-evening catalog (`catalog/index.html` before the rebuild) was a single self-contained "bundled" export (~17MB) — everything (JS app code, all product images, web fonts) inlined as base64 inside two enormous single lines of the file. This format is **no longer used** — the current catalog (§2) is a normal static page. The notes below are kept only in case anything from that era needs to be understood historically; do **not** use this recipe on the current `catalog/index.html`.

- The bundle had a `<script type="__bundler/manifest">` (asset UUID → base64 data) and a `<script type="__bundler/template">` (JSON-escaped full page HTML, including a `REF_SECTIONS` array driving `buildPages()`).
- Modifying it required: decode the template line → edit `REF_SECTIONS`/`imgCounts` → re-encode (`json.dumps`, escape `/` as `\/`) → splice back in → validate by parsing both lines as JSON and running `buildPages()` standalone in Node to check page/image-key counts → test in real Chrome (Safari didn't render the bundle format correctly) → only then deploy.
- `catalog/supplier-source/all_640_products_by_category.json` and `currently_live_155.json` are leftovers from this era (the 16-category grouping and the 155-ring curated selection). Superseded by `catalog/supplier-source/designs.json`. Kept for reference only.

---

## 6. Known pitfalls (still relevant)

**Multiple local repo clones on Sandy's Mac.** Three separate clones exist at different points in history:
- `~/temptation-wedding-partners` — stale
- `~/Desktop/temptation-wedding-partners` — **current, matches origin/main**
- `~/Downloads/temptation-wedding-partners` — stale

Always confirm which clone is current before running commands — don't assume a bare folder name:
```bash
for d in ~/temptation-wedding-partners ~/Desktop/temptation-wedding-partners ~/Downloads/temptation-wedding-partners; do
  echo "== $d =="; git -C "$d" log -1 --oneline 2>/dev/null || echo "not a repo/missing"
done
```

**Cloud Claude sessions have no push access to this repo** — 403 from the session's git proxy. Read/clone works fine. Any cloud-session work gets prepared and verified in the sandbox, then handed off as files + exact git commands for Sandy to run locally. Computer-use (remote control of the Mac) also can't type into Terminal — click-only, for safety — so there's no way around Sandy running the commands herself.

---

## Status summary

| Area | Status |
|---|---|
| GitHub token exposure | Fixed — revoked & rotated |
| Push auth (wrong `gh` account) | Fixed — SSH per-account aliases set up |
| Catalog architecture | Rebuilt Aug 14, 2026 evening — filterable grid, complete 640-ring / 315-design collection, replaces old base64 flipbook |
| Catalog images | 640 individual JPEGs in `catalog/rings-images/`, not embedded |
| Catalog data pipeline | Preserved in `catalog/supplier-source/` (`designs.json` + extraction/classification/grouping scripts + README) for future reuse |
| Vendor branding removed/kept out | Confirmed clean — re-verify with the grep in §2 on every catalog change |
| Sterling Silver labeling | Fixed — silver-category items always show "Sterling Silver", never a gold color name |
| Catalog enquiry button | Fixed — links to the homepage partner application form, not a `mailto:` |
| Commission tiers | Fixed — consistently 10% / 12.5% / 15% |
| Custom Stones section | Live — 12-month birthstone chart, request form |
| Stale leftover files (`catalog/images/`, `catalog/index_preview.html`) | Removed Aug 14, 2026 (unused, not referenced anywhere) |
| White+yellow gold two-tone blend | Not built — waiting on Sandy for reference SKUs/photos |
| Ticker copy on the catalog popup | First draft — not yet finally approved by Sandy |
| Multi-language site (ES/DE/FR/IT/NL/PL) | Scoped, not started |
