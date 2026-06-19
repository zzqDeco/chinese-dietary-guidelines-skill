# Chinese Dietary Guidelines Codex Skill

This repository contains a sanitized public Codex skill package for daily dietary management based on the Chinese Dietary Guidelines for Chinese Residents 2022.

The public package does not include the source PDF, OCR text, verified full-book Markdown extraction, page images, QA review artifacts, or any private diet logs. It does keep the compact guideline knowledge needed by the skill: principle summaries, food-group quantity anchors, profile-specific anchors, page references, schemas, food taxonomy, meal-planning workflow, eating-out guidance, and safety boundaries.

## What This Skill Does

The `chinese-dietary-guidelines` skill supports:

- diet profile setup and updates
- meal logging and record correction
- 1-day, 7-day, 14-day, and 30-day intake analysis
- relative comparison against Chinese dietary-guideline anchors
- cookable 7-day meal plans with ingredient grams
- shopping lists and prep schedules
- eating-out advice for cafeteria, delivery, convenience-store, restaurant, and travel settings
- execution review and next-plan adjustment
- profile adaptation for pregnancy, lactation, children, older adults, and vegetarian users

## Install Locally

Copy the skill directory into the Codex skill directory:

```bash
mkdir -p ~/.codex/skills
cp -R skills/chinese-dietary-guidelines ~/.codex/skills/chinese-dietary-guidelines
```

Private user data should stay outside this repository:

```text
~/.codex/data/chinese-dietary-guidelines/
```

## Safety Boundary

This skill is for everyday diet logging, guideline-level structure review, and meal-planning support. It does not provide medical diagnosis, disease treatment, clinical nutrition prescriptions, pregnancy or child weight-loss plans, or supplement dosage prescriptions.

Users with chronic disease, pregnancy complications, child growth concerns, dysphagia, rapid weight change, eating disorders, medication-diet conflicts, or other high-risk contexts should consult a clinician or registered dietitian.

## Public Release Contents

This public repository intentionally contains only:

- `skills/chinese-dietary-guidelines/`
- `VERSION`
- `CHANGELOG.md`
- `README.md`
- `scripts/validate_skill.sh`
- `.github/workflows/validate.yml`

The skill directory includes the necessary reference pack:

- `references/guideline-principles.md`: compact dietary-guideline anchors and PDF page sources
- `references/food-taxonomy.md`: food groups and portion-estimation hints
- `references/data-schemas.md`: profile, log, analysis, recommendation, shopping, review, and eating-out schemas
- `references/meal-planning.md`: dish-level 7-day planning, shopping, prep, and review guidance
- `references/eating-out.md`: cafeteria, delivery, convenience-store, and restaurant strategies
- `references/recipe-link-policy.md`: live tutorial-link search and verification policy
- `references/safety-boundaries.md`: non-medical safety limits and referral prompts

It intentionally excludes:

- source PDFs
- OCR text directories
- verified full-book Markdown extraction outputs
- QA review CSV/MD artifacts
- page images or manual crops
- local Codex installation copies
- private diet logs or profile data

## Validate

Run:

```bash
bash scripts/validate_skill.sh
```

Public CI runs strict mode:

```bash
STRICT_PUBLIC=1 bash scripts/validate_skill.sh
```

Strict mode rejects OCR/PDF/QA/full Markdown extraction artifacts if they are accidentally added.
It also checks that the compact guideline knowledge pack still contains key anchors and page-source references needed for the skill to work without the full OCR corpus.

## Versioning

Current version: see `VERSION`.

- `0.1.x`: documentation, schema clarification, validation, and small workflow fixes
- `0.2.0`: new sub-functions or output schemas
- `1.0.0`: stable real-world use with mature install and validation workflow
