# Recipe Link Policy

Use live search for recipe tutorial links when generating meal recommendations. Do not store a permanent hardcoded recipe-link library in this skill.

## Search Requirements

For every core dish in a 7-day plan:

- search the web at recommendation time when internet access is available
- prefer pages that show ingredients and step-by-step method without requiring login
- accept image-text articles, ordinary web pages, or videos if the user can reasonably follow them
- prefer home-cooking recipes with ordinary ingredients and equipment
- avoid links that are inaccessible, paywalled, login-only, missing ingredient details, or unrelated to the dish

Use the current date as the verification date in the output.

## Link Fields

Every tutorial link entry must include:

- `dish`
- `tutorial_title`
- `source`
- `url`
- `type`: `image_text`, `video`, `article`, or `unknown`
- `verified_date`
- `verification_notes`

## Verification Standard

A link is acceptable when:

- the page opens successfully
- the title or page content matches the dish
- the page includes either ingredient information or concrete cooking steps
- the recommendation does not depend on unverified health claims from that page

If the agent cannot open or verify links, mark the link section as unverified and say why. Do not invent URLs.

## Search Query Pattern

Use concise dish-specific searches, optionally with `做法`, `家常`, `少油`, `少盐`, `教程`, or the key ingredient.

Examples:

- `清蒸鲈鱼 家常 做法`
- `蒜蓉西兰花 少油 做法`
- `燕麦牛奶粥 做法`
- `豆腐菌菇汤 家常 做法`
- `杂粮饭 做法`

## When No Reliable Link Exists

If no reliable tutorial link is found:

1. Try a simpler dish name with the same ingredients.
2. Try a common equivalent cooking method.
3. If still unavailable, keep the dish only if it is simple and explain the missing link.
4. Never fabricate a source, title, or URL.

## Safety And Nutrition Boundary

Recipe pages are cooking references only. Use guideline principles for nutrition reasoning, not recipe-page claims. If a recipe is high-oil, high-salt, deep-fried, alcohol-heavy, raw-animal-food-heavy, or otherwise conflicts with the user's profile, adapt the dish or choose another tutorial.
