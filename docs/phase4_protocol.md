# Phase 4 Iterative VLM/PDDL Refinement Protocol

## 1. Purpose

Phase 4 is an exploratory refinement study investigating whether iterative
VLM/PDDL refinement can recover failures from single-shot VLM-generated
PDDL, and whether feedback-driven refinement can provide useful information
beyond simply generating additional independent samples.

The study focuses on the **labelled-image condition**, using the failures
already observed in the Phase 3 labelled runs. The existing Phase 3 output
is reused as the initial attempt, avoiding a redundant API call.

The Phase 4 exploratory study distinguishes:

1. **Realistic pipeline feedback** that would be available to a deployed
   planning system.
2. **Self-verification feedback** that uses the image, instruction, and
   generated PDDL without access to ground truth.
3. **Oracle feedback** derived from ground-truth evaluation and therefore
   not deployable.
4. **Independent resampling** as a conceptual comparison for the effect of
   additional generation opportunities.

Because of API rate and token constraints, the full originally planned
Phase 4 factorial design is not executed. The executed study uses one run
per selected scenario-condition and reuses Phase 3 attempt 1.

Phase 4 does not modify the frozen Phase 3 baseline.

---

## 2. Research Question

The primary Phase 4 research question is:

> Can iterative VLM/PDDL refinement recover failures that occur in
> single-shot VLM-generated PDDL, particularly failures that are not
> detectable by the planning pipeline itself?

The exploratory study investigates three related questions:

- Can self-verification detect semantic failures that are invisible to the
  parser, translator, and planner?
- How much recovery is possible when increasingly informative oracle
  feedback is provided?
- When a failure is already accepted by the deployable pipeline, does
  feedback provide useful information beyond simply generating another
  candidate?

The study is exploratory rather than confirmatory because it uses a
resource-constrained subset of the originally planned design, one run per
scenario-condition, and no repeated statistical comparison.
---

## 3. Phase 3 Baseline and Scope

Phase 3 remains frozen and is not rerun or modified.

The Phase 3 baseline used:

* VLM: `qwen/qwen3.8-27b`
* Groq OpenAI-compatible API
* temperature = 0
* Phase 3 prompt: `phase3-v2`

Phase 4 changes the generation temperature to `0.7` so that repeated attempts provide stochastic variation.

The Phase 4 experiment must not modify the Phase 3 results, files, or interpretation.

---

## 4. Conditions

### 4.1 Condition A — Realistic Pipeline Feedback

Condition A represents feedback available from the deployed planning pipeline without access to ground truth.

Possible feedback sources are limited to:

* static PDDL consistency checks;
* PDDL parsing errors;
* translator/type errors;
* planner failure or unsolvability;
* other explicitly pre-specified machine-detectable planning-pipeline errors.

Condition A must not receive:

* `gt_problem.pddl`;
* ground-truth state;
* VAL-vs-ground-truth comparison results;
* ground-truth-derived fact differences;
* hidden benchmark labels.

### Hypothesis A

> Realistic feedback will provide little improvement in the labelled condition because all seven Phase 3 labelled scenarios that produced PDDL were accepted by the planner despite being semantically incorrect.

This is a pre-specified hypothesis, not a post-hoc interpretation.

---

### 4.2 Condition B — Self-Verification

Condition B introduces a separate VLM verification call intended to identify inconsistencies that the parser, translator, or planner cannot detect.

The verifier receives only:

1. the original scene image;
2. the original natural-language instruction;
3. the generated PDDL.

The verifier does not receive ground-truth PDDL, ground-truth state, VAL results, or any other ground-truth-derived information.

The verifier must return exactly one of:

```text
CONSISTENT
```

or:

```text
INCONSISTENT
REASON: <brief explanation>
```

If the available visual and linguistic evidence is insufficient to establish an inconsistency, the verifier should return:

```text
CONSISTENT
```

An `INCONSISTENT` result triggers refinement.

### Hypothesis B

> Self-verification will detect some semantic failures that are not detectable by parser, translator, or planner feedback.

---

### 4.3 Oracle Feedback

