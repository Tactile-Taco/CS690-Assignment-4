"""The agent's tools. Part 1 of HANDOUT.md (and the descriptions are used again in Part 5).

YOU WRITE: safe_path, read_file, edit_file, run_tests, format_report, and the docstring of
each of the three tools you write.
GIVEN (do not change): ToolFailure, use_workspace, workspace, list_files, TOOLS.

A tool's docstring is its description. It is the only thing the model learns about the
tool, both in your own agent and through your MCP server, so write it for the model:
what the tool does, what each input means, what comes back, and its limits. list_files
below is an example of the style.

When a tool cannot do what was asked, raise ToolFailure with a message that teaches: say
what went wrong and what to do next. The model reads that message and decides again.
The exact messages the tests expect are given in the comments above each function.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.mcpserver.exceptions import ToolError

from agent import ROOT
from agent.testrunner import TestReport, run_unittests

TEST_TIMEOUT_SECONDS = 20
READ_LIMIT_MAX = 200
MAX_PROBLEM_LINES = 10


class ToolFailure(ToolError):
    """A failure you saw coming. Its message is shown to the model, so write it to teach.

    It is MCP's own ToolError, so your MCP server passes the message on to the host too.
    """


_workspace: Path | None = None


def use_workspace(path: str | Path) -> Path:
    """Point every tool at one project folder. A relative path counts from the repository root."""
    global _workspace
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    if not p.is_dir():
        raise FileNotFoundError(f"workspace folder not found: {p}")
    _workspace = p
    return p


def workspace() -> Path:
    """The project folder the tools work in."""
    if _workspace is None:
        raise RuntimeError("No workspace is set. Call tools.use_workspace(path) first.")
    return _workspace


# safe_path(path) returns the absolute Path of `path` inside the workspace.
#   - `path` is relative to the workspace, for example "discounts.py" or "tests/test_discounts.py".
#   - Refuse an absolute path, and any path that ends up outside the workspace once it is
#     resolved (for example "../judge/acceptance_test.py"), by raising
#         ToolFailure(f"{path} is outside the project folder. Use a path inside it, such as discounts.py.")
#   - The workspace folder itself counts as inside.
def safe_path(path: str) -> Path:
    root = workspace()
    given = Path(path)
    if given.is_absolute():
        raise ToolFailure(f"{path} is outside the project folder. Use a path inside it, such as discounts.py.")
    resolved = (root / given).resolve()
    if resolved != root and not resolved.is_relative_to(root):
        raise ToolFailure(f"{path} is outside the project folder. Use a path inside it, such as discounts.py.")
    return resolved


def list_files() -> str:
    """List every file in the project, one path per line, relative to the project folder.

    Takes no inputs. Use it first to see what the project contains; the paths it returns
    are the paths read_file and edit_file expect.
    """
    root = workspace()
    rows = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return "\n".join(rows) if rows else "(the project folder is empty)"


# read_file(path, start=1, limit=80) returns part of one text file, with line numbers.
#   - Use safe_path. If the path is not a file, raise
#         ToolFailure(f"{path} is not a file in the project. Call list_files to see the files.")
#   - If start or limit is less than 1, raise ToolFailure("start and limit must be 1 or more.")
#   - Never return more than READ_LIMIT_MAX lines, even if limit is larger.
#   - An empty file returns f"{path} is empty."
#   - If start is past the last line, raise
#         ToolFailure(f"{path} has only {n} lines. Use a start between 1 and {n}.")
#   - Otherwise return, joined with newlines:
#         a header line           f"{path}, lines {start} to {end} of {n}"
#         one line per file line  f"{number:>4}: {text}"   (numbers start at 1)
#         and, only if lines remain after `end`, a last line
#                                 f"(more below: call read_file with start={end + 1})"
def read_file(path: str, start: int = 1, limit: int = 80) -> str:
    """Read part of one text file in the project, showing line numbers.

    Inputs: `path` is a file path relative to the project folder, as list_files returns it.
    `start` is the first line to show, counting from 1 (default 1). `limit` is how many
    lines to show (default 80, never more than 200).

    Returns a header line `path, lines X to Y of N`, then one numbered line per file line,
    then `(more below: call read_file with start=Z)` when lines remain. An empty file
    returns `path is empty`. Fails if the path is not a file in the project, if start or
    limit is below 1, or if start is past the last line."""
    target = safe_path(path)
    if not target.is_file():
        raise ToolFailure(f"{path} is not a file in the project. Call list_files to see the files.")
    if start < 1 or limit < 1:
        raise ToolFailure("start and limit must be 1 or more.")
    lines = target.read_text(encoding="utf-8").splitlines()
    total = len(lines)
    if total == 0:
        return f"{path} is empty."
    if start > total:
        raise ToolFailure(f"{path} has only {total} lines. Use a start between 1 and {total}.")
    end = min(start + min(limit, READ_LIMIT_MAX) - 1, total)
    out = [f"{path}, lines {start} to {end} of {total}"]
    out += [f"{number:>4}: {lines[number - 1]}" for number in range(start, end + 1)]
    if end < total:
        out.append(f"(more below: call read_file with start={end + 1})")
    return "\n".join(out)


# edit_file(path, old_text, new_text) replaces old_text with new_text, once, in one file.
#   - Use safe_path. If the path is not a file, raise the same ToolFailure as read_file.
#   - If old_text is "", raise ToolFailure(
#         "old_text is empty. Copy the exact lines you want to replace from read_file, without the line numbers.")
#   - Count how many times old_text appears in the file.
#       0 times: raise ToolFailure(f"old_text appears 0 times in {path}. Read the file again with "
#                                  "read_file and copy the exact text, including its spaces, without the line numbers.")
#       2 or more: raise ToolFailure(f"old_text appears {count} times in {path}. Include more of the "
#                                    "surrounding lines so that it appears exactly once.")
#   - Exactly once: replace it, write the file back as UTF-8 with "\n" line endings, and
#     return f"Edited {path}: replaced 1 match."
#   - Change nothing in the file when you raise.
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace one exact piece of text in one file. This is the only way to change code.

    Inputs: `path` is a file path relative to the project folder. `old_text` is the exact
    text to replace, copied from read_file WITHOUT the line numbers and without the trailing
    spaces, and it must appear exactly once in the file. `new_text` is what replaces it.

    Returns `Edited path: replaced 1 match.` and changes nothing on failure. Fails with a
    message that says what to do next when the path is not a file, when `old_text` is empty,
    when it appears zero times (re-read the file and copy it exactly), or when it appears
    more than once (include more surrounding lines). The file is rewritten as UTF-8."""
    target = safe_path(path)
    if not target.is_file():
        raise ToolFailure(f"{path} is not a file in the project. Call list_files to see the files.")
    if old_text == "":
        raise ToolFailure(
            "old_text is empty. Copy the exact lines you want to replace from read_file, without the line numbers.")
    text = target.read_text(encoding="utf-8")
    count = text.count(old_text)
    if count == 0:
        raise ToolFailure(f"old_text appears 0 times in {path}. Read the file again with "
                          "read_file and copy the exact text, including its spaces, without the line numbers.")
    if count > 1:
        raise ToolFailure(f"old_text appears {count} times in {path}. Include more of the "
                          "surrounding lines so that it appears exactly once.")
    target.write_text(text.replace(old_text, new_text, 1), encoding="utf-8", newline="\n")
    return f"Edited {path}: replaced 1 match."


