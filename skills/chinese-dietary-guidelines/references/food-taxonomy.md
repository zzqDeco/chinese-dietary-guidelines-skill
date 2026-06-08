# Food Taxonomy

Use these canonical food groups in `diet_log.jsonl`.

## Canonical Groups

| Group | Use for |
|---|---|
| `grains` | rice, noodles, bread, steamed buns, porridge, cereals |
| `whole_grains_legumes` | oats, brown rice, corn, whole wheat, red beans, mung beans, mixed legumes |
| `tubers` | potato, sweet potato, taro, yam |
| `vegetables` | vegetables not otherwise marked dark |
| `dark_vegetables` | spinach, pak choi, broccoli, carrot, pumpkin, dark leafy or red/yellow vegetables |
| `fruits` | fresh fruit |
| `dairy` | milk, yogurt, cheese, dairy equivalents |
| `fish` | fish, shrimp, crab, shellfish |
| `poultry` | chicken, duck, goose |
| `meat` | pork, beef, lamb, other livestock meat |
| `eggs` | chicken eggs, duck eggs, egg products |
| `soy` | tofu, soy milk, soybeans, soy products |
| `fermented_soy` | fermented soybeans, natto, fermented bean curd, douchi |
| `nuts` | peanuts, walnuts, almonds, seeds used as nuts |
| `fungi_algae` | mushrooms, seaweed, kelp, algae |
| `oil` | cooking oil when logged as a food item |
| `salt` | salt when logged as a food item |
| `added_sugar` | added sugar, sweet drinks, desserts when estimating sugar |
| `water` | drinking water |
| `alcohol` | alcoholic drinks converted to alcohol grams |
| `other` | items that cannot be classified confidently |

## Aggregation

- `whole_grains_legumes` also contributes to total grains.
- `dark_vegetables` also contributes to total vegetables.
- `fish`, `poultry`, `meat`, and `eggs` contribute to total animal foods.
- `soy`, `fermented_soy`, and `nuts` contribute to soy/nuts.
- Do not double-count if the user separately provides `oil_g`, `salt_g`, `added_sugar_g`, `water_ml`, or `alcohol_g`.

## Household Unit Estimates

Use explicit grams when available. If the user gives household units, record the estimate and set confidence to `medium` or `low`.

| Unit | Default estimate |
|---|---:|
| `g`, `gram`, `grams`, `克` | direct grams |
| `kg`, `公斤`, `千克` | 1000 g |
| `ml`, `毫升` | 1 g/ml for water and dairy-like liquids |
| `bowl`, `碗` | 250 g |
| `cup`, `杯` | 250 g |
| `serving`, `份` | 100 g |
| `piece`, `个`, `只` | 50 g |
| `egg`, `枚` | 50 g |
| `handful`, `把` | 25 g |
| `spoon`, `勺` | 10 g |

If no amount is available, keep `estimated_grams=null` and `confidence=low`.
