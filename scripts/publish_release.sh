#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Publish GitHub release with skill zip assets.

Required env:
  GITHUB_TOKEN   GitHub token with repo scope

Usage:
  bash scripts/publish_release.sh --repo <owner/name> --tag <tag> [--name <release-name>] [--notes-file <path>]

Example:
  GITHUB_TOKEN=xxx bash scripts/publish_release.sh --repo T1anhu4/Crush.skill --tag v0.1.0 --name "Crush.skill v0.1.0"
EOF
}

REPO=""
TAG=""
NAME=""
NOTES_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --name)
      NAME="$2"
      shift 2
      ;;
    --notes-file)
      NOTES_FILE="$2"
      shift 2
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

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "GITHUB_TOKEN is required" >&2
  exit 1
fi

if [[ -z "$REPO" || -z "$TAG" ]]; then
  echo "--repo and --tag are required" >&2
  usage
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="$ROOT/Crush.skill"
OPENCLAW_ZIP="$SKILL_DIR/dist/crush_skill_openclaw.zip"
QWENPAW_ZIP="$SKILL_DIR/dist/crush_skill_qwenpaw.zip"

if [[ ! -f "$OPENCLAW_ZIP" || ! -f "$QWENPAW_ZIP" ]]; then
  python3 "$ROOT/scripts/package_skill.py"
fi

if [[ -z "$NAME" ]]; then
  NAME="$TAG"
fi

BODY=""
if [[ -n "$NOTES_FILE" ]]; then
  BODY="$(cat "$NOTES_FILE")"
else
  BODY="Crush.skill release $TAG\n\nAssets:\n- crush_skill_openclaw.zip\n- crush_skill_qwenpaw.zip"
fi

TMP_JSON="$(mktemp)"
TAG="$TAG" NAME="$NAME" BODY="$BODY" python3 - <<'PY' > "$TMP_JSON"
import json, os
print(json.dumps({
    "tag_name": os.environ["TAG"],
    "name": os.environ["NAME"],
    "body": os.environ["BODY"],
    "draft": False,
    "prerelease": False,
}, ensure_ascii=False))
PY

CREATE_RESP="$(mktemp)"
HTTP_CODE=$(curl -sS -o "$CREATE_RESP" -w "%{http_code}" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -X POST "https://api.github.com/repos/$REPO/releases" \
  --data-binary @"$TMP_JSON")

if [[ "$HTTP_CODE" != "201" ]]; then
  echo "Create release failed (HTTP $HTTP_CODE):" >&2
  cat "$CREATE_RESP" >&2
  exit 1
fi

UPLOAD_URL=$(python3 - <<'PY' "$CREATE_RESP"
import json, sys
obj = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
print(obj["upload_url"].split('{')[0])
PY
)

RELEASE_URL=$(python3 - <<'PY' "$CREATE_RESP"
import json, sys
obj = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
print(obj.get("html_url", ""))
PY
)

upload_asset() {
  local file="$1"
  local name
  name="$(basename "$file")"
  local code
  code=$(curl -sS -o /tmp/release_asset_resp.json -w "%{http_code}" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -H "Content-Type: application/zip" \
    --data-binary @"$file" \
    "$UPLOAD_URL?name=$name")

  if [[ "$code" != "201" ]]; then
    echo "Upload asset failed for $name (HTTP $code):" >&2
    cat /tmp/release_asset_resp.json >&2
    exit 1
  fi
}

upload_asset "$OPENCLAW_ZIP"
upload_asset "$QWENPAW_ZIP"

echo "Release published: $RELEASE_URL"

rm -f "$TMP_JSON" "$CREATE_RESP" /tmp/release_asset_resp.json
