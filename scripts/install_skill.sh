#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Install Crush.skill into Claude Code / OpenClaw / QwenPaw skill directories.

Usage:
  bash scripts/install_skill.sh --platform <claude|openclaw|qwenpaw> [options]

Options:
  --platform <name>        Target platform: claude | openclaw | qwenpaw
  --repo-url <url>         Clone repo from GitHub first, then install from it
  --source-dir <path>      Source skill directory (must contain SKILL.md)
  --skill-name <name>      Destination folder name (default: crush-skill)
  --target-dir <path>      Explicit skill root directory override
  --mode <copy|symlink>    Install mode (default: copy)
  --force                  Replace existing installed skill directory
  --help                   Show this help

Env overrides:
  OPENCLAW_SKILLS_DIR      OpenClaw skill root override
  QWENPAW_SKILLS_DIR       QwenPaw skill root override

Examples:
  bash scripts/install_skill.sh --platform claude
  bash scripts/install_skill.sh --platform openclaw --repo-url https://github.com/<you>/<repo>.git --force
  bash scripts/install_skill.sh --platform qwenpaw --target-dir /app/working/workspaces/default/skills
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PLATFORM=""
REPO_URL=""
SOURCE_DIR=""
TARGET_DIR=""
SKILL_NAME="crush-skill"
MODE="copy"
FORCE=0
TMP_DIR=""

cleanup() {
  if [[ -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform)
      PLATFORM="$2"
      shift 2
      ;;
    --repo-url)
      REPO_URL="$2"
      shift 2
      ;;
    --source-dir)
      SOURCE_DIR="$2"
      shift 2
      ;;
    --target-dir)
      TARGET_DIR="$2"
      shift 2
      ;;
    --skill-name)
      SKILL_NAME="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
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

if [[ -z "$PLATFORM" ]]; then
  echo "--platform is required" >&2
  usage
  exit 1
fi

if [[ "$MODE" != "copy" && "$MODE" != "symlink" ]]; then
  echo "--mode must be copy or symlink" >&2
  exit 1
fi

resolve_repo_source() {
  local repo_root="$1"

  if [[ -n "$SOURCE_DIR" ]]; then
    printf '%s\n' "$SOURCE_DIR"
    return
  fi

  if [[ -d "$repo_root/Crush.skill" && -f "$repo_root/Crush.skill/SKILL.md" ]]; then
    printf '%s\n' "$repo_root/Crush.skill"
    return
  fi

  if [[ -f "$repo_root/SKILL.md" ]]; then
    printf '%s\n' "$repo_root"
    return
  fi

  local first
  first="$(find "$repo_root" -maxdepth 2 -type f -name 'SKILL.md' | head -n 1 || true)"
  if [[ -n "$first" ]]; then
    printf '%s\n' "$(dirname "$first")"
    return
  fi

  echo "" >&2
  return 1
}

if [[ -n "$REPO_URL" ]]; then
  command -v git >/dev/null 2>&1 || {
    echo "git is required when --repo-url is provided" >&2
    exit 1
  }
  TMP_DIR="$(mktemp -d)"
  git clone --depth 1 "$REPO_URL" "$TMP_DIR/repo"
  SOURCE_DIR="$(resolve_repo_source "$TMP_DIR/repo")"
elif [[ -z "$SOURCE_DIR" ]]; then
  SOURCE_DIR="$ROOT_DIR/Crush.skill"
fi

SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)"
if [[ ! -f "$SOURCE_DIR/SKILL.md" ]]; then
  echo "Invalid source dir: $SOURCE_DIR (SKILL.md not found)" >&2
  exit 1
fi

resolve_target_root() {
  local p="$1"
  case "$p" in
    claude)
      printf '%s\n' "$HOME/.claude/skills"
      ;;
    openclaw)
      if [[ -n "${OPENCLAW_SKILLS_DIR:-}" ]]; then
        printf '%s\n' "$OPENCLAW_SKILLS_DIR"
      elif [[ -d "$HOME/.openclaw/workspace/skills" ]]; then
        printf '%s\n' "$HOME/.openclaw/workspace/skills"
      else
        printf '%s\n' "$HOME/.openclaw/skills"
      fi
      ;;
    qwenpaw)
      if [[ -n "${QWENPAW_SKILLS_DIR:-}" ]]; then
        printf '%s\n' "$QWENPAW_SKILLS_DIR"
      elif [[ -d "/app/working/workspaces/default/skills" ]]; then
        printf '%s\n' "/app/working/workspaces/default/skills"
      elif [[ -d "$HOME/.qwen/skills" ]]; then
        printf '%s\n' "$HOME/.qwen/skills"
      else
        printf '%s\n' "$HOME/.qwen/skills"
      fi
      ;;
    *)
      echo "Unsupported platform: $p" >&2
      exit 1
      ;;
  esac
}

if [[ -z "$TARGET_DIR" ]]; then
  TARGET_DIR="$(resolve_target_root "$PLATFORM")"
fi

mkdir -p "$TARGET_DIR"
DEST_DIR="$TARGET_DIR/$SKILL_NAME"

if [[ -e "$DEST_DIR" ]]; then
  if [[ "$FORCE" -eq 1 ]]; then
    BACKUP_DIR="$DEST_DIR.bak.$(date +%Y%m%d%H%M%S)"
    mv "$DEST_DIR" "$BACKUP_DIR"
    echo "Existing install moved to: $BACKUP_DIR"
  else
    echo "Destination already exists: $DEST_DIR" >&2
    echo "Use --force to replace" >&2
    exit 1
  fi
fi

if [[ "$MODE" == "symlink" ]]; then
  ln -s "$SOURCE_DIR" "$DEST_DIR"
else
  if command -v rsync >/dev/null 2>&1; then
    mkdir -p "$DEST_DIR"
    rsync -a \
      --exclude '__pycache__/' \
      --exclude 'data/' \
      --exclude 'dist/' \
      --exclude 'examples/' \
      --exclude '*.pyc' \
      "$SOURCE_DIR"/ "$DEST_DIR"/
  else
    cp -R "$SOURCE_DIR" "$DEST_DIR"
    rm -rf "$DEST_DIR/__pycache__" "$DEST_DIR/data" "$DEST_DIR/dist" "$DEST_DIR/examples"
    find "$DEST_DIR" -name '*.pyc' -delete
  fi
fi

verify() {
  local dir="$1"
  [[ -f "$dir/SKILL.md" ]] || return 1
  [[ -f "$dir/manifest.json" ]] || return 1
  [[ -f "$dir/execute.py" ]] || return 1
  [[ -d "$dir/engines" ]] || return 1
  return 0
}

if ! verify "$DEST_DIR"; then
  echo "Install verification failed at: $DEST_DIR" >&2
  exit 1
fi

echo "Installed successfully"
echo "Platform: $PLATFORM"
echo "Skill dir: $DEST_DIR"
echo "Verification: SKILL.md, manifest.json, execute.py, engines/"
