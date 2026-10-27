"""Core domain types shared by the simulator, tools, and skills."""

from dataclasses import dataclass, field
from enum import StrEnum


class TicketStatus(StrEnum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"


class PullRequestStatus(StrEnum):
    OPEN = "open"
    REVIEW_REQUESTED = "review_requested"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    MERGED = "merged"


class Priority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"

    @property
    def rank(self) -> int:
        return int(self.value[1:])


@dataclass(frozen=True)
class BusinessIssue:
    id: str
    title: str
    description: str
    priority: Priority
    affected_product: str
    requested_feature: str
    required_capability: str
    estimate: int
    created_at: int


@dataclass
class Ticket:
    id: str
    title: str
    description: str
    priority: Priority
    source_issue_id: str
    feature_tags: frozenset[str]
    required_capability: str
    estimate: int
    created_at: int
    status: TicketStatus = TicketStatus.BACKLOG
    assignee: str | None = None
    sprint: int | None = None
    blocked: bool = False
    blocked_reason: str | None = None


@dataclass
class Developer:
    id: str
    capabilities: frozenset[str]
    capacity: int
    committed: int = 0
    available: bool = True

    @property
    def remaining_capacity(self) -> int:
        return self.capacity - self.committed


@dataclass
class PullRequest:
    id: str
    ticket_id: str
    status: PullRequestStatus = PullRequestStatus.OPEN


@dataclass(frozen=True)
class AuditEvent:
    action: str
    subject_id: str
    detail: str


@dataclass
class WorldState:
    sprint: int = 1
    business_issues: dict[str, BusinessIssue] = field(default_factory=dict)
    tickets: dict[str, Ticket] = field(default_factory=dict)
    developers: dict[str, Developer] = field(default_factory=dict)
    pull_requests: dict[str, PullRequest] = field(default_factory=dict)
    audit: list[AuditEvent] = field(default_factory=list)
