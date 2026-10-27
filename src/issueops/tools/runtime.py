"""Constrained tool interface over the in-memory IssueOps environment."""

from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from issueops.environment import InvariantViolation, IssueOpsEnvironment
from issueops.specs import ToolCall, ToolResult

READ_ONLY_TOOL_NAMES = frozenset(
    {
        "get_business_issue",
        "get_pr_linked_ticket",
        "get_pull_request",
        "list_backlog_tickets",
        "list_eligible_developers",
        "list_rollover_candidates",
        "search_linked_ticket",
    }
)


class ToolRuntime:
    """Execute allowlisted tools and convert exceptions into traceable results."""

    def __init__(self, environment: IssueOpsEnvironment) -> None:
        self.environment = environment
        self._tools: dict[str, Callable[..., Any]] = {
            "get_business_issue": self.get_business_issue,
            "search_linked_ticket": self.search_linked_ticket,
            "create_backlog_ticket": self.create_backlog_ticket,
            "add_feature_tag": self.add_feature_tag,
            "list_backlog_tickets": self.list_backlog_tickets,
            "list_eligible_developers": self.list_eligible_developers,
            "assign_ticket": self.assign_ticket,
            "add_ticket_to_sprint": self.add_ticket_to_sprint,
            "list_rollover_candidates": self.list_rollover_candidates,
            "start_next_sprint": self.start_next_sprint,
            "carry_ticket_to_current_sprint": self.carry_ticket_to_current_sprint,
            "defer_blocked_ticket": self.defer_blocked_ticket,
            "get_pull_request": self.get_pull_request,
            "get_pr_linked_ticket": self.get_pr_linked_ticket,
            "request_pr_review": self.request_pr_review,
            "record_pr_review": self.record_pr_review,
            "merge_pr": self.merge_pr,
        }

    @property
    def tool_names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    @property
    def read_only_tool_names(self) -> frozenset[str]:
        return READ_ONLY_TOOL_NAMES

    def execute(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.tool)
        if tool is None:
            return ToolResult(ok=False, error=f"unknown tool: {call.tool}")
        try:
            return ToolResult(ok=True, value=tool(**call.arguments))
        except (InvariantViolation, KeyError, TypeError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def get_business_issue(self, issue_id: str) -> dict[str, Any]:
        try:
            issue = self.environment.state.business_issues[issue_id]
        except KeyError as exc:
            raise InvariantViolation(f"unknown business issue {issue_id}") from exc
        return asdict(issue)

    def search_linked_ticket(self, issue_id: str) -> dict[str, Any] | None:
        ticket = self.environment.search_ticket_by_source_issue(issue_id)
        return asdict(ticket) if ticket else None

    def create_backlog_ticket(self, issue_id: str) -> dict[str, Any]:
        try:
            issue = self.environment.state.business_issues[issue_id]
        except KeyError as exc:
            raise InvariantViolation(f"unknown business issue {issue_id}") from exc
        return asdict(self.environment.create_ticket(issue))

    def add_feature_tag(self, ticket_id: str, tag: str) -> dict[str, Any]:
        return asdict(self.environment.add_feature_tag(ticket_id, tag))

    def list_backlog_tickets(self) -> list[dict[str, Any]]:
        return [asdict(ticket) for ticket in self.environment.list_backlog_tickets()]

    def list_eligible_developers(self, ticket_id: str) -> list[dict[str, Any]]:
        return [
            asdict(developer)
            for developer in self.environment.list_eligible_developers(ticket_id)
        ]

    def assign_ticket(self, ticket_id: str, developer_id: str) -> dict[str, Any]:
        return asdict(self.environment.assign_ticket(ticket_id, developer_id))

    def add_ticket_to_sprint(self, ticket_id: str) -> dict[str, Any]:
        return asdict(self.environment.add_ticket_to_sprint(ticket_id))

    def list_rollover_candidates(self) -> list[dict[str, Any]]:
        return [
            asdict(ticket) for ticket in self.environment.list_rollover_candidates()
        ]

    def start_next_sprint(self) -> int:
        return self.environment.start_next_sprint()

    def carry_ticket_to_current_sprint(self, ticket_id: str) -> dict[str, Any]:
        return asdict(self.environment.carry_ticket_to_current_sprint(ticket_id))

    def defer_blocked_ticket(self, ticket_id: str) -> dict[str, Any]:
        return asdict(self.environment.defer_blocked_ticket(ticket_id))

    def get_pull_request(self, pr_id: str) -> dict[str, Any]:
        return asdict(self.environment.get_pull_request(pr_id))

    def get_pr_linked_ticket(self, pr_id: str) -> dict[str, Any]:
        return asdict(self.environment.get_pr_linked_ticket(pr_id))

    def request_pr_review(self, pr_id: str) -> dict[str, Any]:
        return asdict(self.environment.request_pr_review(pr_id))

    def record_pr_review(self, pr_id: str, approved: bool) -> dict[str, Any]:
        return asdict(self.environment.review_pr(pr_id, approved))

    def merge_pr(self, pr_id: str) -> dict[str, Any]:
        return asdict(self.environment.merge_pr(pr_id))
