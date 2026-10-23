#!/usr/bin/env bash
# Structural checks for the bundled skills.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for skill in python-dev python-refactor; do
  grep -Fx "name: $skill" "$ROOT/skills/$skill/SKILL.md"
  grep -q '^description: .' "$ROOT/skills/$skill/SKILL.md"
done

# Every python-dev reference is routed from SKILL.md, exists, and ends in a checklist.
DEV="$ROOT/skills/python-dev"
linked="$(grep -o '(references/[a-z-]*\.md)' "$DEV/SKILL.md" | tr -d '()' | sort -u)"
present="$(cd "$DEV" && ls references/*.md | sort)"
[ "$linked" = "$present" ]
for ref in $present; do
  grep -q '^## Checklist$' "$DEV/$ref"
done

# Keep the core cheap to load; code examples live only in the patterns and project-setup references.
[ "$(wc -w < "$DEV/SKILL.md")" -le 1750 ]
[ "$(wc -w < "$ROOT/skills/python-refactor/SKILL.md")" -le 800 ]
! grep -n '^```' "$DEV/SKILL.md" "$ROOT/skills/python-refactor/SKILL.md" \
  $(ls "$DEV"/references/*.md | grep -v -e '/patterns.md$' -e '/project-setup.md$')
grep -Fq 'abc.ABC with @abstractmethod' "$DEV/SKILL.md"

# Manifests parse and point at the skills directory.
node -e 'const p=require(process.argv[1]); if (p.pi.skills[0] !== "./skills") process.exit(1)' "$ROOT/package.json"
node -e 'JSON.parse(require("fs").readFileSync(process.argv[1]))' "$ROOT/.claude-plugin/plugin.json"
node -e 'JSON.parse(require("fs").readFileSync(process.argv[1]))' "$ROOT/.claude-plugin/marketplace.json"
printf 'skill structure checks passed.\n'
