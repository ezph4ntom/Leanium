#!/usr/bin/env python3
"""Scan a BUILT Leanium for leftover "Helium" text that a user could see.

Usage (any Command Prompt, no administrator needed):
  py -3.12 check_leftovers.py <helium-windows folder>    scans the newest build\\*-windows.zip in it
  py -3.12 check_leftovers.py <file.zip or folder>       scans that portable build (zip or unpacked folder)
Options:
  --all             show every hit (default: at most 5 examples per file / resource)
  --brotli <exe>    brotli.exe used to unpack compressed WebUI pages. Default: the "brotli" Python module
                    if installed, else build\\src\\out\\Default\\brotli.exe (made by every build)

It looks inside every file of the portable build (chrome.dll, chrome.exe, ...) and inside every resource of
the .pak files (translated strings in locales\\*.pak, WebUI pages in resources.pak), unpacking gzip and
brotli compressed resources first. It searches, in UTF-8 and UTF-16, for:
  - "Helium" as a whole word (identifiers such as kHeliumFoo are ignored: users never see them)
  - "helium://" (the old internal-page address)
  - "Leannium" (the old misspelling)
Intentional mentions (credits/licence text, "The Helium Authors", "Helium-bin") are listed as allowed.

Installer check (also run automatically for a <helium-windows folder>, on the newest build\\*x64-installer.exe):
  py -3.12 check_leftovers.py --installer <installer.exe or helium-windows folder> [--seven-zip <7z.exe>]
It extracts setup.exe from the NSIS installer with 7-Zip (it does not install anything) and checks the names
Windows will show: the uninstall entry name and the Start-menu shortcut name (setup.exe's IDS_PRODUCT_NAME
strings, every language), the Start-menu apps folder name, the uninstall registry key name and the
installer's own version info. All must say Leanium and none may say Helium.
Exit code: 0 = nothing unexpected, 1 = leftovers found, 2 = error."""
import gzip, re, shutil, struct, subprocess, sys, zipfile
from collections import defaultdict
from pathlib import Path

ALLOWED = [r"The Helium Authors", r"Helium-bin", r"opensource_project.{0,6}Helium", r"Name: Helium",
           r"component of Helium", r"based on Helium", r"github\.com/imputnet/helium",
           # credits page (leanium://credits): correct attribution of the project Leanium is built on
           r"Helium source code is available", r'class="title">Helium<',
           # uBlock Origin's filter lists are Helium's lists, named as such on purpose
           r"Helium filters \(via Leanium\)",
           # data that merely contains the word: USB/PCI device names, the public domain-suffix list
           r"Bus for Helium", r"Helium TLDs"]
EXAMPLES = 10**9 if "--all" in sys.argv else 5


def u16(pattern):
    """Turn an ASCII regex fragment of literal letters into its UTF-16LE form."""
    return b"".join(re.escape(bytes([c])) + b"\x00" for c in pattern)


NOT_WORD = rb"[A-Za-z0-9_]"
PATTERNS = [  # (label, compiled regex, utf16?)
    ("Helium", re.compile(rb"(?<!" + NOT_WORD + rb")Helium(?!" + NOT_WORD + rb")"), False),
    ("Helium", re.compile(rb"(?<!" + NOT_WORD + rb"\x00)" + u16(b"Helium") + rb"(?!" + NOT_WORD + rb"\x00)"), True),
    ("helium://", re.compile(rb"helium://"), False),
    ("helium://", re.compile(u16(b"helium://")), True),
    ("Leannium", re.compile(rb"(?i)leannium"), False),
    ("Leannium", re.compile(u16(b"Leannium") + b"|" + u16(b"leannium")), True),
]
ALLOWED_RE = re.compile("|".join(ALLOWED), re.I)


def snippet(data, start, end, utf16):
    """Readable text around a hit (about 60 characters each side)."""
    width = 120 if utf16 else 60
    a, b = max(0, start - width), min(len(data), end + width)
    if utf16:
        a -= (a - start) % 2  # keep the same byte alignment as the hit
        text = data[max(a, 0):b].decode("utf-16le", "replace")
    else:
        text = data[a:b].decode("utf-8", "replace")
    text = "".join(ch if ch.isprintable() else " " for ch in text)
    return re.sub(r"\s+", " ", text).strip()


COMMENT_STARTS = (b"//", b"/*", b"*", b"#", b"!", b"<!--")


def find(data):
    """Yield (label, snippet, is_comment) for every hit in a block of bytes. A hit on a line that starts like
    a code comment (// # ! ...) is marked, since users never see comments."""
    for label, rx, utf16 in PATTERNS:
        for m in rx.finditer(data):
            comment = False
            if not utf16:
                nl = data.rfind(b"\n", max(0, m.start() - 300), m.start())
                if nl >= 0 or m.start() <= 300:  # found the start of the line (or of the file)
                    comment = data[nl + 1:m.start()].lstrip().startswith(COMMENT_STARTS)
            yield label, snippet(data, m.start(), m.end(), utf16), comment


