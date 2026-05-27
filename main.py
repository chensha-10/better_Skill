import argparse
from pathlib import Path
from typing import Any

from skill_optimizer.cases import create_case_template
from skill_optimizer.config import Config, build_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optimize Claude SKILL.md with test cases")

    # Global path overrides (before subcommands)
    parser.add_argument("--project-root", help="Project root directory (default: script location)")
    parser.add_argument("--config", dest="config_file", help="Path to skill_optimizer.json config file")
    parser.add_argument("--skill-path", help="Path to SKILL.md")
    parser.add_argument("--workspace-dir", help="Workspace directory")
    parser.add_argument("--test-cases-dir", help="Test cases directory")
    parser.add_argument("--runs-dir", help="Runs output directory")
    parser.add_argument("--backups-dir", help="Backups directory")

    subparsers = parser.add_subparsers(dest="command")

    init_case = subparsers.add_parser("init-case", help="Create a test case directory template")
    init_case.add_argument("case_name")
    init_case.add_argument("--type", dest="case_type", choices=["text", "files", "mixed"], default="mixed")
    init_case.add_argument("--min-score", type=float, default=0.85)
    init_case.add_argument("--timeout", type=int, default=300)
    init_case.add_argument("--with-input-files", action="store_true", default=False,
                           help="Create an input_files/ directory in the case template")

    return parser


def _extract_cli_overrides(args: argparse.Namespace) -> dict[str, Any]:
    """Extract non-None path overrides from parsed CLI args."""
    path_keys = ["skill_path", "workspace_dir", "test_cases_dir", "runs_dir", "backups_dir"]
    return {k: v for k in path_keys if (v := getattr(args, k, None)) is not None}


def handle_init_case(args: argparse.Namespace, config: Config) -> int:
    try:
        case_dir = create_case_template(
            config.test_cases_dir,
            args.case_name,
            args.case_type,
            args.min_score,
            args.timeout,
            with_input_files=args.with_input_files,
        )
    except FileExistsError as exc:
        print(str(exc))
        return 1
    except ValueError as exc:
        print(str(exc))
        return 1

    print(f"Created test case: {case_dir}")
    return 0


def _evaluate_text_score(
    result_stdout: str,
    expected_text_path: Path,
    case_run_dir: Path,
    case_timeout_seconds: int,
    judge_args: list[str],
    judge_config: Any,
) -> float | None:
    """Return text similarity score or None if not applicable."""
    from skill_optimizer.judge import build_judge_prompt, parse_judge_output, judge_text_simple
    from skill_optimizer.runner import run_claude_prompt

    expected_text = expected_text_path.read_text(encoding="utf-8").strip()
    if not expected_text:
        return None
    simple = judge_text_simple(result_stdout.strip(), expected_text)
    if simple is not None:
        return simple.score
    judge_prompt = build_judge_prompt(result_stdout.strip(), expected_text)
    judge_run_dir = case_run_dir / "judge"
    judge_result = run_claude_prompt(
        judge_config, judge_prompt, judge_run_dir,
        case_timeout_seconds, extra_args=judge_args,
    )
    if judge_result.return_code == 0:
        parsed = parse_judge_output(judge_result.stdout.strip())
        return parsed.score
    return None


def _evaluate_file_result(expected_files_dir: Path, case_run_dir: Path) -> Any:
    """Return file comparison result or None if not applicable."""
    from skill_optimizer.files import compare_expected_files
    return compare_expected_files(expected_files_dir, case_run_dir)


def _apply_revision(
    config: Config,
    skill_content: str,
    failure_summary: str,
    revision_dir: Path,
    reviser_args: list[str],
) -> int:
    """Generate and apply SKILL revision. Returns 0 on success, 1 on failure."""
    from skill_optimizer.files import backup_file
    from skill_optimizer.optimizer import build_revision_prompt, validate_skill_revision
    from skill_optimizer.runner import run_claude_prompt

    backup_file(config.skill_path, config.backups_dir)

    revision_result = run_claude_prompt(
        config.reviser,
        build_revision_prompt(
            skill_content, failure_summary,
            str(config.skill_path),
        ),
        revision_dir,
        config.default_case_timeout_seconds,
        extra_args=reviser_args, allow_tools=False,
        cwd_override=config.project_root,
    )
    if revision_result.return_code != 0:
        print(f"Revision generation failed: {revision_result.stderr}")
        return 1

    new_skill = revision_result.stdout.strip()
    validate_skill_revision(new_skill, skill_content)
    config.skill_path.write_text(new_skill, encoding="utf-8")
    print("Applied revised SKILL.md (from stdout)")
    return 0


