@echo off
rem ===========================================================================================
rem  Leanium: update to a newer Helium release and rebuild, in one command.
rem
rem  Run it in an ADMINISTRATOR Command Prompt (the "Developer Command Prompt" also works;
rem  build.py loads the Visual Studio tools by itself):
rem
rem    update.bat              update to the newest Helium release, then rebuild (3-4 hours)
rem    update.bat 0.21.3.1     update to that Helium release, then rebuild
rem    update.bat rebuild      same Helium version, rebuild with the current scripts and logo
rem                            (reuses the prepared source when possible: faster)
rem    update.bat resume       continue a build that was interrupted (Ctrl+C, restart, crash)
rem    update.bat status       only show versions; changes nothing
rem
rem  Set LEANIUM_DRY=1 first to only PRINT the steps that change or build anything.
rem  Folders: helium-windows next to this repository (C:\h\helium-windows); set LEANIUM_HW
rem  to use another one. It always asks before deleting anything.
rem  If you edit this repository on GitHub, run "git pull" in it BEFORE starting update.bat
rem  (Windows reads a .bat file while it runs, so it must not change during a run).
rem ===========================================================================================
setlocal EnableExtensions
rem Chromium's bindgen refuses to run if a variable called TARGET exists ("saw TARGET in environment")
set "TARGET="
set "LEAN=%~dp0.."
for %%i in ("%LEAN%") do set "LEAN=%%~fi"
rem helium-windows: LEANIUM_HW if set, else the folder next to this repository (C:\h\helium-windows),
rem else the folder this repository sits in (older layout C:\h\helium-windows\leanium)
if defined LEANIUM_HW (set "HW=%LEANIUM_HW%") else (for %%i in ("%LEAN%\..\helium-windows") do set "HW=%%~fi")
if not defined LEANIUM_HW if not exist "%HW%\build.py" if exist "%LEAN%\..\build.py" for %%i in ("%LEAN%\..") do set "HW=%%~fi"
rem A time far in the future (year 2100): with it, build.py --ci skips the download/patch step
rem and its 5.5-hour limit never triggers. (The older number 1802783400 expires on 16 Feb 2027.)
set "CI=4102444800"
set "RUN="
if "%LEANIUM_DRY%"=="1" (set "RUN=echo [dry run] would run:" & echo *** DRY RUN: nothing will be changed ***)

if not exist "%HW%\build.py" (echo helium-windows not found at "%HW%". Set LEANIUM_HW to its folder. & exit /b 1)
for /f "delims=" %%p in ('py -3.12 -c "import sys,os;print(os.path.dirname(sys.executable))" 2^>nul') do set "PYDIR=%%p"
if not defined PYDIR (echo Python 3.12 not found: install it from python.org. & exit /b 1)
set "PATH=%PYDIR%;%PATH%"
set "PY=py -3.12"
if not exist "%PYDIR%\python3.exe" echo WARNING: "%PYDIR%\python3.exe" is missing; gn may fail with "Python was not found" ^(see docs\BUILDING.md^).
cd /d "%HW%" || exit /b 1

set "MODE=update"
set "NEWTAG=%~1"
if /i "%~1"=="status"  goto :status
if /i "%~1"=="resume"  goto :resume
if /i "%~1"=="rebuild" goto :rebuild
fltmc >nul 2>&1 || (echo Please run this in an ADMINISTRATOR Command Prompt. & exit /b 1)

rem ---------------------------------------------------------------- update to a new release
echo Fetching the list of Helium releases...
git fetch --tags || goto :fail
call :current
if "%NEWTAG%"=="" for /f "delims=" %%t in ('git tag --sort^=-v:refname') do if not defined NEWTAG set "NEWTAG=%%t"
git rev-parse -q --verify "refs/tags/%NEWTAG%" >nul || (echo There is no Helium release called "%NEWTAG%". & exit /b 1)
if "%CUR%"=="%NEWTAG%" (
  echo Already on Helium %CUR%, the version you asked for. Nothing to update.
  echo To rebuild anyway ^(for example after changing the logo or scripts^): update.bat rebuild
  exit /b 0
)
set "BACKUP=%LEAN%\..\backup-%CUR%-edits"
for %%i in ("%BACKUP%") do set "BACKUP=%%~fi"
echo.
echo   Current Helium:  %CUR%
echo   New Helium:      %NEWTAG%
echo.
echo This will:
echo   1. save the current Leanium changes as diff files in %BACKUP%
echo   2. reset helium-windows and switch it to %NEWTAG%
echo   3. run apply.py to make the Leanium changes again
echo   4. DELETE build\src (the old prepared Chromium source, tens of GB)
echo   5. download and prepare Chromium again, then compile it (about 3-4 hours)
echo   6. make the installer and check it for leftover "Helium" text
call :diskspace || exit /b 0
call :ask "Continue?" || exit /b 0

