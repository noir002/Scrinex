#!/usr/bin/env bash
# One-shot setup: makes `nex` runnable as a bare command on this machine,
# without you having to manually chmod/ln each time on a new machine.
#
# Usage:  ./install.sh
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$DIR/nex.py"

chmod +x "$TARGET"

# Prefer /usr/local/bin; fall back to /opt/homebrew/bin (Apple Silicon default)
if [ -w "/usr/local/bin" ] || [ "$(id -u)" = "0" ]; then
  LINK_DIR="/usr/local/bin"
elif [ -d "/opt/homebrew/bin" ]; then
  LINK_DIR="/opt/homebrew/bin"
else
  LINK_DIR="/usr/local/bin"
fi

if [ -e "$LINK_DIR/nex" ]; then
  echo "Something already exists at $LINK_DIR/nex:"
  ls -la "$LINK_DIR/nex"
  echo "Remove it first if you want this installer to replace it (sudo rm $LINK_DIR/nex), then re-run."
  exit 1
fi

if [ -w "$LINK_DIR" ]; then
  ln -s "$TARGET" "$LINK_DIR/nex"
else
  sudo ln -s "$TARGET" "$LINK_DIR/nex"
fi

echo "Installed: nex -> $TARGET"
echo "Try:  nex --help"