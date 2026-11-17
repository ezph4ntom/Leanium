#!/usr/bin/env python3
"""Rename Helium -> Leanium in the parts of the source that build.py DOWNLOADS (so apply.py cannot edit
them beforehand): the first-run setup page and Helium's uBlock Origin build.

build.py calls this automatically (apply.py adds the call, right after build.py's own name substitution
and before translations are added, so the renamed text still matches the renamed translation files).
update_src.py calls it for an already prepared build\\src. Idempotent.

Usage: python rename_deps.py <build\\src folder>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply import ren  # the same rename rule apply.py uses for the patches and translations

FILES = [
    "components/helium_onboarding/helium_onboarding_strings.grdp",  # all setup-page text ("Meet Helium", ...)
    "components/helium_onboarding/index.html",                      # tab title "Helium Setup"
    "third_party/ublock/about.html",                                # "Helium fork:"
    "third_party/ublock/js/about.js",                               # "uBlock Origin x.y (Helium)"
    "third_party/ublock/assets/assets.json",                        # filter list names "Helium filters"
]


def rename(src: Path):
    changed = 0
    for rel in FILES:
        p = src / rel
        if not p.exists():
            print(f"  rename_deps: not found (upstream changed?): {rel}")
            continue
        t = p.read_bytes().decode("utf-8")
        n = ren(t)
        if n != t:
            p.write_bytes(n.encode("utf-8"))
            changed += 1
    print(f"  rename_deps: renamed Helium -> Leanium in {changed} downloaded file(s)")


if __name__ == "__main__":
    if len(sys.argv) != 2 or not (Path(sys.argv[1]) / "BUILD.gn").exists():
        sys.exit(__doc__)
    rename(Path(sys.argv[1]))
