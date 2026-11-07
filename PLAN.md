# PLAN.md — Assignment 4 execution plan (human-in-the-loop)

Source of record: `HANDOUT.md` (484 lines), `RUBRIC.md`, `README.md` in this repo, and the
instructor's own words in `~/school/CS690/recordings/2026-10-27 18-07-07/CS690-2026-10-27.txt`
(assignment assigned that night) and `.../2026-11-03 18-23-47/CS690-2026-11-03.txt`
(deadline, extension ruling).

## 1. Facts that bound the work

| Fact | Value | Source |
| --- | --- | --- |
| Canvas item | Assignment-4, id 768307, 100 points | `/api/v1/courses/73246/assignments` |
| Due / lock | **Mon 2026-11-09 23:59 ET** (`2026-11-10T04:59:59Z`); `lock_at` == `due_at` | `/api/v1/courses/73246/assignments/768307`, re-read 2026-11-07 10:38 ET |
| Instructor ruling | announced 2026-11-07 08:38 ET ("Milestone 2 Uploaded & Milestone 1 extended"): Assignment-4 moved to Monday Nov 9 23:59 | announcement 516665 + the assignment record, which now agrees |
| Repo | `upstream` = md685-njit/Assignment-4 (read-only for us), `origin` = Tactile-Taco/CS690-Assignment-4 (public) | course convention |
| Points | code by tests 50 · runs + terminal files 24 · report/evidence/ledger 26 | RUBRIC.md |
| Sibling deadline | Project Milestone-1: announcement 516665 says "extended ... to Monday, November 9, at 11:59 PM", but assignment 766809 still reads `due_at = lock_at = 2026-11-08T04:59:59Z` = **Sat Nov 7 23:59 ET**, with no overrides, and Canvas says **unsubmitted** (work exists in `~/tmp/CS690-M1`). A hard lock is what the submission actually passes through, so treat Saturday 23:59 as live until the record itself moves | announcement 516665 body + assignment 766809 `all_dates`/`overrides` |

## 2. What is graded, and therefore what we actually build

| Part | Files we write | Gate (command) | API key |
| --- | --- | --- | --- |
| 0 | `.env` (key, model, two prices), ledger entry 1 | `python -m agent check-setup` | yes (one ping) |
| 1 | `agent/tools.py`: `safe_path`, `read_file`, `edit_file`, `format_report`, `run_tests`, 3 docstrings | `pytest tests/test_tools.py` | no |
| 2 | `agent/policy.py`: `gate_for`, `budget_stop`, `is_stuck` | `pytest tests/test_policy.py` | no |
| 3 | `agent/loop.py`: `build_system_prompt`, `run_agent` | `pytest tests/test_loop.py` | no |
| 4 | `agent/reflexion.py`: `judge`, `write_lesson`, `reflexion` | `pytest tests/test_reflexion.py` | no |
| 5 | `server.py` (MCPServer `a4-tools`, 4 tools, `--workspace`, stdio) | `pytest tests/test_server.py`, `python -m agent check-mcp` | no |
| 6 | `runs/runA/`, `runs/runB/`, `NOTES.md` | `check-trace`, `replay` for both | yes |
| 7 | `.agents/mcp_config.json`, `.agents/agents/{reviewer,fixer}/agent.md`, `runs/terminal/`, `runs/vendor/`, `evidence/{terminal_mcp,review,fixer}.md` | `python -m agent judge vendor` | vendor free tier |
| 8 | `REPORT.md` §1–8, `LEDGER.md` ≥5 entries, `prompts/` files | `python -m agent summary` must match §1 row for row | no |

Hidden tests check *the same written rules as the public tests*, so the comment above each
function is the spec: implement the comment literally, including exact error strings, and
do not add behaviour it does not ask for.

## 3. Human-in-the-loop protocol (the same shape as A2/A3)

1. **`DECISIONS.md` is the source of record.** An item exists only after the student rules
   on it. Ids `D-001…`; each records item, referenced content, options, AI recommendation,
   the student's ruling verbatim, and the resulting artifact.
2. **One item per turn.** The assistant shows the referenced source (code comment, trace
   line, transcript quote) and one proposed answer, then asks for a ruling through the
   confirm/reject options. Drafts are never batched, and reference documents never go
   inside the question itself.
3. **Artifacts derive from rulings, never the reverse.** `LEDGER.md` entries, `REPORT.md`
   answers and `prompts/` files are generated from `DECISIONS.md` + traces + commit facts.
4. **The grader-facing ledger is not auto-written.** A monitor may write *facts*
   (`ledger/events.jsonl`) and a *draft* with `REVIEW_REQUIRED` placeholders; the `review`
   and `risk` fields are only ever filled from a recorded student ruling. Fabricated
   ledger entries are an integrity violation under the syllabus, not a points deduction.
5. **Approvals during runs are evidence.** Run A step 1 must be a rejected edit with a
   reason (rubric B3). That rejection and the student's reason are recorded verbatim into
   `DECISIONS.md` at the moment it happens, then quoted into REPORT §2.
