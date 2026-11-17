#!/usr/bin/env python3
"""Rename Helium -> Leanium in the parts of the source that build.py DOWNLOADS (so apply.py cannot edit
them beforehand): the first-run setup page and Helium's uBlock Origin build.

build.py calls this automatically (apply.py adds the call, right after build.py's own name substitution
and before translations are added, so the renamed text still matches the renamed translation files).
update_src.py calls it for an already prepared build\\src. Idempotent.

Usage: python rename_deps.py <build\\src folder>"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply import ren  # the same rename rule apply.py uses for the patches and translations

# uBlock's filter lists are Helium's own lists: name them honestly. The pattern also matches its own
# output after ren() ("Leanium filters (via Leanium)"), so running this twice changes nothing.
FILTER_LISTS = re.compile(r"Leanium filters(?: \(via Leanium\))?")
FILTER_LISTS_NAME = "Helium filters (via Leanium)"

FILES = [
    "components/helium_onboarding/helium_onboarding_strings.grdp",  # all setup-page text ("Meet Helium", ...)
    "components/helium_onboarding/index.html",                      # tab title "Helium Setup"
    "third_party/ublock/about.html",                                # "Helium fork:"
    "third_party/ublock/js/about.js",                               # "uBlock Origin x.y (Helium)"
    "third_party/ublock/assets/assets.json",                        # filter list names "Helium filters"
]


ASSETS = Path(__file__).resolve().parent.parent / "assets" / "onboarding"
# The setup page draws Helium's asterisk logo from its bundled design library, and uses its own favicon.
LOGO_SVELTE = "components/helium_onboarding/node_modules/@imput/helium-prism/dist/components/logos/HeliumLogoRaw.svelte"
FAVICON = "components/helium_onboarding/public/favicon.png"


def replace_logos(src: Path):
    """Put the Leanium cup in place of Helium's asterisk on the setup page (logo and tab icon)."""
    changed = 0
    for rel, new in ((LOGO_SVELTE, (ASSETS / "cup.svg").read_bytes()), (FAVICON, (ASSETS / "favicon.png").read_bytes())):
        p = src / rel
        if not p.exists():
            print(f"  rename_deps: not found (upstream changed?): {rel}")
            continue
        if p.read_bytes() != new:
            p.write_bytes(new)
            changed += 1
    if changed:
        # vite only rebuilds when a listed input changes; index.html is one, so mark it as changed
        (src / "components/helium_onboarding/index.html").touch()
    print(f"  rename_deps: replaced {changed} setup-page logo file(s) with the cup")


def rename(src: Path):
    replace_logos(src)
    changed = 0
    for rel in FILES:
        p = src / rel
        if not p.exists():
            print(f"  rename_deps: not found (upstream changed?): {rel}")
            continue
        t = p.read_bytes().decode("utf-8")
        n = ren(t)
        if rel.endswith("assets.json"):
            n = FILTER_LISTS.sub(FILTER_LISTS_NAME, n)
        if n != t:
            p.write_bytes(n.encode("utf-8"))
            changed += 1
    print(f"  rename_deps: renamed Helium -> Leanium in {changed} downloaded file(s)")


if __name__ == "__main__":
    if len(sys.argv) != 2 or not (Path(sys.argv[1]) / "BUILD.gn").exists():
        sys.exit(__doc__)
    rename(Path(sys.argv[1]))