# format_report(report) turns a TestReport (agent/testrunner.py) into short text.
#   - No problems:  f"PASSED: {report.total} of {report.total} tests passed."
#   - Otherwise the first line is
#         f"FAILED: {len(report.problems)} of {report.total} tests did not pass."
#     then one line per problem, in the report's order, at most MAX_PROBLEM_LINES of them:
#         f"{problem.kind} {problem.name}: {problem.message}"
#     and, only if some were left out, a last line f"({k} more not shown)".
#   - Never include anything else: no timings, no tracebacks, no passing tests.
#     (The stop rule in Part 2 compares two outputs, so the same result must give the same text.)
def format_report(report: TestReport) -> str:
    if report.timed_out:
        return f"FAILED: the tests did not finish within {TEST_TIMEOUT_SECONDS} seconds."
    if not report.problems:
        return f"PASSED: {report.total} of {report.total} tests passed."
    shown = report.problems[:MAX_PROBLEM_LINES]
    lines = [f"FAILED: {len(report.problems)} of {report.total} tests did not pass."]
    lines += [f"{problem.kind} {problem.name}: {problem.message}" for problem in shown]
    hidden = len(report.problems) - len(shown)
    if hidden > 0:
        lines.append(f"({hidden} more not shown)")
    return "\n".join(lines)


# run_tests() runs the unit tests in the workspace's tests/ folder.
#   - Call run_unittests(workspace(), timeout=TEST_TIMEOUT_SECONDS).
#   - If the report timed out, raise ToolFailure(
#         f"The tests did not finish within {TEST_TIMEOUT_SECONDS} seconds. The last edit may "
#         "have caused an endless loop; read the code you changed.")
#   - Otherwise return format_report(report). Failing tests are not a tool failure: the
#     tool worked, and its output says which tests failed.
def run_tests() -> str:
    """Run the project's unit tests and return a short summary of what passed and failed.

    Takes no inputs. Runs every test file in the project's tests/ folder in a separate
    process, with a 20 second limit.

    Returns `PASSED: N of N tests passed.` or `FAILED: N of M tests did not pass.` followed
    by one line per failing test, `FAIL|ERROR test_name: last line of the error`, at most
    10 of them. Failing tests are a normal result, not a tool failure. Fails only when the
    tests do not finish in time, which usually means the last edit caused an endless loop."""
    report = run_unittests(workspace(), timeout=TEST_TIMEOUT_SECONDS)
    if report.timed_out:
        raise ToolFailure(
            f"The tests did not finish within {TEST_TIMEOUT_SECONDS} seconds. The last edit may "
            "have caused an endless loop; read the code you changed.")
    return format_report(report)


# The tools the agent offers, in this order. Do not rename them.
TOOLS = [list_files, read_file, edit_file, run_tests]
