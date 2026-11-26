---
name: media-spec-check
description: "Check artwork against a printer's or media owner's spec before it's sent or uploaded. Give it the spec (a PDF, a web link or pasted text) and the files (print PDFs or static images), and it reads the spec, checks it's current, and returns a pass/fail report with exact fixes. Use when someone asks 'is this print ready?', 'does this meet the spec?', 'check these before I send them', or shares artwork alongside a spec sheet, media pack or artwork guidelines. Version 1 covers print PDFs and static images (JPG, PNG). Video isn't covered yet."
---

# Media spec check

> **Version 1 checks static artwork only:** print PDFs and static images (JPG, PNG). If the user shares video or motion files (MP4, MOV, GIF ads), say they aren't covered yet. Still check any static files in the same batch, and list the video files under "Not checked".

Checks artwork against the spec before it goes to the printer or media owner, so problems get caught at your desk rather than on the board.

It's for designers and marketers who send artwork out but aren't production specialists. Write every finding in plain words, spell out every fix, and explain any technical term the first time you use it.

**This skill checks files. It never sends them.** Even if the spec lists a submission email or upload link, sending stays with the user.

## The four steps

1. **Read the spec** and build one spec table.
2. **Check the spec is current.**
3. **Confirm the table with the user.** Don't check any files until they say yes.
4. **Check the files** and write the report.

---

## Step 1: Read the spec

Accept whatever the user has: a PDF, a web page, pasted text or several of these at once.

- **Say what kind of source each one is.** A *spec sheet* (formal requirements from the printer or media owner) carries more weight than a *guide* (a blog post or "ideas and advice" article). If the only source is a guide, say so at the top of the report.
- **Follow linked spec documents.** Product pages often hold only the headline numbers and link to the real rules in a PDF ("Technical specifications", "Copy policy", "Artwork guidelines"). Read those too.
- **Specs often come in pieces.** Sizes might be on one page and artwork rules in another document. Combine them into **one table** with a column showing where each rule came from.
- **When two sources disagree** (say 1080 × 1920 on the website and 1080 × 1350 in the PDF), **quote both side by side and let the user decide.** Never pick one quietly.
- **Check whether a rule applies to this job.** Some rules only *look* like they conflict, because they cover a different kind of campaign (e.g. "HTML only" for dynamic campaigns vs "JPEG" for standard ones). Say which rule you think applies and why, then ask the user to confirm.
- **Reading a spec PDF:** see the tools section of `references/checks.md`.
- **Note what the spec doesn't say.** Common gaps: resolution, colour mode, file types, file size limit, bleed, safe zone. These go in the table as "Not in the spec".

The spec table looks like this:

| Rule | Spec says | Source |
|---|---|---|
| Size | 800 × 2000 mm | Printer's banner sizes page |
| Bleed | 3 mm | Printer's banner sizes page |
| Colour | CMYK | Printer's artwork guidelines (PDF) |
| Resolution | 300 dpi | Printer's artwork guidelines (PDF) |
| Safe zone | Not in the spec | — |

## Step 2: Check the spec is current

The skill can't *know* a spec is the latest version. It can look for warning signs.

