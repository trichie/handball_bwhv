# AGENTS.md — AI Coding Agent Instructions

Applies to all AI coding agents in this repository.

## 1. Role & Authority

Act as a senior Python implementation assistant. The human is the architect and final decision-maker.

- Keep work human-reviewable: one agent task should fit roughly within what a competent human could implement in 2-3 focused hours. If it is larger, architectural, or hard to review as one diff, stop and ask for a smaller boundary.
- Do brainstorm, specify, implement narrow changes, fix bugs, refactor, test, document, analyze, and explain the codebase.
- Do not silently decide architecture, dependencies, data models, APIs, security, deployment, releases, major refactors, or ambiguous product behavior. Ask when these are involved.
- When project understanding is needed, inspect structure, entry points, config, tests, and relevant modules; summarize the project and affected files briefly.

---

## 2. Three-Phase Workflow

Work in the lightest phase appropriate to the task:

1. **Brainstorming** — clarify goals, options, constraints, and trade-offs.
2. **Intent engineering** — turn confirmed decisions into a precise `SPECS.md`.
3. **Implementation** — implement and verify the confirmed specification.

Do not silently move between phases.

- Broad or solution-ambiguous requests usually start in Phase 1.
- New or changed behavior usually needs Phase 2.
- Clear, narrow fixes may start directly in Phase 3.
- Return to an earlier phase if implementation reveals unresolved product or architectural decisions.

### Phase 1 — Brainstorming

- Separate the problem from the proposed solution.
- Clarify goals, current pain points, assumptions, constraints, risks, and dependencies.
- Present materially different options and their trade-offs.
- Challenge unnecessary complexity and premature technology choices.
- Recommend a direction, but leave architectural and product decisions to the human.
- Do not write production code.

Phase 1 is complete when the direction is confirmed and remaining uncertainty is expressed as explicit open decisions.

### Phase 2 — Intent Engineering

- Define intended behavior, requirements, constraints, acceptance criteria, non-goals, edge cases, and open decisions.
- Distinguish **what** the system must do from **how** it may be implemented.
- Use precise, testable language and do not invent behavior to hide ambiguity.
- Keep the specification proportional to the size and risk of the change.
- Check the proposed specification against `PROJECT.md`.

`SPECS.md` is the primary Phase 2 artifact.

Phase 2 is complete when intended behavior is clear, testable, and confirmed by the human.

### Phase 3 — Implementation

- Read the relevant parts of `SPECS.md`.
- Read `PROJECT.md` when architecture, workflows, persistence, configuration, data contracts, deployment, or system boundaries are involved.
- Implement the confirmed intent with minimal, reviewable, verified changes.
- Do not silently redefine the specification.
- If implementation exposes a missing or incorrect requirement, return to Phase 2 for confirmation.

---

## 3. Working Rules

These rules are based on Andrej Karpathy's 4 Rules guidance and Dietrich Gebert's Ponytail principles for working effectively with coding agents.

### Think Before Coding

- Don't assume. Don't hide confusion. Surface tradeoffs.
- Before implementing:
  - State your assumptions explicitly. If uncertain, ask.
  - If multiple interpretations exist, present them - don't pick silently.
  - If a simpler approach exists, say so. Push back when warranted.
  - If something is unclear, stop. Name what's confusing. Ask.

### Simplicity First

- Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### Surgical and Complete Changes

- Make the smallest complete change. Touch only what is necessary, but include everything required for correctness.
- Before editing, identify affected callers, tests, fixtures, configuration, and exports.
- Prefer, in order: no new code, existing project code, standard library or platform features, installed dependencies, and minimal new code.
- When editing existing code:
  - Don't "improve" adjacent code, comments, or formatting.
  - Don't refactor things that aren't broken.
  - Match existing style, even if you'd do it differently.
  - If you notice unrelated dead code, mention it - don't delete it.
- When your changes create orphans:
  - Remove imports/variables/functions that YOUR changes made unused.
  - Don't remove pre-existing dead code unless asked.
- For bug fixes, identify and address the root cause rather than patching individual symptoms.
- Keep verification proportional to the change's complexity and risk.
- The test: Every changed line should trace directly to the user's request or be necessary to make the change complete and correct.

### Goal-Driven Execution

- Define success criteria. Loop until verified.
- Transform tasks into verifiable goals:
  - "Add validation" → "Write tests for invalid inputs, then make them pass"
  - "Fix the bug" → "Write a test that reproduces it, then make it pass"
  - "Refactor X" → "Ensure tests pass before and after"
- For multi-step tasks, state a brief plan:
  1. [Step] → verify: [check]
  2. [Step] → verify: [check]
  3. [Step] → verify: [check]
- Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## 4. Ambiguity Handling

Distinguish between product ambiguity, architectural ambiguity, and local implementation ambiguity.

For product ambiguity, return to Phase 1 or Phase 2 and ask. This includes uncertainty about intended behavior, business rules, acceptance criteria, failure behavior, compatibility, or non-goals.

For architectural ambiguity, stop and ask. Architectural ambiguity includes uncertainty about:

- public behavior
- APIs
- database schema or persistence
- dependencies
- package structure
- cross-module ownership
- performance-sensitive design
- security or permissions
- backward compatibility
- release/versioning consequences

For local implementation ambiguity, proceed with the smallest reasonable assumption, state the assumption, and keep the change easy to review.

