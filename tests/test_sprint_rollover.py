import copy
import unittest

from issueops.agents import SprintRolloverOracle
from issueops.datasets import generate_records
from issueops.domain import BusinessIssue, Priority, TicketStatus
from issueops.environment.generator import generate_sprint_rollover_scenario
from issueops.specs import ToolCall
from issueops.tools import ToolRuntime


class SprintRolloverGenerationTests(unittest.TestCase):
    def test_oracle_completes_one_hundred_generated_tasks(self) -> None:
        oracle = SprintRolloverOracle()
        for seed in range(100):
            with self.subTest(seed=seed):
                scenario = generate_sprint_rollover_scenario(seed)
                trajectory, report = oracle.run(
                    scenario.task,
                    ToolRuntime(scenario.environment),
                )
                self.assertTrue(trajectory.success)
                self.assertTrue(report.success)

    def test_rollover_allows_existing_over_capacity_work(self) -> None:
        scenario = generate_sprint_rollover_scenario(4)
        SprintRolloverOracle().run(
            scenario.task,
            ToolRuntime(scenario.environment),
        )
        developer = scenario.environment.state.developers["dev-backend"]
        self.assertEqual(7, developer.committed)
        self.assertEqual(5, developer.capacity)
        self.assertLess(developer.remaining_capacity, 0)

    def test_over_capacity_developer_cannot_receive_new_work(self) -> None:
        scenario = generate_sprint_rollover_scenario(5)
        SprintRolloverOracle().run(
            scenario.task,
            ToolRuntime(scenario.environment),
        )
        issue = BusinessIssue(
            "NEW-1",
            "New backend work",
            "Should remain in backlog.",
            Priority.P0,
            "billing",
            "new_backend",
            "backend",
            1,
            999,
        )
        scenario.environment.register_business_issue(issue)
        ticket = scenario.environment.create_ticket(issue)
        self.assertEqual([], scenario.environment.list_eligible_developers(ticket.id))

    def test_done_ticket_and_merged_pr_are_unchanged(self) -> None:
        scenario = generate_sprint_rollover_scenario(6)
        done = next(
            ticket
            for ticket in scenario.environment.state.tickets.values()
            if ticket.status == TicketStatus.DONE
        )
        before_ticket = copy.deepcopy(done)
        before_prs = copy.deepcopy(scenario.environment.state.pull_requests)
        SprintRolloverOracle().run(
            scenario.task,
            ToolRuntime(scenario.environment),
        )
        self.assertEqual(before_ticket, done)
        self.assertEqual(before_prs, scenario.environment.state.pull_requests)

    def test_blocked_ticket_cannot_be_carried(self) -> None:
        scenario = generate_sprint_rollover_scenario(7)
        blocked = next(
            ticket
            for ticket in scenario.environment.state.tickets.values()
            if ticket.blocked
        )
        runtime = ToolRuntime(scenario.environment)
        runtime.execute(ToolCall("start_next_sprint", {}))
        result = runtime.execute(
            ToolCall(
                "carry_ticket_to_current_sprint",
                {"ticket_id": blocked.id},
            )
        )
        self.assertFalse(result.ok)
        self.assertIn("blocked", result.error or "")

    def test_rollover_records_are_serializable(self) -> None:
        records = generate_records(30, 3, family="sprint_rollover")
        self.assertEqual(3, len(records))
        self.assertTrue(all(record["verification"]["success"] for record in records))


if __name__ == "__main__":
    unittest.main()
