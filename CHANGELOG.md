# Changelog

Leanium versions follow the Helium release they are built from. A rebuild of the same Helium
version gets a suffix, for example `0.21.3.1-r2`.

## 0.22.2.1

Based on Helium 0.22.2.1 (Chromium 158.0.8127.36). Newer Chromium with its security fixes.

- The About page (*⋮ → Help → About Leanium*) now says when a newer Leanium is on GitHub, with a
  link to download it. It only asks GitHub while that page is open and never downloads or installs
  anything by itself. It follows the *Allow automatic browser updates* switch in
  *Settings → Privacy and security → Leanium services*.
- The "Import from other browsers" step of the first-run setup shows the Leanium cup instead of
  Helium's icon (the last visible Helium logo).
- Includes everything from 0.21.3.1-ui-r3: the new look, the kept theme colour, and the installer
  that replaces the files of a same-version rebuild.
- Scripts: support Helium 0.22's new build layout; `update_src.py` only copies the logo files that
  changed, so a small change no longer recompiles for an hour.

## 0.21.3.1-ui-r3

Based on Helium 0.21.3.1 (Chromium 157.0.8103.78). Installer fix for 0.21.3.1-ui-r2.

- Installing over an earlier build of the same version now really replaces the browser files.
  Before, the installer kept the old files when their sizes matched, so installing 0.21.3.1-ui-r2
  over 0.21.3.1-ui changed nothing and the theme fix never arrived.
- Includes the theme fix from 0.21.3.1-ui-r2 (the chosen colour is kept after a restart).

## 0.21.3.1-ui-r2

Based on Helium 0.21.3.1 (Chromium 157.0.8103.78). Bug fix for 0.21.3.1-ui.

- The colour you pick in *Customize Leanium* is kept after closing and reopening the browser.
  Before, the grey colour was replaced by the purple accent at every start.

## 0.21.3.1-ui

Based on Helium 0.21.3.1 (Chromium 157.0.8103.78). Same browser as 0.21.3.1 with a new look.

- One top bar: tabs and address bar in a single row (Helium's compact layout, now the default).
- Pill-shaped tabs without separator lines; the page floats as a rounded card.
- Purple accent from the cup logo for tabs, toggles, buttons and the frame.
- New-tab page with the cup logo, a search box (your default search engine) and a soft gradient.
- First-run setup page uses the cup logo and Leanium colours.
- *Password Manager* in the main menu, a "passwords are local only" reminder in password settings,
  and "Leanium, based on Helium" on the About page.
- uBlock Origin's lists are named "Helium filters (via Leanium)".
- Existing profiles that still use the grey default switch once to the new theme and layout; both
  can be changed back in *Settings → Appearance*.

## 0.21.3.1

Based on Helium 0.21.3.1 (Chromium 157.0.8103.78). First release with a downloadable installer.

- *Autofill and passwords* is back in Settings. Helium hides it, so saved passwords were only
  reachable by typing `leanium://password-manager/passwords`.
- Internal pages now use `leanium://` instead of `helium://`.
- New logo: a larger cup with a sparkle, and a matching new-tab icon.
- The first-run setup page and uBlock Origin's labels now say Leanium.
- The setup page no longer claims there is no built-in password manager.
- Fixed "Helium" still showing in the Korean, Amharic, Telugu, Gujarati and Odia translations.

## 0.21.1.1

Based on Helium 0.21.1.1 (Chromium 157.0.8103.38). Build-it-yourself only.

- Chromium's built-in password manager enabled, with saving on by default.
- Renamed to Leanium with its own logo, install IDs and profile, so it installs next to Helium.
