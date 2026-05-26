import subprocess
from dataclasses import dataclass
from pathlib import Path

from skill_optimizer.config import ModelConfig
from skill_optimizer.files import write_text_artifact


@dataclass(frozen=True)
class RunResult:
    stdout: str
    stderr: str
    return_code: int
    run_dir: Path


def run_claude_prompt(
    model_config: ModelConfig,
    prompt: str,
    run_dir: Path,
    timeout_seconds: int,
    extra_args: list[str] | None = None,
) -> RunResult:
    run_dir.mkdir(parents=True, exist_ok=True)
    write_text_artifact(run_dir / "prompt.txt", prompt)

    args = [model_config.command]
    if extra_args:
        args.extend(extra_args)
    if model_config.model:
        args.extend(["--model", model_config.model])
    args.extend(["-p", prompt])

    try:
        completed = subprocess.run(
            args,
            cwd=run_dir,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        return_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = f"Command timed out after {timeout_seconds} seconds"
        return_code = 124
    except FileNotFoundError as exc:
        stdout = ""
        stderr = str(exc)
        return_code = 127

    write_text_artifact(run_dir / "stdout.txt", stdout)
    write_text_artifact(run_dir / "stderr.txt", stderr)
    write_text_artifact(run_dir / "return_code.txt", str(return_code))
    return RunResult(stdout=stdout, stderr=stderr, return_code=return_code, run_dir=run_dir)


def build_skill_execution_prompt(skill_content: str, user_prompt: str) -> str:
    return (
        "You are evaluating the following Claude SKILL instructions.\n\n"
        "<skill>\n"
        f"{skill_content}\n"
        "</skill>\n\n"
        "Apply the skill to this user request:\n\n"
        f"{user_prompt}\n"
    )
