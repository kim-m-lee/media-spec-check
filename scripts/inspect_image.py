#!/usr/bin/env python3
"""Measure static images for media-spec-check. Read-only: never changes the files.

Usage:  python3 inspect_image.py image1.jpg image2.png ...
Needs:  pip install pillow

Prints JSON per file: real format, pixel size, ratio, colour mode, ICC profile
name, alpha/transparency, frame count (animated or not), file size.
"""
import io, json, os, sys

try:
    from PIL import Image, ImageCms
except ImportError:
    sys.exit("Pillow is missing. Install it with:  pip install pillow")


def profile_name(im):
    icc = im.info.get("icc_profile")
    if not icc:
        return None
    try:
        return ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))).strip()
    except Exception:
        return "embedded (name unreadable)"


def has_real_alpha(im):
    """True only if some pixel is actually see-through, not just an alpha channel."""
    if im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info:
        try:
            alpha = im.convert("RGBA").getchannel("A")
            return alpha.getextrema()[0] < 255
        except Exception:
            return True
    return False


def main(paths):
    out = []
    for p in paths:
        im = Image.open(p)
        w, h = im.size
        out.append({
            "file": os.path.basename(p),
            "format": im.format,                       # real format, not the extension
            "extension": os.path.splitext(p)[1].lower(),
            "pixels": [w, h],
            "ratio": round(w / h, 4),
            "orientation": "landscape" if w > h else "portrait" if h > w else "square",
            "mode": im.mode,                           # RGB, RGBA, CMYK, L, P ...
            "icc_profile": profile_name(im),           # e.g. "sRGB IEC61966-2.1", "Display P3"
            "alpha_channel": im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info,
            "see_through_pixels": has_real_alpha(im),
            "frames": getattr(im, "n_frames", 1),      # > 1 means animated
            "bytes": os.path.getsize(p),
            "mb": round(os.path.getsize(p) / 1_000_000, 2),
        })
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
