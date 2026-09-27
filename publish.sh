#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

"${PY:-python3}" build.py

if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -q -m "${1:-Update recipes}"
elif git diff --quiet HEAD origin/main 2>/dev/null; then
    echo "nothing changed"
    exit 0
fi

git push -q origin main
echo "published: https://perevergesboncompte-svg.github.io/recipe-book/"
