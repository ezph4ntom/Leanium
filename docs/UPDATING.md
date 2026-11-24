# Updating to a newer Helium release

Leanium only edits Helium's build files, so updating means: get the new release, re-apply, rebuild.
Rebuild every month or two to pick up Chromium security fixes.

## The easy way: `update.bat`

In an **administrator** Command Prompt:

```bat
C:\h\leanium\scripts\update.bat status
```

shows which Helium version you are on, the newest one known, and what `build\src` was prepared for.
Then:

| Command | What it does |
| --- | --- |
| `update.bat` | Updates to the newest Helium release and rebuilds (3–4 hours). Asks first. |
| `update.bat 0.21.3.1` | The same, for a specific release. |
| `update.bat rebuild` | Same Helium version, rebuilt with the current scripts and logo. Reuses the prepared source when it matches (faster). |
| `update.bat resume` | Continues a build that was stopped (Ctrl+C, restart, crash). |

`update.bat` saves the current changes as diff files in `C:\h\backup-<version>-edits` before resetting,
asks before deleting `build\src`, and runs `check_leftovers.py` on the result. To see the steps without
running any of them: `set LEANIUM_DRY=1` first. If you edited this repository on GitHub, run `git pull`
in it **before** starting `update.bat`.

## By hand

1. Throw away the local edits made by `apply.py`:
   ```bat
   cd /d C:\h\helium-windows
   git checkout -- .
   git submodule foreach --recursive git checkout -- .
   ```
2. Fetch and switch to the new release tag:
   ```bat
   git fetch --tags
   git tag --sort=-v:refname
   git checkout --recurse-submodules <new-tag>
   ```
3. Pull the latest version of this repository (`git -C C:\h\leanium pull`).
4. Run `py -3.12 C:\h\leanium\scripts\apply.py . --assets C:\h\leanium\assets\branding`.
5. Search for leftovers: `git grep --recurse-submodules -n "Helium" -- "*.patch"` should only show
   intentional matches ("The Helium Authors", `Helium-bin`, namespace names such as `helium::`) and
   code names such as `kHeliumBangsEnabled`, which users never see.
6. Delete `build\src` and run `build.py` (without `--ci`) and `package.py` again.
7. Run `check_leftovers.py` (see [BUILDING.md](BUILDING.md), step 5).

If `apply.py` reports nothing to change, prints a WARNING, or a patch fails to apply during the build,
upstream changed something this tool depends on; open an issue.

## Publishing a release

After a build that passed `check_leftovers.py`:

1. Add a `## <version>` section to `CHANGELOG.md` describing what changed, then commit and push.
   For a second build of the same Helium version, use a suffix: `## 0.21.3.1-r2`.
2. Check everything without publishing:
   ```bat
   py -3.12 C:\h\leanium\scripts\make_release.py C:\h\helium-windows --dry
   ```
3. Publish (add `--tag 0.21.3.1-r2` for a rebuild of the same version):
   ```bat
   py -3.12 C:\h\leanium\scripts\make_release.py C:\h\helium-windows
   ```

The script needs the [GitHub CLI](https://cli.github.com/) logged in (`gh auth login`). It refuses to
publish if the checker finds leftovers, if the installer and zip are from different builds, or if this
repository has unpushed changes. It uploads `Leanium-<tag>-x64-installer.exe` and `SHA256SUMS.txt`, and
the release notes name the exact Helium version and commit of this repository.

## Customising

- **Logo:** edit the geometry in `scripts/make_assets.py`, run `py -3 scripts\make_assets.py`, and
  commit the regenerated files in `assets/`. Then `update.bat rebuild`.
- **Name:** change `NEW` (and the identifiers next to it) in `scripts/apply.py` and `NAME` in
  `scripts/make_assets.py`.
- **Already prepared source:** `scripts/update_src.py` applies rename and logo changes to an existing
  `build\src` so you do not have to download and patch Chromium again.
- **Chromium changes:** put a patch in `patches/`. `apply.py` adds it to the end of Helium's patch
  list, and `update_src.py` applies it to an existing `build\src`. Make it against the fully patched
  file in `build\src` (copy, edit, diff), since it is applied after all of Helium's patches.
- **Downloaded parts:** the first-run setup page and uBlock Origin are downloaded by `build.py`, so
  `apply.py` cannot edit them in advance. `apply.py` adds a step to the preparation (in
  `scripts/source.py` since Helium 0.22, in `build.py` before) that runs `scripts/rename_deps.py`
  on them.
