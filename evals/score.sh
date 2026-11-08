#!/usr/bin/env bash
# Scorecard for Python code an agent produced. One column per project, so runs compare side by side.
#   evals/score.sh <project-dir> [<project-dir>...] [--fast]
# --fast skips ruff and mypy.
set -euo pipefail

fast=0
dirs=()
for arg in "$@"; do
  case "$arg" in
    --fast) fast=1 ;;
    -h|--help) sed -n '2,4s/^# \{0,1\}//p' "$0"; exit 0 ;;
    *) [ -d "$arg" ] || { echo "not a directory: $arg" >&2; exit 2; }; dirs+=("$arg") ;;
  esac
done
[ "${#dirs[@]}" -gt 0 ] || { sed -n '2,4s/^# \{0,1\}//p' "$0" >&2; exit 2; }

if [ -t 1 ]; then
  bold=$'\e[1m' dim=$'\e[2m' red=$'\e[31m' yellow=$'\e[33m' green=$'\e[32m' reset=$'\e[0m'
else
  bold='' dim='' red='' yellow='' green='' reset=''
fi

tool() {  # prefer an installed tool, fall back to uvx
  if command -v "$1" >/dev/null; then echo "$1"
  elif command -v uvx >/dev/null; then echo "uvx $1"
  fi
}
RUFF="$(tool ruff)"
MYPY="$(tool mypy)"
# The lint set python-dev recommends, applied with --isolated so every project is judged the same way.
RUFF_RULES="E,F,I,UP,B,BLE,S110,FBT,ERA,ASYNC,C901"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# metric key | label | good when (low|high|info) | yellow above | red above
METRICS=(
  "files|python files|info"
  "loc|lines of code|info"
  "funcs|functions|info"
  "private_pct|_private functions %|low|15|30"
  "short|1-2 letter function names|low|0|3"
  "dict_any|dict[str, Any]|low|0|5"
  "broad|broad except|low|0|3"
  "future|from __future__ annotations|low|0|0"
  "abc|ABC interfaces|high"
  "protocol|Protocol classes|low|0|2"
  "enum|enums|high"
  "tests|test functions|high"
  "ruff|ruff findings|low|0|10"
  "mypy|mypy --strict errors|low|0|10"
)

declare -A score

count() {  # count matching lines across the project's python files
  { xargs -0 -r grep -hE -- "$1" < "$2" 2>/dev/null || true; } | wc -l | tr -d ' '  # no match is a count of 0
}

for i in "${!dirs[@]}"; do
  dir="${dirs[$i]}"
  list="$tmp/files.$i"
  if git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then  # tracked and new files, not ignored ones
    (cd "$dir" && git ls-files -z --cached --others --exclude-standard -- '*.py' \
      | while IFS= read -r -d '' f; do [ -f "$f" ] && printf '%s\0' "$PWD/$f"; done) > "$list"
  else
    find "$dir" -name '*.py' -not -path '*/.venv/*' -not -path '*/venv/*' -not -path '*/site-packages/*' \
      -not -path '*/node_modules/*' -not -path '*/build/*' -not -path '*/dist/*' -print0 > "$list"
  fi

  files="$(tr -cd '\0' < "$list" | wc -c | tr -d ' ')"
  funcs="$(count '^\s*(async\s+)?def ' "$list")"
  private="$(count '^\s*(async\s+)?def _[a-zA-Z]' "$list")"
  score[$i,files]="$files"
  score[$i,loc]="$(count '\S' "$list")"
  score[$i,funcs]="$funcs"
  score[$i,private_pct]="$(( funcs ? private * 100 / funcs : 0 ))"
  score[$i,short]="$(count '^\s*(async\s+)?def _*[a-zA-Z][a-zA-Z0-9]?\(' "$list")"
  score[$i,dict_any]="$(count 'dict\[str, *Any\]' "$list")"
  score[$i,broad]="$(count '^\s*except(\s+(Base)?Exception)?\s*(as \w+)?:' "$list")"
  score[$i,future]="$(count '^from __future__ import annotations' "$list")"
  score[$i,abc]="$(count '^\s*class \w+\((.*\bABC\b|.*metaclass=ABCMeta)' "$list")"
  score[$i,protocol]="$(count '^\s*class \w+\(.*\bProtocol\b' "$list")"
  score[$i,enum]="$(count '^\s*class \w+\(.*\b(Str|Int)?Enum\b' "$list")"
  score[$i,tests]="$(count '^\s*(async\s+)?def test_' "$list")"

  if [ "$fast" -eq 1 ] || [ "$files" -eq 0 ]; then
    score[$i,ruff]="-"; score[$i,mypy]="-"
  else
    [ -t 2 ] && printf '%s' "${dim}checking ${dir}...${reset}" >&2
    score[$i,ruff]="$( [ -n "$RUFF" ] && xargs -0 $RUFF check --isolated --select "$RUFF_RULES" \
      --output-format concise --quiet < "$list" 2>/dev/null | grep -c ':[0-9]*:[0-9]*:' || true)"
    score[$i,mypy]="$( [ -n "$MYPY" ] && xargs -0 $MYPY --strict --ignore-missing-imports \
      --no-error-summary < "$list" 2>/dev/null | grep -c ': error:' || true)"
    [ -t 2 ] && printf '\r\e[K' >&2
  fi
done

color_for() {  # value, good-direction, yellow-above, red-above
  local value="$1" want="$2"
  if [ "$value" = "-" ] || [ "$want" = info ]; then return; fi
  if [ "$want" = high ]; then
    [ "$value" -gt 0 ] && printf '%s' "$green" || printf '%s' "$yellow"
  elif [ "$value" -gt "$4" ]; then printf '%s' "$red"
  elif [ "$value" -gt "$3" ]; then printf '%s' "$yellow"
  else printf '%s' "$green"
  fi
}

width=16
printf '\n%s\n\n' "${bold}python-dev scorecard${reset}"
printf '  %-30s%s' "" "$bold"
for dir in "${dirs[@]}"; do
  name="$(basename "$(cd "$dir" && pwd)")"
  printf "%${width}s" "${name:0:$((width - 1))}"
done
printf '%s\n' "$reset"

for metric in "${METRICS[@]}"; do
  IFS='|' read -r key label want yellow_above red_above <<< "$metric"
  printf '  %-30s' "$label"
  for i in "${!dirs[@]}"; do
    value="${score[$i,$key]}"
    printf "%s%${width}s%s" "$(color_for "$value" "$want" "${yellow_above:-0}" "${red_above:-0}")" "$value" "$reset"
  done
  printf '\n'
done

printf '\n  %s\n' "${dim}green good, yellow look, red fix. ABCs, enums, tests: more is better. Static only: run pytest and docker compose yourself.${reset}"
[ "$fast" -eq 1 ] || [ -n "$RUFF$MYPY" ] || printf '  %s\n' "${yellow}ruff and mypy not found (install them or uv)${reset}"
printf '\n'
