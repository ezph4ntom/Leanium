#!/usr/bin/env python3
"""Generate Leanium branding assets (images + vector icons).

Usage: python make_assets.py [--out ..\\assets\\branding]

Needs: Pillow.  The font "Inter" is used for the wordmark if installed,
otherwise Arial / DejaVu Sans is used.
"""
import argparse, math, os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
NAME = "Leanium"
MONO = (60, 64, 67)
CUP = (176, 72, 196); CUP_HI = (222, 150, 232); LID = (240, 210, 246); CUBE = (246, 220, 250); STRAW_PINK = (236, 120, 214)

# ---------- geometry helpers (screen coordinates, y grows downwards) ----------
def rrect(cx, cy, side, radius, rot_deg=0.0, ccw=False, seg=6):
    """Rounded square as a polygon. Clockwise on screen unless ccw=True."""
    h = side / 2.0
    r = min(radius, h)
    corners = [(h - r, -h + r, -90), (h - r, h - r, 0), (-h + r, h - r, 90), (-h + r, -h + r, 180)]
    pts = []
    for ox, oy, start in corners:
        for i in range(seg + 1):
            a = math.radians(start + 90.0 * i / seg)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    t = math.radians(rot_deg)
    ct, st = math.cos(t), math.sin(t)
    out = [(cx + x * ct - y * st, cy + x * st + y * ct) for x, y in pts]
    return out[::-1] if ccw else out

def round_poly(pts, r, seg=8):
    """Polygon with every corner rounded by radius r (clockwise in -> clockwise out)."""
    n = len(pts); out = []
    for i in range(n):
        p, v, q = pts[i - 1], pts[i], pts[(i + 1) % n]
        a = (p[0] - v[0], p[1] - v[1]); b = (q[0] - v[0], q[1] - v[1])
        la, lb = math.hypot(*a), math.hypot(*b)
        a = (a[0] / la, a[1] / la); b = (b[0] / lb, b[1] / lb)
        ang = math.acos(max(-1, min(1, a[0] * b[0] + a[1] * b[1])))
        t = min(r / math.tan(ang / 2), la / 2, lb / 2)
        re = t * math.tan(ang / 2)
        bis = (a[0] + b[0], a[1] + b[1]); lbis = math.hypot(*bis); bis = (bis[0] / lbis, bis[1] / lbis)
        c = (v[0] + bis[0] * re / math.sin(ang / 2), v[1] + bis[1] * re / math.sin(ang / 2))
        s0 = (v[0] + a[0] * t, v[1] + a[1] * t); e0 = (v[0] + b[0] * t, v[1] + b[1] * t)
        a0 = math.atan2(s0[1] - c[1], s0[0] - c[0]); a1 = math.atan2(e0[1] - c[1], e0[0] - c[0])
        d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        out += [(c[0] + re * math.cos(a0 + d * k / seg), c[1] + re * math.sin(a0 + d * k / seg)) for k in range(seg + 1)]
    return out

