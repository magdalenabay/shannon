#!/usr/bin/env sh
# shannon installer (macOS / Linux)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/magdalenabay/shannon/main/install.sh | sh
#
# Environment:
#   SHANNON_REPO   Override the repo URL (default: https://github.com/magdalenabay/shannon)
#   SHANNON_REF    Git ref to install (default: main)

set -e

REPO="${SHANNON_REPO:-https://github.com/magdalenabay/shannon}"
REF="${SHANNON_REF:-main}"

say() { printf '%s\n' "$*"; }
err() { printf 'error: %s\n' "$*" >&2; exit 1; }

if ! command -v uv >/dev/null 2>&1; then
    say "-> uv not found; installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # uv installs to ~/.local/bin on Linux/macOS by default
    PATH="$HOME/.local/bin:$PATH"
    export PATH
    if ! command -v uv >/dev/null 2>&1; then
        err "uv install completed but 'uv' is still not on PATH. Open a new shell and re-run."
    fi
fi

say "-> installing shannon from $REPO@$REF..."
uv tool install --force "git+$REPO@$REF"

cat <<EOF

shannon installed.

Try:
  shannon --doctor          # see what's installed
  shannon --install-all     # install light backends (ffmpeg, magick, pandoc, ...)
  shannon ~/file.mp4 mp3    # do a conversion
EOF
