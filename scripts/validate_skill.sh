#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SKILL_DIR="skills/chinese-dietary-guidelines"
SKILL_FILE="$SKILL_DIR/SKILL.md"

fail() {
  echo "validate_skill: $*" >&2
  exit 1
}

test -f "$SKILL_FILE" || fail "missing $SKILL_FILE"
grep -q '^---$' "$SKILL_FILE" || fail "SKILL.md missing frontmatter delimiter"
grep -q '^name: chinese-dietary-guidelines$' "$SKILL_FILE" || fail "SKILL.md missing skill name"
grep -q '^description: ' "$SKILL_FILE" || fail "SKILL.md missing description"

required_refs=(
  references/data-schemas.md
  references/feature-workflows.md
  references/guideline-principles.md
  references/food-taxonomy.md
  references/meal-planning.md
  references/eating-out.md
  references/recipe-link-policy.md
  references/safety-boundaries.md
)

for ref in "${required_refs[@]}"; do
  test -f "$SKILL_DIR/$ref" || fail "missing $SKILL_DIR/$ref"
  grep -q "$ref" "$SKILL_FILE" || fail "SKILL.md does not reference $ref"
done

GUIDELINES="$SKILL_DIR/references/guideline-principles.md"
grep -q 'Sources: PDF' "$GUIDELINES" || fail "guideline principles missing PDF page sources"
grep -q 'Food variety.*12 food types per day.*25 per week' "$GUIDELINES" || fail "guideline principles missing food-variety anchor"
grep -q 'Vegetables.*300-500 g/day' "$GUIDELINES" || fail "guideline principles missing vegetable anchor"
grep -q 'Fruit.*200-350 g/day' "$GUIDELINES" || fail "guideline principles missing fruit anchor"
grep -q 'Dairy.*300-500 g/day' "$GUIDELINES" || fail "guideline principles missing adult dairy anchor"
grep -q 'Pregnancy' "$GUIDELINES" || fail "guideline principles missing pregnancy section"
grep -q 'Lactation' "$GUIDELINES" || fail "guideline principles missing lactation section"
grep -q 'Older Adults' "$GUIDELINES" || fail "guideline principles missing older-adult section"
grep -q 'Vegetarian Adults' "$GUIDELINES" || fail "guideline principles missing vegetarian section"

if find "$SKILL_DIR" -path '*/scripts/*' -type f | grep -q .; then
  fail "skill directory must not contain rule-engine scripts"
fi

if grep -R -n -E 'RULES|KEYWORDS|compare_against_rule|render_recommendation|diet_log\.py|summary --days|recommend --days|guideline-rules|fixed recommendation engine|hidden ranking' "$SKILL_DIR"; then
  fail "old deterministic rule-engine wording found"
fi

if grep -R -n -E 'TODO|FIXME' "$SKILL_DIR"; then
  fail "TODO/FIXME found in skill"
fi

if git ls-files | grep -E '(^|/)__pycache__/|\.pyc$|(^|/)\.codex/|diet_log\.jsonl$|profile\.json$'; then
  fail "tracked private/cache file found"
fi

if [[ "${STRICT_PUBLIC:-0}" == "1" ]]; then
  if git ls-files | grep -E '(^|/)ocr_text(_v2)?/|^qa/|^dietary_guidelines_china_2022_.*\.md$|1711104221187059\.pdf$|\.pdf$|\.png$|table_page_images|body_page_images|manual_table_crops'; then
    fail "public release contains full OCR/PDF/QA extraction artifacts"
  fi
fi

echo "validate_skill: ok"
