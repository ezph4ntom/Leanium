# Leanium UI v2 (Zen look, horizontal tabs): progress report

Branch `ui-zen-v2`, created from `main` (`bacd9f7`). `main` and `ui-zen-experiment` are untouched.
**Status: stopped partway because the usage limit was reached.** Tier A is finished and tested. Tier B is
built twice and partly verified. Tier C and the final Tier B rebuild have not been done.

## Step 0: why the first experiment felt the same

The experiment changed one structural thing: Compact layout, which puts the tabs and the address bar in
one row. Everything else was too faint to notice:
- The tabs kept Helium's shape: a rounded rectangle for the active tab and thin separators between the others.
- The page gap grew by only 3 px (12 → 15 px, measured including Windows' invisible border).
- The purple tint was about 10 RGB units away from grey.
- An existing profile kept its saved grey theme (`is_grayscale2: true`). This was reproduced with a
  profile first used by the baseline build.

The ⋮ menu was pixel-identical. The About page, new-tab page and password settings differed in at most 3.1 % of
pixels, which is just the tint. Text was unchanged. Screenshots: `ui-screenshots/step0/`.
So v2 changes **shapes** (pill tabs, card corners, one top bar) and makes the accent and layout reach existing profiles too.

## Safety net
- Original installer backup: `C:\h\leanium-backups\0.21.3.1\Leanium-0.21.3.1-x64-installer.exe`,
  SHA-256 `67cdb0497940386c5cff10f5508c1946b4231c8fd4ad74e1e178df34bf240bbf`. Re-verified, and it matches the recorded value.
- Known-good build copies moved (not deleted) to `C:\h\helium-windows\build\known-good-0.21.3.1\`.
- Moved to `C:\h\_to_delete\ui-zen-experiment-patch-copies\`: duplicates of the experiment's 3 patches.
  The originals are still on branch `ui-zen-experiment`.

## Items

| # | Item | Status | Commit | Evidence |
| --- | --- | --- | --- | --- |
| 9 | Setup-page password sentence | done (already on main) | `a3272d2` | `ui-screenshots/tierA/setup_password_step.png` |
| 10 | Installer name `Leanium-<version>-x64-installer.exe` | done | `2b1d16f` | Tier A build log: `package.py` wrote `build\Leanium-0.21.3.1-x64-installer.exe` (a file name, so no browser screenshot) |
| 11 | About: "Leanium, based on Helium" + repo link | done | `b84330d` | `ui-screenshots/tierA/about_page.png` |
| 12 | uBlock lists "Helium filters (via Leanium)" | done | `7b379bb` | `ui-screenshots/tierA/ublock_filter_lists.png` |
| 13 | Checker also validates the installer | done | `09883c9` | Tier A log: uninstall name, Start-menu name (82 languages), apps folder and uninstall key all OK; a negative test caught Helium names (a script, so no browser screenshot) |
| 14 | Password Manager in the ⋮ menu | done | `1cb7fda` | `ui-screenshots/tierA/app_menu.png` (label is Chromium's translated "Password Manager") |
| 15 | Local-only reminder (README + password settings) | done | `6f3d76f` | `ui-screenshots/tierA/password_settings.png` |
| 16 | `MOODLE_LOGIN_TEST.md` | done | `56c9224` | file in repo root (a document, so no browser screenshot) |
| 17 | Default search / homepage / startup | **skipped** | – | Still placeholders, and no earlier choice exists in the repo, notes or chat. Not guessed. |
| 1 | Floating card (8 px gap, 12 px corners) | built, partly verified | `9b8e65d` | `ui-screenshots/tierB/side_by_side_baseline_vs_tierB.png` (gap 12 → 17 px, rounder corner) |
| 2 | Unified top bar (compact by default, once for existing profiles) | built, partly verified | `b2bd07d` | same side-by-side: one row, page starts at y=36 instead of 67 |
| 3 | Pill tabs, no separators (+ faint pills for inactive tabs) | built in attempt 2, **not yet judged** | `f9b8849`, `fcfa4a7` | `ui-screenshots/tierB/attempt2-window_neutral.png` |
| 5 | Accent #B048C4 (most common logo colour), vibrant | built, verified | `e015edc` | `ui-screenshots/tierB/attempt1-password_settings.png` (purple toggles) |
| 6 | Mica window tint | **skipped** | – | Helium's native-frame-materials is macOS only (`HeliumNativeFrameAvailable()` returns false off Mac). |
| 7 | New-tab page (cup logo, search box, gradient) | **fix committed, not built** | `71b75aa` + next commit | Attempt 1 (`attempt1-window_ntp.png`) had the search box covering the logo, a "Search Google" placeholder, and voice/Lens buttons. All three are fixed in the patch, but not rebuilt yet. |
| 4 | Compact mode toggle (hide toolbar until hover) | not built as a tier yet | – | Already exists as Helium's "Frameless mode" (Settings → Appearance, off by default). Verified on the baseline: the bar hides and reappears at the top edge. |
| 8 | Smoother tab transitions | **skipped** | – | Chromium already animates these. A timing change can't be shown in a screenshot. |

## Tier B side-by-side verdict
**Not final.** Attempt 1 showed a clear change in the top bar and the page margin and corners. The tab
shape was too subtle, so I strengthened it (faint pills for inactive tabs) and rebuilt it as attempt 2. I have
not judged attempt 2 side by side yet, and the new-tab page fix is not built. Tier B is therefore **not reported as passed**.

## Installers (all kept, in `C:\h\helium-windows\build\ui-tiers\`)

| Installer | SHA-256 | Tested |
| --- | --- | --- |
| `tierA\Leanium-0.21.3.1-ui-tierA-x64-installer.exe` | `ea4211d9af8287f57163129323296ae16fea4fc2254cba6546d6f957619493b4` | All 10 checks pass: start, tabs, name, password saving, autofill, export, cleanup |
| `tierB-attempt1\...-ui-tierB-attempt1-x64-installer.exe` | `80a2c844430dab42c1a6dbd16f70086eb2f3fcf553ed60c197eecd38242e4fb8` | Checker OK; new-tab page has the layout bug |
| `tierB-attempt2\...-ui-tierB-attempt2-x64-installer.exe` | `8841042054af903c44753b94650384aad176643f43e0cbb2e9207d840d85cd84` | Checker OK; functional tests not run **[unverified]** |

No `tierC` installer exists yet.

## Revert or keep a tier
- **Revert:** run `C:\h\leanium-backups\0.21.3.1\Leanium-0.21.3.1-x64-installer.exe` and install over the
  current version. It's the same Chromium version, so your profile and passwords stay. The theme and layout
  flags v2 sets in a profile remain; change them back under Settings → Appearance.
- **Keep Tier A:** install the `tierA` installer above.
- **Source:** `git switch ui-zen-v2` in `C:\h\leanium`. Each item is its own patch in `patches/` (`tierA-*`,
  `tierB-*`). To drop one, delete its line from `helium-chromium\patches\series`, reverse it in `build\src`
  (`patch.exe -p1 -R -i ...`), and `git revert` its commit.
- **Note:** `build\src` currently contains Tier A + Tier B, **including the unbuilt new-tab page fix**.

## Left to do
1. Build Tier B once more (`C:\h\ui-test\build_tier.bat tierB`, about 6 min).
2. Run `zen2.py shots` and `tests` and the side-by-side, and decide pass or fail honestly.
3. Tier C: run `zen2.py frameless` on that build and copy it as the tierC installer.
4. Finish this report.

## Notes
- **[unverified]** Installing any test installer: not done (outside the allowed folders).
- One screen-region capture accidentally included another app's window. It was deleted immediately and never saved
  elsewhere or committed; all later captures are window-only (PrintWindow).
- Test logins used a random dummy password. The exported CSV was deleted at once, and test profiles were deleted.
