#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.
"""

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import load_eval_set, parse_skill_md

# Resolve the launcher once. On Windows `claude` is a `.cmd`/`.CMD` shim, so a
# bare "claude" passed to subprocess.Popen fails with WinError 2 — shutil.which
# finds the real path (with extension) that CreateProcess can launch. Each
# ProcessPoolExecutor worker re-imports this module, so this runs per worker.
CLAUDE_BIN = shutil.which("claude") or "claude"


def find_project_root() -> Path:
    """Find the project root by walking up from cwd looking for .claude/.

    Mimics how Claude Code discovers its project root, so the temporary skill
    we create ends up where claude -p will look for it.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> dict:
    """Run a single query and return whether the skill was triggered.

    Creates a temporary skill in .claude/skills/ so it appears in Claude's
    available_skills list, then runs `claude -p` with the raw query.
    Uses --include-partial-messages to detect triggering early from
    stream events (content_block_start) rather than waiting for the
    full assistant message, which only arrives after tool execution.
    """
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    temp_skill_dir = Path(project_root) / ".claude" / "skills" / clean_name
    skill_file = temp_skill_dir / "SKILL.md"

    try:
        temp_skill_dir.mkdir(parents=True, exist_ok=True)
        # Use YAML block scalar to avoid breaking on quotes in description
        indented_desc = "\n  ".join(skill_description.split("\n"))
        skill_content = (
            f"---\n"
            f"name: {clean_name}\n"
            f"description: |\n"
            f"  {indented_desc}\n"
            f"---\n\n"
            f"# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n"
        )
        skill_file.write_text(skill_content, encoding="utf-8")

        cmd = [
            CLAUDE_BIN,
            "-p", query,
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])

        # Remove CLAUDECODE env var to allow nesting claude -p inside a
        # Claude Code session. The guard is for interactive terminal conflicts;
        # programmatic subprocess usage is safe.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=project_root,
            env=env,
        )

        triggered = False
        start_time = time.time()
        # Track state for stream event detection
        pending_tool_name = None
        accumulated_json = ""

        # Read stdout on a background thread and hand whole lines back via a
        # queue. This replaces a select()-based loop, which doesn't work on
        # Windows (select only accepts sockets there, not pipe FDs). The
        # stream-json output is newline-delimited, so iterating by line is
        # equivalent to the old manual buffer-splitting. A sentinel (None)
        # marks end-of-stream. get(timeout=...) keeps the overall timeout live
        # even when the child goes quiet.
        line_queue: queue.Queue = queue.Queue()

        def _reader() -> None:
            try:
                for raw in process.stdout:
                    line_queue.put(raw)
            finally:
                line_queue.put(None)

        reader_thread = threading.Thread(target=_reader, daemon=True)
        reader_thread.start()

        try:
            while time.time() - start_time < timeout:
                try:
                    raw = line_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                if raw is None:
                    break

                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Early detection via stream events
                if event.get("type") == "stream_event":
                    se = event.get("event", {})
                    se_type = se.get("type", "")

                    if se_type == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            tool_name = cb.get("name", "")
                            if tool_name in ("Skill", "Read"):
                                pending_tool_name = tool_name
                                accumulated_json = ""
                            else:
                                return {"triggered": False, "error": None}

                    elif se_type == "content_block_delta" and pending_tool_name:
                        delta = se.get("delta", {})
                        if delta.get("type") == "input_json_delta":
                            accumulated_json += delta.get("partial_json", "")
                            if clean_name in accumulated_json:
                                return {"triggered": True, "error": None}

                    elif se_type in ("content_block_stop", "message_stop"):
                        if pending_tool_name:
                            return {"triggered": clean_name in accumulated_json, "error": None}
                        if se_type == "message_stop":
                            return {"triggered": False, "error": None}

                # Fallback: full assistant message
                elif event.get("type") == "assistant":
                    message = event.get("message", {})
                    for content_item in message.get("content", []):
                        if content_item.get("type") != "tool_use":
                            continue
                        tool_name = content_item.get("name", "")
                        tool_input = content_item.get("input", {})
                        if tool_name == "Skill" and clean_name in tool_input.get("skill", ""):
                            triggered = True
                        elif tool_name == "Read" and clean_name in tool_input.get("file_path", ""):
                            triggered = True
                        return {"triggered": triggered, "error": None}

                elif event.get("type") == "result":
                    if event.get("is_error"):
                        reason = event.get("terminal_reason") or event.get("subtype") or "unknown_error"
                        status = event.get("api_error_status")
                        message = event.get("result") or event.get("error") or ""
                        error = f"claude result error: {reason}"
                        if status:
                            error += f" ({status})"
                        if message:
                            error += f": {message}"
                        return {"triggered": False, "error": error}
                    return {"triggered": triggered, "error": None}

                elif event.get("type") == "rate_limit_event":
                    info = event.get("rate_limit_info", {})
                    rate_type = info.get("rateLimitType", "unknown")
                    resets_at = info.get("resetsAt")
                    error = f"claude rate limit: {rate_type}"
                    if resets_at:
                        error += f", resetsAt={resets_at}"
                    return {"triggered": False, "error": error}
        finally:
            # Clean up process on any exit path (return, exception, timeout)
            if process.poll() is None:
                process.kill()
                process.wait()

        return {"triggered": triggered, "error": "timeout waiting for claude stream"}
    finally:
        if temp_skill_dir.exists():
            shutil.rmtree(temp_skill_dir)


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results."""
    results = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_errors: dict[str, list[str]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
                query_errors[query] = []
            try:
                run_result = future.result()
                query_triggers[query].append(bool(run_result.get("triggered")))
                if run_result.get("error"):
                    query_errors[query].append(run_result["error"])
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_triggers[query].append(False)
                query_errors[query].append(str(e))

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        result = {
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass,
        }
        if query_errors.get(query):
            result["errors"] = query_errors[query]
        results.append(result)

    passed = sum(1 for r in results if r["pass"])
    errored = sum(1 for r in results if r.get("errors"))
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "errored": errored,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = load_eval_set(Path(args.eval_set))
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            error_str = f" errors={len(r['errors'])}" if r.get("errors") else ""
            print(f"  [{status}] rate={rate_str}{error_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)
            for error in r.get("errors", [])[:2]:
                print(f"    error: {error}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
