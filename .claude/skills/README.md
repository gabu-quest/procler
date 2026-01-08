# The Standard - Claude Skills

This directory contains reusable Claude skills for working with projects that adopt **The Standard**.

## Available Skills

### `standard-review` - Code Review
**Use when:** Reviewing pull requests or auditing code quality

Reviews code changes against The Standard's engineering doctrines:
- Code style and patterns
- Testing requirements
- Security baseline
- Git conventions

**Example:**
```
User: "Review my authentication implementation"
[Agent invokes standard-review skill]
```

---

### `standard-design` - Planning & Design Docs
**Use when:** Planning features or making architectural decisions

Creates proper planning artifacts (SPEC, TASKS, DESIGN, PLAN, ADR) according to design doctrine:
- Determines what documentation is needed based on complexity
- Provides templates for each artifact type
- Ensures proper structure and completeness

**Example:**
```
User: "Help me plan a user authentication system"
[Agent invokes standard-design skill]
```

---

### `standard-test` - Test Quality Validation
**Use when:** Writing tests or reviewing test quality

Ensures tests follow The Standard's testing doctrine:
- Realistic (no excessive mocking)
- Deterministic (no sleep, no date.now())
- Documentary (clear behavior descriptions)
- Proper taxonomy (unit vs integration vs E2E)

**Example:**
```
User: "Review the tests in tests/test_auth.py"
[Agent invokes standard-test skill]
```

---

### `standard-handoff` - Multi-Session Handoff
**Use when:** Ending sessions with incomplete work or switching roles

Creates comprehensive handoff documentation:
- Current state (what's done/in-progress/next)
- Technical details (files, DB, dependencies, env vars)
- Testing status
- Key decisions and known issues
- Verification steps for next agent

**Example:**
```
User: "Create a handoff doc for the next session"
[Agent invokes standard-handoff skill]
```

---

## How to Use Skills

Skills are invoked by Claude agents when relevant tasks arise. They:
- Load the appropriate doctrine documents
- Apply standard workflows and templates
- Ensure consistency with The Standard

As a user, you can explicitly request a skill:
- "Use the standard-review skill to check this PR"
- "Create a design doc using standard-design"
- "Validate my tests with standard-test"

---

## Adopting These Skills in Your Project

If your project adopts The Standard:

1. **Copy The Standard's doctrine files** to your repo:
   ```bash
   cp agents.md your-repo/
   cp docs/testing.md your-repo/docs/
   cp -r docs/doctrine your-repo/docs/
   ```

2. **Copy the skills** to your repo:
   ```bash
   cp -r .claude/skills your-repo/.claude/
   ```

3. **Update skill paths** if your doctrine files are in different locations:
   - Edit each skill's "Load [Topic] Doctrine" section
   - Update file paths to match your repo structure

4. **Configure Claude** to use these skills in your project

---

## Skill Development Guidelines

When creating new skills for The Standard:

### Must Have
- Clear purpose statement
- Explicit doctrine file references
- Structured output format
- Usage examples
- "When to Use This Skill" section

### Should Have
- Checklists for validation
- Templates for common outputs
- Anti-patterns to avoid
- Role-specific variations

### Must Not
- Require manual configuration
- Duplicate doctrine content (reference, don't copy)
- Make assumptions without loading context
- Skip quality checks

---

## Contributing New Skills

To add a new skill to The Standard:

1. **Identify the need** - Is there a repetitive workflow that should be standardized?
2. **Create the skill file** - Follow existing skill structure
3. **Link to doctrine** - Reference specific doctrine documents
4. **Add examples** - Show concrete usage
5. **Update this README** - Document the new skill
6. **Test it** - Verify it works across different scenarios

---

## Skill Philosophy

Skills in The Standard are:

- **Doctrine-driven** - They enforce the engineering standards, not ad-hoc preferences
- **Comprehensive** - They consider all aspects (code, tests, docs, security)
- **Objective** - They use normative language (MUST/SHOULD) consistently
- **Reusable** - They work across any project adopting The Standard

Skills are NOT:
- ❌ Shortcuts to skip reading doctrine
- ❌ Substitutes for understanding the standards
- ❌ Overly prescriptive without rationale
- ❌ Coupled to specific tech stacks (beyond our defined standards)

---

## Future Skills (Planned)

Potential skills to add:

- `standard-security` - Security audit focused on security.md doctrine
- `standard-ci` - CI/CD setup validation
- `standard-migration` - Help migrate legacy code to The Standard
- `standard-pr` - Generate proper PR descriptions
- `standard-commit` - Validate commit messages and history

Contributions welcome!

---

## Questions?

See the main [CLAUDE.md](../../CLAUDE.md) for more context on working with The Standard.