Oracle feedback is evaluation-only and is not intended to represent
deployable feedback.

The original Phase 4 protocol specified three oracle information levels:

#### O1 — Binary oracle feedback

The model receives only a binary signal that the generated representation
is incorrect.

#### O2 — Category-level oracle feedback

The model receives the semantic failure category, such as:

* `WRONG_GOAL`
* `MISSING_FACT`

O2 is **not executed** in the resource-constrained Phase 4 study.

#### O3 — Specific discrepancy oracle feedback

The model receives a specific discrepancy derived from comparison with the
ground-truth task representation.

O3 is executed only for the PDDL-producing semantic failures in the
selected labelled-image cases.

O3 provides more specific information than O1 and may approach answer-level
supervision. Oracle conditions are therefore treated as non-deployable
exploratory analyses.

### Oracle hypothesis

> Oracle feedback may provide information that enables refinement of
> failures that are not detectable through realistic pipeline feedback.

The executed oracle comparison is restricted to O1 and O3. No claim of a
progressive O1-to-O2-to-O3 effect is made because O2 is not executed.

---

## 5. Independent Resampling Baseline

Independent resampling was specified in the original Phase 4 design as a
comparison for whether refinement provides information beyond additional
independent VLM generation opportunities.

The original resampling design allowed up to four independent generation
attempts. Each attempt was independent and did not receive the previous
attempt's PDDL or feedback.

This resampling experiment is **not executed as a new API experiment** in
the resource-constrained Phase 4 study.

For the selected Phase 3 labelled failures, an offline resampling analysis
may be derived from the existing Phase 3 outputs where the initial
candidate already passes the predefined deployable pipeline checks. Under
the predefined deployable stopping rule, those cases would stop at
attempt 1, so no additional resampling call is required.

Ground-truth evaluation is never used to select a sample in the deployable
resampling analysis.

---

## 6. Pass@4 Upper Bound

A separate pass@4 analysis was specified in the original Phase 4 design as
an evaluation-only upper-bound analysis using four independent samples.

For evaluation purposes, the original design considered a scenario
successful if any of the four samples succeeded according to the
ground-truth evaluation.

This analysis is **not executed** in the resource-constrained Phase 4
study because no additional independent four-sample generation is
performed.

Pass@4 therefore remains a documented component of the original protocol
and is not reported as an executed Phase 4 result.

---

## 7. Generation Settings

Phase 4 refinement attempts use:

- temperature = `0.7`;
- maximum of four total generation attempts;
- one Phase 4 run per selected scenario-condition;
- the existing Phase 3 labelled output is reused as **attempt 1**;
- no new API call is made to regenerate Phase 3 attempt 1;
- Phase 3 attempt 1 was generated at temperature `0`;
- new Phase 4 refinement attempts are generated at temperature `0.7`;
- the original image is re-sent on every refinement attempt;
- conversation history is retained between refinement attempts.

Thus, a Phase 4 run consists of:

1. the already-existing Phase 3 output as attempt 1;
2. up to three new VLM refinement attempts.

The change from temperature `0` for the reused Phase 3 attempt to
temperature `0.7` for Phase 4 refinement attempts is recorded explicitly.
This means that attempt 1 and subsequent refinement attempts are not
identically sampled.

The Phase 3 attempt 1 output is treated as fixed input to the Phase 4
refinement process and is not regenerated.
---

## 8. Refinement Conversation Structure

For iterative refinement, the conversation history is retained.

### Attempt 1

```text
image + instruction → PDDL
```

### Attempt 2+

```text
image + instruction + previous PDDL + feedback → revised PDDL
```

The image is re-sent on every refinement attempt.

Ground-truth files are never supplied to the prompt builder for Conditions A or B.

---

## 9. Feedback Templates

### 9.1 Condition A — Static/PDDL Validation Error

```text
The generated PDDL could not be accepted by the planning pipeline.

Pipeline error:
{ERROR_TEXT}

Revise the PDDL to correct the reported error. Preserve the original instruction and scene interpretation unless a change is required to correct the error.

Return the revised PDDL only.
```

