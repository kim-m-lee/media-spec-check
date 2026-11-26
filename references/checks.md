# Checks: how to run each one

Run every check on the actual file, and report what you measured, not what you expect. Never change, move or re-save the user's files.

## Measure first, with the bundled scripts

The two scripts in `scripts/` only need Python, plus one library each. They work on a normal Mac or PC without any print software.

```bash
python3 scripts/inspect_pdf.py "artwork.pdf" --target-mm 1220x2440
python3 scripts/inspect_image.py "image1.jpg" "image2.png"
```

- `inspect_pdf.py` needs `pikepdf` and `inspect_image.py` needs `pillow`. If one is missing, the script says so. Ask the user before installing anything (`pip install pikepdf pillow`).
- Always pass `--target-mm` with the spec's size, so the script can work out resolution **at final size**.
- If poppler (`pdfinfo`, `pdfimages`, `pdffonts`) or Ghostscript (`gs`) happen to be installed, use them to double-check. Only Ghostscript's `inkcov` (real ink per channel) has no script equivalent. Without it, list ink coverage under "Not checked".
- **To look at a page** (for safe zones, crop marks, black areas): on a Mac, `sips -s format png "artwork.pdf" --out page.png`. Anywhere else, use Ghostscript or open it in a viewer and describe what you see.
- **To read a spec that's a PDF:** extract the text with `pypdf` (`from pypdf import PdfReader`) or `pdftotext` if installed. Web fetch tools often can't read compressed PDFs, so download the file and extract it instead. Also check the PDF's own metadata (creation date, title) for date clues.

## Result symbols

| Symbol | Means |
|---|---|
| ✅ | Measured, and meets the spec. Also used when the file simply doesn't contain the risk (e.g. no transparency at all). |
| ❌ | Measured, and breaks the spec. |
| ⚠️ | Needs a person: the spec is silent, the check is a judgement call, or a rule is preferred but not required. |

## When the spec is silent

Always phrase it as: *"Not in the spec. Check with your contact. The industry default is …"*. If there's no default, say: *"Not in the spec, and there's no standard default. Ask your contact."* A line checked against a default is always ⚠️.

| Rule | Print default | Static digital default |
|---|---|---|
| Colour | CMYK | sRGB |
| Resolution at final size | 300 dpi for small print (up to about A2). 150 dpi for large format (banners, boards, billboards). 100 dpi is a common minimum for very large formats. | Exact pixel size of the slot. dpi doesn't matter on screens. |
| File type | PDF (PDF/X-4 preferred) | JPG for photos, PNG for flat graphics |
| Bleed | 3 mm for small print. Large format varies, so ask. | None |
| Text | Outlined, 6 pt minimum (many printers ask for 8–10 pt) | Readable at viewing distance |
| Black | Rich black for large areas (a common mix is C40 M30 Y30 K100). K100 only for text and fine lines. | Not applicable |
| Transparency | Fine in PDF/X-4. Some printers want it flattened, so ask. | A solid background, no see-through pixels |
| File size | No standard default, so ask | No standard default, so ask |
| Safe zone | No standard default, so ask | No standard default, so ask |

Report file sizes in **MB** (e.g. 8.2 MB).

---

## Print files (PDF, AI)

