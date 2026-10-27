"""Versioned research records for tasks, skills, traces, and verification."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StateCondition:
    """A machine-checkable predicate over the final simulator state."""

    predicate: str
    arguments: tuple[str, ...]


@dataclass(frozen=True)
class TaskSpec:
    """A generated task with provenance and executable success criteria."""

    id: str
    family: str
    instruction: str
    seed: int
    generator_version: str
    required_skills: tuple[str, ...]
    goal_conditions: tuple[StateCondition, ...]
    protected_entities: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillSpec:
    """A reusable, parameterized capability exposed to an agent."""

    name: str
    description: str
    parameters: tuple[str, ...]
    preconditions: tuple[str, ...]
    actions: tuple[str, ...]
    postconditions: tuple[str, ...]
    failure_modes: tuple[str, ...] = ()
    version: str = "1"


@dataclass(frozen=True)
class ToolCall:
    tool: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    value: Any = None
    error: str | None = None


@dataclass
class Trajectory:
    task_id: str
    calls: list[ToolCall] = field(default_factory=list)
    results: list[ToolResult] = field(default_factory=list)
    success: bool = False
    failure_stage: str | None = None


@dataclass(frozen=True)
class VerificationReport:
    success: bool
    satisfied: tuple[str, ...]
    failed: tuple[str, ...]
    unrelated_state_changes: tuple[str, ...]
