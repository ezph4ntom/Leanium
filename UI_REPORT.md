# Leanium UI experiment (Zen-inspired) – report

Date: 2026-11-17. Branch: `ui-zen-experiment` (from `main` at `bacd9f7`). Base: Helium 0.21.3.1, Chromium 157.0.8103.78.

## 1. Can you go back?

Yes, in both senses. **The installed browser:** reinstall the backed-up `Leanium-0.21.3.1-x64-installer.exe`. Both builds are the same Leanium version (Chromium 157.0.8103.78) with the same install IDs, so the old installer goes over the test one and keeps your profile and saved passwords. **The source:** the known-good recipe is untouched on `main`. The three UI changes exist only as three separate patch files on this branch, and each one reverses cleanly in the real `build\src` (dry-run checked), so you can keep building from the known-good installer's source or from the experiment. The installer itself is only a finished snapshot; you can't build from it.

Checked: `git diff main..ui-zen-experiment` adds only `patches/ui-*.patch` (+ this report); `scripts/apply.py` is identical on both branches (same install IDs); both builds report `Chrome/157.0.8103.78`; `patch -R --dry-run` succeeds for all three patches on `build\src`. **[unverified]** The actual reinstall was not performed, because installing was outside what I was allowed to touch.

## 2. Backup

| What | Where | SHA-256 |
| --- | --- | --- |
| Original installer (known-good) | `C:\h\leanium-backups\0.21.3.1\Leanium-0.21.3.1-x64-installer.exe` | `67cdb0497940386c5cff10f5508c1946b4231c8fd4ad74e1e178df34bf240bbf` (matches the published release) |
| Same build's outputs (installer, mini-installer, zip) | `C:\h\leanium-backups\0.21.3.1\build-outputs\` | installer identical to the above |
| The 3 original source files | `C:\h\leanium-backups\0.21.3.1\build-src-originals\` | |
| Helium patch list before the experiment | `C:\h\leanium-backups\0.21.3.1\series.before-ui` | |

The original installer in `C:\h\helium-windows\build\release\0.21.3.1\` was never touched (hash re-checked after the build). Nothing was deleted, so `_to_delete/` was not needed. Things that were **moved or copied**:
- The 0.21.3.1 outputs in `build\` were moved into the backup before building, then copied back after it.
- The UI-test build's outputs are in `build\ui-test\build-outputs\`, so `build\` still holds only the known-good files.

## 3. Changes (each one is its own patch and commit; revert any one alone)

| Commit | Patch | Change |
| --- | --- | --- |
| `00e3d43` | `patches/ui-compact-layout-default.patch` | Default layout is Helium's **Compact**: tabs and the address bar in **one row**, tabs stay **horizontal**. Only the default; a layout you picked yourself is kept. |
| `44244b7` | `patches/ui-floating-content-card.patch` | The page **floats as a rounded card**: 6 px gap instead of 3 px, and 8 px rounded corners on all four corners. Split view is unchanged; the existing setting "Show a rounded frame around web contents" still turns it off. |
| `b9ad973` | `patches/ui-leanium-soft-theme.patch` | **Softer colours:** a soft purple theme taken from the cup logo (#AF4BC4, "tonal" variant) instead of Helium's grey. It applies to new profiles and to *Settings → Appearance → Reset to default*. An existing profile keeps its current theme, and grey is still in the colour picker. |

**Why these defaults** (there was no UI spec in the repo; the 16 Nov discussion was the guide):
- **No vertical tabs.** On 16 Nov you said you love Zen's look but not its vertical tabs and would keep them horizontal, so I skipped the optional vertical-tabs sidebar. Helium's Vertical layout is still in Settings if you change your mind.
- **Using Helium's own layouts.** Helium already has a tested Compact layout. Making it the default (a 1-line change) is far safer than building a new toolbar.
- **Floating card.** Helium already draws a rounded frame, but its 3 px gap barely shows. Zen uses about 8 px, so 6 px was a modest step towards that.
- **Theme.** I previewed Tonal and Neutral variants of the logo purple on the unchanged build. Neutral looked almost the same as grey; Tonal is soft but clearly Leanium.
- **Not made default:** Helium's "Frameless mode" (hides the toolbar until you hover), "native frame materials" (Mica, which Helium itself labels experimental) and the centred address bar. All three are still in *Settings → Appearance* to try.

## 4. Test results (new build, fresh test profile, default settings)

Tests ran on the portable copy of the build (`C:\h\ui-test\new\app`) with a throwaway profile inside `C:\h\ui-test`. Your installed Leanium and profile were not used. The test login was random and was removed afterwards, and the test profile was deleted. The same suite was run on the original build first, and all checks passed there too (`C:\h\ui-test\baseline\tests\results.json`).

| Check | Result | Evidence |
| --- | --- | --- |
| Build compiles | PASS | `C:\h\build-0.21.3.1-ui-test.log`: `theme_service.obj`, `multi_contents_view.obj`, `tab_strip_prefs.obj` compiled, `LINK(DLL) chrome.dll` finished, `[checker exit 0]` |
| No leftover "Helium" text | PASS | same log: `RESULT: no leftover Helium text found.` |
| Browser starts | PASS | DevTools answered `Chrome/157.0.8103.78` |
| Tabs work | PASS | 4 tabs after opening 3, 3 after closing one; `C:\h\ui-test\new\tests\window_tabs.png` |
| Name "Leanium" shows | PASS | window title `'Tab 2 - Leanium'`; `chrome://version`: "The Leanium Authors"; About page text contains "Leanium" (`about_page.png`) |
| Logo still shows | PASS | `about_page.png` shows the cup; build comparison (`C:\h\ui-test\new\compare_builds.json`): only `chrome.dll` differs, the 43 icons in `chrome.exe` are identical, and 935/935 PNG images in the .pak files (cup logo included) are identical |
| Password saving enabled | PASS | `credentials_enable_service` = True |
| "Autofill and passwords" in Settings | PASS | menu item present; `settings_autofill.png` |
| Password manager stores a login | PASS | 0 → 1 saved login (`leanium-ui-test` for `http://127.0.0.1:<port>`); `password_manager.png` |
| Saved login autofills a real form | PASS | filled on page load: username `leanium-ui-test`, password length matches; `window_autofill.png` |
| Test login removed | PASS | 0 saved logins left |
| Compact layout is the default | PASS | page starts at y=36 (one row) vs y=67 on the original (two rows) |
| Explicit Classic choice respected | PASS | a profile with layout=Classic still starts at y=67 (`C:\h\ui-test\new\explicit_classic\window_tabs.png`) |
| Floating card | PASS | gap 12 → 15 px (incl. Windows' invisible border), bottom-left corner diagonal 1 → 2 px |
| Soft Leanium theme (new profile) | PASS | frame colour (30,32,32) grey → (41,27,43) purple; `C:\h\ui-test\new\ntp\window_tabs.png` |
| Existing grey profile kept, Reset gives Leanium theme | PASS | (30,32,32) before → (41,27,43) after `useDefaultTheme`; `C:\h\ui-test\new\theme_reset\` |

Not tested **[unverified]**:
- installing or uninstalling the new installer
- Windows light mode (this PC is in dark mode)
- split view and a maximised window with the new card gap
- high-DPI scaling
- your real Moodle login

## 5. New installer, how to revert, how to continue

**New installer:** `C:\h\helium-windows\build\ui-test\Leanium-0.21.3.1-ui-test-x64-installer.exe`
SHA-256 `51f530c7524ee78217afbe2d251ca91b2b40ce6a4e85664fabc6ee92338fcccf`. It installs over your current Leanium (same install IDs), not next to it.

**To try it:** export your passwords first (*Settings → Autofill and passwords → Password Manager → Settings → Export passwords*), then run the installer above. Don't uninstall first.

**Revert the installed browser:** run `C:\h\leanium-backups\0.21.3.1\Leanium-0.21.3.1-x64-installer.exe` and install over the test version. Your profile and passwords stay. Any setting you changed while testing (layout, theme) stays in the profile; change it back under *Settings → Appearance*.

**Revert the source** (only needed if you want to *build* the known-good version again). In an administrator Command Prompt, one at a time:

1. `cd /d C:\h\helium-windows\build\src`
2. `third_party\git\usr\bin\patch.exe -p1 -R -i C:\h\helium-windows\helium-chromium\patches\leanium\ui-leanium-soft-theme.patch`
3. `third_party\git\usr\bin\patch.exe -p1 -R -i C:\h\helium-windows\helium-chromium\patches\leanium\ui-floating-content-card.patch`
4. `third_party\git\usr\bin\patch.exe -p1 -R -i C:\h\helium-windows\helium-chromium\patches\leanium\ui-compact-layout-default.patch`
5. `copy /y C:\h\leanium-backups\0.21.3.1\series.before-ui C:\h\helium-windows\helium-chromium\patches\series`
6. `cd /d C:\h\leanium` then `git switch main`

To undo only **one** change, run just its line from steps 2–4, delete its line from `helium-chromium\patches\series`, and `git revert <commit>` on the branch.

**Continue building the experiment:** `git switch ui-zen-experiment` in `C:\h\leanium` (it is the current branch now). `build\src` already contains the changes. After editing, `C:\h\ui-test\build_ui.bat` compiles, packages and runs the checker (about 5 minutes for small changes). It deliberately does not re-copy the logo files, which is why it's faster than `update.bat resume`. `update.bat` also works with this branch: `apply.py` adds every file in `patches/` to the build.

## 6. Not done, and notes

- **No push to `main`, no release, no visibility change.** Only `ui-zen-experiment` was pushed.
- **Test tools** (`uitest.py`, `compare_builds.py`, `theme_reset_test.py`, `mkpatch.py`, `build_ui.bat`) are in `C:\h\ui-test`, not in the repository. `pip install websocket-client` was run for them; it changes the Python install, not Windows settings.
- **[unverified]** Running the test browser may have written Chromium's usual small launch marker to the registry under HKCU; files went only into `C:\h\ui-test`.
- **Not attempted** from the 16 Nov idea list: pill-shaped tabs, auto-hiding top bar by default, cleaner new-tab page, animations. Each would touch more of Helium's tab and layout code.
