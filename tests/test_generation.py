import json
import unittest

from issueops.agents import TicketCreationOracle
from issueops.datasets import generate_records
from issueops.environment.generator import generate_ticket_creation_scenario
from issueops.evaluation import verify_task
from issueops.specs import ToolCall
from issueops.tools import ToolRuntime


class TicketCreationGenerationTests(unittest.TestCase):
    def test_generated_records_are_json_serializable(self) -> None:
        records = generate_records(start_seed=10, count=3)
        self.assertEqual(3, len(records))
        json.dumps(records)

    def test_same_seed_reproduces_task_and_world(self) -> None:
        first = generate_ticket_creation_scenario(42)
        second = generate_ticket_creation_scenario(42)
        self.assertEqual(first.task, second.task)
        self.assertEqual(
            first.environment.state.business_issues,
            second.environment.state.business_issues,
        )

    def test_oracle_completes_one_hundred_generated_tasks(self) -> None:
        oracle = TicketCreationOracle()
        for seed in range(100):
            with self.subTest(seed=seed):
                scenario = generate_ticket_creation_scenario(seed)
                trajectory, report = oracle.run(
                    scenario.task,
                    ToolRuntime(scenario.environment),
                )
                self.assertTrue(trajectory.success)
                self.assertTrue(report.success)
                self.assertEqual(4, len(trajectory.calls))

    def test_wrong_feature_tag_fails_state_verification(self) -> None:
        scenario = generate_ticket_creation_scenario(7)
        runtime = ToolRuntime(scenario.environment)
        issue_id = next(iter(scenario.environment.state.business_issues))
        runtime.execute(ToolCall("create_backlog_ticket", {"issue_id": issue_id}))
        runtime.execute(
            ToolCall(
                "add_feature_tag",
                {"ticket_id": f"T-{issue_id}", "tag": "wrong-product"},
            )
        )
        report = verify_task(
            scenario.task,
            scenario.environment,
            scenario.initial_snapshot,
        )
        self.assertFalse(report.success)
        self.assertTrue(any("ticket_feature_tag" in item for item in report.failed))

    def test_unknown_tool_fails_closed(self) -> None:
        scenario = generate_ticket_creation_scenario(1)
        result = ToolRuntime(scenario.environment).execute(ToolCall("shell", {}))
        self.assertFalse(result.ok)
        self.assertIn("unknown tool", result.error or "")


if __name__ == "__main__":
    unittest.main()
