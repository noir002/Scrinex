#!/usr/bin/env bash
# Rebuilds nex-portable.zip from the current source files. Run this after
# changing nex.py / pygit_core.py / server.py / scrinex/*.html, before
# committing -- the zip is a checked-in artifact, not generated at runtime,
# so it can go stale if you forget.
set -euo pipefail
cd "$(dirname "$0")"

rm -f nex-portable.zip
tmp="$(mktemp -d)"
mkdir -p "$tmp/nex-portable/scrinex"
cp nex.py pygit_core.py server.py README.md install.sh install.ps1 "$tmp/nex-portable/"
cp scrinex/landing.html scrinex/index.html "$tmp/nex-portable/scrinex/"

(cd "$tmp" && zip -rq -X nex-portable.zip nex-portable -x '*.DS_Store')
mv "$tmp/nex-portable.zip" nex-portable.zip
rm -rf "$tmp"

echo "Built nex-portable.zip ($(du -h nex-portable.zip | cut -f1))"
