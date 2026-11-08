#!/usr/bin/env python3
"""Bring an ALREADY-PREPARED build\\src tree up to date without re-extracting Chromium:
  1. renames Helium/Leannium -> Leanium in the source files (text files only),
  2. updates the toolbar/WebUI star icon,
  3. re-copies the generated logo resources.
Run after apply.py.   Usage: python update_src.py <path-to-helium-windows>"""
import re, sys, time
from pathlib import Path

RES_ONLY = '--resources-only' in sys.argv
repo = Path(sys.argv[1]); src = repo / "build" / "src"
if not (src / "BUILD.gn").exists(): sys.exit("build\\src not found")
EXT = {".cc", ".h", ".mm", ".m", ".cpp", ".c", ".py", ".gn", ".gni", ".grd", ".grdp", ".xtb", ".json", ".js", ".ts",
       ".html", ".css", ".txt", ".xml", ".plist", ".strings", ".rc", ".mc", ".mojom", ".proto", ".inc", ".md", ".nsi",
       ".nsh", ".manifest", ".def", ".idl", ".yaml", ".toml", ".list", ".info", ".gyp", ".gypi", ".icon", ".svg", ".bat", ".cmd", ".ps1", ".in", ""}
SKIP_DIRS = {"out", ".git", "llvm-build", "node_modules", "rust-toolchain", "depot_tools", "siso"}
PAIRS = [(b"Leannium", b"Leanium"), (b"leannium", b"leanium"), (b"LEANNIUM", b"LEANIUM"),
         (b"helium://", b"leanium://"), (b'kHeliumUIScheme[] = "helium"', b'kHeliumUIScheme[] = "leanium"'),
         (b'u"helium"', b'u"leanium"'), (b"'helium:'", b"'leanium:'")]
PAIRS += [(a.decode().encode("utf-16le"), b.decode().encode("utf-16le")) for a, b in PAIRS]

t0 = time.time(); changed = 0; scanned = 0
stack = [] if RES_ONLY else [src]
while stack:
    d = stack.pop()
    try: entries = list(d.iterdir())
    except OSError: continue
    for e in entries:
        try:
            if e.is_symlink(): continue
            if e.is_dir():
                if e.name not in SKIP_DIRS: stack.append(e)
                continue
            if e.suffix.lower() not in EXT or e.stat().st_size > 30_000_000: continue
            data = e.read_bytes(); scanned += 1
            new = data
            for a, b in PAIRS: new = new.replace(a, b)
            if new != data:
                e.write_bytes(new); changed += 1
        except OSError as ex:
            print("skip", e, ex)
if not RES_ONLY: print(f"renamed in {changed} files (scanned {scanned}) in {int(time.time()-t0)}s")

# WebUI star icon
icons = src / "ui/webui/resources/cr_elements/icons.html.ts"
pathfile = Path(__file__).resolve().parent.parent / "assets" / "branding" / "chrome_product_path.txt"
if icons.exists() and pathfile.exists():
    d = pathfile.read_text().strip(); t = icons.read_text(encoding="utf-8")
    n = re.sub(r'(<g id="chrome-product" viewBox="0 0 56 56">\s*<path d=")[^"]*(")', lambda m: m.group(1) + d + m.group(2), t)
    if n != t: icons.write_text(n, encoding="utf-8", newline=""); print("updated WebUI icon")

# resources (same calls build.py makes)
sys.path.insert(0, str(repo / "helium-chromium" / "utils"))
import generate_resources, replace_resources
generate_resources.generate_resources(repo / "resources" / "generate_resources.txt", repo / "resources")
replace_resources.copy_resources(repo / "resources" / "platform_resources.txt", repo / "resources", src)
generate_resources.generate_resources(repo / "helium-chromium" / "resources" / "generate_resources.txt", repo / "helium-chromium" / "resources")
replace_resources.copy_resources(repo / "helium-chromium" / "resources" / "helium_resources.txt", repo / "helium-chromium" / "resources", src)
print("resources updated - now run build.py")
