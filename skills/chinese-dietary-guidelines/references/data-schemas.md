# Data Schemas

These schemas define the local data format for agent-managed records. They are not an API contract for a calculation engine. Preserve existing fields for backward compatibility and add new fields when they improve traceability.

Default local data directory:

`~/.codex/data/chinese-dietary-guidelines/`

## profile.json

```json
{
  "schema_version": 2,
  "sex": "female",
  "age": 35,
  "height_cm": 165,
  "weight_kg": 58,
  "activity_level": "low",
  "life_stage": "adult",
  "vegetarian_type": "none",
  "allergies": [],
  "avoid_foods": [],
  "chronic_condition_notes": "",
  "goals": ["improve dietary balance"],
  "updated_at": "2026-06-08T10:00:00"
}
```

Allowed values:

- `sex`: `male`, `female`, `other`, or unknown if not provided.
- `activity_level`: `low`, `medium`, `high`, or unknown.
- `life_stage`: `adult`, `pregnant_early`, `pregnant_mid`, `pregnant_late`, `lactating`, `preschool_2_3`, `preschool_4_5`, `school_age`, `older_adult`, `very_old`.
- `vegetarian_type`: `none`, `vegan`, `lacto_ovo`, or unknown.

If a profile is missing, ask only for details needed for the current task and label analysis provisional.

## diet_log.jsonl

Append one JSON object per line.

```json
{
  "schema_version": 2,
  "id": "2026-06-08-breakfast-001",
  "date": "2026-06-08",
  "meal_type": "breakfast",
  "foods": [
    {
      "name": "牛奶",
      "amount_text": "1杯",
      "estimated_grams": 250,
      "group": "dairy",
      "subgroup": "milk",
      "preparation": "plain",
      "confidence": "medium",
      "evidence_note": "User reported one cup; estimated as about 250 ml."
    }
  ],
  "water_ml": null,
  "alcohol_g": 0,
  "oil_g": null,
  "salt_g": null,
  "added_sugar_g": null,
  "activity_steps": null,
  "notes": "",
  "created_at": "2026-06-08T10:00:00"
}
```

Guidance:

- `meal_type`: `breakfast`, `lunch`, `dinner`, `snack`, `day`, or `other`.
- `confidence`: `high` for explicit weighed/package values, `medium` for common household estimates, `low` for vague quantities.
- Use `null` instead of inventing values when a field is unknown.
- Keep `evidence_note` short and factual.

## analysis_summary

Use this internal structure when presenting analysis to the user. It does not need to be saved unless the user asks.

```json
{
  "period": {"start": "2026-06-01", "end": "2026-06-08", "recorded_days": 5},
  "data_quality": {
    "missing_meals": "some dinners missing",
    "estimated_portion_share": "high",
    "major_unknowns": ["oil", "salt"]
  },
  "observations": [
    {"topic": "vegetables", "evidence": "few vegetable entries", "confidence": "medium"},
    {"topic": "dairy", "evidence": "milk logged on 2 of 5 days", "confidence": "medium"}
  ],
  "relative_calculations": [
    {
      "topic": "dairy",
      "observed": "milk logged on 2 of 5 recorded days",
      "reference_anchor": "adult dairy 300-500 g/day",
      "relative_position": "frequency appears low against a daily dairy anchor",
      "calculation_note": "Portion totals are not reliable because several records lack grams.",
      "confidence": "medium"
    }
  ],
  "principle_comparison": [
    {"principle": "adult dairy 300-500 g/day", "source": "PDF 003, 153", "interpretation": "likely low"}
  ]
}
```

Relative calculations should be included whenever the records support them. Useful forms include:

- `observed / reference_anchor`, expressed as a rough percentage or range when both sides have comparable units
- `days_with_item / recorded_days`, expressed as frequency rather than a medical conclusion
- `current_period / previous_period`, used only when the prior period has comparable data quality
- `low_confidence_entries / relevant_entries`, used to explain uncertainty
- `recommended_delta`, such as adding about one serving, one dish, or one more day per week relative to the current pattern

## recommendation.md

Use this section order for generated recommendation files:

1. `# 7-Day Dietary Recommendation`
2. `## Profile And Context`
3. `## Recent Record Overview`
4. `## Main Observations`
5. `## Relative Calculations`
6. `## Guideline-Principle Comparison`
7. `## 7-Day Meal Plan`
8. `## Daily Ingredient Totals`
9. `## Recipe Tutorial Links`
10. `## Shopping List`
11. `## Prep Schedule`
12. `## Uncertainty And Safety Boundaries`
13. `## Sources`

The `## Relative Calculations` section should show the arithmetic that shaped the recommendation, for example:

```markdown
| Topic | Recent pattern | Guideline anchor | Relative reading | Planning delta |
|---|---|---|---|---|
| Dairy | Logged on 2/7 days; portions partly unknown | Adult dairy 300-500 g/day | Frequency is well below a daily anchor; gram comparison is low confidence | Add unsweetened milk/yogurt on 4-5 more days next week |
| Vegetables | Estimated about 180 g/day across recorded meals | Adult vegetables 300-500 g/day | About 60% of the lower anchor, medium confidence | Add one cooked vegetable dish at lunch or dinner most days |
```

The `## 7-Day Meal Plan` section must use this table shape:

```markdown
| Day | Meal | Dish | Ingredients With Grams | Food Group Contribution | Recipe Link | Prep Notes |
|---|---|---|---|---|---|---|
| Day 1 | Breakfast | 燕麦牛奶粥 + 水煮蛋 + 苹果 | 燕麦40g, 牛奶250g, 鸡蛋50g, 苹果150g | whole_grains_legumes 40g; dairy 250g; eggs 50g; fruit 150g | [教程标题](https://example.com) | 少糖或不加糖 |
```

Rules:

- Include at least breakfast, lunch, and dinner for each of 7 days.
- `Dish` must name cookable dishes, not only food groups.
- `Ingredients With Grams` must list major ingredients and rough grams.
- `Food Group Contribution` must map ingredients back to guideline food groups.
- `Recipe Link` should point to a verified tutorial for the core dish; use `not_verified` only when link verification was impossible.
- `Prep Notes` should include cooking method, oil/salt control, substitutions, or appliance constraints.

The `## Daily Ingredient Totals` section must use this table shape:

```markdown
| Day | vegetables_g | fruit_g | dairy_g | grains_g | whole_grains_legumes_g | tubers_g | animal_foods_g | fish_g | eggs_g | soy_nuts_g | water_ml | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Day 1 | 350 | 250 | 300 | 220 | 60 | 50 | 160 | 80 | 50 | 25 | 1500 | Close to adult anchors; fish contributes to weekly target. |
```

Use `null` or `unknown` rather than inventing precision when a quantity cannot be estimated. If the recommendation is for pregnancy, lactation, children, older adults, or vegetarian users, compare against that profile's anchors rather than adult defaults.

The `## Recipe Tutorial Links` section must use this table shape:

```markdown
| Dish | Tutorial Title | Source | URL | Type | Verified Date | Verification Notes |
|---|---|---|---|---|---|---|
| 清蒸鲈鱼 | 清蒸鲈鱼做法示例 | source name | https://example.com | image_text | 2026-06-20 | Accessible; shows ingredients and steps. |
```

Always distinguish:

- confirmed facts from records
- estimates from household units
- assumptions from missing data
- guideline principles from medical advice
- recipe links verified at recommendation time from unverified or unavailable links
