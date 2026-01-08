# Standard Design Skill

**Purpose:** Create planning artifacts (SPEC, TASKS, DESIGN, PLAN) according to The Standard's design doctrine.

---

## Instructions

You are helping create design documentation according to **The Standard** design doctrine.

### 1. Load Design Doctrine

Read these files:
- `docs/doctrine/design.md` - When and how to write design docs
- `examples/planning-artifacts/` - Reference examples
- `examples/adr/` - Architecture Decision Record templates

### 2. Determine What's Needed

Based on the task complexity:

#### Small Task (< 3 files, < 200 LOC)
- ✅ **TASKS.md** only
- ❌ Skip SPEC/DESIGN/PLAN

#### Medium Task (3-10 files, architectural choices)
- ✅ **SPEC.md** - What and why
- ✅ **TASKS.md** - Ordered checklist
- ⚠️ **DESIGN.md** if multiple approaches exist

#### Large Task (> 10 files, significant architecture)
- ✅ **SPEC.md** - Requirements and scope
- ✅ **DESIGN.md** - Architecture decisions
- ✅ **TASKS.md** - Implementation checklist
- ✅ **PLAN.md** - Sequencing and coordination

#### Architectural Decision
- ✅ **ADR** - Decision record in `docs/adr/NNN-title.md`

### 3. Document Structure

#### SPEC.md Template

```markdown
# [Feature Name] - Specification

## 1. Overview
[What are we building and why?]

## 2. Requirements

### Must Have
- [Core requirements]

### Should Have
- [Important but not critical]

### Won't Have (This Phase)
- [Explicit scope exclusions]

## 3. User Stories
- As a [user], I want [goal] so that [benefit]

## 4. Success Criteria
- [Measurable outcomes]

## 5. Constraints
- [Technical limitations, deadlines, dependencies]
```

#### DESIGN.md Template

```markdown
# [Feature Name] - Design

## 1. Architecture Overview
[High-level system design]

## 2. Key Decisions

### Decision: [Topic]
**Options Considered:**
- Option A: [description] - Pros/Cons
- Option B: [description] - Pros/Cons

**Chosen:** Option A
**Rationale:** [Why this choice]

## 3. Components
[File structure, module breakdown]

## 4. Data Models
[Database schema, API contracts]

## 5. Security Considerations
[Auth, validation, encryption]

## 6. Testing Strategy
[How will we verify correctness]

## 7. Migration Path
[How to roll out safely]
```

#### TASKS.md Template

```markdown
# [Feature Name] - Tasks

## Phase 1: Foundation
- [ ] Task 1 - [Specific, measurable]
- [ ] Task 2 - [With acceptance criteria]

## Phase 2: Implementation
- [ ] Task 3 - [Dependencies noted]
- [ ] Task 4 - [Estimated complexity]

## Phase 3: Testing & Polish
- [ ] Task 5 - [Integration tests]
- [ ] Task 6 - [E2E scenarios]

## Definition of Done
- All tasks completed
- Tests passing
- Documentation updated
- Code reviewed
```

#### ADR Template

```markdown
# ADR-NNN: [Decision Title]

**Status:** Accepted | Proposed | Deprecated | Superseded by ADR-XXX
**Date:** YYYY-MM-DD
**Deciders:** [Who was involved]
**Technical Story:** [Issue/ticket link]

## Context
[What is the issue we're addressing?]

## Decision
[What we're doing about it]

## Consequences

### Positive
- [Benefits]

### Negative
- [Tradeoffs, costs]

### Neutral
- [Side effects]

## Alternatives Considered
- **Option 1:** [Why rejected]
- **Option 2:** [Why rejected]
```

### 4. Writing Guidelines

- Use present tense ("The system validates..." not "will validate")
- Be specific (file names, function signatures, data shapes)
- Include examples for complex concepts
- Reference existing code patterns
- Call out breaking changes explicitly
- Link to relevant ADRs

### 5. Review Criteria

Before finalizing:
- [ ] Clear scope (no ambiguity about what's included)
- [ ] Justified decisions (why, not just what)
- [ ] Testable outcomes (how we verify success)
- [ ] Security considerations addressed
- [ ] Migration path for breaking changes

---

## When to Use This Skill

Invoke this skill when:
- Planning a new feature
- Making architectural decisions
- Breaking down complex work
- Starting multi-session development
- Need to document design rationale

---

## Example Usage

User: "Help me plan a user authentication system"
Agent: [Invokes `standard-design` skill]
Agent: [Determines this is a Large Task]
Agent: [Creates SPEC.md, DESIGN.md, TASKS.md]
Agent: [Includes ADR for authentication strategy]
