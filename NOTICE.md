# Notices

Leanium is a modified build of other people's work. This repository contains Leanium's own scripts,
patches and artwork; it does not contain the browser source code or binaries.

| Project | What Leanium uses | Licence | Licence text |
| --- | --- | --- | --- |
| [Helium for Windows](https://github.com/imputnet/helium-windows) (The Helium Authors) | Build recipe that `scripts/apply.py` edits | GPL-3.0 | [`licenses/helium-windows/LICENSE`](licenses/helium-windows/LICENSE) |
| [Helium](https://github.com/imputnet/helium) patch set (The Helium Authors) | Patches that Leanium's patches are made on top of | GPL-3.0 | [`licenses/helium-chromium/LICENSE`](licenses/helium-chromium/LICENSE) |
| [ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium) (The ungoogled-chromium Authors) | Parts of Helium's build system and patches | BSD 3-Clause | [`licenses/helium-windows/LICENSE.ungoogled_chromium`](licenses/helium-windows/LICENSE.ungoogled_chromium), [`licenses/helium-chromium/LICENSE.ungoogled_chromium`](licenses/helium-chromium/LICENSE.ungoogled_chromium) |
| [Chromium](https://www.chromium.org/) (The Chromium Authors) | The browser; patch context lines quote Chromium code | BSD 3-Clause (plus the licences of its third-party parts, listed in the browser at `leanium://credits`) | [`licenses/chromium/LICENSE`](licenses/chromium/LICENSE) |

The licence files above are unmodified copies from Helium for Windows 0.21.3.1 and its Chromium source.

**Leanium's own changes** (the scripts in `scripts/`, the patches in `patches/`, the logo in `assets/`)
are licensed under GPL-3.0 ([`LICENSE`](LICENSE)), like Helium. The patches in `patches/` modify files
of Helium and Chromium. Each patch and each commit says what it changes and when.

**Binaries.** Installers on the [Releases page](https://github.com/ezph4ntom/Leanium/releases) are built
from the Helium version and the commit of this repository named in each release's notes. The complete
corresponding source is that Helium release (linked in the notes) plus this repository at that commit.

"Helium", "Chromium" and "Google" are trademarks of their respective owners and are used only to
describe what Leanium is based on. Leanium is not affiliated with or endorsed by them.
