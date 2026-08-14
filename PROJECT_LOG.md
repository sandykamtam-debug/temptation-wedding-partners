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

---

## 2. Wedding catalog — how the file actually works

`catalog/index.html` is **not** a normal static page — it's a single self-contained "bundled" export (~17MB) produced by some site-builder/bundler tool. Everything (JS app code, all product images, web fonts) is inlined as base64 inside two enormous single lines of the file. Key structure, for whoever edits this next:

- **Line ~205** — `<script type="__bundler/manifest">`: a JSON object mapping asset UUIDs → `{mime, compressed, data}`. Most entries are gzip+base64-compressed JS. Several of these are literally just:
  ```js
  window.PRODUCT_IMAGES = window.PRODUCT_IMAGES || {};
  Object.assign(window.PRODUCT_IMAGES, { "page9_prod1": "data:image/jpeg;base64,...", ... });
  ```
  i.e. each chunk just registers a batch of product images keyed as `page{N}_prod{index}`.

- **Line ~212** — `<script type="__bundler/template">`: a JSON-escaped string containing the *entire* page HTML, including an inline `<script type="text/x-dc">` block. That block is where the real catalog logic lives:
  ```js
  const REF_SECTIONS = [
    { title: "Novedades 2026", kicker: "NOVEDADES 2026", refs: ["475","467",...], images: [1] },
    ...
  ];
  // buildPages() turns each section into a page, generating items with
  // imgKey: `page${pdfPage}_prod${i+1}` (pdfPage = section index + 2)
  // and label: `Ref. ${ref}` — pulled straight from window.PRODUCT_IMAGES.
  ```
  **To add a new catalog page/category:** add an entry to `REF_SECTIONS` (title, kicker, refs array) and a matching count to the `imgCounts` array right below it, then add a manifest chunk that registers `page{N}_prod1..k` images for that section (N continues from the last used page number). Page numbering, pagination dots, and "X / Y" labels are all derived automatically from `REF_SECTIONS.length` — no other place needs updating.
  Do **not** hand-edit the two giant lines directly with a text editor — always decode → edit the readable HTML/JS → re-encode, exactly as the script in `catalog/supplier-source/` does, and validate before touching the real file (see §4).

- A short footer line was added to both page-flip render layers (`bottomPage`/`topPage`, so it survives the flip animation and shows on every page including the cover):
  > "Alianzas disponibles en 9k, 14k y 18k, con y sin diamante · Garantía de por vida · Joyería de oro y relojes de marca en [temptationjewellery.com](https://temptationjewellery.com/)"

---

## 3. Catalog expansion — DONE (Aug 14, 2026)

**Before:** 8 pages, 73 products, ~14.3MB file.
**After:** 24 pages, 228 products, ~17.2MB file. Live and verified at wedding.temptationjewellery.com/catalog ("Página 1 de 24").

What happened:
1. Sandy uploaded the wholesale supplier's PDF catalog (Simón Franco / Alianzas SSF S.L., Spain — the maker Temptation sources these rings from). 640 individual rings across 16 style/width categories.
2. **Hard requirement confirmed with Sandy: zero Simón Franco / Alianzas SSF branding anywhere on the site.** Only the cover/branding/contact pages of their PDF mention their name — those were deliberately skipped during extraction; only plain product photos were used. Verified after the fact: no "Simón Franco" or "Alianzas SSF" string anywhere in the final file.
3. Wrote `catalog/supplier-source/extract_products.py` (PyMuPDF) to pull every individual ring photo out of the PDF, matched to its SKU/weight/type by position (not by text order — the PDF's raw text stream order doesn't match the visual grid layout, so matching is done by (x,y) proximity to each SKU label).
4. Grouped all 640 into 16 categories → `catalog/supplier-source/all_640_products_by_category.json`.
5. **Sizing decision:** embedding all 640 as base64 would have pushed the file to ~80–100MB, risking mobile browser crashes on load. Sandy chose a curated expansion instead — capped at 12 products per category (evenly sampled for style variety), 155 total. That selection is saved at `catalog/supplier-source/currently_live_155.json`.
6. Built 16 new `REF_SECTIONS` entries (pages 9–24: Alianzas Planas ×5 widths, Media Caña ×4 widths, Colección 3/3.5/4/4.5/5/5.5mm, Plata de Ley 925), added a new gzip-compressed manifest chunk with the 155 images (JPEG, quality 82, ~2.2MB raw), added the footer text + link.
7. **Verified before deploying:**
   - Ran the site's own `buildPages()` logic standalone in Node — confirmed 24 pages, all 228 image references resolve (0 missing, 0 duplicate, 0 orphaned), valid JS syntax.
   - Opened the modified file locally in real Chrome (not Safari — Safari failed to render it; always test with Chrome) and visually confirmed page 1/24 and the footer.
8. Deployed: copied preview → `catalog/index.html`, committed, pushed via the SSH remote (see §1). Confirmed live.

**What's NOT included:** 485 of the 640 supplier products were left out by the size-curation decision (see step 5). If a bigger catalog is wanted later, `all_640_products_by_category.json` already has everything grouped and ready — no need to re-run PDF extraction, just pick more refs per category and repeat steps 6–8. Loose end: `catalog/index_preview.html` is a staging copy left in the folder — safe to delete, was never committed to git.

---

## 4. If you need to modify the catalog again — quick recipe

1. Decide what's changing (new products, text edits, new pages).
2. If adding products from the supplier PDF: pick refs from `catalog/supplier-source/all_640_products_by_category.json` (or re-run `extract_products.py` against a newer PDF).
3. Decode `catalog/index.html` line 212 (the `__bundler/template` line) back to plain HTML/JS with a small Python script (`json.loads` on the string between the `<script type="__bundler/template">` tag and its closing tag).
4. Edit the readable `REF_SECTIONS` / `imgCounts` arrays and/or footer markup.
5. Re-encode: `json.dumps(html, ensure_ascii=True)`, then replace every `/` with `\/` (matches the original escaping — required so a literal `</script>` inside the string doesn't break the HTML parser), splice back into line 212. If adding images, gzip+base64 a new `Object.assign(window.PRODUCT_IMAGES, {...})` chunk and merge it into the manifest JSON on line 205, plus add a `<script src="{uuid}">` tag in the template's `<helmet>` section.
6. **Validate before touching the real file**: parse both edited lines back as JSON to confirm no corruption, and run the `buildPages()` logic standalone in Node to confirm page/image-key counts match expectations (no missing or duplicate `imgKey`s).
7. Test the result by opening it locally in **Chrome** (Safari doesn't render this bundle format correctly).
8. Only then copy over the real `catalog/index.html`, commit, and push.

---

## Status summary

| Area | Status |
|---|---|
| GitHub token exposure | Fixed — revoked & rotated |
| Push auth (wrong `gh` account) | Fixed — SSH per-account aliases set up |
| Catalog structure understood & documented | Done (this file, §2) |
| Catalog expanded 8→24 pages, 73→228 products | Done, live |
| Footer materials/guarantee text + store link | Done, live, on every page |
| Vendor branding removed/kept out | Confirmed clean |
| Remaining 485 supplier products | Not included — available in `all_640_products_by_category.json` if wanted later |
| `catalog/index_preview.html` staging file | Still present locally, not in git — fine to delete |
