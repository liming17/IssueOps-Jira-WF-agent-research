import unittest

from issueops.agents import SprintPlanningOracle
from issueops.datasets import generate_records
from issueops.domain import TicketStatus
from issueops.environment.generator import generate_sprint_planning_scenario
from issueops.specs import ToolCall
from issueops.tools import ToolRuntime


class SprintPlanningGenerationTests(unittest.TestCase):
    def test_oracle_completes_one_hundred_generated_tasks(self) -> None:
        oracle = SprintPlanningOracle()
        for seed in range(100):
            with self.subTest(seed=seed):
                scenario = generate_sprint_planning_scenario(seed)
                trajectory, report = oracle.run(
                    scenario.task,
                    ToolRuntime(scenario.environment),
                )
                self.assertTrue(trajectory.success)
                self.assertTrue(report.success)

    def test_mobile_ticket_without_capable_developer_stays_unchanged(self) -> None:
        scenario = generate_sprint_planning_scenario(3)
        mobile = next(
            ticket
            for ticket in scenario.environment.state.tickets.values()
            if ticket.required_capability == "mobile"
        )
        SprintPlanningOracle().run(
            scenario.task,
            ToolRuntime(scenario.environment),
        )
        self.assertEqual(TicketStatus.BACKLOG, mobile.status)
        self.assertIsNone(mobile.assignee)
        self.assertIsNone(mobile.sprint)

    def test_ineligible_assignment_fails_closed(self) -> None:
        scenario = generate_sprint_planning_scenario(5)
        mobile = next(
            ticket
            for ticket in scenario.environment.state.tickets.values()
            if ticket.required_capability == "mobile"
        )
        result = ToolRuntime(scenario.environment).execute(
            ToolCall(
                "assign_ticket",
                {"ticket_id": mobile.id, "developer_id": "dev-backend"},
            )
        )
        self.assertFalse(result.ok)
        self.assertIn("required capability", result.error or "")

    def test_sprint_records_are_serializable(self) -> None:
        records = generate_records(20, 3, family="sprint_planning")
        self.assertEqual(3, len(records))
        self.assertTrue(all(record["verification"]["success"] for record in records))


if __name__ == "__main__":
    unittest.main()