def pak_resources(data):
    """Yield (id, bytes) for each resource in a Chromium .pak file (format 4 or 5)."""
    version = struct.unpack_from("<I", data, 0)[0]
    if version == 5:
        count, aliases = struct.unpack_from("<HH", data, 8)
        table = 12
    elif version == 4:
        count = struct.unpack_from("<I", data, 4)[0]
        table = 9
    else:
        raise ValueError(f"unknown .pak version {version}")
    entries = [struct.unpack_from("<HI", data, table + 6 * i) for i in range(count + 1)]
    for (rid, off), (_, nxt) in zip(entries, entries[1:]):
        yield rid, data[off:nxt]


class Unpacker:
    def __init__(self, brotli_exe):
        self.module = None
        self.exe = brotli_exe
        try:
            import brotli
            self.module = brotli
        except ImportError:
            pass
        self.skipped = 0

    def __call__(self, blob):
        """Return (kind, uncompressed bytes) or (kind, None) if it cannot be unpacked."""
        if blob[:2] == b"\x1f\x8b":
            try:
                return "gzip", gzip.decompress(blob)
            except OSError:
                return "gzip", None
        if blob[:2] == b"\x1e\x9b":  # Chromium's brotli header: 2 magic bytes + 6 bytes of size
            payload = blob[8:]
            try:
                if self.module:
                    return "brotli", self.module.decompress(payload)
                if self.exe:
                    r = subprocess.run([str(self.exe), "-d", "-c"], input=payload, capture_output=True)
                    if r.returncode == 0:
                        return "brotli", r.stdout
            except Exception:
                pass
            self.skipped += 1
            return "brotli", None
        return "", blob


def open_build(target):
    """Return (description, iterator of (relative name, bytes))."""
    target = Path(target)
    if target.is_dir() and (target / "build.py").exists() and (target / "build").is_dir():
        zips = sorted((target / "build").glob("*-windows.zip"), key=lambda p: p.stat().st_mtime)
        if not zips:
            sys.exit("no build\\*-windows.zip found: run package.py first, or pass a folder or zip")
        target = zips[-1]
    if target.suffix.lower() == ".zip":
        z = zipfile.ZipFile(target)

        def files():
            for info in z.infolist():
                if not info.is_dir():
                    yield info.filename.split("/", 1)[-1], z.read(info)
        return str(target), files()
    if target.is_dir():
        def files():
            for p in sorted(target.rglob("*")):
                if p.is_file():
                    yield p.relative_to(target).as_posix(), p.read_bytes()
        return str(target), files()
    sys.exit(f"not a zip or folder: {target}")


def src_version(repo):
    """Helium version that <repo>\\build\\src was completely prepared for ('' if missing or interrupted).
    build.py appends HELIUM_* to chrome\\VERSION near the end of preparation. Used by update.bat."""
    try:
        d = dict(re.findall(r"(\w+)=(\d+)", (Path(repo) / "build/src/chrome/VERSION").read_text()))
        return ".".join(d[k] for k in ("HELIUM_MAJOR", "HELIUM_MINOR", "HELIUM_PATCH", "HELIUM_PLATFORM"))
    except (OSError, KeyError):
        return ""


def _win_strings(exe):
    """All RT_STRING entries of a Windows executable as {id: text} (loaded as data, never run)."""
    import ctypes
    k = ctypes.windll.kernel32
    for f, res in (("LoadLibraryExW", ctypes.c_void_p), ("FindResourceW", ctypes.c_void_p),
                   ("LoadResource", ctypes.c_void_p), ("LockResource", ctypes.c_void_p)):
        getattr(k, f).restype = res
    k.FindResourceW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    k.LoadResource.argtypes = k.SizeofResource.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    k.LockResource.argtypes = [ctypes.c_void_p]; k.FreeLibrary.argtypes = [ctypes.c_void_p]
    mod = k.LoadLibraryExW(str(exe), None, 0x2 | 0x20)  # LOAD_LIBRARY_AS_DATAFILE | AS_IMAGE_RESOURCE
    if not mod:
        raise OSError(f"cannot read resources of {exe}")
    blocks = []
    cb_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
    cb = cb_type(lambda m, t, name, p: (blocks.append(name) if name and name < 0x10000 else None) or True)
    k.EnumResourceNamesW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, cb_type, ctypes.c_void_p]
    k.EnumResourceNamesW(mod, ctypes.c_void_p(6), cb, None)  # RT_STRING
    out = {}
    for b in blocks:
        r = k.FindResourceW(mod, ctypes.c_void_p(b), ctypes.c_void_p(6))
        data = ctypes.string_at(k.LockResource(k.LoadResource(mod, r)), k.SizeofResource(mod, r))
        pos = 0
        for i in range(16):
            n = struct.unpack_from("<H", data, pos)[0]; pos += 2
            if n:
                out[(b - 1) * 16 + i] = data[pos:pos + 2 * n].decode("utf-16-le")
            pos += 2 * n
    k.FreeLibrary(mod)
    return out


