# Prompt 1 — the request that started the work (plan, HITL method, ledger monitor)

Tool: omp (oh-my-pi), model `deepseek-v4.1-flash` routed through the bifrost gateway to
OpenCode Go, 2026-11-06.

Prompt, verbatim as sent:

```text
Grab the next assignment for my CS690 course and come up with a plan for accomplishing it using a human-in-the loop strategy like we did for assignment two. Consider whatever the teacher said in transcripts of previous lectures as well for how this assignment is meant to be accomplished. As with before, set up a long-running monitoring agent which builds the provenance ledger for this assignment.
```

The only other input in that session was one ruling, chosen from the options put to me:

```text
OpenCode Go, deepseek-v4-flash
```

Used by: ledger entry 1 (plan and scaffolding), and the entries for
`agent/tools.py`, `agent/policy.py`, `agent/loop.py`, `agent/reflexion.py` and
`server.py`, which were written in the same session from the specification comments in
those files.
