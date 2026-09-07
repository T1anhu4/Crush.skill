#!/usr/bin/env bash
set -euo pipefail

# This is a source installer: run from a clone or extracted source archive.
if [[ -z "${BASH_SOURCE[0]:-}" || ! -f "${BASH_SOURCE[0]}" ]]; then
  echo 'Run bash scripts/install_cli.sh from a cloned or extracted Crush source tree; piping this script is unsupported.' >&2
  exit 1
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/install_cli.py" "$@"
