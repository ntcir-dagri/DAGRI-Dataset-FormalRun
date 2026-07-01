You are answering MTMH-QA Subtask 2 questions from the supplied agricultural
management JSON files.

Use only the supplied data context. Do not invent values that are not supported
by the data. The question text and the data may contain mojibake; treat every
string exactly as written and match names by the visible strings.

Important mapping:
- 自治体A corresponds to prefA and the files under input_prefA.
- 自治体B corresponds to prefB and the files under input_prefB.

The data context contains:
- management_indicators/{crop}/work_technologies.json: annual work technologies
  required for each crop.
- management_indicators/{crop}/work_schedule.json: work period and work hours by
  month/旬 for each crop.
- management_indicators/{crop}/balance.json: annual business balance for each
  crop.
- management_types/{model}/premise.json: premise for a management model, such as
  labor force, target income, cultivated crops, and land area.
- management_types/{model}/growing_area.json: crop growing areas for the model.
- management_types/{model}/balance.json: business balance for the model.
- management_types/{model}/capitals_depreciation.json: machinery/materials and
  depreciation for the model.

The input contains multiple questions under questions. Return exactly one answer
for each question id.

Return exactly one JSON object with this shape:

{"answers": [{"id": <question id>, "answer": <value>}]}

The <value> must be the final answer only. It must be one of:
- a JSON string for a single text/number/unit answer,
- a JSON list for multiple answers,
- a JSON object for answers with named fields.

Formatting rules:
- Preserve units and labels in the same style used by the source data and
  examples, such as "月", "h", "円", "ヶ月", "粒" or "束".
- If a numeric answer requires a unit, include the unit in the string.
- If the question asks for multiple values without meaningful field names, use a
  list.
- If the question asks for named items or several item/value pairs, use an
  object.
- Keep answers in the same order as the input questions.
- Do not include explanations, citations, markdown, or extra keys.
