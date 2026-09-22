
````markdown
# VLM-to-PDDL Robotic Task Planning

Code and data accompanying the dissertation:

> **Planning Robot Tasks with Vision-Language Models: Automated PDDL Problem Generation for Robotic Task Execution**
> Surya Dhananjayan, MSc Artificial Intelligence, Aston University
> Academic year: 2025/26

This repository implements and evaluates a pipeline that translates a
rendered household scene image and a natural-language instruction into a
PDDL problem file using a Vision-Language Model (VLM), executes the result
with the Fast Downward planner, and validates the resulting plan against an
independently generated ground truth using VAL.

```text
Scene image + instruction  -->  VLM  -->  PDDL problem (or clarification request)
                                          -->  Fast Downward  -->  plan
                                          -->  VAL (checked against ground truth)
````

## Citing this repository

The code and data used for the dissertation results are pinned at the tag
`dissertation-submission`. Please refer to that tag, rather than the
`master` branch, when checking the submitted results.

```text
https://github.com/suryad8465/vlm-pddl/tree/dissertation-submission
```

## Repository structure

```text
vlm-pddl/
├── domain/
│   └── household.pddl              # Fixed PDDL domain (Dissertation Appendix A)
│
├── sim/                            # Scenario generation (Dissertation §3.4)
│   ├── state.py                    # Canonical SceneState representation
│   ├── pddl.py                     # Ground-truth PDDL generation
│   ├── render_scene.py             # Scene rendering
│   ├── instructions.py             # Instruction generation
│   ├── scenario.py                 # Scenario assembly
│   ├── generate_dataset.py         # Builds the 27-scenario dataset
│   ├── validate_dataset.py         # Fast Downward validation
│   ├── validate_val.py             # Fast Downward + VAL validation
│   └── io.py                       # SceneState JSON serialisation
│
├── scenarios/                      # The 27-scenario dataset
│   └── scenario_NNN/
│       ├── scene.png               # Unlabelled scene image
│       ├── scene_labelled.png      # Scene image with room labels
│       ├── instruction.txt         # Natural-language task instruction
│       ├── gt_problem.pddl         # Ground-truth PDDL problem
│       ├── state.json              # Symbolic scene state
│       ├── scenario.json           # Scenario metadata
│       └── plan.txt                # Fast Downward reference plan
│
├── pipeline/
│   ├── generate_problem.py         # Phase 1 preliminary pipeline
│   │
│   ├── phase3/                     # Phase 3 evaluation pipeline
│   │   ├── prompt.py               # Evaluation prompt
│   │   ├── runner.py               # Normal-condition runner
│   │   ├── runner_labelled.py      # Labelled-image runner
│   │   ├── runner_no_image.py      # No-image runner
│   │   ├── evaluate_state.py       # State-reconstruction diagnostics
│   │   └── evaluate_failures.py    # Failure taxonomy and evaluation
│   │
│   └── phase4/                     # Phase 4 exploratory refinement pilot
│       ├── api.py                  # API interaction helpers
│       ├── evaluation.py           # Phase 4 evaluation utilities
│       ├── prompts.py              # Refinement prompts
│       ├── runner.py               # Iterative refinement runner
│       ├── state_machine.py        # Refinement state machine
│       └── verifier.py             # Verification utilities
│
├── experiments/phase3/             # Phase 3 experimental outputs
│   ├── labelled/                   # Labelled-image experiments
│   ├── normal/                     # Unlabelled-image experiments
│   ├── no_image/                   # No-image experiments
│   └── *.csv                       # Supporting analysis tables
│
├── results/
│   ├── decision_log.md             # Phase 1 design decisions
│   └── phase4/                     # Phase 4 exploratory pilot output
│
├── docs/
│   └── phase4_protocol.md          # Frozen Phase 4 protocol
│
├── requirements.txt
└── .gitignore
```

## Environment

* Python 3.14.4
* WSL/Ubuntu
* Fast Downward, built locally
* VAL, built locally
* VLM: `qwen/qwen3.8-27b`
* Groq OpenAI-compatible API

The VLM requires a `GROQ_API_KEY` environment variable. No API key is
committed to this repository.

Fast Downward is invoked using:

```text
fast-downward.py <domain> <problem> --search "astar(lmcut())"
```

VAL is invoked using:

```text
Validate <domain> <problem> <plan>
```

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

The repository requirements are:

```text
openai==3.3.1
Pillow==12.3.0
numpy==2.5.3
pybullet==3.2.7
pytest==9.1.1
```

Fast Downward and VAL are external local executables and are not installed
by `requirements.txt`.

## Reproducing the results

### Generate the scenario dataset

```bash
python -m sim.generate_dataset
```

### Validate the ground-truth dataset

These commands operate on the ground-truth problems and make no VLM calls:

```bash
python -m sim.validate_dataset
python -m sim.validate_val
```

### Run Phase 3

The Phase 3 runners take the scenario ID as a positional argument.

For the normal condition:

```bash
python pipeline/phase3/runner.py scenario_001
```

A different experiment run identifier can be supplied with `--run-id`:

```bash
python pipeline/phase3/runner.py scenario_001 --run-id run_002
```

For the labelled-image condition:

```bash
python pipeline/phase3/runner_labelled.py scenario_001
```

For the no-image condition:

```bash
python pipeline/phase3/runner_no_image.py scenario_001
```

These commands require `GROQ_API_KEY` and make VLM API calls.

### Evaluate saved Phase 3 results

State reconstruction can be evaluated retrospectively from saved PDDL:

```bash
python pipeline/phase3/evaluate_state.py scenario_001
```

Failure classification operates on a saved Phase 3 result JSON:

```bash
python pipeline/phase3/evaluate_failures.py <result.json>
```

### Phase 4 exploratory pilot

The implemented Phase 4 runner currently supports the exploratory
`scenario_004` pilot:

```bash
python pipeline/phase4/runner.py scenario_004
```

An optional output directory can be supplied:

```bash
python pipeline/phase4/runner.py scenario_004 --output-dir <directory>
```

The Phase 4 pilot requires `GROQ_API_KEY` and makes VLM API calls.

## Key results

The main Phase 3 task-success results were:

| Condition                 | All scenarios (27) | Non-ambiguous (18) |
| ------------------------- | -----------------: | -----------------: |
| Normal (unlabelled image) |       9/27 (33.3%) |               0/18 |
| Labelled image            |      15/27 (55.6%) |               6/18 |
| No image                  |      12/27 (44.4%) |               3/18 |

Ambiguous-instruction handling was correct in 9/9 cases in every condition.

All seven of the labelled condition's PDDL-producing failures
(scenarios 004, 006, 007, 009, 013, 016, 018) were accepted by Fast
Downward as solvable. They were identified as incorrect through comparison
with the independently generated ground-truth problem. Planner success
alone therefore did not establish task-level correctness.

## Known limitations

See Dissertation §3.8 for the full limitations discussion. Key limitations
include:

* one VLM model;
* one run per scenario-condition for the headline evaluation;
* a single symbolic scene state underlying the three rendered layouts;
* 27 scenarios rather than the originally proposed 50;
* iterative refinement was designed and implemented as an exploratory pilot
  but was not fully executed;
* no PyBullet plan execution was used for final task validation; VAL was
  used against the ground-truth problem instead;
* scenarios 001-003 were used during prompt development and were therefore
  not strictly held out.
