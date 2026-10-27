"""An in-memory, fail-closed IssueOps simulator."""

from issueops.domain import (
    AuditEvent,
    BusinessIssue,
    Developer,
    PullRequest,
    PullRequestStatus,
    Ticket,
    TicketStatus,
    WorldState,
)


class InvariantViolation(ValueError):
    """Raised before an action would make the simulated world invalid."""


class IssueOpsEnvironment:
    def __init__(self, developers: list[Developer] | None = None) -> None:
        self.state = WorldState(
            developers={developer.id: developer for developer in developers or []}
        )

    def register_business_issue(self, issue: BusinessIssue) -> BusinessIssue:
        if issue.id in self.state.business_issues:
            raise InvariantViolation(f"business issue {issue.id} already exists")
        if issue.estimate <= 0:
            raise InvariantViolation("estimate must be positive")
        self.state.business_issues[issue.id] = issue
        self._record("register_business_issue", issue.id, issue.title)
        return issue

    def create_ticket(self, issue: BusinessIssue) -> Ticket:
        ticket_id = f"T-{issue.id}"
        if any(
            ticket.source_issue_id == issue.id for ticket in self.state.tickets.values()
        ):
            raise InvariantViolation(f"business issue {issue.id} already has a ticket")
        if issue.estimate <= 0:
            raise InvariantViolation("estimate must be positive")
        registered = self.state.business_issues.get(issue.id)
        if registered is not None and registered != issue:
            raise InvariantViolation(
                f"business issue {issue.id} does not match registry"
            )
        if registered is None:
            self.state.business_issues[issue.id] = issue
        ticket = Ticket(
            id=ticket_id,
            title=issue.title,
            description=issue.description,
            priority=issue.priority,
            source_issue_id=issue.id,
            feature_tags=frozenset(),
            required_capability=issue.required_capability,
            estimate=issue.estimate,
            created_at=issue.created_at,
        )
        self.state.tickets[ticket.id] = ticket
        self._record("create_ticket", ticket.id, f"from {issue.id}")
        self.verify_invariants()
        return ticket

    def add_feature_tag(self, ticket_id: str, tag: str) -> Ticket:
        if not tag.strip():
            raise InvariantViolation("feature tag cannot be empty")
        ticket = self._ticket(ticket_id)
        ticket.feature_tags = ticket.feature_tags | {tag}
        self._record("add_feature_tag", ticket.id, tag)
        return ticket

    def search_ticket_by_source_issue(self, issue_id: str) -> Ticket | None:
        return next(
            (
                ticket
                for ticket in self.state.tickets.values()
                if ticket.source_issue_id == issue_id
            ),
            None,
        )

    def plan_sprint(self) -> list[Ticket]:
        planned: list[Ticket] = []
        for ticket in self.list_backlog_tickets():
            eligible = self.list_eligible_developers(ticket.id)
            if not eligible:
                continue
            self.assign_ticket(ticket.id, eligible[0].id)
            self.add_ticket_to_sprint(ticket.id)
            planned.append(ticket)
        self.verify_invariants()
        return planned

    def list_backlog_tickets(self) -> list[Ticket]:
        return sorted(
            (
                ticket
                for ticket in self.state.tickets.values()
                if ticket.status == TicketStatus.BACKLOG
            ),
            key=lambda ticket: (ticket.priority.rank, ticket.created_at, ticket.id),
        )

    def list_eligible_developers(self, ticket_id: str) -> list[Developer]:
        ticket = self._ticket(ticket_id)
        if ticket.blocked or ticket.status != TicketStatus.BACKLOG:
            return []
        return sorted(
            (
                developer
                for developer in self.state.developers.values()
                if developer.available
                and ticket.required_capability in developer.capabilities
                and developer.remaining_capacity >= ticket.estimate
            ),
            key=lambda developer: (developer.committed, developer.id),
        )

    def assign_ticket(self, ticket_id: str, developer_id: str) -> Ticket:
        ticket = self._ticket(ticket_id)
        if ticket.status != TicketStatus.BACKLOG:
            raise InvariantViolation("only backlog tickets can be assigned")
        try:
            developer = self.state.developers[developer_id]
        except KeyError as exc:
            raise InvariantViolation(f"unknown developer {developer_id}") from exc
        if not developer.available:
            raise InvariantViolation("developer is unavailable")
        if ticket.required_capability not in developer.capabilities:
            raise InvariantViolation("developer lacks the required capability")
        if developer.remaining_capacity < ticket.estimate:
            raise InvariantViolation("developer lacks remaining capacity")
        ticket.assignee = developer.id
        self._record("assign_ticket", ticket.id, f"assigned to {developer.id}")
        return ticket

    def add_ticket_to_sprint(self, ticket_id: str) -> Ticket:
        ticket = self._ticket(ticket_id)
        if ticket.status != TicketStatus.BACKLOG or ticket.assignee is None:
            raise InvariantViolation("ticket must be assigned from backlog")
        developer = self.state.developers[ticket.assignee]
        if developer.remaining_capacity < ticket.estimate:
            raise InvariantViolation("developer lacks remaining capacity")
        developer.committed += ticket.estimate
        ticket.sprint = self.state.sprint
        ticket.status = TicketStatus.TODO
        self._record("add_ticket_to_sprint", ticket.id, f"sprint {self.state.sprint}")
        return ticket

    def open_pr(self, ticket_id: str, pr_id: str) -> PullRequest:
        ticket = self._ticket(ticket_id)
        if ticket.status != TicketStatus.IN_PROGRESS:
            raise InvariantViolation("PR requires an in-progress ticket")
        if pr_id in self.state.pull_requests:
            existing = self.state.pull_requests[pr_id]
            if existing.ticket_id == ticket_id:
                return existing
            raise InvariantViolation(f"PR {pr_id} already exists for another ticket")
        pr = PullRequest(id=pr_id, ticket_id=ticket_id)
        self.state.pull_requests[pr_id] = pr
        self._record("open_pr", pr_id, f"for {ticket_id}")
        return pr

    def start_ticket(self, ticket_id: str) -> Ticket:
        ticket = self._ticket(ticket_id)
        if ticket.status != TicketStatus.TODO or ticket.blocked:
            raise InvariantViolation("only an unblocked TODO ticket can start")
        ticket.status = TicketStatus.IN_PROGRESS
        self._record("start_ticket", ticket.id, "development started")
        return ticket

    def request_pr_review(self, pr_id: str) -> PullRequest:
        pr = self._pr(pr_id)
        ticket = self._ticket(pr.ticket_id)
        if pr.status in {
            PullRequestStatus.REVIEW_REQUESTED,
            PullRequestStatus.APPROVED,
        }:
            if ticket.status == TicketStatus.IN_REVIEW:
                return pr
        if pr.status not in {
            PullRequestStatus.OPEN,
            PullRequestStatus.CHANGES_REQUESTED,
        }:
            raise InvariantViolation("only an open PR can request review")
        if ticket.status != TicketStatus.IN_PROGRESS or ticket.blocked:
            raise InvariantViolation("review requires an unblocked in-progress ticket")
        pr.status = PullRequestStatus.REVIEW_REQUESTED
        ticket.status = TicketStatus.IN_REVIEW
        self._record("request_pr_review", pr.id, f"moved {ticket.id} to review")
        return pr

    def review_pr(self, pr_id: str, approved: bool) -> PullRequest:
        pr = self._pr(pr_id)
        expected = (
            PullRequestStatus.APPROVED
            if approved
            else PullRequestStatus.CHANGES_REQUESTED
        )
        if pr.status == expected:
            return pr
        if pr.status != PullRequestStatus.REVIEW_REQUESTED:
            raise InvariantViolation("PR must have review requested")
        pr.status = expected
        if not approved:
            self._ticket(pr.ticket_id).status = TicketStatus.IN_PROGRESS
        self._record("review_pr", pr.id, pr.status.value)
        return pr

    def merge_pr(self, pr_id: str) -> Ticket:
        pr = self._pr(pr_id)
        ticket = self._ticket(pr.ticket_id)
        if pr.status == PullRequestStatus.MERGED and ticket.status == TicketStatus.DONE:
            return ticket
        if pr.status != PullRequestStatus.APPROVED:
            raise InvariantViolation("only an approved PR can be merged")
        if ticket.status != TicketStatus.IN_REVIEW:
            raise InvariantViolation("merged PR requires a ticket in review")
        pr.status = PullRequestStatus.MERGED
        ticket.status = TicketStatus.DONE
        self._record("merge_pr", pr.id, f"completed {ticket.id}")
        self.verify_invariants()
        return ticket

    def get_pull_request(self, pr_id: str) -> PullRequest:
        return self._pr(pr_id)

    def get_pr_linked_ticket(self, pr_id: str) -> Ticket:
        return self._ticket(self._pr(pr_id).ticket_id)

    def rollover_sprint(self) -> list[Ticket]:
        candidates = self.list_rollover_candidates()
        self.start_next_sprint()
        rolled: list[Ticket] = []
        for ticket in candidates:
            if ticket.blocked:
                self.defer_blocked_ticket(ticket.id)
                continue
            rolled.append(self.carry_ticket_to_current_sprint(ticket.id))
        self.verify_invariants()
        return rolled

    def list_rollover_candidates(self) -> list[Ticket]:
        return sorted(
            (
                ticket
                for ticket in self.state.tickets.values()
                if ticket.status
                in {
                    TicketStatus.TODO,
                    TicketStatus.IN_PROGRESS,
                    TicketStatus.IN_REVIEW,
                }
                and ticket.sprint == self.state.sprint
            ),
            key=lambda ticket: ticket.id,
        )

    def start_next_sprint(self) -> int:
        previous_sprint = self.state.sprint
        self.state.sprint += 1
        for developer in self.state.developers.values():
            developer.committed = 0
        self._record(
            "start_next_sprint",
            str(self.state.sprint),
            f"closed sprint {previous_sprint}",
        )
        return self.state.sprint

    def carry_ticket_to_current_sprint(self, ticket_id: str) -> Ticket:
        ticket = self._ticket(ticket_id)
        if ticket.status not in {
            TicketStatus.TODO,
            TicketStatus.IN_PROGRESS,
            TicketStatus.IN_REVIEW,
        }:
            raise InvariantViolation("only unfinished active work can roll over")
        if ticket.blocked:
            raise InvariantViolation("blocked ticket cannot roll over")
        if ticket.assignee is None:
            raise InvariantViolation("rollover ticket lacks assignee")
        ticket.sprint = self.state.sprint
        self.state.developers[ticket.assignee].committed += ticket.estimate
        self._record(
            "rollover_ticket",
            ticket.id,
            f"moved to sprint {self.state.sprint}",
        )
        return ticket

    def defer_blocked_ticket(self, ticket_id: str) -> Ticket:
        ticket = self._ticket(ticket_id)
        if not ticket.blocked:
            raise InvariantViolation("only blocked tickets can be deferred")
        if ticket.status not in {
            TicketStatus.TODO,
            TicketStatus.IN_PROGRESS,
            TicketStatus.IN_REVIEW,
        }:
            raise InvariantViolation("only unfinished active work can be deferred")
        ticket.status = TicketStatus.BACKLOG
        ticket.assignee = None
        ticket.sprint = None
        self._record("defer_blocked_ticket", ticket.id, "returned to backlog")
        return ticket

    def set_blocked(self, ticket_id: str, reason: str) -> Ticket:
        if not reason.strip():
            raise InvariantViolation("blocked ticket requires a reason")
        ticket = self._ticket(ticket_id)
        if ticket.status == TicketStatus.DONE:
            raise InvariantViolation("done ticket cannot be blocked")
        ticket.blocked = True
        ticket.blocked_reason = reason
        self._record("block_ticket", ticket.id, reason)
        return ticket

    def clear_blocker(self, ticket_id: str) -> Ticket:
        ticket = self._ticket(ticket_id)
        ticket.blocked = False
        ticket.blocked_reason = None
        self._record("clear_blocker", ticket.id, "blocker resolved")
        return ticket

    def verify_invariants(self) -> None:
        for developer in self.state.developers.values():
            if developer.committed < 0:
                raise InvariantViolation(f"developer {developer.id} has negative load")
        for ticket in self.state.tickets.values():
            if ticket.status in {
                TicketStatus.TODO,
                TicketStatus.IN_PROGRESS,
                TicketStatus.IN_REVIEW,
            }:
                if ticket.assignee is None or ticket.sprint != self.state.sprint:
                    raise InvariantViolation(
                        f"active ticket {ticket.id} lacks assignment"
                    )
            if ticket.blocked != (ticket.blocked_reason is not None):
                raise InvariantViolation(
                    f"ticket {ticket.id} has inconsistent blocker state"
                )
            if ticket.source_issue_id not in self.state.business_issues:
                raise InvariantViolation(f"ticket {ticket.id} lacks a source issue")
            if ticket.status == TicketStatus.DONE:
                merged = any(
                    pr.ticket_id == ticket.id and pr.status == PullRequestStatus.MERGED
                    for pr in self.state.pull_requests.values()
                )
                if not merged:
                    raise InvariantViolation(f"done ticket {ticket.id} lacks merged PR")

    def _ticket(self, ticket_id: str) -> Ticket:
        try:
            return self.state.tickets[ticket_id]
        except KeyError as exc:
            raise InvariantViolation(f"unknown ticket {ticket_id}") from exc

    def _pr(self, pr_id: str) -> PullRequest:
        try:
            return self.state.pull_requests[pr_id]
        except KeyError as exc:
            raise InvariantViolation(f"unknown PR {pr_id}") from exc

    def _record(self, action: str, subject_id: str, detail: str) -> None:
        self.state.audit.append(AuditEvent(action, subject_id, detail))
