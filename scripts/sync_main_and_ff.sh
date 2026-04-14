#!/bin/bash

# ---------------------------------------------------------
# 파라미터 파싱 (Push 옵션 확인)
# ---------------------------------------------------------
DO_PUSH=0
for arg in "$@"; do
    if [ "$arg" == "--push" ] || [ "$arg" == "-p" ]; then
        DO_PUSH=1
    fi
done

echo "========================================================"
echo "Syncing 'main' and Fast-Forwarding local branches..."
if [ "$DO_PUSH" -eq 1 ]; then
    echo "[PUSH OPTION ENABLED] Updated branches will be pushed to origin."
fi
echo "========================================================"
echo ""

echo "[1] Checking out and updating 'main' branch..."
if ! git checkout main; then
    echo "[ERROR] Failed to checkout 'main'. Please commit or stash your changes."
    exit 1
fi

if ! git pull origin main --ff-only; then
    echo "[ERROR] Failed to pull latest 'main'. Check your connection or resolve conflicts."
    exit 1
fi

echo ""
echo "[2] Fast-forwarding compatible local branches..."

# 로컬 브랜치 목록 순회
for branch in $(git for-each-ref --format="%(refname:short)" refs/heads/); do
    if [ "$branch" != "main" ]; then
        
        # main의 조상(과거 커밋)인지 확인
        if git merge-base --is-ancestor "$branch" main >/dev/null 2>&1; then
            BRANCH_HASH=$(git rev-parse "$branch")
            MAIN_HASH=$(git rev-parse main)
            
            # 해시값 비교 (업데이트가 필요한가?)
            if [ "$BRANCH_HASH" == "$MAIN_HASH" ]; then
                echo "  - [LOCAL SYNCED] $branch is already up to date locally."
            else
                echo "  - [UPDATE] Fast-forwarding $branch -> main..."
                git branch -f "$branch" main >/dev/null 2>&1
            fi
            
            # Push 옵션이 켜져 있을 경우 Push 실행 (로컬이 최신이므로 무조건 시도)
            if [ "$DO_PUSH" -eq 1 ]; then
                echo "    -> [PUSH] Syncing $branch to origin..."
                if ! git push origin "$branch" >/dev/null 2>&1; then
                    echo "    -> [ERROR] Failed to push $branch."
                fi
            fi
        else
            echo "  - [IGNORE] $branch has diverged [non-fast-forward]."
        fi
    fi
done

echo ""
echo "========================================================"
echo "All done!"
echo "========================================================"