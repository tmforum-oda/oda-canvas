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
**Status:** ✅ Complete

Evaluated 3 custom agents and refactored:
- `bdd-feature-generator` → **Split**: thin agent (40 lines) + `write-bdd-feature` skill
- `docs` → **Split**: thin agent (55 lines) + `canvas-usecase-documentation` skill
- `plantuml-renderer` → **Kept** as agent (tooling-dependent, persona-driven)
- Updated `.github/agents/README.md` with skills table and thin-agent architecture docs

### Sub-section 4: Create New Agent Skills
**Status:** ✅ Complete

Implement proposed skills:
- ✅ `write-bdd-feature` — created in Sub-section 3
- ✅ `canvas-usecase-documentation` — created in Sub-section 3
- ✅ `create-oda-operator` — KOPF patterns, handler conventions, Dockerfile, Helm chart
- ✅ `oda-component-yaml` — v1 CRD schema, segments, ExposedAPIs, events, security
- ✅ `helm-chart-development` — umbrella chart, sub-charts, _helpers.tpl, versioning
- ✅ `ai-native-component` — MCP, dependent models, A2A, AI Gateway, evaluation
- ✅ `github-actions-debugging` — CI/CD workflows, Docker builds, test pipeline, debugging

### Sub-section 5: Update Documentation & Cleanup
**Status:** ✅ Complete

Updated `ai-coding-assistants.md` with shared AGENTS.md configuration section, skills table, and corrected references from CLAUDE.md/Windsurf to AGENTS.md. Agents README already updated in Sub-section 3/4.

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

---

## Human Validation Activities

Manual testing activities to verify the new AGENTS.md hierarchy and skills work correctly across tools. Each activity includes the tool, what to do, and what to look for.

### V1. AGENTS.md Context — GitHub Copilot

**Tool:** VS Code with GitHub Copilot  
**Steps:**
1. Open the repository in VS Code
2. Open Copilot Chat (Agent mode)
3. Ask: *"What is the ODA Canvas and what operators does it include?"*
4. Ask: *"What namespace should I deploy components to?"*
5. Ask: *"What BDD framework does this project use?"*

**Expected:** Answers should reference KOPF operators, `components` namespace, and Cucumber.js — all from `AGENTS.md`. No references to stale content from the old `CLAUDE.md` body.

### V2. AGENTS.md Context — Claude Code

**Tool:** Claude Code CLI  
**Steps:**
1. Open terminal in the repo root
2. Run `claude` to start a session
3. Ask: *"Summarise the project structure and technology stack"*
4. Ask: *"What are the rules I should follow when contributing?"*

**Expected:** Answers should draw from `AGENTS.md` Do/Don't rules, project structure section, and technology stack. Verify `CLAUDE.md` redirect doesn't cause errors — Claude should transparently read `AGENTS.md`.

### V3. AGENTS.md Context — Windsurf

**Tool:** Windsurf IDE  
**Steps:**
1. Open the repository in Windsurf
2. Start a Cascade session
3. Ask: *"What Helm chart conventions does this project follow?"*

**Expected:** Answer should reference umbrella chart architecture, prerelease suffixes, `_helpers.tpl` patterns — content from `AGENTS.md` and/or the `charts/AGENTS.md` child file. Verify `.windsurf/rules/oda-canvas.md` redirect works without error.

### V4. Directory-Level AGENTS.md Inheritance

**Tool:** Any AI assistant (Copilot recommended)  
**Steps:**
1. Open a file in `source/operators/component-management/`
2. Ask: *"What handler pattern should I use for a new KOPF operator?"*
3. Open a file in `feature-definition-and-test-kit/features/`
4. Ask: *"What tagging convention should I use for a new BDD feature?"*
5. Open a file in `charts/component-operator/`
6. Ask: *"How should I version this Helm chart?"*

**Expected:** Each answer should incorporate both root `AGENTS.md` conventions AND the directory-specific `AGENTS.md` guidance. The operator question should mention triple-stacked handlers; the BDD question should mention `@UC{number} @UC{number}-F{number}` tags; the Helm question should mention prerelease suffixes.

### V5. Skill Activation — write-bdd-feature

**Tool:** GitHub Copilot (Agent mode)  
**Steps:**
1. Ask: *"Create a BDD feature file for UC009 testing internal authentication with Keycloak"*
2. Review the generated feature file

**Expected:** The skill should activate automatically. Output should include the standard header comment, two-level tagging (`@UC009 @UC009-F001`), `Scenario Outline` with `Examples` table, and steps following patterns from the skill (e.g., `Given a running helm release`). Check that it references existing step definition files rather than inventing new ones.

### V6. Skill Activation — canvas-usecase-documentation

**Tool:** GitHub Copilot (Agent mode)  
**Steps:**
1. Ask: *"Create a use case document for UC013 describing how the Canvas manages PodDisruptionBudgets"*
2. Review the generated markdown

**Expected:** Output should follow the use case template (heading pattern `# {Verb} {Object} use case`, Assumptions section, scenario sections with PlantUML placeholders). Terminology should use "ODA Canvas" (never standalone "Canvas"), "Behaviour-Driven Development" (British spelling), and backtick-wrapped CRD names.

### V7. Skill Activation — create-oda-operator

**Tool:** GitHub Copilot (Agent mode)  
**Steps:**
1. Ask: *"Scaffold a new KOPF operator that watches SecretManagement CRDs and creates Kubernetes Secrets"*
2. Review the generated Python file

