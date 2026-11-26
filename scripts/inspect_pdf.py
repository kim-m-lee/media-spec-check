#!/usr/bin/env python3
"""Measure a print PDF for media-spec-check. Read-only: never changes the file.

Usage:  python3 inspect_pdf.py artwork.pdf [--target-mm 2440x1220]
Needs:  pip install pikepdf

Prints JSON with page size, boxes, PDF/X, colour spaces, images (with effective
ppi at the current size AND at the target size), fonts, transparency and file size.
"""
import json, os, sys, argparse

try:
    import pikepdf
except ImportError:
    sys.exit("pikepdf is missing. Install it with:  pip install pikepdf")

PT_TO_MM = 25.4 / 72


def mm(v):
    return round(v * PT_TO_MM, 1)


def box(page, name):
    b = page.obj.get(name)
    if b is None:
        return None
    x0, y0, x1, y1 = [float(v) for v in b]
    w, h = abs(x1 - x0), abs(y1 - y0)
    return {"pt": [round(w, 2), round(h, 2)], "mm": [mm(w), mm(h)]}


def colour_space_name(cs):
    """Return a readable name for a colour space object, e.g. 'ICCBased RGB'."""
    try:
        if isinstance(cs, pikepdf.Name):
            return str(cs)[1:]
        if isinstance(cs, pikepdf.Array) and len(cs) > 0:
            kind = str(cs[0])[1:]
            if kind == "ICCBased":
                n = int(cs[1].get("/N", 0))
                return "ICCBased " + {1: "Gray", 3: "RGB", 4: "CMYK"}.get(n, f"N={n}")
            if kind == "Indexed":
                return "Indexed (" + colour_space_name(cs[1]) + ")"
            if kind in ("Separation", "DeviceN"):
                return f"{kind} ({cs[1]})"
            return kind
    except Exception:
        pass
    return "unknown"


def mat_mul(a, b):
    return [a[0]*b[0] + a[1]*b[2],       a[0]*b[1] + a[1]*b[3],
            a[2]*b[0] + a[3]*b[2],       a[2]*b[1] + a[3]*b[3],
            a[4]*b[0] + a[5]*b[2] + b[4], a[4]*b[1] + a[5]*b[3] + b[5]]


def walk(content_owner, resources, ctm, out, depth=0):
    """Walk a content stream, tracking the transform so placed image sizes are known."""
    if depth > 8:
        return
    stack = []
    try:
        ops = pikepdf.parse_content_stream(content_owner)
    except Exception:
        return
    xobjs = resources.get("/XObject", {}) if resources else {}
    gstates = resources.get("/ExtGState", {}) if resources else {}
    for operands, op in ops:
        op = str(op)
        if op == "q":
            stack.append(ctm[:])
        elif op == "Q" and stack:
            ctm = stack.pop()
        elif op == "cm":
            ctm = mat_mul([float(v) for v in operands], ctm)
        elif op in ("rg", "RG"):
            out["ops"]["DeviceRGB"] += 1
        elif op in ("k", "K"):
            out["ops"]["DeviceCMYK"] += 1
        elif op in ("g", "G"):
            out["ops"]["DeviceGray"] += 1
        elif op == "gs" and operands:
            g = gstates.get(operands[0])
            if g is not None:
                for key in ("/ca", "/CA"):
                    if key in g and float(g[key]) < 1:
                        out["transparency"].append(f"opacity {float(g[key]):.2f} ({key[1:]})")
                if "/BM" in g and str(g["/BM"]) not in ("/Normal", "/Compatible"):
                    out["transparency"].append(f"blend mode {str(g['/BM'])[1:]}")
                if "/SMask" in g and str(g["/SMask"]) != "/None":
                    out["transparency"].append("soft mask (graphics state)")
        elif op == "Do" and operands:
            x = xobjs.get(operands[0])
            if x is None:
                continue
            sub = str(x.get("/Subtype", ""))
            if sub == "/Image":
                w_pt = (ctm[0]**2 + ctm[1]**2) ** 0.5
                h_pt = (ctm[2]**2 + ctm[3]**2) ** 0.5
                px_w, px_h = int(x.get("/Width", 0)), int(x.get("/Height", 0))
                img = {
                    "name": str(operands[0]),
                    "pixels": [px_w, px_h],
                    "colour": colour_space_name(x.get("/ColorSpace")) if x.get("/ColorSpace") is not None else ("mask" if x.get("/ImageMask") else "unknown"),
                    "placed_mm": [mm(w_pt), mm(h_pt)],
                    "ppi_now": [round(px_w / (w_pt / 72)) if w_pt else None,
                                round(px_h / (h_pt / 72)) if h_pt else None],
                    "has_soft_mask": "/SMask" in x,
                    "stencil_mask": "/Mask" in x,
                }
                if "/SMask" in x:
                    out["transparency"].append(f"image {operands[0]} has a soft mask")
                out["images"].append(img)
            elif sub == "/Form":
                m = [float(v) for v in x.get("/Matrix", [1, 0, 0, 1, 0, 0])]
                if "/Group" in x and str(x["/Group"].get("/S", "")) == "/Transparency":
                    out["transparency"].append("transparency group")
                walk(x, x.get("/Resources", resources), mat_mul(m, ctm), out, depth + 1)


