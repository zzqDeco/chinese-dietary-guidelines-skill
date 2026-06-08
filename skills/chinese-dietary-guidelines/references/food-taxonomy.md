# Food Taxonomy

Use this taxonomy to help the agent classify and explain foods in `diet_log.jsonl`. Classify by context, ingredient meaning, and user wording. Do not treat this as keyword matching code.

## Food Groups

| Group | Use for | Notes |
|---|---|---|
| `grains` | rice, noodles, bread, steamed buns, porridge, refined cereals | Staple grain foods. |
| `whole_grains_legumes` | oats, brown rice, corn, whole wheat, red beans, mung beans, mixed legumes | Also relevant to staple-food variety. |
| `tubers` | potato, sweet potato, taro, yam | Usually counted separately from grains in guideline discussion. |
| `vegetables` | non-dark vegetables | Use `dark_vegetables` when the color/nutrient category is clear. |
| `dark_vegetables` | spinach, pak choi, broccoli, carrot, pumpkin, dark leafy or red/yellow vegetables | Also part of vegetables. |
| `fruits` | fresh fruit | Avoid counting juice as equivalent to fruit unless explaining limitations. |
| `dairy` | milk, yogurt, cheese, dairy equivalents | Prefer unsweetened versions when recommending. |
| `fish` | fish, shrimp, crab, shellfish | Useful for weekly fish/seafood discussion. |
| `poultry` | chicken, duck, goose | Prefer lean and less processed forms. |
| `meat` | pork, beef, lamb, other livestock meat | Distinguish lean meat from processed meat when possible. |
| `eggs` | chicken eggs, duck eggs, egg products | Record yolk avoidance in notes if mentioned. |
| `soy` | tofu, soy milk, soybeans, soy products | Be careful: food weight is not always equal to dry soybean equivalent. |
| `fermented_soy` | fermented soybeans, natto, fermented bean curd, douchi | Especially relevant for vegan users. |
| `nuts` | peanuts, walnuts, almonds, seeds used as nuts | Prefer original/unsalted nuts in recommendations. |
| `fungi_algae` | mushrooms, seaweed, kelp, algae | Especially relevant for vegetarian users. |
| `oil` | cooking oil when directly reported | Usually better captured as `oil_g`. |
| `salt` | salt when directly reported | Usually better captured as `salt_g`. |
| `added_sugar` | added sugar, sweet drinks, desserts when estimating sugar | Keep uncertainty explicit. |
| `water` | drinking water | Usually better captured as `water_ml`. |
| `alcohol` | alcoholic drinks converted to alcohol grams when possible | Do not recommend alcohol. |
| `other` | unclear or mixed foods | Use `evidence_note` to explain ambiguity. |

## Mixed Dishes

For mixed dishes, either:

- split into multiple foods when the user gives ingredients or portions, or
- record one `other` or dominant group item with `confidence=low` and explain the uncertainty.

Examples:

- “番茄鸡蛋面”：can be split into grains, eggs, vegetables if portion details are available.
- “麻辣香锅一份”：usually mixed and oil/salt-heavy; record as mixed/other unless ingredients are known.
- “奶茶”：usually `added_sugar` plus possible dairy; note sugar uncertainty.

## Portion Estimates

Use explicit grams or package labels whenever possible. If estimating from household units, set `confidence=medium` or `low` and write the basis in `evidence_note`.

| Household description | Rough estimate |
|---|---:|
| 1 bowl / 1 碗 | about 250 g |
| 1 cup / 1 杯 | about 250 ml |
| 1 serving / 1 份 | about 100 g unless context suggests otherwise |
| 1 piece / 1 个 | about 50 g, highly context-dependent |
| 1 egg / 1 枚鸡蛋 | about 50 g |
| 1 handful / 1 把 | about 25 g |
| 1 spoon / 1 勺 | about 10 g |

When the estimate would materially change the analysis, ask the user for clarification instead of silently assuming.
