@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ---------------------------------------------------------
:: 파라미터 파싱 (Push 옵션 확인)
:: ---------------------------------------------------------
set "DO_PUSH=0"
for %%A in (%*) do (
    if /I "%%A"=="--push" set "DO_PUSH=1"
    if /I "%%A"=="-p" set "DO_PUSH=1"
)

echo ========================================================
echo Syncing 'main' and Fast-Forwarding local branches...
if "!DO_PUSH!"=="1" echo [PUSH OPTION ENABLED] Updated branches will be pushed to origin.
echo ========================================================

echo.
echo [1] Checking out and updating 'main' branch...
git checkout main
if %errorlevel% neq 0 (
    echo [ERROR] Failed to checkout 'main'. Please commit or stash your changes.
    pause
    exit /b 1
)

git pull origin main --ff-only
if %errorlevel% neq 0 (
    echo [ERROR] Failed to pull latest 'main'. Check your connection or resolve conflicts.
    pause
    exit /b 1
)

echo.
echo [2] Fast-forwarding compatible local branches...
for /f "delims=" %%b in ('git for-each-ref --format="%%(refname:short)" refs/heads/') do (
    if not "%%b"=="main" (
        call :process_branch "%%b"
    )
)

echo.
echo ========================================================
echo All done!
echo ========================================================
pause
exit /b 0

:: ---------------------------------------------------------
:: 개별 브랜치 처리 함수
:: ---------------------------------------------------------
:process_branch
set "BRANCH=%~1"

:: 조상(과거 커밋)인지 확인
git merge-base --is-ancestor "%BRANCH%" main >nul 2>&1
if !errorlevel! neq 0 (
    echo  - [IGNORE] %BRANCH% has diverged [non-fast-forward].
    exit /b 0
)

:: 해시값 추출
for /f "delims=" %%c in ('git rev-parse "%BRANCH%"') do set "BRANCH_HASH=%%c"
for /f "delims=" %%m in ('git rev-parse main') do set "MAIN_HASH=%%m"

:: 해시값 비교 (업데이트가 필요한가?)
if "!BRANCH_HASH!"=="!MAIN_HASH!" (
    echo  - [LOCAL SYNCED] %BRANCH% is already up to date locally.
) else (
    echo  - [UPDATE] Fast-forwarding %BRANCH% -^> main...
    git branch -f "%BRANCH%" main >nul 2>&1
)

:: Push 옵션이 켜져 있을 경우 Push 실행 (로컬이 최신이므로 무조건 시도)
if "!DO_PUSH!"=="1" (
    echo    -^> [PUSH] Syncing %BRANCH% to origin...
    git push origin "%BRANCH%" >nul 2>&1
    if !errorlevel! neq 0 (
        echo    -^> [ERROR] Failed to push %BRANCH%.
    )
)
exit /b 0