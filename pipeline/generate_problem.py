import os
import base64
import re
import subprocess
import sys
import time
from pathlib import Path

from openai import OpenAI


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "qwen/qwen3.8-27b"

DOMAIN_FILE = Path("domain/household.pddl")
PROBLEM_FILE = Path("problems/generated_001.pddl")
RESULT_FILE = Path("results/generated_001.txt")

FAST_DOWNWARD = Path.home() / "downward" / "fast-downward.py"


# ============================================================
# GROQ CLIENT
# ============================================================

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


# ============================================================
# IMAGE ENCODING
# ============================================================

def encode_image(path):

    with open(path, "rb") as image_file:
        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


# ============================================================
# PROMPT
# ============================================================
def build_prompt(domain_text, instruction):

    return f"""
You are a STRICT visual-to-PDDL translator for a household robot.

Your job is to translate the household scene and the user's
natural-language task into ONE syntactically valid PDDL problem.

You must faithfully represent:

1. The actual scene shown in the image.
2. The COMPLETE meaning of the user's task.

============================================================
FIXED PDDL DOMAIN
============================================================

The following PDDL domain is FIXED.

Use ONLY the types, predicates, and actions defined in it.

Do NOT modify the domain.

Do NOT invent:

- predicates
- actions
- types
- objects
- locations
- relationships

FIXED DOMAIN:

{domain_text}

============================================================
SCENE
============================================================

Use the image as the primary source of truth.

The scene contains:

- kitchen
- living room
- one table
- mug
- kettle
- robot

Scene facts:

- kitchen is on the left
- living room is on the right
- the kitchen and living room are connected by an opening
- the table is in the kitchen
- the mug is on the table
- the kettle is on the table
- the robot is in the living room

There is NO table in the living room.

There is NO bedroom.

NEVER invent an object or location that is not present.

NEVER invent a second table.

NEVER invent a connection that is not supported by the scene.

============================================================
USER TASK
============================================================

The exact user task is:

{instruction}

You MUST preserve the complete meaning of this task.

Do NOT silently simplify it.

Do NOT replace a destination with another destination.

Do NOT remove constraints.

Do NOT ignore words that change the requested result.

In particular, distinguish carefully between:

"bring the mug to the living room"

and

"bring the mug to the living room table"

The first requests the living room as the destination.

The second refers to a specific table in the living room.

If a requested destination object does NOT exist in the scene,
DO NOT invent that object.

============================================================
TASK ANALYSIS
============================================================

Before producing PDDL, internally determine:

1. What object is being moved?
2. Where is that object initially?
3. Is the task requesting a location?
4. Is the task requesting a specific object or surface?
5. Are there additional constraints?
6. Does the requested object/location/surface actually exist?
7. Can the complete task be represented by the fixed domain?

Never change the scene to make the task possible.

============================================================
PDDL REPRESENTATION
============================================================

The output MUST be a complete PDDL problem.

Use exactly this overall structure:

(define (problem problem-name)
  (:domain household)

  (:objects
    ...
  )

  (:init
    ...
  )

  (:goal
    ...
  )
)

The outer (define ...) wrapper is REQUIRED.

The problem MUST contain:

- exactly one (:domain household)
- one (:objects ...) section
- one (:init ...) section
- one (:goal ...) section

Every object used in a predicate must be declared.

Every location must have type location.

Every physical object must have type object.

Use the exact predicate names from the supplied domain.

============================================================
SCENE CONSISTENCY CHECK
============================================================

Before returning the answer, verify:

1. Every object exists in the scene.
2. Every location exists in the scene.
3. No invented furniture exists.
4. No invented rooms exist.
5. Every connection is supported by the scene.
6. Every initial-state fact is supported by the scene.
7. Every predicate exists in the domain.
8. The user's requested object is preserved.
9. The user's requested destination is preserved.
10. Specific destination surfaces are not replaced by locations.
11. Additional task constraints are not silently removed.
12. Impossible or unrepresentable requirements are NOT solved by
    inventing objects or facts.
13. The PDDL is syntactically valid.
14. Parentheses are balanced.
15. The outer (define ...) wrapper is present.
16. The domain name is household.

============================================================
OUTPUT
============================================================

Return ONLY the complete PDDL problem.

Do NOT return:

- explanations
- comments
- markdown
- code fences
- JSON
- <think> tags
- analysis

Return ONLY the PDDL problem.
"""

