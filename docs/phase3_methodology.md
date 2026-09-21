# Phase 3 Experimental Methodology

## 1. Purpose

Phase 3 evaluates the ability of a Vision-Language Model (VLM) to translate a rendered robotic scene and a high-level natural-language instruction into a PDDL problem that can be solved by a symbolic planner.

The baseline pipeline is:

Scene image + instruction
→ VLM
→ PDDL problem
→ Fast Downward
→ candidate plan
→ VAL validation against the ground-truth problem.

The image is treated as the source of scene information. The VLM prompt does not provide the ground-truth scene facts.

---

## 2. Experimental Conditions

Three input conditions are evaluated:

1. Normal image
   - Original rendered scene image (`scene.png`).
   - No semantic room labels added.

2. Labelled image
   - Same underlying scene.
   - Room names are explicitly rendered into the image (`scene_labelled.png`).
   - Labels identify room names only and do not reveal object or robot state.

3. No-image control
   - The instruction and PDDL domain are provided to the VLM.
   - No scene image is provided.

The no-image condition is a control condition for assessing the contribution of visual scene information.

---

## 3. Scenario Dataset

The evaluation uses 27 frozen scenarios from Phase 2.

The scenarios comprise:

- 3 spatial layouts;
- 3 task types:
  - navigation,
  - object retrieval,
  - multi-step navigation/manipulation;
- 3 instruction styles:
  - precise,
  - ambiguous,
  - novel.

The Phase 2 ground-truth PDDL problem (`gt_problem.pddl`) and reference plan (`plan.txt`) remain unchanged and are authoritative for evaluation.

Phase 2 artifacts are not regenerated during Phase 3.

---

## 4. VLM Configuration

The baseline VLM is:

`qwen/qwen3.8-27b`

The API temperature is:

`0`

The Phase 3 prompt version is:

`phase3-v2`

The prompt supplies the PDDL domain and candidate vocabulary but does not provide the actual scene facts. The model must determine scene entities and relations from the input image when an image is available.

A temperature of zero is not assumed to guarantee deterministic outputs. Therefore repeated experimental runs are retained separately.

---

## 5. Expected Response Status

Expected response status is determined from the frozen scenario metadata rather than from the ground-truth PDDL goal.

Expected status:

- `PDDL` for precise and novel instructions.
- `CLARIFICATION_REQUIRED` for ambiguous instructions.

A clarification response is therefore not inherently a failure.

It is classified as a failure only when it disagrees with the expected status.

---
## 6. Primary Task-Level Outcome

The primary evaluation concerns whether the generated symbolic problem correctly supports the requested task.

Task-level evaluation differs according to the expected response status.

For scenarios where `CLARIFICATION_REQUIRED` is expected, task-level success is recorded when the VLM returns `CLARIFICATION_REQUIRED`.

For scenarios where `PDDL` is expected, task-level success requires all of the following:

1. A PDDL response is produced when PDDL is expected.
2. The generated PDDL is valid and can be processed by the planner.
3. The generated problem has the correct task goal.
4. Fast Downward can produce a plan.
5. The resulting plan is valid when evaluated by VAL against the ground-truth problem.

For generated PDDL cases, VAL is run using:

- the original household domain;
- the Phase 2 ground-truth problem;
- the VLM-generated plan.

This prevents a plan from being considered successful merely because it is valid under the VLM-generated problem while being inconsistent with the ground-truth task specification.

Task-level success is therefore associated with successful completion and validation of the requested task, rather than exact reconstruction of every fact in the scene.

A generated PDDL problem is not considered a task failure solely because it omits scene facts that are irrelevant to the requested task.

---

## 7. Secondary Full-State Reconstruction Analysis

Full symbolic state reconstruction is evaluated separately from task-level success.

The generated initial state is compared with the Phase 2 ground-truth initial state.

Metrics include:

- state exact match;
- per-predicate precision;
- per-predicate recall;
- per-predicate F1;
- goal exact match.

Predicates are additionally grouped by observability:

### DIRECT_VISUAL

Facts directly represented by visible spatial relationships.

- `on`

### VISUAL_PLUS_SEMANTIC

Facts requiring visual information together with interpretation of the symbolic domain.

- `robot-at`
- `connected`
- `located`
- `holding`

### SEMANTIC_DOMAIN

Facts determined primarily by domain semantics rather than direct visual evidence.

- `manipulable`

`on` and `located` are not treated as fully independent evidence because an object's location may be inferred from its support object's location.

