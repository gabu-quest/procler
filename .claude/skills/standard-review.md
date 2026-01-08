# Standard Review Skill

**Purpose:** Review code changes against The Standard's engineering doctrines.

---

## Instructions

You are performing a code review according to **The Standard** engineering doctrine.

### 1. Load Core Doctrines

Read these files to understand the standards:
- `agents.md` - Core principles
- `docs/testing.md` - Testing requirements
- `docs/doctrine/style.md` - Code style rules
- `docs/doctrine/security.md` - Security baseline

### 2. Review Checklist

Evaluate the code changes against these criteria:

#### Code Quality
- [ ] Follows style.md naming conventions
- [ ] No clever code - boring, obvious solutions preferred
- [ ] Proper error handling (fail loudly, no silent failures)
- [ ] Type safety enforced (Python type hints, Vue TypeScript)
- [ ] No TODO comments without issue tracking

#### Testing
- [ ] Tests exist for all new functionality
- [ ] Tests are realistic (no mocks unless truly necessary)
- [ ] Tests are deterministic (no sleep, no date.now())
- [ ] Test names follow Given-When-Then pattern
- [ ] Proper test taxonomy (unit vs integration vs E2E)

#### Security
- [ ] No secrets in code
- [ ] Input validation at boundaries
- [ ] Parameterized queries (no SQL injection)
- [ ] Proper authentication/authorization checks
- [ ] HTTPS enforced for external connections

#### Git Standards
- [ ] Commit messages follow conventional commits
- [ ] Logical, atomic commits
- [ ] No merge commits (rebase preferred)
- [ ] Clean history

### 3. Review Format

Structure your review as:

```markdown
## Standard Review

### ✅ Strengths
[List what follows The Standard well]

### ⚠️ Issues Found
[List violations with specific file:line references]

#### Critical
[MUST fix before merge]

#### Recommended
[SHOULD fix for quality]

### 📝 Suggestions
[Optional improvements]

### Verdict
- [ ] Approve (meets all MUST requirements)
- [ ] Request changes (has critical issues)
- [ ] Comment only (suggestions for consideration)
```

### 4. Tone

- Be direct and objective
- Reference specific doctrine rules
- Provide examples of how to fix issues
- No excessive praise - quality is expected
- Flag security issues immediately

---

## When to Use This Skill

Invoke this skill when:
- Reviewing pull requests
- Auditing existing code
- Validating changes before commit
- Doing code quality checks

---

## Example Usage

User: "Review my authentication implementation"
Agent: [Invokes `standard-review` skill]
Agent: [Reads relevant code and doctrines]
Agent: [Provides structured review output]
