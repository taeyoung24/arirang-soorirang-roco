#!/bin/bash

echo "========================================================"
echo "Syncing 'main' and Fast-Forwarding local branches..."
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
            
            if [ "$BRANCH_HASH" == "$MAIN_HASH" ]; then
                echo "  - [SKIP] $branch is already up to date."
            else
                echo "  - [UPDATE] Fast-forwarding $branch -> main..."
                git branch -f "$branch" main >/dev/null 2>&1
            fi
        else
            echo "  - [IGNORE] $branch has diverged (non-fast-forward)."
        fi
    fi
done

echo ""
echo "========================================================"
echo "All done!"
echo "========================================================"