echo [1/6] Saving the current changes...
%RUN% mkdir "%BACKUP%" 2>nul
%RUN% git diff --binary --output="%BACKUP%\helium-windows.diff" || goto :fail
%RUN% git -C helium-chromium diff --binary --output="%BACKUP%\helium-chromium.diff" || goto :fail
echo [2/6] Switching to Helium %NEWTAG%...
%RUN% git checkout -- . || goto :fail
%RUN% git submodule foreach --recursive git checkout -- . || goto :fail
%RUN% git checkout --recurse-submodules %NEWTAG% || goto :fail
echo [3/6] Applying the Leanium changes...
%RUN% %PY% "%LEAN%\scripts\apply.py" "%HW%" --assets "%LEAN%\assets\branding" || goto :fail
call :checkhook || exit /b 1
goto :full

rem ---------------------------------------------------------------- rebuild the same version
:rebuild
fltmc >nul 2>&1 || (echo Please run this in an ADMINISTRATOR Command Prompt. & exit /b 1)
call :current
call :srcver
echo Applying the Leanium changes to Helium %CUR%...
%RUN% %PY% "%LEAN%\scripts\apply.py" "%HW%" --assets "%LEAN%\assets\branding" || goto :fail
call :checkhook || exit /b 1
if "%SRCVER%"=="%CUR%" (
  echo build\src is already prepared for Helium %CUR%: reusing it.
  %RUN% %PY% "%LEAN%\scripts\update_src.py" "%HW%" || goto :fail
  goto :compile
)
if exist build\src (
  if defined SRCVER (echo build\src was prepared for Helium %SRCVER%, not %CUR%, so it must be made again.) else (echo build\src was not completely prepared ^(interrupted?^), so it must be made again.)
  call :diskspace || exit /b 0
  call :ask "Delete build\src and prepare it again (adds about 1 hour)?" || exit /b 0
)
goto :full

rem ---------------------------------------------------------------- continue an interrupted build
:resume
fltmc >nul 2>&1 || (echo Please run this in an ADMINISTRATOR Command Prompt. & exit /b 1)
call :srcver
if not defined SRCVER (
  echo build\src is not completely prepared ^(the download/patch step was interrupted^).
  echo Run "update.bat rebuild": it deletes build\src and prepares it again.
  exit /b 1
)
call :current
if not "%SRCVER%"=="%CUR%" (
  echo build\src is prepared for Helium %SRCVER%, but helium-windows is now on %CUR%.
  echo Run "update.bat rebuild" to prepare build\src for %CUR%.
  exit /b 1
)
echo Continuing the build of Helium %SRCVER%...
rem cheap safety step: make sure the logo files and downloaded parts are renamed/copied
%RUN% %PY% "%LEAN%\scripts\update_src.py" "%HW%" --resources-only || goto :fail
goto :compile

rem ---------------------------------------------------------------- the build steps
:full
if exist build\src (
  echo [4/6] Deleting build\src, this can take several minutes...
  %RUN% rmdir /s /q build\src
  if not defined RUN if exist build\src (echo Could not delete all of build\src. Close programs using it, then run "update.bat rebuild". & goto :fail)
)
echo [5/6] Downloading, preparing and compiling Chromium. This takes hours.
echo       It is safe to stop with Ctrl+C; continue later with: update.bat resume
%RUN% %PY% build.py || goto :build_failed
goto :package