def _evaluate_cases(
    config: Config,
    cases: list,
    skill_content: str,
    iteration_dir: Path,
    exec_args: list[str],
    judge_args: list[str],
) -> tuple[int, int, list[float], list[str]]:
    """Run all cases for one iteration. Returns (passed_count, total, scores, failure_details)."""
    from skill_optimizer.files import compare_expected_files, copy_input_files
    from skill_optimizer.judge import combine_scores, judge_text_simple, parse_judge_output
    from skill_optimizer.runner import build_skill_execution_prompt, run_claude_prompt

    passed_count = 0
    scores: list[float] = []
    failure_details: list[str] = []

    for case in cases:
        case_run_dir = iteration_dir / case.name
        if case.input_files_dir is not None:
            copy_input_files(case.input_files_dir, case_run_dir)
        prompt = case.prompt_path.read_text(encoding="utf-8")
        input_files = None
        if case.input_files_dir is not None:
            input_files = {}
            for f in sorted(case.input_files_dir.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(case.input_files_dir).as_posix()
                    input_files[rel] = f.read_text(encoding="utf-8")
        system_prompt, user_prompt = build_skill_execution_prompt(skill_content, prompt, input_files)
        result = run_claude_prompt(
            config.executor, user_prompt, case_run_dir,
            case.timeout_seconds, extra_args=exec_args,
            system_prompt=system_prompt,
        )

        if result.return_code != 0:
            scores.append(0.0)
            failure_details.append(f"{case.name}: execution failed (rc={result.return_code})")
            continue

        text_score = None
        if case.expected_text_path is not None:
            text_score = _evaluate_text_score(
                result.stdout, case.expected_text_path, case_run_dir,
                case.timeout_seconds, judge_args, config.judge,
            )

        file_result = None
        if case.expected_files_dir is not None:
            file_result = _evaluate_file_result(case.expected_files_dir, case_run_dir)

        score, passed = combine_scores(text_score=text_score, file_result=file_result, min_score=case.min_score)
        scores.append(score)
        if passed:
            passed_count += 1
        else:
            failure_details.append(f"{case.name}: score={score:.2f} (threshold={case.min_score})")

    return passed_count, len(cases), scores, failure_details


def run_optimization(
    config: Config,
    extra_executor_args: list[str] | None = None,
    extra_judge_args: list[str] | None = None,
    extra_reviser_args: list[str] | None = None,
    max_iterations_override: int | None = None,
) -> int:
    from skill_optimizer.cases import load_cases
    from skill_optimizer.files import backup_file, create_iteration_dir
    from skill_optimizer.optimizer import build_revision_prompt, validate_skill_revision
    from skill_optimizer.runner import run_claude_prompt

    if not config.skill_path.is_file():
        print(f"Missing SKILL.md: {config.skill_path}")
        return 1

    cases = load_cases(
        config.test_cases_dir,
        default_min_score=config.score_threshold,
        default_timeout_seconds=config.default_case_timeout_seconds,
    )
    if not cases:
        print(f"No test cases found in: {config.test_cases_dir}")
        return 1

    max_iterations = max_iterations_override or config.max_iterations
    exec_args = extra_executor_args or []
    judge_args = extra_judge_args or []
    reviser_args = extra_reviser_args or []

    for iteration in range(1, max_iterations + 1):
        iteration_dir = create_iteration_dir(config.runs_dir, iteration)
        skill_content = config.skill_path.read_text(encoding="utf-8")

        passed_count, total, scores, failures = _evaluate_cases(
            config, cases, skill_content, iteration_dir, exec_args, judge_args,
        )
        average_score = sum(scores) / len(scores) if scores else 0.0
        print(f"Iteration {iteration}/{max_iterations}: passed {passed_count}/{total}, avg score {average_score:.2f}")

        if passed_count == total and average_score >= config.score_threshold:
            print("All cases passed.")
            return 0

        if iteration == max_iterations:
            print(f"Failed to reach threshold after {max_iterations} iterations.")
            return 1

        # --- Generate and apply revision ---
        failure_summary = "; ".join(failures) if failures else f"avg score {average_score:.2f} below threshold"
        revision_dir = iteration_dir / "revision"
        try:
            result = _apply_revision(config, skill_content, failure_summary, revision_dir, reviser_args)
            if result != 0:
                return result
        except Exception as exc:
            print(f"Revision failed: {exc}")
            return 1

    return 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else Path(__file__).resolve().parent
    config_file = Path(args.config_file) if args.config_file else None
    cli_overrides = _extract_cli_overrides(args)

    config = build_config(
        project_root=project_root,
        config_file_path=config_file,
        cli_overrides=cli_overrides,
    )

    if args.command == "init-case":
        return handle_init_case(args, config)
    return run_optimization(config)


if __name__ == "__main__":
    raise SystemExit(main())
