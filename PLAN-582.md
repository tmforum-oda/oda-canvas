# Plan: Introduce Agent Skills & Refactor (Issue #582)

> **Temporary planning document** — delete when issue #582 is closed.
> GitHub Issue: https://github.com/tmforum-oda/oda-canvas/issues/582

---

## Overview

Consolidate three overlapping AI instruction files into a unified, tool-agnostic `AGENTS.md` hierarchy, refactor suitable custom agents into on-demand skills, and create new skills for common contributor tasks.

**Current state:** 10 files across 3 tool-specific configs, 3 custom agents, 1 agent index, 1 overview doc, and 2 agent user guides.

---

## Sub-sections

### Sub-section 1: Audit & Create Root AGENTS.md
**Status:** ✅ Complete

Consolidate `CLAUDE.md`, `.github/copilot-instructions.md`, and `.windsurf/rules/oda-canvas.md` into a single root-level `AGENTS.md`. Create backward-compatible symlinks/redirects.

### Sub-section 2: Create Folder-Level AGENTS.md Hierarchy
**Status:** ✅ Complete

Design and create child `AGENTS.md` files for: `source/`, `source/operators/`, `feature-definition-and-test-kit/`, `usecase-library/`, `charts/`, `canvas-portal/`. Each inherits root context and adds directory-specific conventions.

### Sub-section 3: Audit Custom Agents & Refactor to Skills
**Status:** 🔲 Not started

Evaluate the 3 custom agents against keep/refactor/split criteria:
- `bdd-feature-generator` → likely **Split** (keep thin agent, extract workflow to skill)
- `docs` → likely **Split** (keep thin agent, extract templates to skill)
- `plantuml-renderer` → likely **Keep** as agent (requires specific tooling)

### Sub-section 4: Create New Agent Skills
**Status:** 🔲 Not started

Implement proposed skills: `create-oda-operator`, `write-bdd-feature`, `oda-component-yaml`, `helm-chart-development`, `canvas-usecase-documentation`, `ai-native-component`, `github-actions-debugging`.

### Sub-section 5: Update Documentation & Cleanup
**Status:** 🔲 Not started

Update `ai-coding-assistants.md` and `.github/agents/README.md`. Archive deprecated files. Update `docs/` agent guides.

---

## Sub-section 1: Detailed Plan — Audit & Create Root AGENTS.md

### Context

Three files currently provide AI agent instructions:

| File | Lines | Notes |
|------|-------|-------|
| `CLAUDE.md` | ~140 | Richest content: commands, tech stack, component versions |
| `.github/copilot-instructions.md` | ~55 | Lightest: project context only, unique contribution process items |
| `.windsurf/rules/oda-canvas.md` | ~140 | Verbatim copy of CLAUDE.md with Windsurf YAML frontmatter |

**Key finding:** Windsurf is a verbatim copy of CLAUDE.md. The real merge work is between CLAUDE.md (detailed, command-rich) and copilot-instructions.md (lighter, but has unique contribution/process guidance).

### Content Audit Matrix

| Content | CLAUDE.md | Copilot | Windsurf | Best Source |
|---------|:---------:|:-------:|:--------:|-------------|
| Project Overview | ✅ | ✅ (shorter) | ✅ | CLAUDE.md |
| Key Concepts | ✅ (concise) | ✅ (verbose) | ✅ | **Copilot** — more descriptive |
| Architecture | ✅ (concise) | ✅ (verbose) | ✅ | **Copilot** — more descriptive |
| Project Structure | ✅ | ✅ (shorter) | ✅ | **Merge** — CLAUDE.md base + `docs/` from Copilot |
| Development Guidelines | ✅ (technical) | ✅ (process) | ✅ | **Merge** — combine both sets |
| Development Commands | ✅ | ❌ | ✅ | CLAUDE.md |
| Technology Stack | ✅ | ❌ | ✅ | CLAUDE.md |
| Testing (commands) | ✅ | ❌ | ✅ | CLAUDE.md |
| Testing (compliance prose) | ❌ | ✅ | ❌ | Copilot |
| Important Files | ✅ | ❌ | ✅ | CLAUDE.md |
| Further Documentation refs | ❌ | ✅ | ❌ | Copilot |
| Component Spec Versions | ✅ | ❌ | ✅ | CLAUDE.md |
| CONTRIBUTING.md / ADR refs | ❌ | ✅ | ❌ | Copilot |

### Steps

#### Step 1.1: Draft root AGENTS.md content

Create `AGENTS.md` at repo root with these sections (no YAML frontmatter — not part of the AGENTS.md spec):

1. **Title & Intro** — Tool-agnostic: "Instructions for AI coding agents working in the ODA Canvas repository."
2. **Project Overview** — From CLAUDE.md (mentions K8s Operator Pattern, most complete)
3. **Key Concepts and Terminology** — From copilot-instructions.md (more descriptive per-term explanations)
4. **Modular Architecture** — From copilot-instructions.md (includes decomposition details like "handles decomposition into ExposedAPIs, IdentityConfigs")
5. **Do / Don't Rules** — **New section** following AGENTS.md best practices:
   - Do: use K8s Operator Pattern with kopf, follow v1 CRD schema, write implementation-agnostic BDD features, use PlantUML for diagrams, default to small diffs
   - Don't: hard-code namespaces, add CRD fields without webhook updates, write BDD steps referencing specific operators