:compile
echo [5/6] Compiling. It is safe to stop with Ctrl+C; continue later with: update.bat resume
%RUN% %PY% build.py --ci %CI% || goto :build_failed

:package
echo [6/6] Making the installer...
%RUN% %PY% package.py || goto :fail
echo Checking the result for leftover "Helium" text...
if defined RUN (echo [dry run] would run: %PY% "%LEAN%\scripts\check_leftovers.py" "%HW%" & set "CHECK=0") else (%PY% "%LEAN%\scripts\check_leftovers.py" "%HW%" & call set "CHECK=%%errorlevel%%")
set "INST="
for /f "delims=" %%f in ('dir /b /o:d build\*_x64-installer.exe 2^>nul') do set "INST=%%f"
echo.
echo ================================================================================
if defined INST (echo  Done. Installer: %HW%\build\%INST%) else (echo  Done, but no installer was found in %HW%\build.)
echo  Install it "for current user only" ^(uninstall the old Leanium first if it asks^).
if not "%CHECK%"=="0" echo  NOTE: the checker found leftover "Helium" text; see the list above.
echo ================================================================================
exit /b 0

rem ---------------------------------------------------------------- status (read-only)
:status
call :current
call :srcver
set "LATEST="
for /f "delims=" %%t in ('git tag --sort^=-v:refname') do if not defined LATEST set "LATEST=%%t"
set "INST="
for /f "delims=" %%f in ('dir /b /o:d build\*_x64-installer.exe 2^>nul') do set "INST=%%f"
echo   helium-windows is on:   %CUR%
echo   Newest release known:   %LATEST%   (run "git fetch --tags" in %HW% to refresh)
if defined SRCVER (echo   build\src prepared for: %SRCVER%) else (echo   build\src prepared for: nothing ^(missing or incomplete^))
if defined INST (echo   Newest installer:       build\%INST%) else (echo   Newest installer:       none)
findstr /c:"Leanium: rename Helium in downloaded parts" build.py >nul && (echo   Leanium changes:        applied) || (echo   Leanium changes:        NOT applied ^(apply.py has not run on this version^))
exit /b 0

rem ---------------------------------------------------------------- helpers
:current
set "CUR="
for /f "delims=" %%c in ('git describe --tags 2^>nul') do set "CUR=%%c"
exit /b 0

:srcver
rem The Helium version that build\src was COMPLETELY prepared for (build.py writes it near the end
rem of preparation), or empty if build\src is missing or its preparation was interrupted.
set "SRCVER="
if not exist build\src\chrome\VERSION exit /b 0
for /f "delims=" %%v in ('%PY% "%LEAN%\scripts\check_leftovers.py" --src-version "%HW%"') do set "SRCVER=%%v"
exit /b 0

:checkhook
if defined RUN exit /b 0
findstr /c:"Leanium: rename Helium in downloaded parts" build.py >nul && exit /b 0
echo WARNING: apply.py could not add its step to build.py ^(see the WARNING above^).
echo The first-run page and uBlock Origin would still say "Helium".
call :ask "Continue anyway?"
exit /b

:diskspace
set "FREEGB="
for /f "delims=" %%g in ('%PY% -c "import shutil,sys;print(shutil.disk_usage(sys.argv[1]).free//2**30)" "%HW%"') do set "FREEGB=%%g"
if not defined FREEGB exit /b 0
if %FREEGB% GEQ 80 exit /b 0
echo WARNING: only %FREEGB% GB free on this drive; a full build needs about 80 GB.
call :ask "Continue anyway?"
exit /b

:ask
set "ANS="
set /p "ANS=%~1 [y/N] "
if /i "%ANS%"=="y" exit /b 0
if /i "%ANS%"=="yes" exit /b 0
echo Stopped. Nothing else was changed.
exit /b 1

:build_failed
echo.
echo The build stopped.
echo  - If you pressed Ctrl+C or the PC restarted: continue with   update.bat resume
echo  - If it failed with an error: scroll up to the FIRST error message ^(docs\BUILDING.md has fixes^).
exit /b 1

:fail
echo.
echo Something went wrong ^(see the message above^). Nothing after this step was run.
exit /b 1
