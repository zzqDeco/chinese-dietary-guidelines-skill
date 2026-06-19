# Meal Planning

Use this file when turning guideline gaps into concrete meals. The output should help the user cook, shop, and prep, while preserving uncertainty about rough household estimates.

## Planning Flow

1. Identify the applicable profile section in `guideline-principles.md`.
2. Calculate recent gaps and excesses from the user's records.
3. Convert the main gaps into a 7-day ingredient budget.
4. Fill breakfast, lunch, and dinner with cookable dishes.
5. Sum each day by food group and compare the totals with guideline anchors.
6. Add substitutions for allergies, avoid foods, budget, time, kitchen equipment, and vegetarian type.

Do not output only food-group instructions. Every main meal should include dish names and major ingredient grams.

## Meal-Level Requirements

Each meal should include:

- dish name or dish combination
- major ingredients with rough grams
- food-group contribution
- cooking method
- oil and salt control point
- substitution option when a common allergen or disliked food is present
- tutorial link placeholder to be filled according to `recipe-link-policy.md`

## Building A Day

For a general adult day, build around the guideline anchors rather than exact calorie prescription:

- staple base: grains, whole grains or mixed legumes, and sometimes tubers
- vegetables in lunch and dinner, with dark vegetables in at least one meal
- fruit as breakfast side, snack, or dessert
- dairy at breakfast or snack when tolerated
- animal foods distributed across lunch and dinner; use fish or seafood several times per week
- soy products or nuts daily when possible
- water plan across the day

Example day structure:

| Meal | Dish Pattern | Contribution |
|---|---|---|
| Breakfast | 燕麦牛奶粥 + 水煮蛋 + 水果 | dairy, whole grains, eggs, fruit |
| Lunch | 杂粮饭 + 清蒸鱼 + 蒜蓉西兰花 + 紫菜豆腐汤 | grains, fish, dark vegetables, soy, fungi/algae |
| Dinner | 番茄鸡蛋面 + 凉拌黄瓜木耳 | grains, eggs, vegetables, fungi |
| Optional snack | 原味坚果 or 无糖酸奶 | nuts or dairy |

## Cookable Dish Examples

Use these as style examples, not as a fixed menu:

| Goal | Dish Examples |
|---|---|
| Add vegetables | 蒜蓉西兰花, 清炒小白菜, 番茄炒蛋, 凉拌黄瓜木耳, 香菇油菜 |
| Add fish/seafood | 清蒸鲈鱼, 番茄龙利鱼, 虾仁西兰花, 紫菜虾皮豆腐汤 |
| Add dairy | 燕麦牛奶粥, 无糖酸奶水果碗, 牛奶蒸蛋 |
| Add whole grains/legumes | 杂粮饭, 燕麦粥, 红豆小米粥, 玉米发糕 |
| Add soy | 家常豆腐, 豆腐菌菇汤, 麻婆豆腐少油版, 凉拌豆腐 |
| Reduce oily/salty meals | 清蒸, 水煮后凉拌, 炖汤少盐, 少酱汁 stir-fry |

## 7-Day Plan Rules

- Include 7 days unless the user requests a shorter range.
- Include breakfast, lunch, and dinner every day.
- Give ingredient grams for major ingredients; use rough grams where needed and label estimates.
- Vary dishes enough to support food variety.
- Track weekly fish/seafood, dairy frequency, soy/nuts frequency, and vegetable color mix.
- If restaurant meals are planned, specify what to order and how it contributes to the daily totals.
- If the plan cannot meet every anchor because of user constraints, state the tradeoff clearly.

## Profile Adaptation

- Pregnancy: use pregnancy anchors; do not recommend weight loss; avoid alcohol; include food-safety caution for undercooked animal foods.
- Lactation: use lactation anchors; emphasize water, diverse foods, dairy, quality protein, and soups without excessive salt.
- Children: use age anchors; make meals age-appropriate; do not recommend weight loss; avoid choking-risk phrasing.
- Older adults: prefer soft, digestible, protein-containing meals; avoid aggressive restriction; flag dysphagia or unintended weight loss.
- Vegetarian users: replace fish/meat with soy products, legumes, nuts, dairy/eggs if allowed, fungi/algae, and fermented soy where appropriate; mention B12 risk without prescribing supplement doses.

## Output Quality Bar

A useful recommendation should let the user answer:

- What do I cook for each meal?
- How much of the main ingredients should I buy or prepare?
- Which guideline gap does this dish address?
- Where can I learn the cooking method?
- What should I swap if I dislike or cannot eat an ingredient?
