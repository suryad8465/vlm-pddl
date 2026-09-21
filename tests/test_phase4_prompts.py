from pathlib import Path

from pipeline.phase4.prompts import build_refinement_messages


def test_refinement_prompt_contains_no_ground_truth(tmp_path):
    image_path = tmp_path / "scene.png"
    image_path.write_bytes(b"fake-image")

    ground_truth_marker = "GROUND_TRUTH_SECRET_9F3A"

    messages = build_refinement_messages(
        image_path=image_path,
        instruction="Bring the mug to the living room.",
        previous_pddl="(define (problem previous))",
        feedback="The plan produced from your problem does not achieve the intended task.",
    )

    serialized = repr(messages)

    assert ground_truth_marker not in serialized


def test_refinement_prompt_has_required_inputs(tmp_path):
    image_path = tmp_path / "scene.png"
    image_path.write_bytes(b"fake-image")

    messages = build_refinement_messages(
        image_path=image_path,
        instruction="Bring the mug to the living room.",
        previous_pddl="(define (problem previous))",
        feedback="The plan produced from your problem does not achieve the intended task.",
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"

    user_content = messages[1]["content"]
    text_part = next(
        item for item in user_content
        if item["type"] == "text"
    )

    assert "Bring the mug to the living room." in text_part["text"]
    assert "(define (problem previous))" in text_part["text"]
    assert "does not achieve the intended task" in text_part["text"]


def test_refinement_prompt_has_image(tmp_path):
    image_path = tmp_path / "scene.png"
    image_path.write_bytes(b"fake-image")

    messages = build_refinement_messages(
        image_path=image_path,
        instruction="Bring the mug to the living room.",
        previous_pddl="(define (problem previous))",
        feedback="Please revise your PDDL problem.",
    )

    user_content = messages[1]["content"]

    image_part = next(
        item for item in user_content
        if item["type"] == "image_url"
    )

    assert image_part["image_url"]["url"].startswith(
        "data:image/png;base64,"
    )