6. **Development Commands** — From CLAUDE.md (all 6 subsections: BDD, Vue.js, Java, Python, TMF Services, K8s)
7. **Project Structure** — Merged: CLAUDE.md base + `docs/` entry from Copilot
8. **Technology Stack** — From CLAUDE.md
9. **Development Guidelines** — Merged: CLAUDE.md technical rules (BDD-first, N-2 versions, docstrings, tests) + Copilot process rules (CONTRIBUTING.md, ADR, GitHub issues)
10. **Testing** — From CLAUDE.md commands + Copilot compliance prose merged
11. **Important Files and Documentation** — Merged: CLAUDE.md operational files + Copilot design doc references + Event-based/Observability docs
12. **Component Specification Versions** — From CLAUDE.md
13. **Safety and Permissions** — **New section** following AGENTS.md best practices:
    - Allowed without prompt: read files, run lint, dry-run validation, run individual BDD scenarios
    - Ask first: modifying CRD schemas, changing Helm chart defaults, adding new dependencies
14. **Good and Bad Examples** — **New section**: pointer to preferred patterns (e.g., `source/operators/componentOperator/` for operator pattern)

Target length: ~180-200 lines (reasonable consolidation of ~140 + ~55 with dedup and new sections).

#### Step 1.2: Create backward-compatible redirects

- **CLAUDE.md** — Replace content with a short note redirecting to AGENTS.md. Claude Code reads `AGENTS.md` natively, but keep this file during transition for any direct references. Content: a one-liner saying "See AGENTS.md" plus include the key instruction to read AGENTS.md.
- **`.github/copilot-instructions.md`** — Replace with a thin redirect. VS Code Copilot reads AGENTS.md natively. Content: one-liner pointing to AGENTS.md.
- **`.windsurf/rules/oda-canvas.md`** — Replace with redirect or delete. Windsurf reads AGENTS.md natively. Content: one-liner with `trigger: always_on` frontmatter pointing to root AGENTS.md.

> **Decision:** Use thin text redirects rather than symlinks. Symlinks are fragile on Windows and some CI systems. A 2-line file saying "See [AGENTS.md](../AGENTS.md) for all AI agent instructions" is more portable.

#### Step 1.3: Validate content completeness

After creating AGENTS.md:
- Diff against each original file to confirm no unique content was lost
- Verify all shell commands from CLAUDE.md are preserved
- Verify all documentation references from copilot-instructions.md are preserved
- Verify the new Do/Don't and Safety sections follow the best practices from the issue

#### Step 1.4: Test agent compatibility

- Verify GitHub Copilot picks up AGENTS.md (open VS Code, check Copilot context)
- Verify the redirect in `.github/copilot-instructions.md` doesn't cause issues
- Verify CLAUDE.md redirect is functional for Claude Code users

### Files Changed

| Action | File | Notes |
|--------|------|-------|
| **CREATE** | `AGENTS.md` | New consolidated file (~180-200 lines) |
| **MODIFY** | `CLAUDE.md` | Replace with thin redirect (~5 lines) |
| **MODIFY** | `.github/copilot-instructions.md` | Replace with thin redirect (~5 lines) |
| **MODIFY** | `.windsurf/rules/oda-canvas.md` | Replace with thin redirect (~5 lines) |

### Verification

1. `grep -c "##" AGENTS.md` — should show ~14 section headings
2. Manually review that all 6 Development Commands subsections are present
3. Confirm copilot-instructions.md unique items (CONTRIBUTING.md ref, ADR ref, Event-based/Observability doc refs) are in the merged file
4. Open repo in VS Code, ask Copilot "What is the ODA Canvas?" — should draw from AGENTS.md context
5. Check no broken links in redirect files

### Decisions

- **Thin text redirects over symlinks** — Windows compatibility, CI robustness
- **No YAML frontmatter in AGENTS.md** — not part of the AGENTS.md spec (Windsurf-specific convention dropped)
- **Copilot's verbose Key Concepts preferred** — more descriptive helps agents understand domain concepts
- **New Do/Don't and Safety sections added** — follows issue's best practices guidance
- **~180-200 line target** — consolidation shouldn't exceed the sum of unique content from both primary files

---

## Dependencies Between Sub-sections

```
Sub-section 1 (Root AGENTS.md)
    └──> Sub-section 2 (Folder hierarchy) — child files reference root
    └──> Sub-section 5 (Docs & cleanup) — docs reference new structure

Sub-section 3 (Agent audit) ──> Sub-section 4 (New skills) — refactored agents become skills

Sub-section 4 (New skills) — independent of 1 & 2 but skills may reference AGENTS.md conventions
Sub-section 5 (Docs & cleanup) — depends on 1, 2, 3, 4 being done first (or nearly done)
```

**Recommended execution order:** 1 → 2 → 3 → 4 → 5
(But 3 and 4 can be parallelised with 2 since they're independent of the AGENTS.md hierarchy.)
