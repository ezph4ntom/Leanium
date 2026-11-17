#!/usr/bin/env python3
"""Leanium: turn a helium-windows checkout (tested with tags 0.21.1.1 and 0.21.3.1) into a personal,
rebranded build with the built-in password manager enabled.
Idempotent. Usage: python apply.py <path-to-helium-windows> [--assets <dir>] [--dry]
"""
import argparse, re, shutil, sys
from pathlib import Path

NEW = "Leanium"
# new identifiers so Leanium never collides with a real Helium install
GUID_OLD = "{FB68A146-637A-48C2-A0C4-1565DE45FEBD}"
GUID_NEW = "{3A7C51D2-9E04-4B8F-A1D6-5C2E70B8F4A3}"
SUBS_LITERAL = [  # (old, new) applied to windows change-branding.patch / nsi
    (GUID_OLD, GUID_NEW),
    ("0xE9852F6C", "0x5B1D93A4"),   # toast activator clsid
    ("0x140DE20F", "0x7E42C0B9"),   # elevator clsid
    ("0xC89A04FF", "0x2F9A61D3"),   # elevator iid
    ("{C89A04FF-00C6", "{2F9A61D3-00C6"),
    ('direct_launch_url_scheme = "helium"', 'direct_launch_url_scheme = "leanium"'),
    ('kSafeBrowsingName[] = "helium"', 'kSafeBrowsingName[] = "leanium"'),
    ("HeliumHTM", "LeaniumHTM"), ("HeliumPDF", "LeaniumPDF"),
]
# Not \b: Python counts Korean, Amharic, Telugu... letters as word characters, so "\bHelium\b" misses
# "Helium이" in translations. Only ASCII letters/digits/_ next to it mean "part of a longer name".
WORD = re.compile(r"(?<![A-Za-z0-9_])Helium(?![A-Za-z0-9_])(?!-bin)(?! Authors)")
SCHEME = [("helium://", "leanium://"), ('kHeliumUIScheme[] = "helium"', 'kHeliumUIScheme[] = "leanium"'),
          ('u"helium"', 'u"leanium"'), ("'helium:'", "'leanium:'")]   # the internal-page address (was helium://)
# Sentences that become FALSE for Leanium after the rename (Leanium has the password manager enabled).
# Applied by ren(), so the setup page (.grdp, via rename_deps.py) and the i18n sources always match.
PW_OLD = "Leanium doesn't have a built-in password manager. Would you like to install one from the Web Store?"
PW_NEW = ("Leanium has a built-in password manager. You can find it in Settings, under Autofill and passwords. "
          "You can also install another one from the Web Store.")
PW_TRANSLATED = {  # language file -> translated message; every other language shows the English sentence
    "pt-PT": "O Leanium tem um gestor de palavras-passe integrado. Pode encontrá-lo nas Definições, em "
             "Preenchimento automático e palavras-passe. Também pode instalar outro a partir da Web Store.",
}
FIXES = [(PW_OLD, PW_NEW)]
def ren(t):
    """Helium -> Leanium, and fix the earlier misspelling Leannium -> Leanium (idempotent)."""
    t = WORD.sub(NEW, t).replace("Leannium", "Leanium").replace("leannium", "leanium")
    for o, n in SCHEME: t = t.replace(o, n)
    for o, n in FIXES: t = t.replace(o, n)
    return t
PW_ENTRY = re.compile(r'("source": "' + re.escape(PW_NEW) + r'",\s*"message": ")((?:[^"\\]|\\.)*)(")')
def fix_translation(t, lang):
    """The translated text of a fixed sentence still says the old (false) thing: replace it."""
    new = PW_TRANSLATED.get(lang, PW_NEW)
    return PW_ENTRY.sub(lambda m: m.group(1) + new + m.group(3), t)
SKIP = ("update-credits.patch", "licenses-in-credits.patch")

changed = []
def write(p: Path, text: str, orig: str, dry):
    if text != orig:
        changed.append(str(p))
        if not dry:
            p.write_bytes(text.encode("utf-8", newline=None) if False else text.encode("utf-8"))

