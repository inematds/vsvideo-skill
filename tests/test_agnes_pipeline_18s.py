import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from skills.agnes.pipeline_18s import (
    HEIGHT,
    PHYSICS_LOCK,
    VIDEO_PROMPTS,
    WIDTH,
    ConsistencyError,
    _dimensions,
    _generate_stages,
    _normalize_reference,
    _write_report,
)


class FakeAgnesClient:
    def __init__(self) -> None:
        self.references = []

    def gerar_imagem(self, prompt, *, size, refs):
        self.references.append(tuple(refs))
        return f"image-{len(self.references)}".encode()


class AgnesPipelineTests(unittest.TestCase):
    def test_generates_backwards_with_original_as_first_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "stage-4-final-reference.png"
            reference.write_bytes(b"original")
            output = root / "output"
            output.mkdir()
            client = FakeAgnesClient()
            validated_pairs = []

            def approve(stage, earlier, later):
                validated_pairs.append((stage, earlier.name, later.name))
                return 0.9

            stages, metrics = _generate_stages(
                client,
                reference,
                output,
                validator=approve,
            )

            self.assertEqual([path.name for path in stages], [
                "stage-1.png",
                "stage-2.png",
                "stage-3.png",
                "stage-4-final-reference.png",
            ])
            self.assertEqual(
                validated_pairs,
                [
                    (3, "stage-3.png", "stage-4-final-reference.png"),
                    (2, "stage-2.png", "stage-3.png"),
                    (1, "stage-1.png", "stage-2.png"),
                ],
            )
            self.assertEqual([len(refs) for refs in client.references], [1, 2, 2])
            original_anchor = client.references[0][0]
            self.assertTrue(
                all(refs[0] == original_anchor for refs in client.references)
            )
            self.assertEqual(len(metrics), 3)

    def test_regenerates_a_stage_rejected_by_consistency_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "stage-4-final-reference.png"
            reference.write_bytes(b"original")
            output = root / "output"
            output.mkdir()
            client = FakeAgnesClient()
            attempts = 0

            def reject_twice(stage, earlier, later):
                nonlocal attempts
                attempts += 1
                if stage == 3 and attempts < 3:
                    raise ConsistencyError("deriva")
                return 0.9

            stages, _ = _generate_stages(
                client,
                reference,
                output,
                validator=reject_twice,
            )

            self.assertEqual(len(stages), 4)
            self.assertEqual(len(client.references), 5)

    def test_uses_best_attempt_after_third_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "stage-4-final-reference.png"
            reference.write_bytes(b"original")
            output = root / "output"
            output.mkdir()
            client = FakeAgnesClient()
            scores = iter((0.20, 0.40, 0.30))

            def reject_stage_three(stage, earlier, later):
                if stage == 3:
                    score = next(scores)
                    raise ConsistencyError("deriva", similarity=score)
                return 0.9

            stages, metrics = _generate_stages(
                client,
                reference,
                output,
                validator=reject_stage_three,
            )
            report = _write_report(output, metrics)

            self.assertEqual(stages[2].read_bytes(), b"image-2")
            self.assertEqual(metrics["stage-3-to-4"], 0.40)
            self.assertEqual(
                json.loads(report.read_text(encoding="utf-8"))["status"],
                "approved_with_warnings",
            )
            self.assertTrue((output / "consistency-warning.txt").is_file())

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg não instalado")
    def test_normalizes_reference_to_pipeline_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "reference.jpg"
            output = root / "output"
            output.mkdir()
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=white:s=626x417",
                    "-frames:v",
                    "1",
                    str(reference),
                ],
                check=True,
            )

            normalized = _normalize_reference(reference, output)

            self.assertEqual(_dimensions(normalized), (WIDTH, HEIGHT))

    def test_each_segment_has_own_prompt_and_requires_workers(self) -> None:
        self.assertEqual(len(set(VIDEO_PROMPTS)), 3)
        for prompt in VIDEO_PROMPTS:
            self.assertIn("Exactly two construction workers", prompt)
        self.assertIn("No worker or object may pass through", PHYSICS_LOCK)
        self.assertIn("exactly two adult construction workers", PHYSICS_LOCK)
        self.assertIn("both feet on the visible floor", PHYSICS_LOCK)


if __name__ == "__main__":
    unittest.main()
