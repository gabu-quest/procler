# Claude Context: The Standard

**Version:** 1.0.0 | **Type:** Engineering Doctrine Repository

---

## What This Is

**The Standard** is a personal engineering doctrine for AI-assisted software development. It defines opinionated standards for tooling, testing, and code quality.

**This is a documentation repository, not a code repository.** When working here, you're maintaining the standard itself.

---

## Repository Structure

```
/
├── agents.md              ← Core agent doctrine (START HERE)
├── docs/
│   ├── testing.md         ← Testing doctrine (critical)
│   ├── doctrine/          ← Domain-specific doctrines (git, ci, design, security, style, handoff, nodejs)
│   ├── testing-*.md       ← Framework-specific testing guides
│   ├── quick-reference/   ← One-page summaries
├── examples/              ← Reference implementations
├── .claude/skills/        ← Reusable Claude skills
├── adoption/              ← Adoption checklist
└── .github/               ← Issue/PR templates
```

---

## Key Files

| File | Purpose |
|------|---------|
| [`agents.md`](./agents.md) | Core operating rules, workflow, roles |
| [`docs/testing.md`](./docs/testing.md) | Testing doctrine - "A failing test is a gift" |
| [`docs/doctrine/README.md`](./docs/doctrine/README.md) | Index of all domain doctrines |
| [`.claude/skills/README.md`](./.claude/skills/README.md) | Available Claude skills |

For the complete documentation index with token counts, see [`docs/doctrine/README.md`](./docs/doctrine/README.md).

---

## Working in This Repository

### Principles

1. **Clarity is paramount** - Docs must be clear for both humans and AI
2. **Normative language** - Use MUST/MUST NOT/SHOULD (RFC 2119)
3. **Opinionated with rationale** - Strong opinions, justified
4. **Internal consistency** - All doctrine docs must align

### Common Tasks

**Adding doctrine:** Create in `docs/doctrine/`, update `docs/doctrine/README.md`, add quick-reference.

**Adding skills:** Create in `.claude/skills/`, update `.claude/skills/README.md`.

**Adding examples:** Put in `examples/` with README explaining what it shows.

See existing files for templates and patterns.

---

## Instruction Hierarchy

When editing this repo:

1. User's explicit request
2. This CLAUDE.md
3. agents.md (our own standards apply to us)
4. Existing patterns in this repo

---

## ADRs (Architectural Decisions)

### ADR-001: Normative Language

All doctrine uses RFC 2119 style (MUST/MUST NOT/SHOULD) to remove ambiguity for AI agents.

### ADR-002: Flat Doctrine Structure

Doctrine lives in `docs/doctrine/` as flat files, not nested. Easy to link and reference.

---

## Versioning

Semantic versioning in `CHANGELOG.md`:
- **MAJOR:** Breaking changes to core doctrine
- **MINOR:** New doctrines or significant additions
- **PATCH:** Clarifications, typo fixes

---

## Before Committing

- [ ] Does this align with existing doctrine?
- [ ] Are cross-references updated?
- [ ] Is CHANGELOG.md updated?
- [ ] Would both a human and AI understand this?