### 9.2 Condition A — Translator Error

```text
The generated PDDL could not be translated into a planning problem.

Translator error:
{ERROR_TEXT}

Revise the PDDL to correct the reported error. Preserve the original instruction and scene interpretation unless a change is required to correct the error.

Return the revised PDDL only.
```

### 9.3 Condition A — Planner Failure

```text
The generated PDDL was accepted by the translator, but the planner could not find a solution.

Planner result:
{ERROR_TEXT}

Revise the PDDL so that the requested task can be represented as a solvable planning problem. Preserve the original instruction and scene interpretation unless a change is required.

Return the revised PDDL only.
```

Only actual pipeline-generated errors may populate `{ERROR_TEXT}`.

---

### 9.4 Condition B — Verification Prompt

```text
Check whether the generated PDDL is consistent with the scene shown in the image and with the requested task.

You have access only to:
1. the image,
2. the original instruction, and
3. the generated PDDL.

Do not assume access to any hidden ground-truth representation.

Return exactly one of:

CONSISTENT

or

INCONSISTENT
REASON: <brief explanation of the inconsistency>

If the available visual and linguistic evidence is insufficient to establish an inconsistency, return CONSISTENT.
```

### 9.5 Condition B — Refinement Feedback

If the verifier returns `INCONSISTENT`:

```text
A self-verification check identified a possible inconsistency in the generated PDDL.

Verification feedback:
{VERIFIER_REASON}

Review the original image, instruction, and generated PDDL. Revise the PDDL to address the reported inconsistency.

Return the revised PDDL only.
```

The verifier's reason must be generated without access to ground truth.

---

### 9.6 Oracle O1 — Binary Feedback

```text
Oracle evaluation indicates that the generated representation does not achieve the intended task.

Revise the PDDL so that it represents the intended task.

Return the revised PDDL only.
```

---

### 9.7 Oracle O2 — Category Feedback

```text
Oracle evaluation indicates that the generated representation does not achieve the intended task.

Failure category:
{WRONG_GOAL | MISSING_FACT}

Revise the PDDL to correct this failure while preserving the intended task.

Return the revised PDDL only.
```

---

### 9.8 Oracle O3 — Specific Discrepancy Feedback

```text
Oracle evaluation indicates that the generated representation does not correctly represent the intended task.

Specific discrepancy identified by oracle evaluation:
{GROUND_TRUTH_FACT_DIFFERENCE}

Revise the PDDL to correct this discrepancy.

Return the revised PDDL only.
```

`{GROUND_TRUTH_FACT_DIFFERENCE}` is explicitly derived from ground-truth evaluation.

---

## 10. Clarification Handling

Clarification is treated as a legitimate terminal outcome when clarification is expected.

### Expected clarification

If the scenario's expected outcome is `CLARIFICATION_REQUIRED`:

* stop immediately;
* count the scenario as successful;
* do not perform refinement;
* do not provide oracle feedback.

This rule applies to all conditions.

Oracle feedback must never be used to override a correct clarification.

### Unexpected clarification

If the expected outcome is PDDL but the VLM returns `CLARIFICATION_REQUIRED`:

#### Condition A

Stop and count the attempt/scenario as a failure.

No realistic pipeline error exists indicating that clarification was unnecessary.

#### Condition B

The self-verification mechanism may assess whether the clarification is inconsistent with the image and instruction.

If the verifier returns `CONSISTENT`, stop and count the outcome as a failure.

If the verifier returns `INCONSISTENT`, its reason becomes refinement feedback.

#### Conditions O1–O3

The oracle may provide feedback stating that clarification was not required.

This is explicitly oracle-only feedback.

---

## 11. Deployment-Time Versus Evaluation-Time Information

This distinction is central to Phase 4.

### Deployment-time information

Conditions A and B may use only information that could be available without knowing the benchmark ground truth:

* image;
* instruction;
* generated PDDL;
* static PDDL checks;
* parser/translator output;
* planner output;
* self-verification output.

### Evaluation-time information

