# Building Leanium (Windows x64)

Expect 3–6 hours for the first build on a modern 8+ core CPU, and about **60 GB** of free disk space.
16 GB of RAM works; make sure the page file is large (≈ 32 GB total) because linking is memory hungry.

## 1. Install the prerequisites

- **Git**
- **Python 3.12** (python.org installer; tick *Add to PATH*)
- **7-Zip**
- **Visual Studio 2022 Community** with the *Desktop development with C++* workload, plus the
  individual components *C++ MFC for latest v143 build tools* and *C++ ATL for latest v143 build tools*
- **Windows SDK 10.0.28000** (Chromium 157 requires exactly this one; it is *not* offered by the
  Visual Studio installer): `winget install Microsoft.WindowsSDK.10.0.28000`, and make sure
  *Debugging Tools for Windows* is included
- Python packages: `py -3.12 -m pip install httplib2==0.22.0 Pillow`
- **Long paths enabled** in Windows (and a reboot afterwards)
- (Optional) an antivirus exclusion for the build folder; it makes the build noticeably faster

Windows ships a Microsoft-Store shortcut called `python3.exe` that shadows the real Python and breaks
Chromium's `gn`. Turn off *python.exe* and *python3.exe* under *Settings → Apps → Advanced app settings →
App execution aliases*, then run this once so a real `python3.exe` exists:

```bat
copy "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%LOCALAPPDATA%\Programs\Python\Python312\python3.exe"
```

## 2. Get the sources

In an **administrator** *Developer Command Prompt for VS 2022*:

```bat
mkdir C:\h && cd /d C:\h
git clone --recurse-submodules https://github.com/imputnet/helium-windows.git
cd helium-windows
git checkout --recurse-submodules 0.21.1.1
git clone https://github.com/YOUR-USERNAME/leanium.git leanium
```

Use a **short path** such as `C:\h`, not a deep folder: Chromium has very long file names.

## 3. Apply Leanium

```bat
set PATH=%LOCALAPPDATA%\Programs\Python\Python312;%PATH%
py -3.12 leanium\scripts\apply.py . --assets leanium\assets\branding
```

It prints the list of files it changed. It is safe to run more than once.

## 4. Build and package

```bat
py -3.12 build.py
py -3.12 package.py
```

`build.py` downloads Chromium (~30 GB), applies the patches and compiles. If you stop it with Ctrl+C
you can resume; once the source is prepared, resume with `py -3.12 build.py --ci 1802783400` (the
number only disables a time limit that `--ci` otherwise imposes) instead of preparing everything again.

The installer is written to `build\helium_<version>_x64-installer.exe`; the name still says
"helium" but the program inside is Leanium. Install it **for the current user only**.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Python was not found` during `gn gen` | Disable the App execution aliases and create `python3.exe` (step 1). |
| `.../include/10.0.28000.0/um does not exist` | Install Windows SDK 10.0.28000 (step 1). |
| `Access is denied` while unpacking `chromium-…` | `apply.py` contains the fix; delete `build\src` and run `build.py` again. |
| `invalid digit 'f' in decimal constant` in `vector_icons.cc` | Re-run `scripts/make_assets.py` and `apply.py`, then rebuild (whole numbers in `.icon` files must not end in `f`). |
| Out-of-memory or freezes while linking | Enlarge the page file; try `build.py -j 10`. |
