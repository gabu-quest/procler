# Standard Handoff Skill

**Purpose:** Create proper handoff documentation for multi-session work according to The Standard.

---

## Instructions

You are creating a handoff document according to **The Standard** handoff doctrine.

### 1. Load Handoff Doctrine

Read these files:
- `docs/doctrine/handoff.md` - Handoff protocol
- `examples/handoff/` - Example handoff documents (if available)

### 2. Handoff Document Structure

Create a `HANDOFF.md` file with this format:

```markdown
# Handoff: [Feature/Task Name]

**Date:** YYYY-MM-DD HH:MM UTC
**Session:** [Session identifier]
**Status:** [In Progress | Blocked | Ready for Review]
**Next Agent:** [Role - Planner/Dev/Test/Security/etc.]

---

## Context

### What We're Building
[Brief description of the overall goal]

### Why This Matters
[Business/technical rationale]

---

## Current State

### What's Done ✅
- [Completed task 1 - with file references]
- [Completed task 2 - with test status]
- [Completed task 3 - with commit hash]

### What's In Progress 🚧
- [Current task - exact state]
- [Blockers or pending decisions]
- [Files currently being edited]

### What's Next 📋
- [Next immediate task]
- [Dependencies that must be resolved first]
- [Estimated complexity]

---

## Critical Information

### Key Decisions Made
1. **[Decision topic]**
   - Chose: [Option A]
   - Rationale: [Why]
   - See: [ADR or file reference]

### Known Issues
- [Issue 1] - [Impact and workaround]
- [Issue 2] - [Status and owner]

### Assumptions
- [Assumption 1] - [If this changes, we need to revisit...]
- [Assumption 2]

---

## Technical Details

### File Changes
- `src/auth/service.py` - Added OAuth provider integration
- `tests/test_auth.py` - Added 12 new test cases (all passing)
- `docs/api.md` - Updated authentication endpoints

### Database Changes
- Migration `0005_add_oauth_tokens.py` created but not applied
- Requires: PostgreSQL 14+ for new JSON operators

### Dependencies
- Added: `authlib==1.3.0` for OAuth
- Conflict: Current `httpx` version incompatible, needs upgrade to 0.27+

### Environment Variables
- New: `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`
- Changed: `AUTH_PROVIDER` now accepts "local|github|google"

---

## Testing Status

### Passing ✅
- Unit tests: 45/45
- Integration tests: 12/12
- E2E tests: 5/5

### Failing ❌
- None

### Not Yet Written 📝
- E2E test for GitHub OAuth callback flow
- Property test for token expiration edge cases

---

## For the Next Agent

### Immediate Next Steps
1. [Specific task - what to do]
2. [File to edit - where]
3. [Test to write - why]

### Watch Out For
- [Gotcha 1 - explanation]
- [Edge case to handle]
- [Performance consideration]

### Questions to Answer
- [Open question 1]
- [Decision that needs user input]

### Resources
- [Link to relevant design doc]
- [Reference implementation]
- [External documentation]

---

## Git Status

**Branch:** `feature/oauth-integration`
**Last Commit:** `a3f4c2d` - "feat: add OAuth provider integration"
**Clean Working Tree:** Yes | No - [uncommitted changes description]

**Upstream Status:**
- [ ] Pushed to remote
- [ ] PR created
- [ ] Ready for review

---

## Verification

Before picking this up, the next agent should:
- [ ] Read this handoff completely
- [ ] Review the last 3 commits
- [ ] Run the test suite
- [ ] Check for any new issues/comments
- [ ] Verify environment is set up correctly

---

## Questions?

If anything is unclear:
1. Check the referenced design docs
2. Review recent commit messages
3. Look at test cases for usage examples
4. Ask the user if critical information is missing
```

### 3. Handoff Quality Checklist

Ensure the handoff includes:

- [ ] Complete context (what/why)
- [ ] Explicit current state
- [ ] Clear next steps (no ambiguity)
- [ ] All technical details (files, DB, deps, env)
- [ ] Test status (what's passing/failing)
- [ ] Key decisions with rationale
- [ ] Known issues and workarounds
- [ ] Git status and branch info
- [ ] Verification steps for next agent

### 4. When to Create a Handoff

Create handoff documentation when:
- Session is ending with work incomplete
- Switching between specialized roles (Dev → Test → Security)
- Blocked waiting for user input
- Task is large and needs multi-session coordination
- Context is complex and needs preservation

### 5. Handoff for Different Roles

#### To Planner
- Emphasize: Open questions, design alternatives, scope concerns
- Include: User stories, requirements clarity, missing specs

#### To Developer
- Emphasize: File structure, implementation approach, tech stack
- Include: Design decisions, code patterns, API contracts

#### To Test Engineer
- Emphasize: What needs testing, edge cases, integration points
- Include: Test strategy, coverage gaps, known failure modes

#### To Security Reviewer
- Emphasize: Auth flows, data boundaries, external integrations
- Include: Threat model, security requirements, compliance needs

---

## When to Use This Skill

Invoke this skill when:
- Ending a session with incomplete work
- Preparing for role handoff (Dev → Test)
- Work is blocked pending user decision
- Starting multi-session complex feature
- Orchestrator requests handoff documentation

---

## Example Usage

User: "I need to stop for today. Create a handoff for the next session."
Agent: [Invokes `standard-handoff` skill]
Agent: [Analyzes current work state]
Agent: [Creates comprehensive HANDOFF.md]
Agent: [Commits handoff doc to repo]
