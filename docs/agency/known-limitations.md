# Known Limitations & Future Work

## Current Limitations

**No automated phase orchestration.** The human user must manually invoke each agent in the correct order. There is no state machine or automated sequencing. The user reads the gate output (e.g., APPROVED/REPROVED in `VALIDATION.md`) and decides the next step.

**Hooks are advisory only.** The current hooks exit with code 0 and print reminders to stderr. They do not block tool execution. A hook could block (non-zero exit code), but none currently do.

**No state tracking between phases.** There is no persistent state file that records which phases have been completed, which gates passed, or which agents have run. The user tracks progress by checking which artifact files exist and reading gate verdicts.

**Single-session agents.** Each agent invocation is a fresh Claude Code skill activation. There is no memory between invocations of the same agent across different phases. Continuity comes from the artifact documents each agent reads and writes.

**No parallel agent execution.** Agents run one at a time within a single Claude Code session. You cannot invoke `/tl review` and `/qa review` simultaneously.

**No automated testing integration.** The QA agent writes and runs tests, but there is no CI/CD hook to automatically trigger tests or report results back to the workflow.

## Future Work

- **Phase state file:** A `docs/PHASE_STATUS.md` or JSON file that tracks completion, gate verdicts, and which agents have contributed per phase.
- **Blocking hooks:** Hooks that enforce gates (e.g., prevent `/dev implement` if `VALIDATION.md` does not contain dual APPROVED verdicts).
- **Automated sequencing:** A meta-agent or orchestration script that invokes agents in order and routes based on gate results.
- **Multi-project support:** Better tooling for managing multiple projects under the same agency, including shared configuration inheritance.
- **CI/CD integration:** Hooks that trigger CI pipelines and feed results back into test reports.