def _version_info(exe):
    import ctypes
    v = ctypes.windll.version
    size = v.GetFileVersionInfoSizeW(str(exe), None)
    if not size:
        return {}
    buf = ctypes.create_string_buffer(size); v.GetFileVersionInfoW(str(exe), 0, size, buf)
    p, n = ctypes.c_void_p(), ctypes.c_uint()
    v.VerQueryValueW(buf, "\\VarFileInfo\\Translation", ctypes.byref(p), ctypes.byref(n))
    lang, cp = struct.unpack("<HH", ctypes.string_at(p, 4)) if n.value else (0x409, 1200)
    info = {}
    for key in ("ProductName", "FileDescription", "CompanyName"):
        if v.VerQueryValueW(buf, f"\\StringFileInfo\\{lang:04x}{cp:04x}\\{key}", ctypes.byref(p), ctypes.byref(n)) and n.value:
            info[key] = ctypes.wstring_at(p, n.value).rstrip("\x00")
    return info


def check_installer(target, seven_zip=None):
    """Validate the names an installed Leanium shows in Windows. Returns the number of problems."""
    import tempfile
    target = Path(target)
    if target.is_dir():
        cands = sorted((target / "build").glob("*x64-installer.exe"), key=lambda p: p.stat().st_mtime)
        if not cands:
            print("\nInstaller check: no build\\*x64-installer.exe found (run package.py); skipped.")
            return 0
        target = cands[-1]
    seven_zip = seven_zip or shutil.which("7z") or r"C:\Program Files\7-Zip\7z.exe"
    print(f"\nInstaller check: {target}")
    problems = []
    def expect(what, value, ok):
        print(f"  [{'ok' if ok else 'PROBLEM'}] {what}: {value!r}")
        if not ok:
            problems.append(what)
    word = re.compile(r"(?<![A-Za-z0-9_])Helium(?![A-Za-z0-9_])")
    vi = _version_info(target)
    expect("installer ProductName", vi.get("ProductName"), "Leanium" in (vi.get("ProductName") or "") and not word.search(vi.get("ProductName") or ""))
    expect("installer FileDescription", vi.get("FileDescription"), not word.search(vi.get("FileDescription") or ""))
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([seven_zip, "e", str(target), f"-o{tmp}", "-y", r"$TEMP\helium_install\setup.exe"],
                           capture_output=True, text=True)
        setup = Path(tmp) / "setup.exe"
        if r.returncode != 0 or not setup.exists():
            print(f"  [PROBLEM] could not extract setup.exe with {seven_zip}: {r.stderr.strip()[:200]}")
            return 1
        strings = _win_strings(setup)
        data = setup.read_bytes()
        ids = {}
        hdr = None
        for root in (target.parent.parent, target.parent.parent.parent):
            h = root / "build/src/out/Default/gen/chrome/installer/util/installer_util_strings.h"
            if h.exists():
                hdr = h
                break
        if hdr:
            ids = {m[0]: int(m[1]) for m in re.findall(r"#define (IDS_\w+?) (\d+)", hdr.read_text())}
        def group(prefix):
            return {name[len(prefix):]: strings.get(i) for name, i in ids.items()
                    if name.startswith(prefix) and name[len(prefix):].isupper() and i in strings}
        names = group("IDS_PRODUCT_NAME_")
        if names:
            en = names.get("EN_US")
            expect("uninstall entry name (Apps & features), en-US", en, en == "Leanium")
            expect("Start-menu shortcut name, en-US", en, en == "Leanium")
            bad = {l: s for l, s in names.items() if "Leanium" not in s or word.search(s)}
            expect(f"product name in all {len(names)} languages", "all Leanium" if not bad else bad, not bad)
            sub = group("IDS_APP_SHORTCUTS_SUBDIR_NAME_")
            if sub:
                bad = {l: s for l, s in sub.items() if word.search(s)}
                expect("Start-menu apps folder name, en-US", sub.get("EN_US"), not bad and "Leanium" in (sub.get("EN_US") or ""))
        else:
            print("  (installer_util_strings.h not found: checking all setup.exe strings instead)")
            expect("a setup.exe string that is exactly 'Leanium'", "found" if "Leanium" in strings.values() else None,
                   "Leanium" in strings.values())
        hits = sorted({s for s in strings.values() if word.search(s) and not ALLOWED_RE.search(s)})
        expect(f"visible 'Helium' in setup.exe's {len(strings)} strings", hits[:5], not hits)
        key = "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\".encode("utf-16-le")
        product = "\x00Leanium\x00".encode("utf-16-le")[2:-2]
        expect("uninstall registry key ...\\Uninstall\\<product>", "...\\Uninstall\\Leanium" if (key in data and product in data) else None,
               key in data and product in data)
    print(f"  Installer check: {'OK' if not problems else str(len(problems)) + ' problem(s)'}")
    return len(problems)