Full-state reconstruction is therefore reported as a diagnostic measure rather than being required for primary task success.

---

## 8. Failure Taxonomy

Failure information is represented using independent boolean flags. Multiple flags may be true for a single scenario.

The fixed failure flags are:

- `api_error`
- `empty_response`
- `parse_error`
- `invalid_pddl`
- `clarification_mismatch`
- `wrong_goal`
- `missing_fact`
- `hallucinated_fact`
- `planner_unsolvable`
- `val_invalid`

Definitions:

### api_error

The VLM/API request failed.

### empty_response

The VLM produced no usable response.

### parse_error

A response expected to contain PDDL could not be extracted into the required structured representation.

### invalid_pddl

The generated PDDL cannot be processed as a valid planning problem, including errors such as undefined objects or PDDL translation/parsing failures.

### clarification_mismatch

The model's response status differs from the expected status defined by the instruction style.

### wrong_goal

The generated goal does not exactly match the ground-truth task goal.

### missing_fact

A ground-truth initial-state fact is absent from an otherwise scoreable generated PDDL state.

### hallucinated_fact

A generated initial-state fact is not present in the ground-truth initial state.

### planner_unsolvable

The generated PDDL is sufficiently valid to reach the planner stage but no valid plan is found, without evidence that the failure is caused by PDDL parsing/translation.

### val_invalid

The generated plan fails validation against the ground-truth environment using VAL.

---

## 9. Primary Failure Category

Although all failure flags are retained, exactly one primary failure category is derived using the following fixed priority order:

1. `api_error`
2. `empty_response`
3. `parse_error`
4. `invalid_pddl`
5. `clarification_mismatch`
6. `wrong_goal`
7. `missing_fact`
8. `hallucinated_fact`
9. `planner_unsolvable`
10. `val_invalid`

The priority order is defined before the main experimental results are collected.

It is used only to provide a single primary categorical description; it does not discard the remaining failure flags.

---

## 10. Computational Efficiency

Computational efficiency is measured using recorded latency information, including:

- VLM response latency;
- planner latency;
- VAL latency;
- total pipeline latency where available.

Plan length and plan cost are also recorded for successful planning cases.

Latency measurements are retained per scenario and per experimental run.

---

## 11. Repeated Runs

Repeated runs are stored in separate run-specific directories.

Example:

`experiments/phase3/normal/run_001/`

`experiments/phase3/normal/run_002/`

and equivalently for the labelled and no-image conditions.

Run-specific storage prevents repeated trials from overwriting earlier observations.

---

## 12. Development/Pilot Disclosure

Scenarios 001–003 were used during development and prompt inspection before the full controlled evaluation.

These scenarios are therefore treated as development/pilot cases when interpreting headline experimental results.

The final evaluation protocol is frozen before the complete 27-scenario experimental runs.

---

## 13. Refinement Evaluation

Iterative refinement is evaluated separately from the baseline experiment.

The baseline experiment first measures the unrefined pipeline.

A later refinement condition may use information from failed planning, parsing, or validation to request a revised PDDL representation.

Refinement is not applied to the baseline runs so that improvements can be attributed to the refinement procedure rather than being confounded with baseline performance.

---

## 14. Model Comparison

The initial baseline evaluation uses the specified Qwen model.

A second VLM is evaluated later as a model-choice factor using the same frozen scenarios, instructions, evaluation metrics, and failure taxonomy.

The model comparison is performed after the baseline protocol has been established.

---

## 15. Statistical Analysis

Statistical analysis is performed after data collection using the pre-defined experimental factors.

Results are analysed by:

- experimental condition;
- instruction style;
- task type;
- spatial layout;
- VLM model where applicable.

Repeated runs are retained as separate observations.

The analysis reports descriptive performance measures and appropriate statistical comparisons for the collected data rather than selecting evaluation criteria after observing the results.

---

## 16. Reproducibility and Data Integrity

The following are frozen before the headline Phase 3 experiment:

- Phase 2 scenarios;
- Phase 2 ground-truth PDDL;
- reference plans;
- VLM prompt version;
- model configuration;
- experimental conditions;
- expected-status rule;
- primary task-level outcome definition;
- secondary state-reconstruction metrics;
- observability categories;
- failure flags;
- primary failure priority;
- run-storage structure.

The Phase 3 experiment must not modify the Phase 2 ground-truth artifacts.

All raw VLM responses, generated PDDL, planner outputs, plans, VAL outputs, and run metadata are retained for subsequent analysis.