# ---------- the cup (design space ~1024) ----------
STRAW_A, STRAW_B, STRAW_W = (565, 420), (700, 175), 78
def _straw_polys():
    (x0, y0), (x1, y1) = STRAW_A, STRAW_B
    L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = -uy, ux; w = STRAW_W
    def seg(a0, a1):
        return [(x0 + ux * a0 + nx * w / 2, y0 + uy * a0 + ny * w / 2), (x0 + ux * a1 + nx * w / 2, y0 + uy * a1 + ny * w / 2),
                (x0 + ux * a1 - nx * w / 2, y0 + uy * a1 - ny * w / 2), (x0 + ux * a0 - nx * w / 2, y0 + uy * a0 - ny * w / 2)]
    whole = seg(0, L)
    stripes = [seg(i * w * 0.9, min(L, (i + 1) * w * 0.9)) for i in range(1, int(L // (w * 0.9)) + 1, 2)]
    return whole, stripes

def star(cx, cy, r):
    """4-point sparkle polygon."""
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2; rad = r if i % 2 == 0 else r * 0.26
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts

def grow(poly, f):
    cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
    return [(cx + (x - cx) * f, cy + (y - cy) * f) for x, y in poly]

def cup_parts():
    straw, stripes = _straw_polys()
    body = round_poly([(268, 380), (756, 380), (680, 850), (344, 850)], 28)
    lid = round_poly([(236, 328), (788, 328), (788, 410), (236, 410)], 38)
    hi = round_poly([(298, 442), (356, 442), (396, 800), (368, 800)], 8, seg=4)
    cubes = [rrect(cx, cy, s, s * 0.24, r) for cx, cy, s, r in [(425, 525, 160, -10), (598, 565, 150, 14), (498, 710, 160, 6)]]
    spark = star(322, 238, 76)
    return dict(straw=straw, stripes=stripes, body=body, lid=lid, hi=hi, cubes=cubes, spark=spark)

def fit(parts, N, margin, keys=("straw", "body", "lid", "spark")):
    pts = [p for k in keys for p in parts[k]]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    sc = (N - 2 * margin) / max(x1 - x0, y1 - y0)
    ox, oy = (N - (x1 - x0) * sc) / 2 - x0 * sc, (N - (y1 - y0) * sc) / 2 - y0 * sc
    T = lambda poly: [(x * sc + ox, y * sc + oy) for x, y in poly]
    out = {}
    for k, v in parts.items():
        out[k] = [T(p) for p in v] if k in ("stripes", "cubes") else T(v)
    return out, sc

def mono_shapes():
    """56x56 monochrome mark: cup + lid + straw, ice cubes punched out (counter-clockwise holes)."""
    p, _ = fit(cup_parts(), 56, 1.5, keys=("straw", "body", "lid"))
    return [p["straw"], p["body"], p["lid"]] + [c[::-1] for c in p["cubes"]]

def color_parts():
    p, _ = fit(cup_parts(), 256, 5.0)
    return p

def poly_to_icon(poly):
    lines = [f"MOVE_TO, {f(poly[0][0])}, {f(poly[0][1])},"]
    lines += [f"LINE_TO, {f(x)}, {f(y)}," for x, y in poly[1:]]
    lines.append("CLOSE,")
    return "\n".join(lines)

def f(v):
    t = ("%.2f" % v).rstrip("0").rstrip(".")
    return t if "." not in t else t + "f"   # whole numbers must NOT carry the f suffix

def poly_to_svgpath(poly):
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in poly) + " Z"

HEADER = ("// Copyright 2026 The Helium Authors\n"
          "// You can use, redistribute, and/or modify this source code under\n"
          "// the terms of the GPL-3.0 license that can be found in the LICENSE file.\n"
          f"// Modified for {NAME}.\n\n")

def hexc(c): return "#%02X%02X%02X" % c

# ---------- vector files ----------
def write_vectors(out):
    mono = "\n".join(poly_to_icon(p) for p in mono_shapes())
    (out / "product_logo.icon").write_text(
        HEADER + "CANVAS_DIMENSIONS, 56,\nFILL_RULE_NONZERO,\n" + mono + "\n", encoding="utf-8")

    cp = color_parts()
    def path(color, poly):
        return "NEW_PATH,\nPATH_COLOR_ARGB, 0xFF, 0x%02X, 0x%02X, 0x%02X,\n" % color + poly_to_icon(poly) + "\n"
    body = path((255, 255, 255), cp["straw"])
    for st in cp["stripes"]: body += path(STRAW_PINK, st)
    body += path(STRAW_PINK, grow(cp["spark"], 1.18)) + path((255, 255, 255), cp["spark"])
    body += path(CUP, cp["body"]) + path(CUP_HI, cp["hi"]) + path(LID, cp["lid"])
    for c in cp["cubes"]: body += path(CUBE, c)
    (out / "product_logo_color.icon").write_text(HEADER + "CANVAS_DIMENSIONS, 256,\n" + body, encoding="utf-8")

    def p(color, poly): return f'<path fill="{hexc(color)}" d="{poly_to_svgpath(poly)}"/>'
    parts = [p(STRAW_PINK, grow(cp["spark"], 1.18)), p((255, 255, 255), cp["spark"]), p((255, 255, 255), cp["straw"])] + [p(STRAW_PINK, s) for s in cp["stripes"]]
    parts += [p(CUP, cp["body"]), p(CUP_HI, cp["hi"]), p(LID, cp["lid"])] + [p(CUBE, c) for c in cp["cubes"]]
    svg = '<svg width="256" height="256" viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg">' + "".join(parts) + "</svg>"
    (out / "product_logo.svg").write_text(svg, encoding="utf-8")
    (ASSETS / "logo.svg").write_text(svg, encoding="utf-8")

    # path data for the WebUI "chrome-product" symbol (viewBox 0 0 56 56)
    d = " ".join(poly_to_svgpath(q) for q in mono_shapes())
    (out / "chrome_product_path.txt").write_text(d, encoding="utf-8")

# ---------- the 1024px logo (transparent background, thin white outline) ----------
def render_logo(N=1024):
    k = 2; S = N * k
    p, sc = fit(cup_parts(), S, 15 * k)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    ow = 9 * k
    shapes = [p["straw"], p["body"], p["lid"]]
    for poly in shapes:                                   # white outline underneath
        pts = [(x, y) for x, y in poly]
        d.polygon(pts, fill=(255, 255, 255, 255))
        d.line(pts + [pts[0]], fill=(255, 255, 255, 255), width=ow * 2, joint="curve")
    def fill(poly, col): d.polygon(poly, fill=col + (255,))
    fill(p["straw"], (255, 255, 255))
    for s in p["stripes"]: fill(s, STRAW_PINK)
    sp = p["spark"]
    d.polygon(sp, fill=(255, 255, 255, 255)); d.line(sp + [sp[0]], fill=STRAW_PINK + (255,), width=int(ow * 0.8), joint="curve")
    d.polygon(grow(sp, 0.93), fill=(255, 255, 255, 255))
    fill(p["body"], CUP); fill(p["hi"], CUP_HI); fill(p["lid"], LID)
    for c in p["cubes"]:
        fill(c, CUBE)
    return img.resize((N, N), Image.LANCZOS)

# ---------- raster files ----------
def find_font(size):
    cands = []
    try:
        import subprocess
        p = subprocess.run(["fc-match", "-f", "%{file}", "Inter:style=Medium"], capture_output=True, text=True)
        if p.stdout: cands.append(p.stdout.strip())
    except Exception:
        pass
    cands += [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    for c in cands:
        if c and os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()

def wordmark(logo, w, h, text_rgb):
    """Logo mark + 'Leanium' text on a transparent w x h canvas, rendered 8x then downsampled."""
    k = 8
    W, H = w * k, h * k
    mark = int(H * 0.88)
    gap = int(H * 0.2)
    size = int(H * 0.62)
    while size > 10:
        font = find_font(size)
        tw = font.getlength(NAME)
        if mark + gap + tw <= W * 0.985:
            break
        size -= 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = logo.resize((mark, mark), Image.LANCZOS)
    canvas.alpha_composite(m, (0, (H - mark) // 2))
    d = ImageDraw.Draw(canvas)
    bbox = d.textbbox((0, 0), NAME, font=font)
    ty = (H - (bbox[3] - bbox[1])) // 2 - bbox[1]
    d.text((mark + gap, ty), NAME, font=font, fill=text_rgb + (255,))
    return canvas.resize((w, h), Image.LANCZOS)

def mono22(n=22):
    k = 16
    mask = Image.new("L", (n * k, n * k), 0)
    sc = n * k / 56.0
    d = ImageDraw.Draw(mask)
    for i, p in enumerate(mono_shapes()):          # first 3 shapes are solid, the rest are holes
        d.polygon([(x * sc, y * sc) for x, y in p], fill=255 if i < 3 else 0)
    img = Image.new("RGBA", mask.size, MONO + (0,))
    img.putalpha(mask)
    return img.resize((n, n), Image.LANCZOS)

def doc_icon(logo):
    """Own 'document' icon: white page with folded corner + the logo (no Helium artwork needed)."""
    k = 4; S = 256 * k
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    page = [(52, 14), (168, 14), (212, 58), (212, 242), (52, 242)]
    pg = round_poly([(x * k, y * k) for x, y in page], 10 * k)
    d.polygon(pg, fill=(250, 250, 252, 255)); d.line(pg + [pg[0]], fill=(185, 185, 195, 255), width=4 * k, joint="curve")
    fold = [(168, 14), (168, 58), (212, 58)]
    d.polygon([(x * k, y * k) for x, y in fold], fill=(222, 222, 232, 255))
    d.line([(x * k, y * k) for x, y in fold] + [(168 * k, 14 * k)], fill=(185, 185, 195, 255), width=3 * k)
    side = 130 * k
    img.alpha_composite(logo.resize((side, side), Image.LANCZOS), (int(132 * k - side / 2), int(150 * k - side / 2)))
    return img.resize((256, 256), Image.LANCZOS)

def write_rasters(out, repo):
    logo = render_logo(1024); logo.save(ASSETS / "logo_1024.png")
    (out / "app_icon").mkdir(parents=True, exist_ok=True)
    logo.save(out / "app_icon" / "raw.png")
    doc_icon(logo).save(out / "app_icon" / "file.png")
    wordmark(logo, 140, 32, (0, 0, 0)).save(out / "product_logo.png")
    wordmark(logo, 280, 64, (0, 0, 0)).save(out / "product_logo_200.png")
    wordmark(logo, 140, 32, (255, 255, 255)).save(out / "product_logo_white.png")
    wordmark(logo, 280, 64, (255, 255, 255)).save(out / "product_logo_white_200.png")
    mono22().save(out / "product_logo_22_mono.png")
    fav = out.parent / "favicons"; fav.mkdir(parents=True, exist_ok=True)      # new-tab page tab icon
    for n in (16, 32): mono22(n).save(fav / f"favicon_ntp_{n}.png")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", help="(unused, kept for compatibility)")
    ap.add_argument("--out", default=str(ASSETS / "branding"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    write_vectors(out)
    write_rasters(out, a.repo)
    print("assets written to", out)

if __name__ == "__main__":
    main()