After each attempt, the experiment may independently evaluate the generated result against the Phase 2 ground-truth problem using VAL or the established Phase 3 task-level evaluation procedure.

This evaluation is used only to measure:

* actual task success;
* final success;
* failure category;
* recovery;
* attempt-wise performance.

Ground-truth evaluation must never be passed to Conditions A or B or used to select a successful candidate during resampling.

---

## 12. Detected Failure

An attempt is considered a **detected failure** when the condition's predefined feedback mechanism produces a non-empty error signal for that attempt.

Examples:

### Condition A

Detected if the pipeline produces:

* static PDDL error;
* parser error;
* translator error;
* planner failure;
* another pre-specified deployable pipeline error.

### Condition B

Detected if the verifier produces:

```text
INCONSISTENT
REASON: ...
```

### Oracle conditions

For the executed oracle conditions, a failure is detected when the oracle
generates the predefined O1 or O3 feedback.

O2 is retained as part of the original protocol definition but is not
executed in the resource-constrained Phase 4 study.

An attempt that is incorrect according to ground-truth evaluation but
produces no feedback signal under that condition is classified as an
**undetected failure**.

---

## 13. Stopping Rule

The refinement loop uses **deployment-time stopping criteria**. Ground-truth task evaluation is performed independently after each attempt for research measurement only and never determines whether a deployable condition continues, stops, or selects a candidate.

Each run stops when the first applicable stopping condition is reached:

1. **Expected clarification** → stop and count as a successful clarification outcome.
2. **Deployment-success signal** → stop and retain the current candidate.
3. **Detected failure with remaining attempts** → provide the condition-specific feedback and continue.
4. **Undetected failure under Condition A** → stop because no deployable feedback signal is available.
5. **Undetected failure under Condition B** → stop if the self-verifier returns `CONSISTENT` and the planning pipeline has no detectable error.
6. **Oracle-detected failure with remaining attempts** → provide the appropriate oracle feedback and continue.
7. **Four total generation attempts exhausted** → stop and retain the final candidate.

### Deployment-success signal

The definition of a deployment-success signal depends on the condition:

* **Condition A:** the generated PDDL passes the predefined static checks, parses/translates successfully, and the planner finds a solution. No ground-truth comparison is used.
* **Condition B:** the generated PDDL passes the same pipeline checks and the self-verifier returns `CONSISTENT`. No ground-truth comparison is used.
* **Resampling baseline:** the generated candidate passes the predefined deployable pipeline checks. No ground-truth comparison is used to select a candidate.
* **Oracle conditions:** the oracle feedback mechanism determines whether refinement continues; ground-truth-derived information is permitted because these are explicitly non-deployable oracle conditions.

A deployment-success signal therefore means:

> **The system has no condition-specific deployable signal indicating that further refinement is necessary.**

It does **not** mean that the candidate is known to be correct.

### Evaluation-time success

After the run stops, the retained candidate is independently evaluated using the established Phase 3 ground-truth evaluation procedure.

This determines whether the final candidate actually achieved the intended task.

Therefore, a run can legitimately have:

* **deployment-success signal = yes**
* **ground-truth task success = no**

This is an important expected outcome for semantically incorrect but planner-solvable PDDL.

Ground-truth evaluation must never alter the stopping decision for Conditions A, B, or the deployable resampling baseline.

---

## 14. Primary Exploratory Comparisons

The Phase 4 study does not make an inferential primary comparison because
each selected scenario-condition is run only once.

The main exploratory comparisons are performed within the labelled-image
condition:

1. self-verification refinement (B) versus the existing Phase 3
   attempt-1 outcome;
2. binary oracle refinement (O1) versus the existing Phase 3 attempt-1
   outcome;
3. specific-discrepancy oracle refinement (O3) versus the existing Phase 3
   attempt-1 outcome.

The existing Phase 3 results also provide offline evidence about realistic
pipeline feedback (A). In particular, the seven labelled semantic failures
that produced PDDL were all accepted by the parser, translator, and
planner. Therefore, Condition A provides no deployable feedback signal for
those seven cases and requires no additional API calls.

