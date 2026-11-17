#!/usr/bin/env python3
"""Publish the newest Leanium build as a GitHub release (needs the GitHub CLI, logged in: gh auth login).

    py -3.12 make_release.py <path-to-helium-windows> [--tag 0.21.3.1-r2] [--dry]

It refuses to publish unless:
  - the leftover checker finds no "Helium" text in the build,
  - the installer and the scanned zip come from the same build,
  - this repository has no uncommitted changes and is pushed (the release points at that commit).
It uploads the installer as Leanium-<tag>-x64-installer.exe plus SHA256SUMS.txt. The release notes are
the CHANGELOG.md section for the tag (or its Helium version), followed by install and source details.
"""
import argparse, hashlib, re, shutil, subprocess, sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
GH_REPO = "ezph4ntom/Leanium"

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)

def fail(msg):
    sys.exit("STOPPED: " + msg)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hw", help="path to helium-windows")
    ap.add_argument("--tag", help="release tag (default: the Helium version, e.g. 0.21.3.1)")
    ap.add_argument("--dry", action="store_true", help="check everything and write the files, but do not publish")
    a = ap.parse_args()
    hw = Path(a.hw).resolve(); build = hw / "build"

    # the newest installer and the zip the checker scans
    inst = sorted([*build.glob("Leanium-*-x64-installer.exe"), *build.glob("helium_*_x64-installer.exe")],
                  key=lambda p: p.stat().st_mtime)
    zips = sorted(build.glob("*-windows.zip"), key=lambda p: p.stat().st_mtime)
    if not inst or not zips: fail("no installer or zip in " + str(build) + " (run package.py)")
    inst, zp = inst[-1], zips[-1]
    m = re.match(r"(?:Leanium-(.+)-|helium_(.+)_)x64-installer\.exe$", inst.name)
    ver = m.group(1) or m.group(2)
    if ver not in zp.name: fail(f"newest installer ({inst.name}) and zip ({zp.name}) are different versions")
    if abs(inst.stat().st_mtime - zp.stat().st_mtime) > 600:
        fail(f"{inst.name} and {zp.name} were made more than 10 minutes apart; run package.py again")
    tag = a.tag or ver
    if not re.fullmatch(r"[0-9][0-9A-Za-z.\-]*", tag): fail("odd tag: " + tag)

    # versions for the notes
    described = run(["git", "-C", str(hw), "describe", "--tags"]).stdout.strip()
    if described != ver: fail(f"helium-windows is on {described!r} but the installer is {ver}")
    v = dict(re.findall(r"(\w+)=(\S+)", (hw / "build/src/chrome/VERSION").read_text()))
    chromium = ".".join(v[k] for k in ("MAJOR", "MINOR", "BUILD", "PATCH"))

    # the checker must be clean
    print("Running the leftover checker on", zp.name, "...")
    chk = subprocess.run([sys.executable, str(REPO_DIR / "scripts/check_leftovers.py"), str(zp)])
    if chk.returncode != 0: fail("the checker found leftover Helium text (or failed); fix that first")

    # this repository must be committed and pushed
    if run(["git", "-C", str(REPO_DIR), "status", "--porcelain"]).stdout.strip():
        fail("this repository has uncommitted changes; commit and push them first")
    run(["git", "-C", str(REPO_DIR), "fetch", "-q", "origin"])
    head = run(["git", "-C", str(REPO_DIR), "rev-parse", "HEAD"]).stdout.strip()
    remote = run(["git", "-C", str(REPO_DIR), "rev-parse", "origin/main"]).stdout.strip()
    if head != remote: fail("this repository is not pushed (HEAD differs from origin/main); push first")

    if run(["gh", "release", "view", tag, "-R", GH_REPO]).returncode == 0:
        fail(f"release {tag} already exists; use --tag {ver}-r2 (and add a '## {ver}-r2' section to CHANGELOG.md)")

    # files
    out = build / "release" / tag
    out.mkdir(parents=True, exist_ok=True)
    asset = out / f"Leanium-{tag}-x64-installer.exe"
    shutil.copyfile(inst, asset)
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    (out / "SHA256SUMS.txt").write_text(f"{digest}  {asset.name}\n", encoding="utf-8", newline="\n")

    # notes: the changelog section, then fixed details
    log = (REPO_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    section = ""
    for key in (tag, ver):
        m = re.search(r"^## " + re.escape(key) + r"[ \t]*\n(.*?)(?=^## |\Z)", log, re.M | re.S)
        if m: section = m.group(1).strip(); break
    if not section: fail(f"CHANGELOG.md has no '## {tag}' or '## {ver}' section; add one and push")
    notes = f"""{section}

### Install

Download **{asset.name}** below and run it. Windows SmartScreen will warn that the publisher is
unknown because the installer is not code-signed: choose *More info → Run anyway*. To update, install
over the previous version; there is no need to uninstall first.

SHA-256: `{digest}`

### Built from

- Helium [{ver}](https://github.com/imputnet/helium-windows/releases/tag/{ver}) (Chromium {chromium})
- This repository at [`{head[:7]}`](https://github.com/{GH_REPO}/tree/{head})

Unofficial build, not affiliated with the Helium project. The source code for everything in this
installer is available from the links above, under the licences of each project.
"""
    nf = out / "NOTES.md"; nf.write_text(notes, encoding="utf-8", newline="\n")
    print(f"\nRelease {tag}: {asset} ({asset.stat().st_size // 2**20} MB)\nSHA-256 {digest}\nNotes: {nf}")
    cmd = ["gh", "release", "create", tag, str(asset), str(out / "SHA256SUMS.txt"), "-R", GH_REPO,
           "--title", f"Leanium {tag}", "--notes-file", str(nf), "--target", head]
    if a.dry:
        print("[dry run] would run:", " ".join(cmd)); return
    print("Uploading (about 120 MB)...")
    r = subprocess.run(cmd)
    if r.returncode != 0: fail("gh release create failed (see above)")
    print("Published: https://github.com/" + GH_REPO + "/releases/tag/" + tag)

if __name__ == "__main__":
    main()