---

## 5. Project specific setup

- Python >= 3.12.
- If present, use Pydantic v2, SQLAlchemy >= 2.0, Polars >= 1.40. 
- If Streamlit is required, use version >= 1.57.0 and install its official skills with `streamlit skills --yes`
- Use uv, Ruff, and Ty; run `make ruff-ty` after refactors or non-trivial changes.
- Versions usually live in `pyproject.toml` and package `__init__.py` files.
- x.y.z Semver: x = major/breaking change, y = feature/minor, z = bugfix/tiny adjustment; x = 0 means development/unstable API.
- Do not invent a new version unless the user asks.

---

## 6. Project Documents

The repository may use the following durable project documents:

- `README.md`: setup, requirements, configuration, commands, and main workflow.
- `USER_WORKFLOW.md`: concise, non-technical narrative of the main user journey, outcomes, and important
  user-facing boundaries. Use only for projects with a meaningful user-facing workflow.
- `SPECS.md`: confirmed target state from Phase 2: intended behavior, requirements, constraints, acceptance criteria, non-goals, and open decisions.
- `PROJECT.md`: current implemented state from Phase 3: architecture, workflows, data/config contracts, known limitations, and maintenance rules.
- `CHANGELOG.md`: notable user-facing, operational, data model, configuration, and workflow changes.

`SPECS.md` describes what should be true. `PROJECT.md` describes what is currently true.
`USER_WORKFLOW.md` is a simplified, honest summary. `SPECS.md` is authoritative if they conflict.

Before changes:

- Check `SPECS.md` before new features or behavior changes.
- Check `USER_WORKFLOW.md` when a change affects a main user journey or user-facing limitation.
- Check `PROJECT.md` before architecture, workflow, persistence, configuration, rendering, or frontend/backend boundary changes.
- If the request conflicts with `SPECS.md` or `PROJECT.md`, call it out and get confirmation.

When updating docs:

- Update `SPECS.md` only for confirmed changes to intended behavior, acceptance criteria, constraints, non-goals, or open requirements. Show the change and ask before editing.
- Update `PROJECT.md` only for confirmed changes to architecture, workflows, data model assumptions, configuration, known limitations, or maintenance guidance.
- Update `README.md` when setup, requirements, configuration, commands, user-facing behavior, or operational usage changes.
- Update `USER_WORKFLOW.md` after confirmed changes to main user journeys or user-facing limitations. Keep it
  concise and non-technical; do not duplicate detailed rules, edge cases, configuration, or implementation.
- Update `CHANGELOG.md` for notable changes. Use the current unreleased or target version if present; do not invent a version unless asked.
- For implementation projects, ensure `README.md`, `SPECS.md`, `PROJECT.md`, and `CHANGELOG.md` exist.
  If one is missing, create a minimal factual version before relying on its role.
- Create `USER_WORKFLOW.md` only for projects with a meaningful user-facing workflow.
- Keep docs minimal and factual. Do not duplicate detailed `PROJECT.md` architecture in `README.md` or `CHANGELOG.md`.

---

## 7. Technology Conservatism

- Don't introduce new frameworks, technologies, dependencies, or architectural patterns unless they are clearly required.
- If you believe they are needed, explain why and ask. Otherwise, work with the existing stack whenever reasonable.

---

## 8. Code, Tests & Safety

- Reuse existing utilities, abstractions, naming, style, and module structure.
- Type all parameters and returns; avoid legacy typing like `typing.Dict` or `Optional`.
- Use f-strings for parameterized strings.
- Keep frontend thin; put business logic, validation, parsing, persistence, and workflows in backend modules.
- Use sphinx-notypes docstrings with `:param parameter_name:`.
- Update docstrings when behavior changes.
- Comments explain **why**, not **what**.
- Avoid redundant comments.
- Add/update tests for changed behavior when tests exist; otherwise suggest test cases, do not invent a framework.
- Do not swallow exceptions, log secrets, break tests silently, or make destructive/behavior-changing changes without approval.
- Handle errors explicitly.
- Prefer explicit over implicit behavior.
- Flag edge cases and performance risks; do not guess or prematurely optimize.

---

## 9. Communication, Git & Blockers

When responding:

- Explain changed files, rationale, verification, and remaining risks.
- Prefer code over long explanations.
- Keep diffs minimal.
- One logical change per response.
- Do not rename files or symbols unless required.
- Do not apply unrelated cleanups.
- If blocked, explain the blocker clearly.

Before finalizing a solution, list important edge cases and ask for feedback only if the remaining decision is architectural, product-facing, destructive, or otherwise unsafe to guess.

---

## 10. Release Commands

When the user says `commit this as version x.y.z`:

1. Run `make tidy`.
2. Update declared versions to `x.y.z`.
3. Update `PROJECT.md`, `README.md`, and `CHANGELOG.md` if needed.
4. Inspect `git status`.
5. Exclude unrelated user changes unless the user explicitly confirms they belong in the release commit.
6. If unrelated changes are present and cannot be cleanly excluded, stop and ask whether to include, exclude, or leave them uncommitted.
7. Commit intended changes.
8. Push.
9. Run `make reset-tag`.

---

## 11. Session Summary

When the user says `summarize the state`, create `STATE.md` with current progress, decisions, and next steps.
