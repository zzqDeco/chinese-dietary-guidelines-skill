# Changelog

## 0.1.1 - 2026-06-20

Repository organization and documentation refresh.

- Reorganized the repository into `skills/`, `corpus/`, `qa/`, `scripts/`, and `docs/` sections.
- Moved verified, extracted, and OCR corpus files under `corpus/`.
- Split QA artifacts into `qa/audit/`, `qa/corrections/`, and `qa/indexes/`.
- Moved extraction tooling under `scripts/extraction/` while keeping `scripts/validate_skill.sh` as the CI entrypoint.
- Rewrote `README.md` as a public project introduction with install, corpus, validation, privacy, safety, and versioning notes.
- Added docs for extraction methodology, public data policy, and skill usage.
- Updated validation to check the new corpus paths, 374 full-text page markers, and 99 verified table candidate sections.
- No skill behavior change.

## 0.1.0 - 2026-06-20

Initial usable public skill release.

- Built verified Markdown outputs from the scanned《中国居民膳食指南（2022）》workspace.
- Completed table and body-text verification artifacts in the local full extraction workspace.
- Added `chinese-dietary-guidelines` as an agent-led Codex skill.
- Replaced deterministic recommendation logic with principle references and schemas.
- Added transparent relative-calculation guidance for analysis and recommendations.
- Added cookable 7-day meal plans with ingredient grams and recipe tutorial-link policy.
- Expanded the skill into a daily dietary management workflow covering profile setup, logging, correction, analysis, meal planning, shopping/prep, eating-out advice, execution review, and special population adaptation.

### Versioning Policy

- `0.1.x`: documentation, schema clarifications, validation, and small workflow fixes.
- `0.2.0`: new sub-functions or output schemas.
- `1.0.0`: stable real-world use with a mature install and validation workflow.
