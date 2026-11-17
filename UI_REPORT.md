# Leanium UI v2 (Zen look, horizontal tabs): report

Branch `ui-zen-v2`, created from `main` (`bacd9f7`). `main` and `ui-zen-experiment` are untouched; only
`ui-zen-v2` was pushed. Base: Helium 0.21.3.1, Chromium 157.0.8103.78. Date: 2026-11-17.

## Step 0: why the first experiment felt the same

The `ui-zen-experiment` build changed one structural thing: Compact layout, which puts the tabs and the
address bar in one row. Everything else was too faint to notice:
- The tabs kept Helium's shape: a rounded rectangle for the active tab and thin separator lines between the others.
- The page gap grew by only 3 px (12 → 15 px, measured including Windows' invisible border).
- The purple tint was about 10 RGB units away from grey (top bar (30,32,32) → (41,27,43)).
- An existing profile kept its saved grey theme (`is_grayscale2: true`), so for you even the tint did not appear.

The ⋮ menu was pixel-identical. The About page, new-tab page and password settings differed in at most 3.1 % of
pixels, which is just the tint. Text was unchanged. So v2 changes **shapes** (pill tabs, card corners, one top
bar) and makes the accent colour and layout reach existing profiles once. Screenshots: `ui-screenshots/step0/`
(1280×800, same neutral page; `existing_experiment-*` = a baseline profile opened with the experiment).

## Safety net
- **Original installer backup:** `C:\h\leanium-backups\0.21.3.1\Leanium-0.21.3.1-x64-installer.exe`,
  SHA-256 `67cdb0497940386c5cff10f5508c1946b4231c8fd4ad74e1e178df34bf240bbf`. Re-verified before any change;
  it matches the recorded value.
- **Known-good build copies:** moved, not deleted, from `build\` to `C:\h\helium-windows\build\known-good-0.21.3.1\`.
- **`C:\h\_to_delete\ui-zen-experiment-patch-copies\`:** the experiment's 3 patch copies that were in Helium's patch folder.
  They are duplicates; the originals are on branch `ui-zen-experiment`.

## Items

Every code item is its own patch file in `patches/` and its own commit. Screenshots are in `ui-screenshots/<tier>/`.

| # | Item | Status | Commit | Screenshot / evidence | Reason |
| --- | --- | --- | --- | --- | --- |
| 1 | Floating content card | done | `9b8e65d` | `tierB/side_by_side_baseline_vs_tierB.png` | 8 px gap (was 3), 12 px corners on all four corners (was 8/5) |
| 2 | Unified top bar | done | `b2bd07d` | `tierB/window_neutral.png`, `tierB/existing_profile-window_neutral.png` | Helium's Compact layout as default: one row, one background, no line. A profile still on Classic is moved once |
| 3 | Pill tabs, no separators | done | `f9b8849`, `fcfa4a7` | `tierB/window_neutral.png` | Active tab is a solid pill and inactive tabs are faint pills; the first version was too subtle, so I strengthened it |
| 4 | Compact mode toggle (hide toolbar until top-edge hover) | done (no code) | – | `tierC/frameless_on_pointer_in_page.png`, `tierC/frameless_on_pointer_at_top_edge.png` | Already exists as Helium's **Frameless mode** (Settings → Appearance), off by default. I didn't add a second toggle with the same job |
| 5 | Leanium accent colour | done | `e015edc` | `tierB/password_settings.png` (purple toggles), `tierB/window_neutral.png` | #B048C4 = the most common colour of `assets/logo_1024.png` (31.7 % of opaque pixels), vibrant variant; applied once to grey profiles |
| 6 | Window tint (Mica) | **skipped** | – | – | Helium's native-frame-materials is macOS-only (`HeliumNativeFrameAvailable()` returns false off Mac; `PlatformSupportsNativeFrameMaterials()` returns false) |
| 7 | Cleaner new-tab page | done | `71b75aa`, `b3d303d` | `tierB/window_ntp.png` | Cup logo, search box (default engine), shortcuts, soft gradient; no voice/Lens buttons; neutral placeholder |
| 8 | Smoother tab transitions | **skipped** | – | – | Chromium already animates tab open/close and hover; a timing change can't be shown in a screenshot, so it couldn't meet the "done" rule |
| 9 | Setup-page password sentence | done | `a3272d2` (on main) | `tierA/setup_password_step.png` | – |
| 10 | Installer name `Leanium-<version>-x64-installer.exe` | done | `2b1d16f` | build logs: `package.py` wrote `build\Leanium-0.21.3.1-x64-installer.exe` | a file name, so no browser screenshot |
| 11 | About: "Leanium, based on Helium" + link | done | `b84330d` | `tierA/about_page.png` | – |
| 12 | uBlock lists "Helium filters (via Leanium)" | done | `7b379bb` | `tierA/ublock_filter_lists.png` | – |
| 13 | Checker validates the installer | done | `09883c9` | build logs: uninstall entry and Start-menu name "Leanium" in 82 languages, "Leanium Apps" folder, `...\Uninstall\Leanium`; a negative test caught Helium names | a script, so no browser screenshot |
| 14 | Passwords in the ⋮ menu | done | `1cb7fda` | `tierA/app_menu.png` | Label is Chromium's existing translated "Password Manager" |
| 15 | Local-only reminder (README + password settings) | done | `6f3d76f` | `tierA/password_settings.png` | – |
| 16 | `MOODLE_LOGIN_TEST.md` | done | `56c9224` | file in repo root | a document, so no browser screenshot |
| 17 | Default search / homepage / startup | **skipped** | – | – | Still placeholders, and no earlier choice exists in the repo, notes or this chat. Not guessed |

## Tier B side-by-side verdict: **PASS**

Baseline vs final Tier B, full 1280×800 window, same neutral page:
`ui-screenshots/step0/baseline-window_neutral.png` vs `ui-screenshots/tierB/window_neutral.png`, combined in
`ui-screenshots/tierB/side_by_side_baseline_vs_tierB.png` (numbers in `side_by_side.json`).
- **Top bar:** two dark grey rows became one purple row. The page starts at y = 36 instead of 67, and 55.8 % of the top-band pixels changed.
- **Page margin and corners:** the page is a white card inside a purple frame. The gap is 17 px instead of 12 (including Windows' invisible border), and the
  corner is clearly rounder (zoom panel; corner diagonal 4 px instead of 1).
- **Tab shape:** a flat strip with separator lines became a row of capsules with one solid pill. This is the subtlest of the three at full
  size, but visible at a glance in the strip crop.

An honest note: the first Tier B build did **not** pass on tab shape, because Helium already drew a rounded active tab. I fixed it (`fcfa4a7`)
and rebuilt before calling it a pass. Attempt 1 also had the search box covering the logo on the new-tab page; that's fixed in `b3d303d`.

**Existing profile:** a profile created with the baseline (grey theme saved), opened with Tier B, shows the
new look on first start: accent theme applied, single row, both one-time flags set
(`tierB/existing_profile-window_neutral.png`).

## Checks after each build

All 10 checks pass on the Tier A build and on the final Tier B build, which is also Tier C (`tierA/tests.json`, `tierB/tests.json`):
- the browser starts, and tabs open and close
- the window title, `chrome://version` and the About page say Leanium
- password saving is on
- a login is **saved**, **autofilled** on a real form and **exported** through the real Save dialog to a CSV (checked by username, then deleted at once)
- the test login is removed again

**Logo:** the About page shows the cup (`tierA/about_page.png`, `tierB/about_page.png`). Compared with the known-good build, only
`chrome.dll` and `resources.pak` changed. All 43 icons in `chrome.exe` are identical, and no PNG resource changed
(`tierB/compare_builds.json`). The leftover checker and the installer check were clean for every build.

## Installers (`C:\h\helium-windows\build\ui-tiers\`)

| Tier | File | SHA-256 |
| --- | --- | --- |
| A | `tierA\Leanium-0.21.3.1-ui-tierA-x64-installer.exe` | `ea4211d9af8287f57163129323296ae16fea4fc2254cba6546d6f957619493b4` |
| B | `tierB\Leanium-0.21.3.1-ui-tierB-x64-installer.exe` | `2fa14f8bfdb46eb39efdcf03f1ac125eeb93e44a0a6fb44c482c61bc20ad732b` |
| C | `tierC\Leanium-0.21.3.1-ui-tierC-x64-installer.exe` | `2fa14f8bfdb46eb39efdcf03f1ac125eeb93e44a0a6fb44c482c61bc20ad732b`. Same file as B: Tier C added no code (item 4 is Helium's own toggle, item 8 was skipped) |
| (kept) | `tierB-attempt1\...-attempt1-x64-installer.exe` | `80a2c844430dab42c1a6dbd16f70086eb2f3fcf553ed60c197eecd38242e4fb8`. Superseded: tab shape too subtle, new-tab page layout bug |
| (kept) | `tierB-attempt2\...-attempt2-x64-installer.exe` | `8841042054af903c44753b94650384aad176643f43e0cbb2e9207d840d85cd84`. Superseded: new-tab page layout bug |

All of them install over your current Leanium (same install IDs), not next to it.

## Revert, or keep one tier

- **Back to the known-good browser:** run `C:\h\leanium-backups\0.21.3.1\Leanium-0.21.3.1-x64-installer.exe` and install
  over the current version. It's the same Chromium version, so your profile and saved passwords stay. Tier B
  changed two settings in your profile (theme → Leanium purple, layout → Compact). After reverting, set them
  back in *Settings → Appearance* (theme colour grey, Layout: Classic) if you want.
- **Keep Tier A:** install the Tier A installer (text, menu, About, reminders; the old look).
- **Keep Tier B or C:** install the Tier B installer (Tier C is the same file). Turn on *Frameless mode* in Settings →
  Appearance to try item 4.
- **Before any install:** export your passwords first (*⋮ → Password Manager → Settings → Export passwords*).
- **Source for one tier:** in `C:\h\leanium`, `git switch ui-zen-v2`, then:
  - **Tier A:** `git checkout 56c9224`
  - **Tier B/C:** `git checkout b3d303d`, or the branch tip, which adds only screenshots and this report
- **Drop one item:**
  1. Delete its `leanium/<patch>` line from `helium-chromium\patches\series`.
  2. Reverse it in `build\src`: `third_party\git\usr\bin\patch.exe -p1 -R -i <patch>`.
  3. Run `git revert` on its commit.
  4. Rebuild with `C:\h\ui-test\build_tier.bat <name>` (about 6 min).
- **Note:** `build\src` and `helium-windows` now contain Tier A + Tier B. Before building `main` again, reverse the
  `tierA-*`/`tierB-*` patches in `build\src`, copy `C:\h\leanium-backups\0.21.3.1\series.before-ui` over
  `helium-chromium\patches\series`, and run `git -C C:\h\helium-windows checkout -- package.py` (only that file).

## Decisions I made
- **Vertical tabs:** never considered; you want horizontal.
- **Accent variant:** Vibrant, not Tonal. In the preview, Tonal looked too close to grey, and that was the original complaint.
- **Existing profiles:** a one-time switch to the accent theme and to Compact. Without it your profile would have kept looking
  the same, as with the first experiment. A theme or layout you choose afterwards is kept.
- **Menu label:** "Password Manager", because it's already translated into every language.
- **New-tab search box:** Chromium's own box, which uses your default search engine, rather than a hard-coded site.
  Its voice/Lens buttons were removed because they rely on Google. The placeholder is English-only.

## Unverified / notes
- **[unverified]** Installing any of these installers: not done, because it writes outside the allowed folders.
- **[unverified]** Typing a search into the new-tab search box and pressing Enter (not tested; it would send a query
  to the search engine). Windows light mode, split view, maximised windows and high-DPI weren't tested.
- One early screen-region capture accidentally included another application's window. It was deleted immediately,
  never committed, and I switched to window-only capture (PrintWindow) for everything else.
- Test logins used a random dummy password. The exported CSV was deleted at once, and every test profile was deleted.
- Test tools (not in the repo): `C:\h\ui-test\zen2.py` (screenshots, tests, frameless check), `sxs.py`,
  `compare_builds.py`, `build_tier.bat`. `pip install websocket-client` was used for them.

## Follow-up: setup page logo (2026-11-17)

leanium://setup showed Helium's asterisk (logo and tab icon). Fixed in `9e12157` (rename_deps.py swaps in the cup).
New installer: `C:\h\helium-windows\build\ui-tiers\tierB2\Leanium-0.21.3.1-ui-tierB2-x64-installer.exe`, SHA-256 `a3fa7a2e67aa55fc136f6e5d5268fddc8ab1a96261429d4b36e9b4c35e78dec8`. Same as Tier B plus this fix; all 10 checks pass. Screenshots: `ui-screenshots/tierB2/`.

