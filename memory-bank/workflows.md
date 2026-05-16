# Engineering Workflows

## Workflow Principles
- Every workflow is deterministic and auditable
- No autonomous execution; human confirms each step
- Workflows are defined in YAML (when implemented)
- All workflow outputs are written to memory bank

---

## WF-001: Architecture Review Workflow

**Purpose:** Validate a new component or system design before implementation.

**Steps:**
1. Load relevant memory (architecture.md, decisions.md, constraints.md)
2. Analyze proposed design against constraints
3. Identify coupling risks and dependency issues
4. Run reliability check (are all dependencies real and validated?)
5. Identify failure modes
6. Generate architecture review document
7. Human reviews and approves/rejects
8. Update decisions.md with outcome

---

## WF-002: Implementation Workflow

**Purpose:** Implement a feature reliably with memory-grounded context.

**Steps:**
1. Load relevant memory (architecture.md, roadmap.md, technical-debt.md)
2. Load repo intelligence (structure, existing patterns)
3. Assemble context package for Claude
4. Generate implementation plan (not code yet)
5. Human reviews plan
6. Generate code in small verified steps
7. Run reliability review on generated code
8. Human reviews and approves each step
9. Update roadmap.md and changelog.md

---

## WF-003: Debugging Workflow

**Purpose:** Diagnose and resolve engineering issues with context continuity.

**Steps:**
1. Load relevant memory (lessons.md, technical-debt.md, evaluations.md)
2. Characterize the failure (symptoms, reproduction, impact)
3. Load repo intelligence for affected components
4. Hypothesize root causes (ranked by likelihood)
5. Validate hypotheses against known facts (reliability check)
6. Generate targeted fix
7. Human approves fix
8. Update lessons.md with root cause and resolution

---

## WF-004: Evaluation Workflow

**Purpose:** Assess system reliability, correctness, and quality.

**Steps:**
1. Load reliability-status.md and evaluations.md
2. Define evaluation criteria
3. Run checks against criteria
4. Assign confidence scores
5. Flag risks and gaps
6. Generate evaluation report
7. Update reliability-status.md and evaluations.md

---

## WF-005: Documentation Workflow

**Purpose:** Generate and maintain engineering documentation.

**Steps:**
1. Load relevant memory and repo intelligence
2. Identify documentation gaps
3. Generate documentation using templates
4. Human reviews and approves
5. Write approved documentation to memory bank

---

## WF-006: Release Preparation Workflow

**Purpose:** Prepare a reliable, auditable release.

**Steps:**
1. Load roadmap.md, changelog.md, technical-debt.md
2. Validate all P0 features complete
3. Run full evaluation workflow
4. Identify known issues and document them
5. Generate release notes
6. Human approves release
7. Update changelog.md and reliability-status.md