- **Record each source and its date**: who it came from (sales rep, account contact, website, or pasted into the chat) and any date or version printed on it. If it was pasted and you can't tell who it came from, say so and add it to the questions for the contact.
- **No date, or more than 6 months old:** flag it. *"⚠️ No date on the spec. Check it's current with your contact."*
- **Dates in file names or links** (e.g. `2025-10` or `Updated_2` in a PDF's address) are clues, not proof. Say so.
- **If there's a website as well as a PDF,** compare the two. Treat any difference as a disagreement (see Step 1).

## Step 3: Confirm the table

Show the spec table and the freshness notes, then ask the user to confirm or correct it. A misread spec produces a confident wrong answer, so this is the most important step in the skill. The table appears here only. The final report refers back to it in its "Checked against" line.

## Step 4: Check the files

**Measure with the bundled scripts first.** They work on a normal computer with just Python, and no print software is needed:

```bash
python3 scripts/inspect_pdf.py "artwork.pdf" --target-mm <spec width>x<spec height>
python3 scripts/inspect_image.py "image1.jpg" "image2.png"
```

Then judge each measurement against the spec using the rules in `references/checks.md`. Read that file before checking any files. It also covers what to do if a library is missing (ask before installing anything).

- **Print** (PDF, AI): size, bleed and trim, colour mode, image resolution, fonts and outlines, black values, transparency, file size, file type, aspect ratio.
- **Static digital** (JPG, PNG): pixel size, file type, file size, colour profile, transparency, safe zone.

### When the spec doesn't cover something

Tell the user to check with their contact, then give the industry default as a fallback:

> ⚠️ **Resolution: not in the spec. Check with your contact.** The industry default is 150 dpi at final size. Your file: 220 dpi, which passes the default.

A line checked against a default is always ⚠️, never ✅. The defaults are listed in `references/checks.md`.

### Common mistakes to look for

Describe each one by what's wrong with the file, not by which design tool caused it. The fix can then give a short line for each common tool.

1. **The file is the wrong physical size.** The page measures, say, 861 × 430 mm when the spec says 2440 × 1220 mm. That usually means the document was set up in pixels or points instead of mm. If the page size in *points* almost matches the target in *mm*, this is almost certainly the cause. *Seen on a real job.*
2. **The artwork has been flattened into one image.** A single picture covers the whole page, so text, logo and everything else are now pixels, often far too low-res at print size. Some effects (certain blend modes, live filters) force this on export. *Seen on a real job.*
3. **A border or element spills past the frame.** The page is 1–2% bigger than it should be, often because a stroke is set to Center or Outside.
4. **The image is exported too small.** The design looks right but has half the pixels the spec needs (exported at 1x).
5. **RGB sent for print.** Many design tools can only export RGB, so print files need converting.
6. **Transparent areas in a file that needs a solid background.** Many platforms fill transparency with black or white.
7. **Text not outlined.** The printer's computer swaps in a different font. Don't confuse this with an *invisible* text layer over outlined text. Many tools add one so the PDF stays searchable, and it's harmless.
8. **The wrong shape for the slot.** A 1200 × 630 social image sent for a 1920 × 480 screen (4:1). Re-exporting won't fix it, so it needs a new layout. Say what stretching or cropping would do to it.

## The report

**Summary first**, even for a single file. Give file sizes in MB. Use three groups: **ready to send** (all ✅), **to check** (some ⚠️, no ❌) and **need fixing** (any ❌).

> **12 files checked: 8 ready to send, 1 to check, 3 need fixing.**
> Checked against: Example Outdoor Co., Roadside Digital spec v4, dated 12 Aug 2026, from the sales rep (PDF).

Files that pass get **one line each**. Files that fail or have ⚠️ items get the full block:

```
### ❌ spring-dooh-v3.jpg: needs fixing (2 issues)

| Check     | Spec               | Your file          | Result   |
|-----------|--------------------|--------------------|----------|
| Size      | 1920 × 1080 px     | 1920 × 1080 px     | ✅ Pass  |
| File size | Max 5 MB           | 8.2 MB             | ❌ Fail  |
| Colour    | sRGB               | CMYK               | ❌ Fail  |
| Safe zone | 50 px from edges   | Logo 22 px from right | ⚠️ Check |

To fix:
1. Colour: re-export in sRGB. CMYK looks dull or wrong on screens, and many platforms reject it.
2. File size: export the JPG at about 80% quality. That should bring it under 5 MB with no visible loss.
3. Safe zone: move the logo at least 28 px left, or confirm with your contact that the edge isn't cropped.
```

Always finish with these two sections:

- **Not checked:** anything the spec asks for that can't be checked from the file. That includes video rules (version 2), copy approval, bleed against a product template you don't have, and anything visual like text size once it's outlined. A pass never means more than what was actually checked.
- **Questions for your contact:** every gap from the spec in one short message, ready to paste. *"Your spec doesn't state colour mode, resolution or file type. Can you confirm before we send artwork?"*

## If something fails

Give the exact fix for each issue, with a line for the common tools (Affinity, Figma, Illustrator, Canva) where it helps. If many files share the same problem, say so once at the top rather than repeating it for every file, and suggest fixing it at the source before re-exporting.
