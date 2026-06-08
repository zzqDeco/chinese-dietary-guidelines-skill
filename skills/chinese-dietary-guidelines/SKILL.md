---
name: chinese-dietary-guidelines
description: Agent-led dietary logging, review, and meal-planning support based on the Chinese Dietary Guidelines for Chinese Residents 2022. Use when the user asks to record meals, maintain local JSONL diet logs, review recent eating patterns, compare diet habits against Chinese resident dietary principles, plan meals for the next few days or week, or adapt guidance for pregnancy, lactation, children, older adults, or vegetarian diets.
---

# Chinese Dietary Guidelines

## Operating Model

Use this skill as an agent-led workflow. Keep recommendations interpretive and context-aware instead of reducing the guidelines to a mechanical scoring table. Use the references to reason from principles, user context, recent records, and uncertainty.

Analysis and recommendation must include relative calculations whenever the available records support them. These calculations are performed by the agent at runtime from the local records and guideline anchors; they are not produced by a separate rule engine.

Store private records locally under `~/.codex/data/chinese-dietary-guidelines/`:

- `profile.json`
- `diet_log.jsonl`
- `recommendations/*.md`

Read and write these files directly when the user asks to record, analyze, or plan. Do not commit private diet data into any repository.

## Reference Use

- Read `references/data-schemas.md` before writing or interpreting records.
- Read `references/guideline-principles.md` before analyzing or recommending.
- Read `references/food-taxonomy.md` when classifying foods or estimating rough portions.
- Read `references/safety-boundaries.md` whenever the user mentions disease, pregnancy complications, child growth, frailty, dysphagia, supplements, rapid weight change, or other high-risk contexts.

## Relative Calculation Policy

Use transparent arithmetic to compare recent intake with the user's own baseline and the applicable guideline principles. Prefer relative comparisons over absolute conclusions.

Calculate and report, when data quality allows:

- period totals and per-recorded-day averages by food group or field
- frequency ratios, such as dairy on 2 of 7 recorded days
- food-variety counts per day and per week
- approximate gap or excess relative to a guideline anchor, such as about 60% of the lower vegetable reference
- shifts versus a previous comparable period when enough history exists
- low-confidence share, missing-meal share, and fields that cannot support reliable calculation

For recommendation, translate the relative gaps into practical deltas from the user's current pattern, such as adding one dairy serving on most days, increasing vegetables by one dish at lunch, replacing some refined staples with whole grains, or reducing salty/oily restaurant meals. Keep the arithmetic visible in the explanation and label rough household-unit estimates as approximate.

Do not turn these calculations into a rigid health grade, diagnosis, disease treatment plan, or hidden ranking formula. If a field is missing or too uncertain, say that the relative calculation is not reliable instead of inventing precision.

## Recording Workflow

1. Identify date, meal type, foods, portion descriptions, water, alcohol, cooking oil, salt, added sugar, activity, and notes.
2. Ask for missing high-impact facts only when they affect record quality; otherwise record with explicit uncertainty.
3. Classify foods into schema groups using context and the taxonomy reference. Do not rely on keyword matching alone.
4. Estimate grams only when useful and clearly mark `confidence` and `evidence_note`.
5. Append one JSON object per line to `diet_log.jsonl`. Never overwrite historical records unless the user explicitly asks to correct an entry.

## Analysis Workflow

1. Load `profile.json` if present; if missing, infer only minimal context from the request and say the analysis is provisional.
2. Read recent records, usually 7-14 days depending on the user request.
3. Start with data quality: recorded days, missing meals, estimated portions, low-confidence fields, and major unknowns.
4. Calculate relative measures that the data can support: averages, frequencies, proportions, trend shifts, and gap/excess against guideline anchors.
5. Analyze dynamically against the applicable principles: food variety, vegetables and fruit, dairy, whole grains and legumes, tubers, fish/poultry/eggs/lean meat, soy and nuts, oil, salt, added sugar, alcohol, water, and activity.
6. Explain reasoning in natural language. Use numbers from records when useful, but avoid pretending rough estimates are precise.

## Recommendation Workflow

For 7-day planning, generate directionally useful guidance rather than a rigid menu unless the user asks for a menu.

Include:

- profile and context summary
- recent record overview
- main observations and uncertainties
- relative calculations and guideline-principle comparison with PDF page sources
- next 7-day priorities
- practical meal, shopping, and prep suggestions
- safety boundaries and referral prompts when relevant

For pregnancy, lactation, children, older adults, and vegetarian users, switch to the matching principle section and avoid adult-default assumptions. Do not recommend weight loss during pregnancy or childhood. Do not prescribe supplement dosages or disease-specific nutrition therapy.