def font_info(resources, seen, out):
    fonts = resources.get("/Font", {}) if resources else {}
    for key, f in fonts.items():
        if f.objgen in seen:
            continue
        seen.add(f.objgen)
        sub = str(f.get("/Subtype", ""))[1:]
        base = str(f.get("/BaseFont", "(none)"))[1:] if "/BaseFont" in f else "(none)"
        info = {"name": base, "type": sub, "embedded": None, "note": ""}
        if sub == "Type3":
            procs = f.get("/CharProcs", {})
            sizes = [len(p.read_bytes()) for p in [v for _, v in procs.items()]] if procs else []
            # Glyphs that only declare a width and draw nothing = invisible, searchable text
            # layer on top of outlined artwork (common in Figma exports). Not live text.
            if sizes and max(sizes) < 80:
                info["note"] = "glyphs draw nothing: invisible searchable text layer, the visible text is outlined"
            info["embedded"] = True
        else:
            desc = f.get("/FontDescriptor")
            if sub == "Type0":
                d = f.get("/DescendantFonts")
                desc = d[0].get("/FontDescriptor") if d else None
            info["embedded"] = bool(desc is not None and any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3")))
        out.append(info)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--target-mm", help="spec size, e.g. 2440x1220, to work out ppi at final size")
    a = ap.parse_args()

    pdf = pikepdf.open(a.pdf)
    pages = []
    target = [float(v) for v in a.target_mm.lower().split("x")] if a.target_mm else None

    for i, page in enumerate(pdf.pages):
        out = {"ops": {"DeviceRGB": 0, "DeviceCMYK": 0, "DeviceGray": 0},
               "images": [], "transparency": []}
        res = page.obj.get("/Resources", {})
        mb = [float(v) for v in page.obj.MediaBox]
        walk(page, res, [1, 0, 0, 1, -mb[0], -mb[1]], out)

        cs = sorted({colour_space_name(v) for v in [v for _, v in res.get("/ColorSpace").items()]}) if res.get("/ColorSpace") else []
        fonts = []
        font_info(res, set(), fonts)
        for x in [v for _, v in res.get("/XObject").items()] if res.get("/XObject") else []:
            if str(x.get("/Subtype", "")) == "/Form":
                font_info(x.get("/Resources", {}), set(), fonts)

        p = {
            "page": i + 1,
            "boxes": {n[1:]: box(page, n) for n in ("/MediaBox", "/CropBox", "/BleedBox", "/TrimBox", "/ArtBox")},
            "rotate": int(page.obj.get("/Rotate", 0)),
            "colour_spaces": cs,
            "colour_operators": out["ops"],
            "images": out["images"],
            "fonts": fonts,
            "transparency": sorted(set(out["transparency"])),
        }
        # One-line colour summary across vector colours and images
        kinds = set()
        for name in cs + [i["colour"] for i in out["images"]]:
            for k in ("RGB", "CMYK", "Gray", "Separation", "DeviceN", "Lab"):
                if k in name:
                    kinds.add(k)
        for k, n in out["ops"].items():
            if n:
                kinds.add(k.replace("Device", ""))
        p["colour_summary"] = sorted(kinds) or ["none found"]
        size = p["boxes"]["TrimBox"] or p["boxes"]["MediaBox"]
        w_pt, h_pt = size["pt"]
        if target:
            tw, th = target
            # match orientation
            if (w_pt > h_pt) != (tw > th):
                tw, th = th, tw
            scale = tw / (w_pt * PT_TO_MM)
            p["target_mm"] = [tw, th]
            p["scale_to_target"] = round(scale, 4)
            p["orientation_matches_spec_as_written"] = (w_pt > h_pt) == (target[0] > target[1])
            # Wrong-units signal: size in points ~= target in mm
            p["points_equal_target_mm"] = abs(w_pt - tw) < 2 and abs(h_pt - th) < 2
            for img in p["images"]:
                img["ppi_at_target"] = [round(v / scale) if v else None for v in img["ppi_now"]]
        pages.append(p)

    try:
        pdfx = str(pdf.open_metadata().get("pdfxid:GTS_PDFXVersion", "")) or None
    except Exception:
        pdfx = None
    if not pdfx and "/GTS_PDFXVersion" in pdf.docinfo:
        pdfx = str(pdf.docinfo["/GTS_PDFXVersion"])

    report = {
        "file": os.path.basename(a.pdf),
        "bytes": os.path.getsize(a.pdf),
        "mb": round(os.path.getsize(a.pdf) / 1_000_000, 2),
        "pdf_version": pdf.pdf_version,
        "pdf_x": pdfx,
        "output_intent": "/OutputIntents" in pdf.Root,
        "output_intent_name": (str(pdf.Root.OutputIntents[0].get("/OutputConditionIdentifier", "")) or None)
                              if "/OutputIntents" in pdf.Root and len(pdf.Root.OutputIntents) else None,
        "producer": str(pdf.docinfo.get("/Producer", "")) or None,
        "pages": pages,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
