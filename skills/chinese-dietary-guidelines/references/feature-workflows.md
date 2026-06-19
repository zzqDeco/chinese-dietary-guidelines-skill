# Feature Workflows

Use this file to choose the right sub-function and output shape. The skill is a daily dietary management workflow, not only a meal-plan generator.

## Profile Setup Or Update

Triggers:

- `建立我的饮食画像`
- `我不吃牛肉`
- `我只有电饭煲`
- `我预算低/没时间做饭`

Workflow:

1. Load `profile.json` if present.
2. Ask only for fields that matter to the user's current goal.
3. Update allergies, avoid foods, disliked foods, cooking time, tools, budget, cuisine preferences, life stage, and vegetarian type as needed.
4. Preserve unknown fields as unknown rather than forcing a complete questionnaire.

Output:

- concise profile summary
- changed fields
- remaining assumptions

## Meal Logging

Triggers:

- `记录今天早餐`
- `午餐吃了...`
- `帮我记一下`

Workflow:

1. Parse date, meal type, foods, portions, drinks, alcohol, activity, oil, salt, sugar, and notes.
2. Split mixed dishes when ingredients are clear.
3. Estimate grams only when useful; mark confidence and evidence.
4. Preserve `source_text`.
5. Append JSONL and summarize what was recorded.

Output:

- human-readable confirmation
- JSONL-compatible record when useful
- uncertainty notes

## Record Correction

Triggers:

- `昨天晚餐鸡肉不是100g，是150g`
- `把午餐的奶茶删掉`
- `刚才记录错了`

Workflow:

1. Locate the likely record by date, meal, food, and source text.
2. Ask for clarification when multiple records match.
3. Use `correction_of` and `updated_reason`, or clearly mark the modified record if editing in place is required by the user.
4. Re-run any requested analysis affected by the correction.

Output:

- corrected value
- affected record id or date/meal
- whether analysis should be refreshed

## Period Analysis

Triggers:

- `分析最近7天`
- `这周吃得怎么样`
- `和上周比呢`

Workflow:

1. Load profile and relevant logs.
2. Determine window: default 7 days; support 1, 14, and 30 days.
3. Start with data quality.
4. Calculate food-group averages, frequencies, relative gaps, low-confidence share, and trends versus previous period if available.
5. Tie observations to guideline principles and page sources.

Output:

- `analysis_report.md` structure from `data-schemas.md`
- priority actions ranked by impact and confidence

## Concrete Meal Recommendation

Triggers:

- `推荐下周饮食`
- `给我7天菜单`
- `按指南帮我安排饭`

Workflow:

1. Analyze recent gaps.
2. Convert gaps into ingredient budgets.
3. Generate cookable meals with grams and food-group contribution.
4. Verify recipe tutorial links when internet access is available.
5. Add daily totals, shopping list, prep schedule, uncertainty, and sources.

Output:

- `recommendation.md` structure from `data-schemas.md`

## Shopping And Prep

Triggers:

- `生成购物清单`
- `周末怎么备餐`
- `只有空气炸锅能做吗`

Workflow:

1. Use an existing meal plan when available.
2. Group purchases by category.
3. Estimate purchase quantities from planned grams.
4. Add prep-ahead tasks and storage notes.
5. Adapt to budget, cooking time, tools, and household size.

Output:

- `shopping_list.md` structure from `data-schemas.md`

## Eating-Out Advice

Triggers:

- `今天只能外卖`
- `食堂怎么吃`
- `便利店买什么`
- `聚餐怎么选`

Workflow:

1. Identify the eating-out setting and constraints.
2. Recommend concrete order combinations.
3. Explain likely food-group contribution.
4. Mark oil, salt, sugar, and portion uncertainty.
5. Tell the user what to log afterwards.

Output:

- `eating_out_advice.md` structure from `data-schemas.md`

## Execution Review

Triggers:

- `这周执行得怎么样`
- `哪些菜我没做到`
- `下周按实际情况调整`

Workflow:

1. Compare planned dishes and actual logs.
2. Identify completed, skipped, replaced, liked, disliked, or impractical meals.
3. Keep successful defaults.
4. Adjust the next plan based on actual behavior and guideline gaps.

Output:

- `meal_plan_review.md` structure from `data-schemas.md`
