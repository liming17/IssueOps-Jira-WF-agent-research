"""State-based verification for generated IssueOps tasks."""

from dataclasses import asdict
from typing import Any

from issueops.domain import TicketStatus
from issueops.environment import IssueOpsEnvironment
from issueops.specs import StateCondition, TaskSpec, VerificationReport


def snapshot_entities(
    environment: IssueOpsEnvironment,
) -> dict[str, dict[str, Any]]:
    """Capture entities that must remain unchanged unless a task targets them."""

    state = environment.state
    return {
        **{f"ticket:{key}": asdict(value) for key, value in state.tickets.items()},
        **{
            f"developer:{key}": asdict(value) for key, value in state.developers.items()
        },
        **{f"pr:{key}": asdict(value) for key, value in state.pull_requests.items()},
    }


def verify_task(
    task: TaskSpec,
    environment: IssueOpsEnvironment,
    before: dict[str, dict[str, Any]],
) -> VerificationReport:
    satisfied: list[str] = []
    failed: list[str] = []
    for condition in task.goal_conditions:
        label = f"{condition.predicate}{condition.arguments}"
        if _evaluate(condition, environment):
            satisfied.append(label)
        else:
            failed.append(label)

    after = snapshot_entities(environment)
    unrelated_changes = tuple(
        entity_id
        for entity_id in task.protected_entities
        if before.get(entity_id) != after.get(entity_id)
    )
    return VerificationReport(
        success=not failed and not unrelated_changes,
        satisfied=tuple(satisfied),
        failed=tuple(failed),
        unrelated_state_changes=unrelated_changes,
    )


def _evaluate(condition: StateCondition, environment: IssueOpsEnvironment) -> bool:
    state = environment.state
    predicate = condition.predicate
    arguments = condition.arguments
    if predicate == "current_sprint":
        (expected,) = arguments
        return state.sprint == int(expected)
    if predicate == "one_ticket_for_issue":
        (issue_id,) = arguments
        return sum(t.source_issue_id == issue_id for t in state.tickets.values()) == 1

    if predicate == "ticket_status_by_id":
        ticket_id, expected = arguments
        ticket = state.tickets.get(ticket_id)
        return ticket is not None and ticket.status == TicketStatus(expected)
    if predicate == "ticket_assignee":
        ticket_id, expected = arguments
        ticket = state.tickets.get(ticket_id)
        return ticket is not None and ticket.assignee == expected
    if predicate == "ticket_sprint":
        ticket_id, expected = arguments
        ticket = state.tickets.get(ticket_id)
        return ticket is not None and ticket.sprint == int(expected)
    if predicate == "ticket_has_no_sprint":
        (ticket_id,) = arguments
        ticket = state.tickets.get(ticket_id)
        return ticket is not None and ticket.sprint is None
    if predicate == "ticket_has_no_assignee":
        (ticket_id,) = arguments
        ticket = state.tickets.get(ticket_id)
        return ticket is not None and ticket.assignee is None
    if predicate == "ticket_blocked":
        ticket_id, expected = arguments
        ticket = state.tickets.get(ticket_id)
        return ticket is not None and ticket.blocked is (expected == "true")
    if predicate == "ticket_blocked_reason":
        ticket_id, expected = arguments
        ticket = state.tickets.get(ticket_id)
        return ticket is not None and ticket.blocked_reason == expected
    if predicate == "ticket_priority_by_id":
        ticket_id, expected = arguments
        ticket = state.tickets.get(ticket_id)
        return ticket is not None and ticket.priority.value == expected
    if predicate == "ticket_source_issue":
        ticket_id, expected = arguments
        ticket = state.tickets.get(ticket_id)
        return ticket is not None and ticket.source_issue_id == expected
    if predicate == "ticket_feature_tags":
        ticket_id, expected = arguments
        ticket = state.tickets.get(ticket_id)
        return ticket is not None and ",".join(sorted(ticket.feature_tags)) == expected
    if predicate == "developer_committed":
        developer_id, expected = arguments
        developer = state.developers.get(developer_id)
        return developer is not None and developer.committed == int(expected)
    if predicate == "pr_status":
        pr_id, expected = arguments
        pr = state.pull_requests.get(pr_id)
        return pr is not None and pr.status.value == expected
    if predicate == "pr_linked_ticket":
        pr_id, expected = arguments
        pr = state.pull_requests.get(pr_id)
        return pr is not None and pr.ticket_id == expected

    issue_id, expected = arguments
    ticket = environment.search_ticket_by_source_issue(issue_id)
    issue = state.business_issues.get(issue_id)
    if ticket is None or issue is None:
        return False
    if predicate == "ticket_priority":
        return ticket.priority.value == expected
    if predicate == "ticket_description":
        return ticket.description == expected
    if predicate == "ticket_feature_tag":
        return expected in ticket.feature_tags
    if predicate == "ticket_status":
        return ticket.status == TicketStatus(expected)
    raise ValueError(f"unknown state predicate: {predicate}")
