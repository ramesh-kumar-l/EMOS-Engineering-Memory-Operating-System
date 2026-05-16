from dataclasses import dataclass, field


@dataclass
class StepDefinition:
    name: str
    description: str
    requires_human_approval: bool = True


@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str
    steps: list[StepDefinition] = field(default_factory=list)


WORKFLOW_DEFINITIONS: dict[str, WorkflowDefinition] = {
    "WF-001": WorkflowDefinition(
        id="WF-001",
        name="Architecture Review",
        description="Validate a new component or system design before implementation.",
        steps=[
            StepDefinition("Load relevant memory", "Load architecture.md, decisions.md, constraints.md"),
            StepDefinition("Analyze proposed design", "Analyze design against documented constraints"),
            StepDefinition("Identify coupling risks", "Identify coupling risks and dependency issues"),
            StepDefinition("Reliability check", "Verify all dependencies are real and validated"),
            StepDefinition("Identify failure modes", "Enumerate potential failure scenarios"),
            StepDefinition("Generate review document", "Produce architecture review document"),
            StepDefinition("Human review", "Human reviews and approves or rejects design"),
            StepDefinition("Update decisions.md", "Record outcome in decisions.md"),
        ],
    ),
    "WF-002": WorkflowDefinition(
        id="WF-002",
        name="Implementation",
        description="Implement a feature reliably with memory-grounded context.",
        steps=[
            StepDefinition("Load relevant memory", "Load architecture.md, roadmap.md, technical-debt.md"),
            StepDefinition("Load repo intelligence", "Load repo structure and existing patterns"),
            StepDefinition("Assemble context package", "Assemble context package for Claude"),
            StepDefinition("Generate implementation plan", "Generate plan — not code yet"),
            StepDefinition("Human reviews plan", "Human reviews and approves the plan"),
            StepDefinition("Generate code", "Generate code in small verified steps"),
            StepDefinition("Reliability review", "Run reliability review on generated code"),
            StepDefinition("Human reviews code", "Human reviews and approves each step"),
            StepDefinition("Update roadmap and changelog", "Record progress in roadmap.md and changelog.md"),
        ],
    ),
    "WF-003": WorkflowDefinition(
        id="WF-003",
        name="Debugging",
        description="Diagnose and resolve engineering issues with context continuity.",
        steps=[
            StepDefinition("Load relevant memory", "Load lessons.md, technical-debt.md, evaluations.md"),
            StepDefinition("Characterize failure", "Document symptoms, reproduction steps, and impact"),
            StepDefinition("Load repo intelligence", "Load repo intelligence for affected components"),
            StepDefinition("Hypothesize root causes", "Rank hypotheses by likelihood"),
            StepDefinition("Validate hypotheses", "Validate against known facts (reliability check)"),
            StepDefinition("Generate fix", "Generate targeted fix"),
            StepDefinition("Human approves fix", "Human reviews and approves the fix"),
            StepDefinition("Update lessons.md", "Record root cause and resolution in lessons.md"),
        ],
    ),
    "WF-004": WorkflowDefinition(
        id="WF-004",
        name="Evaluation",
        description="Assess system reliability, correctness, and quality.",
        steps=[
            StepDefinition("Load reliability data", "Load reliability-status.md and evaluations.md"),
            StepDefinition("Define evaluation criteria", "Define criteria for this evaluation"),
            StepDefinition("Run checks", "Run checks against criteria"),
            StepDefinition("Assign confidence scores", "Assign scores to each check"),
            StepDefinition("Flag risks and gaps", "Identify and document risks"),
            StepDefinition("Generate evaluation report", "Produce evaluation report"),
            StepDefinition("Update reliability docs", "Update reliability-status.md and evaluations.md"),
        ],
    ),
    "WF-005": WorkflowDefinition(
        id="WF-005",
        name="Documentation",
        description="Generate and maintain engineering documentation.",
        steps=[
            StepDefinition("Load relevant memory and repo data", "Load memory bank and repo intelligence"),
            StepDefinition("Identify documentation gaps", "Find missing or outdated docs"),
            StepDefinition("Generate documentation", "Generate docs using templates"),
            StepDefinition("Human review", "Human reviews and approves documentation"),
            StepDefinition("Write to memory bank", "Commit approved docs to memory bank"),
        ],
    ),
    "WF-006": WorkflowDefinition(
        id="WF-006",
        name="Release Preparation",
        description="Prepare a reliable, auditable release.",
        steps=[
            StepDefinition("Load release docs", "Load roadmap.md, changelog.md, technical-debt.md"),
            StepDefinition("Validate P0 features", "Confirm all P0 features are complete"),
            StepDefinition("Run evaluation workflow", "Execute WF-004 evaluation"),
            StepDefinition("Document known issues", "Identify and document known issues"),
            StepDefinition("Generate release notes", "Produce release notes"),
            StepDefinition("Human approves release", "Human reviews and approves the release"),
            StepDefinition("Update changelog", "Update changelog.md and reliability-status.md"),
        ],
    ),
}
