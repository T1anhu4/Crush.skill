#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Install the standalone Crush.skill CLI.

Usage:
  bash scripts/install_cli.sh [options]

Options:
  --prefix <dir>       Install root (default: ~/.crush)
  --source-dir <dir>   Repository root to install from (default: current repo)
  --force              Replace existing app directory
  --help               Show help

After install:
  ~/.crush/bin/crush

Add this to your shell profile if needed:
  export PATH="$HOME/.crush/bin:$PATH"
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PREFIX="$HOME/.crush"
SOURCE_DIR="$ROOT_DIR"
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix)
      PREFIX="$2"
      shift 2
      ;;
    --source-dir)
      SOURCE_DIR="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)"
APP_DIR="$PREFIX/app"
BIN_DIR="$PREFIX/bin"
VENV_DIR="$PREFIX/venv"

if [[ -e "$APP_DIR" ]]; then
  if [[ "$FORCE" -eq 1 ]]; then
    rm -rf "$APP_DIR"
  else
    echo "App dir already exists: $APP_DIR" >&2
    echo "Use --force to replace it." >&2
    exit 1
  fi
fi

mkdir -p "$APP_DIR" "$BIN_DIR" "$PREFIX/data"

if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude '.claude/' \
    --exclude '.learnings/' \
    --exclude 'Crush.skill/data/' \
    --exclude 'Crush.skill/dist/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    "$SOURCE_DIR"/ "$APP_DIR"/
else
  cp -R "$SOURCE_DIR"/. "$APP_DIR"/
  rm -rf "$APP_DIR/.git" "$APP_DIR/.venv" "$APP_DIR/.claude" "$APP_DIR/.learnings" "$APP_DIR/Crush.skill/data" "$APP_DIR/Crush.skill/dist"
  find "$APP_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} +
  find "$APP_DIR" -name '*.pyc' -delete
fi

PYTHON_BIN=""
python3 -m venv "$VENV_DIR"
PIP_LOG="$PREFIX/install-pip.log"
if PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_CACHE_DIR="$PREFIX/pip-cache" "$VENV_DIR/bin/python" -m pip install -q -r "$APP_DIR/requirements.txt" >"$PIP_LOG" 2>&1; then
  PYTHON_BIN="$VENV_DIR/bin/python"
else
  echo "Dependency install failed; continuing with built-in lightweight fallbacks. Log: $PIP_LOG" >&2
  PYTHON_BIN="$VENV_DIR/bin/python"
fi

cat > "$BIN_DIR/crush" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export CRUSH_HOME="${PREFIX}"
cd "${APP_DIR}"
exec "${PYTHON_BIN}" -m crush_cli "\$@"
EOF
chmod +x "$BIN_DIR/crush"

echo "Crush CLI installed."
echo "Binary: $BIN_DIR/crush"
echo "Memory: $PREFIX/data"
echo
echo "Run:"
echo "  $BIN_DIR/crush"
