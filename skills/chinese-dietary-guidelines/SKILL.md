---
name: chinese-dietary-guidelines
description: Record daily meals, summarize recent intake, and recommend 7-day meal directions using the Chinese Dietary Guidelines for Chinese Residents 2022. Use when the user asks to log food, review diet quality, compare intake against Chinese resident dietary guidance, plan meals for the next few days or week, handle pregnancy/lactation/children/older adult/vegetarian guideline profiles, or create local JSONL diet records and guideline-based recommendations.
---

# Chinese Dietary Guidelines

## Core Workflow

Use this skill for daily diet logging and guideline-based planning. It is not a medical nutrition therapy tool.

1. Establish or load the user profile from `~/.codex/data/chinese-dietary-guidelines/profile.json`.
2. Record meals into `diet_log.jsonl` with normalized food groups and gram estimates.
3. Summarize recent records before recommending changes.
4. Generate a 7-day recommendation by comparing the recent pattern against the relevant guideline profile.
5. Mention confidence limits when foods lack grams, when records are sparse, or when the user has medical conditions.

Use `scripts/diet_log.py` for deterministic storage, validation, summaries, and recommendation files. Keep private diet records outside git.

## Data Commands

Run from the skill directory or pass the script path explicitly.

```bash
python3 scripts/diet_log.py init-profile --sex female --age 35 --height-cm 165 --weight-kg 58 --life-stage adult
python3 scripts/diet_log.py add --date 2026-06-08 --meal-type lunch --food "米饭|150|g|grains" --food "菠菜|250|g|dark_vegetables" --food "鸡蛋|50|g|eggs"
python3 scripts/diet_log.py summary --days 7
python3 scripts/diet_log.py recommend --days 7 --print
python3 scripts/diet_log.py validate
```

Use `--data-dir PATH` for tests or non-default storage. The default data directory is `~/.codex/data/chinese-dietary-guidelines/`.

## References

- Read `references/guideline-rules.md` when choosing rules for adult, pregnant, lactating, preschool, school-age, older adult, or vegetarian users.
- Read `references/food-taxonomy.md` when normalizing food names, units, and groups.
- Read `references/safety-boundaries.md` when the user mentions disease, pregnancy complications, eating disorders, children, older adults, supplements, or weight-loss goals.

## Recording Rules

- Prefer explicit grams or milliliters. Estimate only when the user gives household units.
- Use canonical groups from `references/food-taxonomy.md`; do not invent new group names unless recorded as `other`.
- Mark `confidence=low` when the amount is missing or only qualitative.
- Do not store allergy, medical, or personal data in the repository.

## Recommendation Rules

- Recommend food-group adjustments first: vegetables, fruits, dairy, whole grains/legumes, tubers, animal foods, fish, soy/nuts, oil, salt, sugar, water, alcohol, and activity.
- Use the profile `life_stage` first; use vegetarian rules when `vegetarian_type` is `vegan` or `lacto_ovo` and no pregnancy/lactation/child rule overrides it.
- Preserve guideline page citations in summaries and recommendations.
- For sparse logs, say that the recommendation is based on incomplete records.
- For chronic disease, pregnancy complications, child growth concerns, frailty, dysphagia, or rapid weight change, give only guideline-level advice and suggest clinician or registered dietitian review.
