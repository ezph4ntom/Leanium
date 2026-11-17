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
The NSIS installer itself is compressed and is not scanned; apply.py edits installer\\helium.nsi.
Exit code: 0 = nothing unexpected, 1 = leftovers found, 2 = error."""
import gzip, re, shutil, struct, subprocess, sys, zipfile
from collections import defaultdict
from pathlib import Path

ALLOWED = [r"The Helium Authors", r"Helium-bin", r"opensource_project.{0,6}Helium", r"Name: Helium",
           r"component of Helium", r"based on Helium", r"github\.com/imputnet/helium",
           # credits page (leanium://credits): correct attribution of the project Leanium is built on
           r"Helium source code is available", r'class="title">Helium<',
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


def main():
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
    if total:
        print(f"\nRESULT: {total} leftover(s) found in {len(bad) + len(locale)} place(s).")
        print("Strings in locales\\*.pak come from translation files; text in chrome.dll / resources.pak"
              " comes from C++ or WebUI code. Search the patches for the snippet to find the source.")
        return 1
    print("\nRESULT: no leftover Helium text found.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