def main():
    if "--installer" in sys.argv:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        sz = None
        if "--seven-zip" in sys.argv:
            sz = sys.argv[sys.argv.index("--seven-zip") + 1]; args.remove(sz)
        return 1 if check_installer(args[0], sz) else 0
    if "--src-version" in sys.argv:
        v = src_version(sys.argv[-1])
        if v:
            print(v)
        return 0
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    brotli_exe = None
    if "--brotli" in sys.argv:
        brotli_exe = Path(sys.argv[sys.argv.index("--brotli") + 1])
        args.remove(str(sys.argv[sys.argv.index("--brotli") + 1]))
    if len(args) != 1:
        sys.exit(__doc__)
    target = Path(args[0])
    if brotli_exe is None:
        for root in (target, target.parent, target.parent.parent):
            cand = root / "build" / "src" / "out" / "Default" / "brotli.exe"
            if cand.exists():
                brotli_exe = cand
                break
        else:
            brotli_exe = shutil.which("brotli")
    unpack = Unpacker(brotli_exe)

    where, files = open_build(target)
    print(f"Scanning {where}")
    bad = defaultdict(list)       # place -> [(label, snippet)]
    allowed = defaultdict(int)    # snippet -> count
    locale = defaultdict(dict)    # (resource id) -> {language: [(label, snippet)]}
    nfiles = nres = comments = 0
    for name, data in files:
        nfiles += 1
        if name.endswith(".pak"):
            try:
                resources = list(pak_resources(data))
            except (ValueError, struct.error) as e:
                print(f"  (could not read {name}: {e}; scanned as plain bytes)")
                resources = [(None, data)]
            for rid, blob in resources:
                nres += 1
                kind, body = unpack(blob)
                if body is None:
                    continue
                for label, snip, comment in find(body):
                    if comment:
                        comments += 1
                    elif ALLOWED_RE.search(snip):
                        allowed[snip] += 1
                    elif name.startswith("locales/"):
                        locale[rid].setdefault(name[8:-4], []).append((label, snip))
                    else:
                        bad[f"{name} resource {rid}" + (f" ({kind})" if kind else "")].append((label, snip))
        else:
            for label, snip, comment in find(data):
                if comment:
                    comments += 1
                elif ALLOWED_RE.search(snip):
                    allowed[snip] += 1
                else:
                    bad[name].append((label, snip))

    print(f"Scanned {nfiles} files and {nres} .pak resources.")
    if unpack.skipped:
        print(f"WARNING: {unpack.skipped} brotli-compressed resources were NOT checked: install the module with"
              f" 'py -3.12 -m pip install brotli' or pass --brotli <path to brotli.exe>.")
    total = 0
    for place, hits in sorted(bad.items()):
        total += len(hits)
        print(f"\n{place}: {len(hits)} hit(s)")
        for label, snip in hits[:EXAMPLES]:
            print(f"   [{label}] {snip}")
        if len(hits) > EXAMPLES:
            print(f"   ... {len(hits) - EXAMPLES} more (use --all)")
    for rid, langs in sorted(locale.items()):
        total += sum(len(h) for h in langs.values())
        lang = "en-US" if "en-US" in langs else sorted(langs)[0]
        print(f"\nlocales\\*.pak string {rid}: in {len(langs)} language(s), e.g. {lang}:")
        for label, snip in langs[lang][:EXAMPLES]:
            print(f"   [{label}] {snip}")
    if allowed:
        print(f"\nAllowed (intentional) mentions: {sum(allowed.values())}")
        for snip, n in sorted(allowed.items(), key=lambda kv: -kv[1])[:EXAMPLES]:
            print(f"   {n}x  {snip}")
    if comments:
        print(f"Ignored {comments} mention(s) inside code comments (never shown to users).")
    installer_problems = 0
    if target.is_dir() and (target / "build.py").exists():
        installer_problems = check_installer(target)
    if total:
        print(f"\nRESULT: {total} leftover(s) found in {len(bad) + len(locale)} place(s).")
        print("Strings in locales\\*.pak come from translation files; text in chrome.dll / resources.pak"
              " comes from C++ or WebUI code. Search the patches for the snippet to find the source.")
        return 1
    if installer_problems:
        print("\nRESULT: no leftover Helium text in the build, but the installer check found problems (see above).")
        return 1
    print("\nRESULT: no leftover Helium text found.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
