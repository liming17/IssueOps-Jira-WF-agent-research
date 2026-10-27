import unittest

from issueops.agents import RolloverThenPlanningOracle
from issueops.datasets import generate_records
from issueops.domain import TicketStatus
from issueops.environment.generator import generate_rollover_then_planning_scenario
from issueops.tools import ToolRuntime


class RolloverThenPlanningTests(unittest.TestCase):
    def test_oracle_completes_one_hundred_heldout_compositions(self) -> None:
        oracle = RolloverThenPlanningOracle()
        for seed in range(100):
            with self.subTest(seed=seed):
                scenario = generate_rollover_then_planning_scenario(seed)
                trajectory, report = oracle.run(
                    scenario.task,
                    ToolRuntime(scenario.environment),
                )
                self.assertTrue(trajectory.success)
                self.assertTrue(report.success)

    def test_rollover_precedes_backlog_planning(self) -> None:
        scenario = generate_rollover_then_planning_scenario(1)
        trajectory, _ = RolloverThenPlanningOracle().run(
            scenario.task,
            ToolRuntime(scenario.environment),
        )
        tools = [call.tool for call in trajectory.calls]
        self.assertLess(
            tools.index("start_next_sprint"),
            tools.index("list_backlog_tickets"),
        )

    def test_infeasible_p0_does_not_block_feasible_p1(self) -> None:
        scenario = generate_rollover_then_planning_scenario(2)
        RolloverThenPlanningOracle().run(
            scenario.task,
            ToolRuntime(scenario.environment),
        )
        new_tickets = {
            ticket.required_capability: ticket
            for ticket in scenario.environment.state.tickets.values()
            if ticket.source_issue_id.startswith("CP-")
        }
        self.assertEqual(TicketStatus.BACKLOG, new_tickets["backend"].status)
        self.assertEqual(TicketStatus.TODO, new_tickets["frontend"].status)
        self.assertEqual("dev-frontend", new_tickets["frontend"].assignee)

    def test_blocked_rollover_ticket_is_not_replanned(self) -> None:
        scenario = generate_rollover_then_planning_scenario(3)
        RolloverThenPlanningOracle().run(
            scenario.task,
            ToolRuntime(scenario.environment),
        )
        blocked = next(
            ticket
            for ticket in scenario.environment.state.tickets.values()
            if ticket.blocked
        )
        self.assertEqual(TicketStatus.BACKLOG, blocked.status)
        self.assertIsNone(blocked.assignee)
        self.assertIsNone(blocked.sprint)

    def test_composed_records_are_serializable(self) -> None:
        records = generate_records(50, 3, family="rollover_then_planning")
        self.assertEqual(3, len(records))
        self.assertTrue(all(record["verification"]["success"] for record in records))
        self.assertTrue(
            all(len(record["task"]["required_skills"]) == 8 for record in records)
        )


if __name__ == "__main__":
    unittest.main()
