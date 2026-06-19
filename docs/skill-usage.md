# Skill Usage

The `chinese-dietary-guidelines` skill helps a Codex agent manage daily diet tasks using the Chinese Dietary Guidelines for Chinese Residents (2022) as a reference.

## Install

```bash
mkdir -p ~/.codex/skills
cp -R skills/chinese-dietary-guidelines ~/.codex/skills/chinese-dietary-guidelines
```

After installation, Codex can trigger the skill when the user asks to record meals, analyze recent diet, plan meals, generate shopping lists, handle eating-out choices, or adapt guidance for special populations.

## Data Location

Personal data belongs outside this repository:

```text
~/.codex/data/chinese-dietary-guidelines/
├── profile.json
├── diet_log.jsonl
└── recommendations/
```

The skill references schemas for those files, but it does not require this repository to contain real user data.

## Main Functions

- Profile setup and update.
- Natural-language meal logging.
- Historical meal correction with traceable update fields.
- Recent intake analysis for 1, 7, 14, or 30 days.
- Transparent relative calculations against guideline anchors.
- Concrete 7-day meal plans with dish names, ingredient grams, food-group contributions, and tutorial-link policy.
- Shopping lists and prep schedules.
- Eating-out advice for cafeterias, takeout, convenience stores, and social meals.
- Weekly review and next-plan adjustment.
- Special-population adaptation for pregnancy, lactation, children, older adults, and vegetarian diets.

## Example Prompts

```text
记录今天早餐：一杯牛奶、一个鸡蛋、两片全麦面包。
```

```text
分析我最近 7 天饮食，重点看蔬菜、奶类、鱼类和盐油糖。
```

```text
给我下周 7 天具体餐食计划，要有菜名、食材克重、教程链接、购物清单。
```

```text
今天只能吃食堂，午餐怎么选更接近中国居民膳食指南？
```

```text
这周推荐菜单我只执行了 4 天，帮我复盘并调整下周计划。
```

## Recommendation Style

The skill is agent-led. It does not ship a fixed recommendation script or hidden scoring engine. During analysis and planning, the agent should:

- read the user profile and recent logs;
- summarize data completeness and uncertainty;
- estimate recent food-group intake when enough data is available;
- compare current patterns with applicable guideline principles;
- calculate relative gaps or overages transparently;
- convert gaps into concrete dishes and ingredient quantities;
- cite guideline page references from the skill references;
- clearly separate facts, estimates, and safety cautions.

## Safety Boundary

The skill is for daily dietary guidance. It must not provide medical diagnosis, disease treatment, clinical nutrition prescriptions, pregnancy or child weight-loss instructions, or supplement dosage prescriptions. Risk scenarios should be routed to a physician or registered dietitian.
