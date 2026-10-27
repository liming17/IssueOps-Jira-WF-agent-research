import copy
import unittest

from issueops.domain import (
    BusinessIssue,
    Developer,
    Priority,
    PullRequestStatus,
    TicketStatus,
)
from issueops.environment import InvariantViolation, IssueOpsEnvironment


def issue(
    issue_id: str,
    *,
    priority: Priority = Priority.P1,
    capability: str = "backend",
    estimate: int = 3,
    created_at: int = 1,
) -> BusinessIssue:
    return BusinessIssue(
        id=issue_id,
        title=f"Issue {issue_id}",
        description=f"Business request {issue_id}",
        priority=priority,
        affected_product="billing",
        requested_feature="invoice_export",
        required_capability=capability,
        estimate=estimate,
        created_at=created_at,
    )


class IssueOpsEnvironmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = IssueOpsEnvironment(
            [
                Developer("alice", frozenset({"backend"}), capacity=5),
                Developer("bob", frozenset({"frontend"}), capacity=3),
            ]
        )

    def test_ticket_copies_business_fields_and_prevents_duplicates(self) -> None:
        business_issue = issue("1", priority=Priority.P0)
        ticket = self.environment.create_ticket(business_issue)
        self.environment.add_feature_tag(ticket.id, business_issue.affected_product)
        self.assertEqual(business_issue.id, ticket.source_issue_id)
        self.assertEqual(business_issue.description, ticket.description)
        self.assertEqual(business_issue.priority, ticket.priority)
        self.assertEqual(frozenset({"billing"}), ticket.feature_tags)
        with self.assertRaises(InvariantViolation):
            self.environment.create_ticket(business_issue)

    def test_planning_respects_priority_capability_and_capacity(self) -> None:
        low = self.environment.create_ticket(
            issue("2", priority=Priority.P2, estimate=3, created_at=1)
        )
        high = self.environment.create_ticket(
            issue("1", priority=Priority.P0, estimate=4, created_at=2)
        )
        planned = self.environment.plan_sprint()
        self.assertEqual([high.id], [ticket.id for ticket in planned])
        self.assertEqual(TicketStatus.BACKLOG, low.status)
        self.assertEqual("alice", high.assignee)

    def test_review_request_and_merge_drive_ticket_lifecycle(self) -> None:
        ticket = self.environment.create_ticket(issue("1"))
        self.environment.plan_sprint()
        self.environment.start_ticket(ticket.id)
        pr = self.environment.open_pr(ticket.id, "PR-1")
        self.assertEqual(TicketStatus.IN_PROGRESS, ticket.status)
        self.environment.request_pr_review(pr.id)
        self.assertEqual(TicketStatus.IN_REVIEW, ticket.status)
        self.environment.review_pr(pr.id, approved=True)
        completed = self.environment.merge_pr(pr.id)
        self.assertEqual(PullRequestStatus.MERGED, pr.status)
        self.assertEqual(TicketStatus.DONE, completed.status)

    def test_merge_requires_review_and_approval(self) -> None:
        ticket = self.environment.create_ticket(issue("1"))
        self.environment.plan_sprint()
        self.environment.start_ticket(ticket.id)
        pr = self.environment.open_pr(ticket.id, "PR-1")
        with self.assertRaises(InvariantViolation):
            self.environment.merge_pr(pr.id)

    def test_unblocked_work_rolls_over_and_keeps_assignment(self) -> None:
        ticket = self.environment.create_ticket(issue("1"))
        self.environment.plan_sprint()
        rolled = self.environment.rollover_sprint()
        self.assertEqual([ticket.id], [item.id for item in rolled])
        self.assertEqual(TicketStatus.TODO, ticket.status)
        self.assertEqual("alice", ticket.assignee)
        self.assertEqual(2, ticket.sprint)
        self.assertEqual(
            ticket.estimate,
            self.environment.state.developers["alice"].committed,
        )

    def test_blocked_work_returns_to_backlog(self) -> None:
        ticket = self.environment.create_ticket(issue("1"))
        self.environment.plan_sprint()
        self.environment.set_blocked(ticket.id, "Waiting for vendor")
        rolled = self.environment.rollover_sprint()
        self.assertEqual([], rolled)
        self.assertEqual(TicketStatus.BACKLOG, ticket.status)
        self.assertIsNone(ticket.assignee)
        self.assertIsNone(ticket.sprint)

    def test_pr_event_does_not_modify_unrelated_ticket(self) -> None:
        target = self.environment.create_ticket(issue("1", estimate=2))
        unrelated = self.environment.create_ticket(issue("2", estimate=2))
        self.environment.plan_sprint()
        before = copy.deepcopy(unrelated)
        self.environment.start_ticket(target.id)
        pr = self.environment.open_pr(target.id, "PR-1")
        self.environment.request_pr_review(pr.id)
        self.assertEqual(before, unrelated)


if __name__ == "__main__":
    unittest.main()