**Expected:** Should include `GROUP = "oda.tmforum.org"`, triple-stacked handlers with `retries=5`, `kopf.TemporaryError` for retryable failures, structured logging, and `kubernetes.client.CustomObjectsApi()` calls. Should NOT produce a Go/kubebuilder operator.

### V8. Skill Activation — oda-component-yaml

**Tool:** GitHub Copilot (Agent mode)  
**Steps:**
1. Ask: *"Create an ODA Component YAML for a Product Inventory component with one coreFunction API and a Prometheus metrics endpoint"*
2. Validate the output

**Expected:** `apiVersion: oda.tmforum.org/v1`, `kind: Component`, all three segments present (coreFunction, managementFunction, securityFunction), `apiType: openapi` for core, `apiType: prometheus` for metrics, `canvasSystemRole` in securityFunction.

### V9. Skill Activation — helm-chart-development

**Tool:** GitHub Copilot (Agent mode)  
**Steps:**
1. Ask: *"Create a new Helm sub-chart for a secrets-operator including deployment, RBAC, and configmap templates"*
2. Review the generated chart structure

**Expected:** Should produce `Chart.yaml` (apiVersion v2, type application), `values.yaml` with image/version/prereleaseSuffix, `_helpers.tpl` with Docker image construction helper, `deployment.yaml` using `{{ .Release.Namespace }}` (never hardcoded), and `rbac.yaml` with `zalando.org` peering permissions.

### V10. Skill Activation — github-actions-debugging

**Tool:** GitHub Copilot (Agent mode)  
**Steps:**
1. Ask: *"A BDD test is failing in CI — what debugging steps should I follow?"*
2. Ask: *"How do I modify the Docker build workflow for the component operator?"*

**Expected:** First answer should reference checking operator logs (`kubectl -n canvas logs deployment/component-operator`), uploaded CI artifacts, and common failure table. Second answer should warn that Docker workflows are auto-generated and direct you to `automation/generators/dockerbuild-workflow-generator/dockerbuild-config.yaml` — not to edit the workflow YAML directly.

### V11. Skill Activation — ai-native-component

**Tool:** GitHub Copilot (Agent mode)  
**Steps:**
1. Ask: *"How do I add an MCP server endpoint to an ODA Component?"*
2. Ask: *"Can I declare AI model dependencies in a component YAML?"*

**Expected:** First answer should reference `apiType: mcp` in exposedAPIs, long-running connection considerations, and the test data example in `productcatalog-dynamic-roles-v1`. Second answer should note that `dependentModels` is in the design document but NOT yet in the CRD schema.

### V12. Custom Agent — @bdd-feature-generator (thin agent + skill)

**Tool:** GitHub Copilot Chat  
**Steps:**
1. Invoke: `@bdd-feature-generator Create a feature for UC007-F003 testing dependent API resolution with multiple downstream components`
2. Review generated artifacts

**Expected:** Agent should produce a feature file, check for existing step definitions, suggest new stubs only where needed, and update `feature-definition-and-test-kit/README.md`. Behaviour should be identical to before the refactor — the thin agent loads the `write-bdd-feature` skill transparently.

### V13. Custom Agent — @docs (thin agent + skill)

**Tool:** GitHub Copilot Chat  
**Steps:**
1. Invoke: `@docs Create a README for the secretsmanagement-operator chart`
2. Review generated README

**Expected:** Should follow the Helm Chart README template from the skill, include an Overview, Architecture, Usage Examples, and Troubleshooting section. Should never touch helm-docs markers. Terminology should be consistent ("ODA Canvas", British spelling).

### V14. Redirect File Integrity

**Tool:** Manual inspection  
**Steps:**
1. Open `CLAUDE.md` — verify it contains only a short redirect to `AGENTS.md`
2. Open `.github/copilot-instructions.md` — verify redirect to `AGENTS.md`
3. Open `.windsurf/rules/oda-canvas.md` — verify redirect with `trigger: always_on` frontmatter
4. Verify no residual content (old commands, tech stack, etc.) in any redirect file

**Expected:** Each file should be ≤10 lines. No operational content should remain.

### V15. Cross-Tool Consistency Check

**Tool:** Compare outputs across Copilot, Claude Code, and Windsurf  
**Steps:**
1. Ask all three tools the same question: *"What are the Do and Don't rules for contributing to this project?"*
2. Compare responses

**Expected:** All three should produce substantially similar answers drawn from the same `AGENTS.md` Do/Don't section. Minor phrasing differences are fine, but the factual content should be consistent.

### Validation Summary Checklist

| # | Activity | Tool | Status |
|---|----------|------|--------|
| V1 | AGENTS.md context | Copilot | ⬜ |
| V2 | AGENTS.md context | Claude Code | ⬜ |
| V3 | AGENTS.md context | Windsurf | ⬜ |
| V4 | Directory inheritance | Any | ⬜ |
| V5 | write-bdd-feature skill | Copilot | ⬜ |
| V6 | canvas-usecase-documentation skill | Copilot | ⬜ |
| V7 | create-oda-operator skill | Copilot | ⬜ |
| V8 | oda-component-yaml skill | Copilot | ⬜ |
| V9 | helm-chart-development skill | Copilot | ⬜ |
| V10 | github-actions-debugging skill | Copilot | ⬜ |
| V11 | ai-native-component skill | Copilot | ⬜ |
| V12 | @bdd-feature-generator agent | Copilot | ⬜ |
| V13 | @docs agent | Copilot | ⬜ |
| V14 | Redirect file integrity | Manual | ⬜ |
| V15 | Cross-tool consistency | All | ⬜ |