6. **Prompts are captured at use.** Every prompt typed into an AI tool is saved to
   `prompts/<entry>-<slug>.md` before it is used, and the ledger names that path. A ledger
   entry naming a missing prompts file is a known deduction (A3 lost 1 point exactly there).

## 4. Order of work, with checkpoints

No-key block first (Parts 1–5 are free, scripted model):

| Checkpoint | Work | Verify |
| --- | --- | --- |
| S1 | Part 1 tools + docstrings | `pytest tests/test_tools.py` green |
| S2 | Part 2 policy | `pytest tests/test_policy.py` green |
| S3 | Part 3 loop | `pytest tests/test_loop.py` green |
| S4 | Part 4 reflexion | `pytest tests/test_reflexion.py` green |
| S5 | Part 5 server | `pytest tests/test_server.py` green, `check-mcp` all passed |
| S6 | Full suite + commit | `pytest` green (41 tests) |
| S7 | Practice run `try1` with the real key, read trace | `check-trace try1` |
| S8 | **Commit code; freeze it** | 3 practice runs deleted before submission |
| S9 | Run A (reject first edit with a reason) | `check-trace runA`, `replay runA` |
| S10 | Run B (`--tools mcp --judge`) | `check-trace runB`, `replay runB` |
| S11 | Part 7A terminal MCP evidence | `evidence/terminal_mcp.md` |
| S12 | Part 7B reviewer + review evidence | `evidence/review.md` |
| S13 | Part 7C fixer + `judge vendor` | `runs/vendor/judge.txt` |
| S14 | REPORT §1–8 from traces, ledger finished | `summary` matches §1 |
| S15 | Push, open link, submit on Canvas | incognito check |

Hard ordering constraints from the handout:

- Code freezes after S8. `replay` re-runs the *committed* code against saved replies; any
  later edit to `agent/*.py` invalidates both runs and forces a re-record.
- `NOTES.md` must be empty *before* run A and before run B's attempt 1 (`git checkout NOTES.md`).
- `python -m agent summary` prints **every** directory under `runs/` that has a `run.json`,
  runA/runB first. Practice runs therefore must be deleted (not just left uncommitted) or
  REPORT §1 will not match the grader's output row for row.
- Do not modify `fixture/`, `judge/`, `tests/` — `check-setup` compares a digest of
  `fixture/`+`judge/` (`8aaab9373de615a5`) and the grader restores them anyway.

## 5. Risks and their handling

| Risk | Handling |
| --- | --- |
| Assignment-2 `.env` key is **expired** (`api_key_expired` from opencode.ai/zen/go) | D-001: pick provider/model with a live key before S7; Parts 1–5 proceed without it |
| `lock_at` == `due_at` on Canvas: a late push is hard-closed | target S15 by Sat 18:00 ET; extension exists only as an in-class offer, so ask the instructor in writing if we slip |
| Claude Code not installed (`claude` absent), only `agy` (Antigravity) | D-002: agy route is free and matches the handout's alternative; the read-only rule then degrades from lock to request, which REPORT §7 must say explicitly |
| Vendor agent is interactive, so its transcript is manual | prepare exact commands and a capture template; the student runs it and pastes; the assistant checks the paste against the rubric item |
| Practice runs pollute `summary` | delete `runs/try*` before S14; `runs/terminal` and `runs/vendor` have no `run.json` so they never appear |
| Multi-agent authorship ambiguity (instructor's "lost authorship" failure mode, 2026-10-27 02:33) | one owner per file, one integrator (the student), and `ledger/events.jsonl` records which tool touched what |
| Gate fatigue (instructor: "after the 20th prompt people press y without reading") | approvals are only edits (4 per run at most); each approval is read against the diff and the decision recorded |

## 6. Provenance monitor

`a4-ledger-watch` (systemd user service, state in `~/school/CS690/assignments/A4-ledger/`)
polls the repo **and the AI-tool transcripts** and writes:

- `events.jsonl` — append-only facts: commit SHAs with diffstat, pytest results,
  `runs/*/trace.jsonl` summaries (steps, gates, rejections, judge verdicts, tokens),
  `prompts/` additions, `DECISIONS.md` rulings, and one `session` event per relevant omp
  transcript with each model's provider, calls, tokens, cache reads and cost, plus tool
  calls by name and the repo files the assistant touched.
- `staged-prompts/` — every message the student typed in those sessions, verbatim, one
  file each, so a ledger entry's `prompts` field can name real text; anything that looks
  like a credential is refused and logged as `prompt_skipped` instead.
- `LEDGER.draft.md` — candidate entries with the seven schema fields, plus a
  "AI tool use on record" section; `review`, `risk` and unmatched `prompts` stay
  `REVIEW_REQUIRED` until a ruling exists in `DECISIONS.md`.
- `QUEUE.md` — what still needs a ruling, oldest first.

The monitor never writes `LEDGER.md`. Which model and which tool calls belong in an
entry's `tool` line is a student ruling, not a monitor fact.