The deployable resampling baseline is also evaluated conceptually from the
existing Phase 3 outputs where the candidate already passes the deployable
pipeline checks. Such a candidate would stop at attempt 1 under the
predefined resampling stopping rule, so no additional resampling call is
required for those cases.

Results are reported descriptively using counts and proportions. No
p-values, confidence intervals, or claims of statistical significance are
reported for the exploratory Phase 4 study.

---

## 15. Detection and Repair Metrics

### Detection rate

[
Detection\ Rate =
\frac{Initial\ failures\ detected\ by\ the\ condition}
{All\ initial\ failures}
]

### Repair rate

[
Repair\ Rate =
\frac{Detected\ failures\ subsequently\ repaired}
{Detected\ failures}
]

### Overall final success

[
Final\ Success\ Rate =
\frac{Scenarios\ successful\ after\ the\ complete\ protocol}
{All\ evaluated\ scenarios}
]

### Attempt-wise success

Report cumulative success after:

* attempt 1;
* attempt 2;
* attempt 3;
* attempt 4.

---

## 16. Repeated Runs and Statistical Treatment

Each selected scenario-condition is evaluated once in the resource-
constrained exploratory Phase 4 study.

The study therefore does not estimate sampling variance through repeated
runs and does not treat individual attempts as independent observations.

Results are reported descriptively using:

- number of scenarios initially successful;
- number of failures detected;
- number of failures repaired;
- final number of successful scenarios;
- proportion repaired among detected failures;
- attempts used;
- per-attempt success counts;
- latency and API call counts.

No inferential statistical testing is performed for Phase 4.

The absence of repeated runs is treated as a limitation and is explicitly
reported when interpreting the results.
---

## 17. Development and Selected Phase 4 Cases

Phase 3 scenarios 001–003 were used during development and prompt
inspection.

Phase 4 does not run a new experiment across all 27 scenarios. Instead,
the resource-constrained exploratory study selects the 12 non-ambiguous
labelled-condition failures observed in Phase 3:

- 4 `MISSING_FACT` failures;
- 3 `WRONG_GOAL` failures;
- 5 unexpected clarification failures.

These cases are selected because they represent the failure modes targeted
by the Phase 4 refinement mechanisms.

The selected cases are not treated as a randomly sampled or statistically
representative subset of the Phase 3 dataset. Selection based on observed
failure is explicitly acknowledged as a source of selection bias.

Phase 4 results are therefore reported as an exploratory case-based
analysis of these selected failures rather than as a confirmatory estimate
of performance across the full Phase 3 dataset.

---

## 18. Exploratory Hypotheses

### H1 — Realistic feedback

> Realistic pipeline feedback will provide little improvement in the
> labelled condition because the seven Phase 3 labelled semantic failures
> that produced PDDL were accepted by the parser, translator, and planner.

This hypothesis is assessed primarily through the offline Phase 3
evidence for Condition A.

### H2 — Self-verification

> Self-verification may detect some semantic failures that are invisible to
> parser, translator, and planner feedback.

The Phase 4 B condition provides an exploratory assessment of this
possibility.

### H3 — Oracle feedback

> Oracle feedback may provide information that enables refinement of
> failures that are not detectable through realistic pipeline feedback.

The executed oracle conditions are O1 binary feedback and O3
specific-discrepancy feedback for PDDL-producing semantic failures.

These hypotheses are exploratory and are not subjected to inferential
statistical testing.

---

## 19. Logging Requirements

Every generation attempt must log at least:

* scenario ID;
* condition;
* repeat number;
* attempt number;
* input instruction;
* model identifier;
* temperature;
* whether image was supplied;
* generated raw response;
* extracted PDDL or clarification;
* parse status;
* static-check status;
* translator status;
* planner status;
* planner result;
* VAL status for evaluation;
* task-level success;
* failure category;
* feedback source;
* feedback text;
* detected-failure status;
* refinement triggered;
* stopping reason;
* VLM latency;
* planner latency;
* VAL latency;
* total attempt latency;
* plan length/cost where applicable.