def rd(p):  # keep line endings untouched
    return p.read_bytes().decode("utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo"); ap.add_argument("--assets"); ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo); hc = repo / "helium-chromium"
    assets = Path(a.assets) if a.assets else Path(__file__).resolve().parent.parent / "assets" / "branding"
    if not (hc / "patches" / "series").exists():
        sys.exit("not a helium-windows checkout (submodule missing?)")

    # 1. password manager: drop the policy handler patch, default to enabled
    s = hc / "patches" / "series"; t = rd(s)
    n = "\n".join(l for l in t.split("\n") if l.strip() != "helium/core/disable-password-manager.patch")
    write(s, n, t, a.dry)
    p = hc / "patches/inox-patchset/modify-default-prefs.patch"
    if p.exists():
        t = rd(p); n = re.sub(r"(\+\s*prefs::kCredentialsEnableService,\s*)false", r"\1true", t)
        write(p, n, t, a.dry)

    # 2. rename inside patches (same line counts -> hunks stay valid)
    pats = list((hc / "patches").rglob("*.patch")) + list((repo / "patches").rglob("*.patch"))
    for p in pats:
        if p.name in SKIP or "password-manager.patch" == p.name and "disable" in p.name: continue
        t = rd(p); n = ren(t)
        if p.name == "change-branding.patch" and "windows" in str(p):
            for o, w in SUBS_LITERAL: n = n.replace(o, w)
        if p.name == "glue.patch":
            n = n.replace('L"Helium"', 'L"Leanium"')
        write(p, n, t, a.dry)

    # 3. i18n text + name substitution
    for p in [hc / "i18n/source.gen.json"] + sorted((hc / "i18n/translations").glob("*.json")):
        if p.exists():
            t = rd(p); write(p, fix_translation(ren(t), p.stem), t, a.dry)
    for f in ("name_substitution_utils.py", "name_substitution.py"):
        p = hc / "utils" / f
        if p.exists():
            t = rd(p)
            n = ren(t)
            write(p, n, t, a.dry)

    # 4. NSIS installer
    p = repo / "installer/helium.nsi"
    if p.exists():
        t = rd(p); n = ren(t.replace('PRODUCT_NAME "Helium"', 'PRODUCT_NAME "Leanium"').replace(GUID_OLD, GUID_NEW))
        write(p, n, t, a.dry)

    # 4b. Windows fix: 7-Zip can create symlinks that raise "Access is denied" in the merge step
    p = hc / "utils/_extraction.py"
    if p.exists():
        t = rd(p); nl = "\r\n" if "\r\n" in t else "\n"
        old = ("        if (source.is_dir() and not source.is_symlink() and destination.is_dir()" + nl +
               "                and not destination.is_symlink()):")
        new = ("        if (not source.is_symlink() and source.is_dir() and not destination.is_symlink()" + nl +
               "                and destination.is_dir()):")
        write(p, t.replace(old, new), t, a.dry)

    # 5. logo: resources + toolbar vector star
    if assets.exists() and not a.dry:
        dst = hc / "resources/branding"
        for f in assets.rglob("*"):
            if f.is_file() and f.suffix != ".txt":
                o = dst / f.relative_to(assets); o.parent.mkdir(parents=True, exist_ok=True)
                if not o.exists() or o.read_bytes() != f.read_bytes():
                    shutil.copyfile(f, o); changed.append(str(o))
    fav = assets.parent / "favicons"
    if fav.exists() and not a.dry:
        for f in fav.glob("*.png"):
            o = hc / "resources/favicons" / f.name
            if o.parent.exists() and (not o.exists() or o.read_bytes() != f.read_bytes()):
                shutil.copyfile(f, o); changed.append(str(o))
    lp = hc / "patches/helium/ui/helium-logo-icons.patch"
    pathfile = assets / "chrome_product_path.txt"
    if lp.exists() and pathfile.exists():
        t = rd(lp); new_d = pathfile.read_text().strip(); lines = t.split("\n")
        for i in range(1, len(lines)):
            if 'id="chrome-product" viewBox="0 0 56 56"' in lines[i - 1] and lines[i].startswith("+") and '<path d="' in lines[i]:
                lines[i] = re.sub(r'(<path d=")[^"]*(")', lambda m: m.group(1) + new_d + m.group(2), lines[i], count=1)
        write(lp, "\n".join(lines), t, a.dry)

    # 6. build.py: rename Helium in the parts it downloads (setup page, uBlock Origin). Must run after
    #    build.py's own name substitution and before it appends translations (see rename_deps.py).
    p = repo / "build.py"
    if p.exists():
        t = rd(p); nl = "\r\n" if "\r\n" in t else "\n"
        anchor = "            # Append translations" + nl
        hook = ("            # Leanium: rename Helium in downloaded parts (setup page, uBlock Origin)" + nl +
                "            subprocess.run([sys.executable, r'" + str(Path(__file__).resolve().parent / "rename_deps.py") +
                "', str(source_tree)], check=True)" + nl + nl)
        if "# Leanium: rename Helium in downloaded parts" not in t:
            if anchor not in t:
                print("WARNING: build.py changed upstream; could not add the rename_deps.py step")
            else:
                write(p, t.replace(anchor, hook + anchor, 1), t, a.dry)

    # 7. Leanium's own patches (leanium/patches/*.patch), applied after all of Helium's. For example
    #    restore-autofill-settings.patch puts back the "Autofill and passwords" settings page that
    #    helium/settings/remove-autofill.patch hides. They are made against the fully patched files.
    own = Path(__file__).resolve().parent.parent / "patches"
    if own.exists():
        dst = hc / "patches" / "leanium"
        s = hc / "patches" / "series"; t = rd(s); n = t
        for f in sorted(own.glob("*.patch")):
            o = dst / f.name
            if not o.exists() or o.read_bytes() != f.read_bytes():
                changed.append(str(o))
                if not a.dry:
                    dst.mkdir(parents=True, exist_ok=True); shutil.copyfile(f, o)
            entry = "leanium/" + f.name
            if entry not in [l.strip() for l in n.split("\n")]:
                n = n + ("" if n.endswith("\n") or not n else "\n") + entry + "\n"
        write(s, n, t, a.dry)

    print(("[dry] " if a.dry else "") + f"{len(changed)} files changed")
    for c in changed[:60]: print("  ", c)

if __name__ == "__main__":
    main()
