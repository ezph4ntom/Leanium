# Updating to a newer Helium release

Leanium only edits Helium's build files, so updating means: get the new release, re-apply, rebuild.

1. Throw away the local edits made by `apply.py`:
   ```bat
   cd /d C:\h\helium-windows
   git checkout -- .
   git submodule foreach --recursive git checkout -- .
   ```
2. Fetch and switch to the new release tag:
   ```bat
   git fetch --tags
   git checkout --recurse-submodules <new-tag>
   ```
3. Pull the latest version of this repository (`cd leanium && git pull && cd ..`).
4. Run `py -3.12 leanium\scripts\apply.py . --assets leanium\assets\branding`.
5. Search for leftovers: `git grep --recurse-submodules -n "Helium" -- "*.patch"` should only show
   intentional matches ("The Helium Authors", `Helium-bin`, namespace names such as `helium::`).
6. Delete `build\src` (or the whole `build` folder) and run `build.py` and `package.py` again.

If `apply.py` reports nothing to change or a patch fails to apply during the build, upstream changed
something this tool depends on; open an issue.

## Customising

- **Logo:** edit the geometry in `scripts/make_assets.py`, run `py -3 scripts\make_assets.py`, and
  commit the regenerated files in `assets/`.
- **Name:** change `NEW` (and the identifiers next to it) in `scripts/apply.py` and `NAME` in
  `scripts/make_assets.py`.
- **Already prepared source:** `scripts/update_src.py` applies rename and logo changes to an existing
  `build\src` so you do not have to download and patch Chromium again.
