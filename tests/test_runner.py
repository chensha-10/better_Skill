import sys
import tempfile
import unittest
from subprocess import CompletedProcess
from unittest.mock import patch
from pathlib import Path

from skill_optimizer.config import ModelConfig
from skill_optimizer.runner import build_skill_execution_prompt, run_claude_prompt


class RunnerTests(unittest.TestCase):
    def test_run_claude_prompt_captures_stdout_stderr_and_exit_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            model_config = ModelConfig(command=sys.executable, model="")
            script = "import sys; print('ok'); print('warn', file=sys.stderr)"

            result = run_claude_prompt(model_config, "ignored prompt", run_dir, 30,
                                       extra_args=["-c", script])

            self.assertEqual(result.return_code, 0)
            self.assertEqual(result.stdout.strip(), "ok")
            self.assertEqual(result.stderr.strip(), "warn")
            self.assertEqual((run_dir / "stdout.txt").read_text(encoding="utf-8").strip(), "ok")
            self.assertEqual((run_dir / "stderr.txt").read_text(encoding="utf-8").strip(), "warn")
            self.assertIn("ignored prompt", (run_dir / "prompt.txt").read_text(encoding="utf-8"))

    def test_run_claude_prompt_records_timeout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            model_config = ModelConfig(command=sys.executable, model="")
            script = "import time; time.sleep(3)"

            result = run_claude_prompt(model_config, "prompt", run_dir, 1,
                                       extra_args=["-c", script])

            self.assertNotEqual(result.return_code, 0)
            self.assertIn("timed out", result.stderr.lower())

    def test_run_claude_prompt_uses_cwd_for_file_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            model_config = ModelConfig(command=sys.executable, model="")
            script = "import os; print(os.getcwd())"

            result = run_claude_prompt(model_config, "prompt", run_dir, 30,
                                       extra_args=["-c", script])

            self.assertEqual(Path(result.stdout.strip()), run_dir)

    def test_build_skill_execution_prompt_includes_skill_and_user_prompt(self):
        skill = "---\nname: test\ndescription: a test skill\n---\n\nBe helpful."
        user = "answer the question"

        system_prompt, user_prompt = build_skill_execution_prompt(skill, user)

        self.assertIn("Be helpful.", system_prompt)
        self.assertIn("answer the question", user_prompt)

    def test_run_claude_prompt_uses_non_shell_invocation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            model_config = ModelConfig(command=sys.executable, model="")

            with patch("skill_optimizer.runner.subprocess.run") as mock_run:
                mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")

                result = run_claude_prompt(model_config, "prompt", run_dir, 30)

            self.assertEqual(result.return_code, 0)
            self.assertFalse(mock_run.call_args.kwargs["shell"])

    def test_run_claude_prompt_fails_fast_for_missing_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            model_config = ModelConfig(command="definitely_missing_command_12345", model="")

            with patch("skill_optimizer.runner.subprocess.run", side_effect=AssertionError("subprocess.run should not be called")) as mock_run:
                result = run_claude_prompt(model_config, "prompt", run_dir, 30)

            self.assertEqual(result.return_code, 127)
            self.assertIn("not found", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
