import copy
import unittest

from issueops.agents import PullRequestSynchronizationOracle
from issueops.datasets import generate_records
from issueops.domain import PullRequest, PullRequestStatus, TicketStatus
from issueops.environment.generator import generate_pr_synchronization_scenario
from issueops.specs import ToolCall
from issueops.tools import ToolRuntime


class PullRequestSynchronizationTests(unittest.TestCase):
    def test_oracle_completes_one_hundred_generated_tasks(self) -> None:
        oracle = PullRequestSynchronizationOracle()
        for seed in range(100):
            with self.subTest(seed=seed):
                scenario = generate_pr_synchronization_scenario(seed)
                trajectory, report = oracle.run(
                    scenario.task,
                    ToolRuntime(scenario.environment),
                )
                self.assertTrue(trajectory.success)
                self.assertTrue(report.success)

    def test_review_and_merge_events_are_idempotent(self) -> None:
        scenario = generate_pr_synchronization_scenario(2)
        runtime = ToolRuntime(scenario.environment)
        pr_id = next(iter(scenario.environment.state.pull_requests))
        calls = (
            ToolCall("request_pr_review", {"pr_id": pr_id}),
            ToolCall("request_pr_review", {"pr_id": pr_id}),
            ToolCall("record_pr_review", {"pr_id": pr_id, "approved": True}),
            ToolCall("record_pr_review", {"pr_id": pr_id, "approved": True}),
            ToolCall("merge_pr", {"pr_id": pr_id}),
            ToolCall("merge_pr", {"pr_id": pr_id}),
        )
        self.assertTrue(all(runtime.execute(call).ok for call in calls))
        pr = scenario.environment.state.pull_requests[pr_id]
        ticket = scenario.environment.state.tickets[pr.ticket_id]
        self.assertEqual(PullRequestStatus.MERGED, pr.status)
        self.assertEqual(TicketStatus.DONE, ticket.status)

    def test_merge_before_review_is_rejected(self) -> None:
        scenario = generate_pr_synchronization_scenario(3)
        runtime = ToolRuntime(scenario.environment)
        pr_id = next(iter(scenario.environment.state.pull_requests))
        result = runtime.execute(ToolCall("merge_pr", {"pr_id": pr_id}))
        self.assertFalse(result.ok)
        self.assertIn("approved", result.error or "")

    def test_broken_pr_ticket_link_is_rejected(self) -> None:
        scenario = generate_pr_synchronization_scenario(4)
        broken = PullRequest("BROKEN-PR", "missing-ticket")
        scenario.environment.state.pull_requests[broken.id] = broken
        result = ToolRuntime(scenario.environment).execute(
            ToolCall("get_pr_linked_ticket", {"pr_id": broken.id})
        )
        self.assertFalse(result.ok)
        self.assertIn("unknown ticket", result.error or "")

    def test_unrelated_ticket_and_developers_remain_unchanged(self) -> None:
        scenario = generate_pr_synchronization_scenario(5)
        pr = next(iter(scenario.environment.state.pull_requests.values()))
        unrelated = next(
            ticket
            for ticket in scenario.environment.state.tickets.values()
            if ticket.id != pr.ticket_id
        )
        before_ticket = copy.deepcopy(unrelated)
        before_developers = copy.deepcopy(scenario.environment.state.developers)
        PullRequestSynchronizationOracle().run(
            scenario.task,
            ToolRuntime(scenario.environment),
        )
        self.assertEqual(before_ticket, unrelated)
        self.assertEqual(before_developers, scenario.environment.state.developers)

    def test_pr_records_are_serializable(self) -> None:
        records = generate_records(40, 3, family="pr_synchronization")
        self.assertEqual(3, len(records))
        self.assertTrue(all(record["verification"]["success"] for record in records))


if __name__ == "__main__":
    unittest.main()
