# Changelog

All notable changes to The Standard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- **Moved design systems to separate repository**
  - Extracted `docs/design-systems/` to **[The Style](https://github.com/gabu-quest/the-style)**
  - Goshuin and Cyberpunk editions now maintained independently
  - Cleaner separation: The Standard = doctrine, The Style = design systems
  - Updated all references to point to new repository

### Added
- **Light Mode adoption path** in `adoption/CHECKLIST.md`
  - Two-file minimal adoption: just agents.md + testing.md
  - Clear upgrade paths when you need more
  - Small projects can skip the 8-phase process

### Changed
- **Renamed from "Codex Agents" to "AI Agents"** throughout
  - Updated agents.md title and description
  - Updated handoff.md references
  - Now tech-agnostic (Claude, etc.)
- **Compressed CLAUDE.md by ~80%** (510 → 110 lines)
  - Removed duplicated documentation index
  - Links to docs/doctrine/README.md for complete index
  - Kept only essential context for working in this repo
- **Compressed agents.md section 7 (Testing)**
  - Now a brief summary with link to full testing.md
  - Reduces duplication while keeping key rules visible

## [1.0.0] - 2025-12-13

### Added (from v1.0.0)
- **Cyberpunk Edition design system** - Second design system variant with neon/tech aesthetic (now in The Style)
  - Electric colors (hot pink, cyan, purple, lime)
  - Space Grotesk typography for modern geometric feel
  - Duotone and varied icon weights for layered complexity
  - Best for dev tools, SaaS, gaming, and tech-focused applications
- **Design systems index** - Comprehensive comparison and guide for choosing between variants
  - Goshuin Edition (calm, ceremonial, cultural)
  - Cyberpunk Edition (energetic, rebellious, modern)
  - Quick comparison table and integration guides
- **Complete documentation index** in CLAUDE.md
  - Minimal reading path for LLMs (with token counts)
  - All available doctrines listed with descriptions
  - "When to Load Which Doctrine" table
  - Context-aware loading strategy (200k/100k/32k contexts)
- **Table of contents** in agents.md
  - Internal sections indexed with anchor links
  - Related documentation section with all doctrines
  - "Doctrine Index: What to Read When" table
  - Prime directives for each doctrine
- **Doctrine index quick reference** - New one-page summary
  - All doctrines with prime directives and token counts
  - "What it covers" for each doctrine
  - Decision matrix: what to read when
  - Loading strategy by context size

### Changed
- Reorganized design system structure to support multiple variants
  - `docs/design-system/` → `docs/design-systems/goshuin/` (original)
  - Added `docs/design-systems/cyberpunk/` (new variant)
  - Created `docs/design-systems/README.md` with comprehensive comparison
- Updated main README to reference both design system variants
- Updated adoption checklist to mention design system choice
- **Compressed testing-quick-ref.md** from 274 lines to 183 lines (43% compression)
  - Removed verbose examples, kept rules and checklists
  - More concise format while maintaining all key information
  - Better token efficiency for LLM context

### Improved
- **LLM-friendliness** significantly enhanced:
  - Agents now know all available documentation and when to read it
  - Clear token budgets help LLMs manage context efficiently
  - Multiple entry points (full docs, quick-refs, doctrine index)
  - Total documentation remains ~24,000 tokens (excellent for 200k context)

---

## [1.0.0] - 2025-12-13

### Added

#### Core Documentation
- **agents.md** - Authoritative operating rules for AI agents
  - Instruction precedence hierarchy
  - Non-negotiable execution rules
  - Default workflow (Orient → Plan → Execute → Verify → Commit → Report)
  - Standard artifacts (SPEC, TASKS, DESIGN, PLAN, HANDOFF, CHANGELOG, ADR)
  - Git doctrine integration
  - Modern stack enforcement (Python 3.12+, Vue 3)
  - Comprehensive testing requirements
  - Nine specialized roles (Planner, Dev, Test Engineer, UX/DevX Reviewer, etc.)

- **README.md** - Comprehensive repository overview and adoption guide

#### Testing Doctrine
- **docs/testing.md** - Modern, strict testing rules
  - Prime directive: "A failing test is a gift"
  - Test taxonomy (unit, integration, feature, E2E, stress)
  - Definition of done per feature type
  - Non-negotiable quality rules (determinism, meaningful assertions, public API testing)
  - Frontend testing requirements (Playwright mandatory)
  - Python testing doctrine (pytest-first)
  - LLM-agent operating protocol

#### Engineering Doctrines
- **docs/doctrine/ci.md** - CI/CD practices
  - Fast vs full suite strategy
  - Caching and artifacts
  - Flake policy
  - Quality gates

- **docs/doctrine/design.md** - Design documentation requirements
  - When DESIGN docs are required
  - When ADRs are required
  - Kiro-style planning phases (SPEC → TASKS → DESIGN → PLAN)
  - 17-section DESIGN template
  - Public interface stability rules

- **docs/doctrine/git.md** - Git workflow
  - Git history as product
  - Branching strategy
  - Commit discipline
  - Merge philosophy and conflict resolution
  - `.gitignore` policy (non-negotiable)

- **docs/doctrine/handoff.md** - Multi-session work protocol
  - Handoff format
  - State tracking
  - Orchestrator compatibility

- **docs/doctrine/security.md** - Security baseline
  - Secure defaults
  - OWASP alignment
  - Security testing readiness
  - Threat modeling

- **docs/doctrine/style.md** - Code style guide
  - Code layout and naming
  - API envelope patterns
  - UI/A11Y consistency
  - Language-specific conventions

#### Design System
- **docs/design-system/** - Complete Vue 3 + Naive UI design system
  - Token-based design system (colors, typography, spacing)
  - Naive UI theme integration
  - Phosphor Icons defaults
  - Comprehensive documentation (split into 8 focused files + full guide)
  - Working examples (AppConfigProvider.vue, IconExamples.vue)
  - Source files (tokens.ts, naive-theme.ts, base.css, icons.ts)

### Changed
- Repository structure reorganized into logical hierarchy:
  - Core docs at root (agents.md, README.md, LICENSE)
  - All specialized docs in `docs/` directory
  - Doctrine documents in `docs/doctrine/`
  - Design system in `docs/design-system/`

- File naming simplified:
  - `agents_aggressive.md` → `agents.md`
  - `testing-doctrine-perfect.md` → `docs/testing.md`
  - `ci-doctrine.md` → `ci.md` (and similar for all doctrine files)

### Removed
- `agents_final.md` - Superseded by `agents.md`
- `doctrine_pack.zip` - Extracted and organized
- `unified-design-system-naive.zip` - Extracted and organized

---

## Version Number Meanings

### MAJOR.MINOR.PATCH (Semantic Versioning)

**MAJOR version** (X.0.0) - Breaking changes:
- Removing or fundamentally changing core doctrine
- Changes that would break existing adopters
- Major philosophical shifts
- Example: Changing from MUST to MUST NOT for core rules

**MINOR version** (1.X.0) - Additive changes:
- New doctrine documents
- New sections in existing documents
- New examples or guides
- Significant clarifications that change interpretation
- Example: Adding a new "database.md" doctrine

**PATCH version** (1.0.X) - Non-breaking improvements:
- Typo fixes
- Clarifying language without changing meaning
- Adding examples to existing sections
- Documentation improvements
- Link fixes
- Example: Fixing grammar or adding missing cross-references

---

## Upgrade Guides

### Upgrading to 1.0.0

This is the initial release. To adopt:

1. Copy relevant doctrine files to your repository
2. Link from your main README
3. Configure agents/engineers to reference the standards
4. Adapt for your domain while maintaining core principles

See `adoption/CHECKLIST.md` for detailed steps.

---

## Deprecation Policy

When we deprecate doctrine or patterns:

1. **Announce in MINOR version** - Mark as deprecated with migration guidance
2. **Maintain for one MAJOR version** - Give adopters time to migrate
3. **Remove in next MAJOR version** - Clean break with upgrade guide

Example timeline:
- v1.5.0: Deprecate feature X, document migration
- v1.6.0 - v1.9.0: Feature X marked deprecated but still documented
- v2.0.0: Feature X removed, migration guide in upgrade docs

---

## Philosophy of Change

Changes to this standard should:

1. **Reduce friction** - Make it easier to build quality software
2. **Increase clarity** - Remove ambiguity for both humans and AI
3. **Maintain consistency** - Align with existing doctrine philosophy
4. **Provide value** - Solve real problems, not hypothetical ones
5. **Be justified** - Include rationale, not just changes

---

## How to Contribute

See the main README for contribution guidelines. All changes must:

1. Update this CHANGELOG in the [Unreleased] section
2. Follow the existing documentation patterns
3. Use normative language (MUST/MUST NOT/SHOULD)
4. Include examples where applicable
5. Add cross-references to related documents

---

## Links

- [Repository](https://github.com/gabu-quest/the-standard)
- [Issues](https://github.com/gabu-quest/the-standard/issues)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)

---

[Unreleased]: https://github.com/gabu-quest/the-standard/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/gabu-quest/the-standard/releases/tag/v1.0.0