For Condition B, also log:

* verifier response;
* verifier reason;
* verifier latency.

The raw VLM response and exact feedback text must be retained.

---

## 20. Ground-Truth Isolation Test

The implementation must ensure that ground-truth files are never passed to prompt builders for Conditions A or B.

A test should inspect the generated prompt strings and verify that they do not contain:

* contents of `gt_problem.pddl`;
* ground-truth fact lists;
* VAL ground-truth comparison output;
* other hidden ground-truth representations.

Oracle conditions are exempt because ground-truth-derived feedback is their defined experimental manipulation.

---
## 21. Phase 4 Executed Experimental Scope

The executed Phase 4 exploratory study is restricted to the **labelled-image
condition** and reuses the existing Phase 3 outputs as attempt 1.

Because of the available API token budget, the executed refinement study is
restricted to **three selected semantic failure cases**, with one run per
case-condition. The cases are selected before the refinement runs according
to the following rule:

* **004** — a `MISSING_FACT` failure;
* **006** — a `WRONG_GOAL` failure;
* **007** — a `MISSING_FACT` failure.

This selection covers both semantic failure types represented among the
seven non-ambiguous labelled semantic failures. Scenario 004 is also used
as the Phase 4 pilot case; this is reported explicitly and all three cases
are treated as exploratory rather than as an independent confirmatory
sample.

The executed refinement conditions are:

1. **O1 — binary oracle feedback**;
2. **O3 — specific-discrepancy oracle feedback**;
3. **B — self-verification**.

Each selected case is run once under each of the three conditions, giving a
maximum of:

* 3 selected cases × 3 conditions = **9 refinement runs**.

The five unexpected clarification cases are **not included in the Phase 4
refinement runs**. Their treatment is outside the executed refinement scope
because the implemented B and oracle feedback study was designed around an
existing generated PDDL/task representation, while these cases produced
unexpected clarification responses rather than PDDL candidates. They remain
documented as unresolved Phase 3 failures.

Condition A requires no new API calls for the seven semantic Phase 3
failures because:

* all seven semantic PDDL failures were accepted by the parser, translator,
  and planner;
* consequently, realistic deployment-time pipeline feedback detected 0/7
  of these semantic failures.

The deployable resampling baseline likewise requires no additional generation
for cases whose existing Phase 3 candidate already passes the deployable
pipeline checks.

The following originally proposed components are not executed in this
resource-constrained study:

* O2 category-level oracle feedback;
* pass@4;
* additional repeated runs;
* refinement on the other four semantic failure cases unless additional
(.venv) surya@LAPTOP-5H00F030:~/dissertation/vlm/vlm-pddl$ sed -n '870,940p' docs/phase4_protocol.md
9 \times 3 = 27
$$

because each run may use up to three new refinement generation attempts
after the reused Phase 3 attempt 1.

Condition B additionally requires a verification call for generated
candidates that reach the verification stage. Therefore, total API calls
and token consumption may exceed the generation-call count alone. Actual
API usage, token consumption, rate-limit events, retries, early stopping,
and incomplete conditions must be recorded.

The token-budget guard remains active throughout execution. The runner must
not silently continue after a rate-limit or token-budget failure, and
incomplete runs must be retained and reported transparently.

The experimental execution priority is:

1. **Pilot: O1 on scenario 004**, to measure actual per-call token growth
   under refinement history;
2. **O1 on scenarios 006 and 007**;
3. **O3 on scenarios 004, 006, and 007**;
4. **B on scenarios 004, 006, and 007**;
5. If sufficient API budget remains after the planned nine runs, additional
   O1 runs on the four remaining semantic failures may be performed as an
   explicitly labelled exploratory extension. They are not required for
   completion of the primary three-case study.

If API or token limits prevent completion, completed runs are retained and
reported transparently; incomplete conditions are not represented as
completed experiments.

---

## 22. Resource and Budget Constraint

The Phase 4 design was further reduced because the available API token
budget does not support the broader 31-run refinement scope within a single
experimental period.

