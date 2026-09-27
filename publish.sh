#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

"${PY:-python3}" build.py

if [ -z "$(git status --porcelain)" ]; then
    echo "nothing changed"
    exit 0
fi

git add -A
git commit -q -m "${1:-Update recipes}"
git push -q origin main
echo "published: https://perevergesboncompte-svg.github.io/recipe-book/"