### Size and orientation
Use `boxes.TrimBox` (or `MediaBox` if there's no trim) in mm. Compare with the spec, within 1 mm.
- **Wrong units (`points_equal_target_mm: true`):** the size in points matches the spec in mm, so the file is about a third of the size (×2.835). This is ❌ and **overrides** any "custom sizes are OK" leniency in the spec. Name the cause.
- **Other mismatches:** the size may be a deliberate custom size. Mark it ⚠️ and ask. Don't fail it outright.
- **Orientation:** if the file is landscape and the spec is written portrait-first (or the other way round), the ratio can match but the board may be hung differently. Mark it ⚠️ and ask (`orientation_matches_spec_as_written: false`).

### Aspect ratio
Compare the ratio with the spec, within 0.5%. Being 1–2% off usually means an element spilling past the frame (a stroke set to Center or Outside). Mark it ❌ and name the likely cause.

### Bleed and trim
- **Spec asks for bleed:** BleedBox should exceed TrimBox by the bleed amount on every side.
- **Spec says no bleed:** there should be no BleedBox or TrimBox bigger than the page, and no crop marks in a page preview.
- **Product template needed** (cut-outs, drill holes, "ornament zones"): list it under Not checked.

### Colour mode
Start with `colour_summary`, which combines everything on the page. Then use `colour_spaces`, `colour_operators` and each image's `colour` to say what's affected. An image-only page has empty `colour_spaces` and zero operators. That's normal, and its colour is in the image. Mention `output_intent_name` if it's generic and the spec names a specific profile.
- Anything RGB (`ICCBased RGB`, `DeviceRGB`) when the spec says CMYK: ❌. Name what's affected (all colours, or one image).
- `Separation` or `DeviceN` means spot colours: ❌ if the spec says CMYK only, otherwise ⚠️.
- `Lab`: ⚠️, because colours may shift.
- After the user converts to CMYK, suggest checking bright blues and greens, which often go duller.

### Image resolution
Use each image's **`ppi_at_target`**, never `ppi_now`. If the file is the wrong size, `ppi_now` is misleading.
- **Below the minimum:** ❌.
- **Above the minimum but below a *preferred* value:** ⚠️. Say it's acceptable, and give the pixel size needed to reach the preferred value.
- **One image covering the whole page** (its `placed_mm` ≈ the page size): the artwork has been flattened. Always name the mistake, whatever the ppi. ❌ if the ppi is under the minimum, otherwise ⚠️. Suggest a vector re-export (look for a "rasterise everything" export setting, or a filter or blend mode forcing it). Look at a crop of the small text and any QR code at 100%, and report whether they're crisp.
- **An image with a `stencil_mask`:** usually harmless (often a 1 px edge). Mention it only if the masked area is visible in the preview.
- **No images:** pure vector. ✅, and it explains a small file.

### Fonts and text
- **No fonts:** text is outlined (or there's none). ✅ if the spec asks for outlines.
- **A font noted as "invisible searchable text layer":** the visible text is already outlined. Many design tools add a hidden copy so the PDF stays searchable. This is **not** live text, so don't flag it. You can use its sizes to estimate the smallest text.
- **Other fonts:** text is live. ❌ if the spec asks for outlines. Otherwise check `embedded: true` for each one (❌ if not embedded).
- **Minimum text size:** once text is outlined it can't be measured. Give an estimate if possible and mark it ⚠️ for a visual check at 100%.

### Black values
Only if the spec gives black values. Look at a page preview and the colour operators. Flag large plain-K100 areas where rich black is asked for, and small text or fine lines built from four-colour black. If the design has no black, say "No black in the design" and mark it ✅. If you can't tell reliably, put it under Not checked.

### Transparency
From `transparency`: opacity below 1, soft masks, blend modes, transparency groups.
- The spec asks for flattened files: ❌.
- The spec is silent: ⚠️. Name each item ("logo has a soft-edged mask", "divider line at 35% opacity") and give the default from the table.
- None found: ✅.

### PDF standard
`pdf_x` and `output_intent`. If the spec only *prefers* PDF/X-4, a missing one is ⚠️. If it requires it, ❌.

### File type and size
Check the real format (the script opened it as a PDF) and `mb` against any limit.

---

## Static digital files (JPG, PNG)

### Pixel size and shape
`pixels` must match exactly, and so must `orientation`. 1919 × 1080 is a fail.
- **Wrong shape** (the `ratio` is more than about 2% off the slot's ratio): a re-export won't fix it. The design needs **a new layout** on a canvas of the right size. Say so plainly, and say what stretching or cropping would do ("cropping a 4:3 image to 4:1 keeps only a quarter of its height").
- **Right shape, wrong size:** re-export at the exact size. Warn if it would need scaling **up** (it'll look soft).

### File type
`format` must be on the spec's list. Check the real format, not just `extension`. If they disagree (a PNG renamed to .jpg), that's ❌: re-export, don't rename.

### File size
`mb` against the limit. If it's over, suggest JPG at about 80% quality, or PNG compression for flat graphics.

### Colour
- `mode: CMYK`: ❌ for screens. Re-export in sRGB.
- `icc_profile` contains "P3", "Adobe RGB" or "ProPhoto": ⚠️. Colours may look oversaturated or shifted on ad screens, so export in sRGB.
- No profile: ⚠️. The screen has to guess, so export with sRGB embedded.
- An sRGB profile: ✅.

### Transparency
`see_through_pixels: true`: ❌ if the spec wants a solid background, ⚠️ if it's silent. An alpha channel with no see-through pixels is ✅. Mention it only as a tidy-up.

### Static vs motion
`frames > 1` means animated: ❌ if the spec says static only.

### Safe zone
If the spec gives one, look at the image and report the measured gap ("logo is 22 px from the right edge, and the safe zone is 50 px"). Mark it ⚠️ unless it's clearly outside. If the spec gives none, it goes in the questions for the contact. It isn't a row in the table.

### Display time
A "standard length" (e.g. a 20 s slot) on a still image isn't a file check. List it under Not checked, and ask the contact whether the still loops or holds for the whole slot.