A two-call representative API test using the Phase 3 labelled-image prompt
and scenario 004 measured **3,501 total tokens per generation call**, of
which 3,360 were prompt tokens and 141 were completion tokens. This
measurement is used as an empirical planning baseline rather than as a
guaranteed fixed cost for all later calls, because refinement chains retain
conversation history and therefore may consume progressively more input
tokens.

The executed design therefore limits the new refinement study to three
selected cases and one run per case-condition.

The maximum number of new generation calls for the nine planned refinement
runs is:

$$
9 \times 3 = 27
$$

because each run may use up to three new refinement generation attempts
after the reused Phase 3 attempt 1.

Condition B additionally requires a verification call for generated
candidates that reach the verification stage. Therefore, total API calls
and token consumption may exceed the generation-call count alone. Actual
API usage, token consumption, rate-limit events, retries, early stopping,
and incomplete conditions must be recorded.

The token-budget guard remains active throughout execution. The runner must
not silently continue after a rate-limit or token-budget failure, and
incomplete runs must be retained and reported transparently.

The experimental execution priority is:

1. **Pilot: O1 on scenario 004**, to measure actual per-call token growth
   under refinement history;
2. **O1 on scenarios 006 and 007**;
3. **O3 on scenarios 004, 006, and 007**;
4. **B on scenarios 004, 006, and 007**;
5. If sufficient API budget remains after the planned nine runs, additional
   O1 runs on the four remaining semantic failures may be performed as an
   explicitly labelled exploratory extension. They are not required for
   completion of the primary three-case study.

If API or token limits prevent completion, completed runs are retained and
reported transparently; incomplete conditions are not represented as
completed experiments.

---

## 23. Protocol Deviations and Resource Constraints

The originally specified Phase 4 protocol included:

* three repeated runs per scenario-condition;
* independent four-attempt resampling;
* pass@4;
* oracle feedback levels O1, O2, and O3;
* refinement across the broader image conditions;
* refinement of the full set of selected Phase 3 failures.

The full design was not executed because of available API rate and token
constraints and the limited experimental period.

The executed exploratory study therefore:

* reuses the existing Phase 3 labelled output as attempt 1;
* uses one run per selected scenario-condition;
* restricts the primary refinement study to scenarios **004, 006, and
  007**;
* includes both `MISSING_FACT` and `WRONG_GOAL` semantic failure types;
* evaluates binary oracle feedback (O1);
* evaluates specific-discrepancy oracle feedback (O3);
* evaluates self-verification (B);
* omits O2 and pass@4;
* does not perform additional independent repeats;
* does not regenerate Phase 3 attempt 1;
* does not perform additional Phase 4 refinement in the normal-image or
  no-image conditions;
* excludes the five unexpected clarification failures from the executed
  refinement study.

Scenario 004 is used as the pilot case. Its pilot status is disclosed in
the reporting, and the three selected cases are treated as an exploratory
case study rather than as a statistically representative sample.

The seven labelled semantic failures provide an offline result for
Condition A: all seven passed the deployable parser, translator, and
planner pipeline, so realistic pipeline feedback detected **0/7** of these
semantic failures. This result uses the complete set of seven semantic
labelled failures and does not depend on the three-case Phase 4 sample.

The five unexpected clarification failures likewise produced no parser,
translator, or planner error signal and are not included in the executed
refinement study.

The selection of Phase 4 cases from observed Phase 3 failures introduces
selection bias: the cases were selected because they had already exhibited
failure, and the resulting refinement outcomes cannot be interpreted as an
estimate of general refinement success on new or randomly selected tasks.

Accordingly, the three-case Phase 4 results are reported as an **exploratory
case study of the refinement mechanism**. Results are presented per chain,
including feedback received, model changes, number of attempts, API usage,
and whether the resulting candidate passed the relevant evaluation
procedure. No success rates, confidence intervals, p-values, statistical
significance tests, or claims that refinement improves overall task success
are reported from the three-case sample.

The principal quantitative observation concerning realistic deployment-time
feedback remains the offline finding that it detected **0/7** of the seven
semantic labelled Phase 3 failures.
