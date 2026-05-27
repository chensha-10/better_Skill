import os
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
    allow_tools: bool = True,
    cwd_override: Path | None = None,
    system_prompt: str | None = None,
) -> RunResult:
    run_dir.mkdir(parents=True, exist_ok=True)
    write_text_artifact(run_dir / "prompt.txt", prompt)

    cwd = cwd_override if cwd_override is not None else run_dir

    args = [model_config.command]
    args.append("--disable-slash-commands")
    if allow_tools:
        args.append("--permission-mode")
        args.append("bypassPermissions")
    if extra_args:
        args.extend(extra_args)
    if model_config.model:
        args.extend(["--model", model_config.model])
    args.append("-p")

    env = os.environ.copy()
    if model_config.model:
        env["ANTHROPIC_MODEL"] = model_config.model

    # Combine system_prompt into the input to avoid Windows cmd.exe arg length limits
    combined_input = prompt
    if system_prompt:
        combined_input = f"{system_prompt}\n\n{prompt}"

    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env=env,
            encoding="utf-8",
            errors="replace",
            input=combined_input,
            shell=True,
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


def build_skill_execution_prompt(
    skill_content: str,
    user_prompt: str,
    input_files: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for skill execution."""
    system = skill_content

    parts = [user_prompt]
    if input_files:
        for filename, content in input_files.items():
            parts.append(f"\n<source path=\"{filename}\">\n{content}\n</source>\n")
    return system, "".join(parts)
