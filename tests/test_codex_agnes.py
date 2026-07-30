import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "skills" / "codex-agnes" / "rodar.py"
)
SPEC = importlib.util.spec_from_file_location("codex_agnes_rodar", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
codex_agnes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codex_agnes)

_codex_command = codex_agnes._codex_command
_generate_codex_stages = codex_agnes._generate_codex_stages
_image_prompt = codex_agnes._image_prompt


class CodexAgnesPipelineTests(unittest.TestCase):
    def test_command_uses_subscription_cli_and_isolated_workspace(self) -> None:
        work = Path("/tmp/job/codex-attempt")
        references = [Path("/tmp/job/final.png"), Path("/tmp/job/later.png")]

        command = _codex_command(
            binary="/usr/bin/codex",
            work_directory=work,
            references=references,
        )

        self.assertEqual(command[:2], ["/usr/bin/codex", "exec"])
        self.assertIn("--ephemeral", command)
        self.assertIn("workspace-write", command)
        self.assertNotIn("--ignore-user-config", command)
        self.assertEqual(command.count("--image"), 2)

    def test_prompt_requires_builtin_imagegen_and_saved_candidate(self) -> None:
        prompt = _image_prompt(2)

        self.assertIn("$imagegen", prompt)
        self.assertIn("candidate-source.png", prompt)
        self.assertIn("Image 1 is the immutable", prompt)
        self.assertIn("No people", prompt)

    def test_keeps_best_of_three_codex_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "stage-4-final-reference.png"
            reference.write_bytes(b"final")
            candidates = []

            def generate_candidate(**kwargs):
                attempt = kwargs["attempt"]
                candidate = root / f"candidate-{attempt}.png"
                candidate.write_bytes(f"candidate-{attempt}".encode())
                candidates.append(candidate)
                return candidate

            scores = iter((0.20, 0.40, 0.30, 0.90, 0.90))

            with (
                patch.object(
                    codex_agnes,
                    "_generate_candidate",
                    side_effect=generate_candidate,
                ),
                patch.object(
                    codex_agnes,
                    "_validate_pair",
                    side_effect=lambda *args: next(scores),
                ),
            ):
                stages, metrics = _generate_codex_stages(
                    binary="codex",
                    reference=reference,
                    output=root,
                    timeout_seconds=5,
                )

            self.assertEqual(stages[2].read_bytes(), b"candidate-2")
            self.assertEqual(metrics["stage-3-to-4"], 0.40)
            self.assertEqual(len(candidates), 5)


if __name__ == "__main__":
    unittest.main()
