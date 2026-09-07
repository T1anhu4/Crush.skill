# CLI motion and preview release

**Goal:** Publish the tested source preview with honest README capability status and accessible, Claude Code-inspired terminal activity feedback.

**Architecture:** Keep Python, existing `crush` interactive commands and the JSON-only `crush v3` / Skill adapter. Isolate terminal animation in a small module; stdout JSON must never contain animation. No private model calls or user data changes for this release verification.

**Design decision:** A low-frequency single-line star pulse with stage label and elapsed time; no fake token stream, whole-screen redraw or invented character thought. Fall back to static text for pipes, dumb terminals, plain mode or reduced motion. Preserve README artwork and opening/closing copy. This scope does not claim a complete v3 interactive TUI or host-native Skill model integration.

## Execution

- [x] Add failing terminal rendering tests: non-TTY and plain output contain no ANSI, narrow CJK layout fits, reduced motion is static, exception cleanup stops the animation.
- [x] Implement `crush_cli/motion.py` and integrate existing Spinner call sites; move model error printing outside the active animation so failures cannot be erased.
- [x] Run pytest for motion and existing CLI regressions; smoke the real animation through a disposable PTY without a model request. Review spec compliance, then code quality.
- [x] Update README.md and README_EN.md: implemented preview features, current Skill/CLI/GUI entry points, real evaluation result and limitations, terminal motion controls. Preserve existing image references and closing/opening copy.
- [x] Run `.venv/bin/python -m pytest tests -q` (133 passed), `npm --prefix web test` (4 passed), `npm --prefix web run build`, `bash scripts/smoke_test.sh`, package builds and `git diff --check`.
- [ ] Inspect staging for private files and verify git author/committer are T1anhu4 with linked noreply identity. Commit on the current development branch, then atomically fast-forward both `main` and `codex/v3-living-mind`; do not force push, create a PR, or change the default-branch setting. Confirm the remote refs and attributed author after pushing.
