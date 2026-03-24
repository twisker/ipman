@echo off
setlocal enabledelayedexpansion

if "%MOCK_CLAWHUB_STATE%"=="" set "MOCK_CLAWHUB_STATE=.mock_clawhub_state"
set "SKILLS_DIR=%MOCK_CLAWHUB_STATE%\skills"
if not exist "%SKILLS_DIR%" mkdir "%SKILLS_DIR%"

set "CMD=%~1"
shift

if "%CMD%"=="install" goto :install
if "%CMD%"=="uninstall" goto :uninstall
if "%CMD%"=="list" goto :list
echo error: unknown command: %CMD% >&2
exit /b 1

:install
set "NAME=%~1"
shift
set "FORCE=false"
set "WORKDIR="
:install_loop
if "%~1"=="" goto :install_exec
if "%~1"=="--force" (set "FORCE=true" & shift & goto :install_loop)
if "%~1"=="--hub" (shift & shift & goto :install_loop)
if "%~1"=="--workdir" (shift & set "WORKDIR=%~1" & shift & goto :install_loop)
shift
goto :install_loop
:install_exec
if "%NAME%"=="" (echo error: missing skill name >&2 & exit /b 1)
if "%WORKDIR%"=="" set "WORKDIR=%SKILLS_DIR%"
if not exist "%WORKDIR%\%NAME%" mkdir "%WORKDIR%\%NAME%"
(echo ---
echo name: %NAME%
echo version: 1.0.0
echo ---
echo Mock skill installed by mock clawhub.) > "%WORKDIR%\%NAME%\SKILL.md"
echo Installed %NAME%
exit /b 0

:uninstall
set "NAME=%~1"
shift
set "YES=false"
:uninstall_loop
if "%~1"=="" goto :uninstall_exec
if "%~1"=="--yes" (set "YES=true" & shift & goto :uninstall_loop)
shift
goto :uninstall_loop
:uninstall_exec
if "%NAME%"=="" (echo error: missing skill name >&2 & exit /b 1)
if "%YES%"=="false" (echo error: Pass --yes ^(no input^) >&2 & exit /b 1)
if exist "%SKILLS_DIR%\%NAME%" rmdir /s /q "%SKILLS_DIR%\%NAME%"
echo Uninstalled %NAME%
exit /b 0

:list
if "%~1"=="--json" (echo error: unknown flag: --json >&2 & exit /b 1)
for /d %%d in ("%SKILLS_DIR%\*") do (
    echo %%~nxd  1.0.0  enabled
)
exit /b 0