# ============================================================
# EXTRACT PDDL
# ============================================================

def extract_pddl(text):

    # If the model nevertheless uses a code block,
    # remove it.

    match = re.search(
        r"```(?:pddl|lisp)?\s*(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return text.strip()


# ============================================================
# QUERY VLM
# ============================================================

def query_vlm(image_path, domain_text, instruction):

    image_data = encode_image(image_path)

    prompt = build_prompt(
        domain_text,
        instruction
    )

    response = client.chat.completions.create(

        model=MODEL,

        messages=[
            {
                "role": "user",
                "content": [

                    {
                        "type": "text",
                        "text": prompt
                    },

                    {
                        "type": "image_url",
                        "image_url": {
                            "url":
                            f"data:image/png;base64,{image_data}"
                        }
                    }

                ]
            }
        ],

        temperature=0,

        max_tokens=1000,

        reasoning_effort="none"
    )

    output = response.choices[0].message.content

    return extract_pddl(output)


# ============================================================
# RUN FAST DOWNWARD
# ============================================================

def run_planner(domain, problem):

    result = subprocess.run(

        [
            sys.executable,
            str(FAST_DOWNWARD),
            str(domain),
            str(problem),
            "--search",
            "astar(lmcut())"
        ],

        capture_output=True,

        text=True,

        timeout=60
    )

    return (
        result.returncode,
        result.stdout + result.stderr
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) < 3:

        print(
            "Usage:\n"
            "python pipeline/generate_problem.py "
            "<image> \"<instruction>\""
        )

        sys.exit(1)


    image_path = Path(sys.argv[1])

    instruction = sys.argv[2]


    if not DOMAIN_FILE.exists():

        print(
            f"ERROR: Domain file not found: "
            f"{DOMAIN_FILE}"
        )

        sys.exit(1)


    if not image_path.exists():

        print(
            f"ERROR: Image file not found: "
            f"{image_path}"
        )

        sys.exit(1)


    if not os.getenv("GROQ_API_KEY"):

        print(
            "ERROR: GROQ_API_KEY environment variable "
            "is not set."
        )

        sys.exit(1)


    print("Reading domain...")

    domain_text = DOMAIN_FILE.read_text()


    print("Sending image + domain + task to Qwen-VL...")

    start_time = time.time()


    try:

        pddl = query_vlm(
            image_path,
            domain_text,
            instruction
        )

    except Exception as e:

        print("VLM ERROR:")
        print(e)

        sys.exit(1)


    elapsed = time.time() - start_time


    print()
    print("Generated PDDL:")
    print("----------------------------------------")
    print(pddl)
    print("----------------------------------------")


    PROBLEM_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    PROBLEM_FILE.write_text(pddl)


    print()
    print(
        f"Saved generated problem to: "
        f"{PROBLEM_FILE}"
    )


    # ========================================================
    # RUN PLANNER
    # ========================================================

    print()
    print("Running Fast Downward...")


    try:

        code, log = run_planner(
            DOMAIN_FILE,
            PROBLEM_FILE
        )

    except subprocess.TimeoutExpired:

        print("Planner timed out.")

        sys.exit(1)


    print()
    print("========================================")
    print("RESULT")
    print("========================================")

    print(f"VLM generation time: {elapsed:.2f} seconds")
    print(f"Planner exit code:   {code}")

    print()
    print("Planner output:")
    print("----------------------------------------")

    print(log)

    print("----------------------------------------")
    
    # ========================================================
    # SAVE EXPERIMENT RESULT
    # ========================================================

    RESULT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result_text = f"""PHASE 1 EXPERIMENT

Task:
{instruction}

VLM generation time:
{elapsed:.2f} seconds

Generated PDDL:
----------------------------------------
{pddl}
----------------------------------------

Planner exit code:
{code}

Planner output:
----------------------------------------
{log}
----------------------------------------
"""

    RESULT_FILE.write_text(result_text)

    print()
    print(
        f"Saved experiment result to: "
        f"{RESULT_FILE}"
    )
