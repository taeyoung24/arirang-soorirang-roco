@echo off
:: CMD 창에서 한글 깨짐 방지를 위해 UTF-8 인코딩 설정
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================================
echo Syncing 'main' and Fast-Forwarding local branches...
echo ========================================================

echo.
echo [1] Checking out and updating 'main' branch...
:: 워킹 디렉토리를 main으로 변경 (uncommitted 변경사항이 있으면 여기서 멈춤)
git checkout main
if !errorlevel! neq 0 (
    echo [ERROR] Failed to checkout 'main'. Please commit or stash your changes.
    pause
    exit /b 1
)

:: main 브랜치 최신화
git pull origin main --ff-only
if !errorlevel! neq 0 (
    echo [ERROR] Failed to pull latest 'main'. Check your connection or resolve conflicts.
    pause
    exit /b 1
)

echo.
echo [2] Fast-forwarding compatible local branches...
:: 로컬에 있는 모든 브랜치를 순회
for /f "delims=" %%b in ('git for-each-ref --format="%%(refname:short)" refs/heads/') do (
    if not "%%b"=="main" (
        
        :: 해당 브랜치가 main의 조상(과거 커밋)인지 확인
        git merge-base --is-ancestor "%%b" main >nul 2>&1
        
        if !errorlevel! equ 0 (
            :: 조상이 맞다면(FF 가능), 이미 main과 완전히 똑같은 상태인지 해시값 비교
            for /f "delims=" %%c in ('git rev-parse "%%b"') do set BRANCH_HASH=%%c
            for /f "delims=" %%m in ('git rev-parse main') do set MAIN_HASH=%%m

            if "!BRANCH_HASH!"=="!MAIN_HASH!" (
                echo  - [SKIP] %%b is already up to date.
            ) else (
                echo  - [UPDATE] Fast-forwarding %%b -^> main...
                :: 브랜치를 main 커밋으로 강제 업데이트 (어차피 조상이라 FF와 완전히 동일한 안전한 동작)
                git branch -f "%%b" main >nul 2>&1

                
            )
        ) else (
            :: 브랜치에 별도의 커밋이 쌓여서 갈라진(diverged) 경우
            echo  - [IGNORE] %%b has diverged (non-fast-forward).
        )
    )
)

echo.
echo ========================================================
echo All done!
echo ========================================================
pause