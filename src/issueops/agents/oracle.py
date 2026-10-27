"""Deterministic oracle for producing verified ticket-creation traces."""

from issueops.evaluation import snapshot_entities, verify_task
from issueops.specs import TaskSpec, ToolCall, Trajectory, VerificationReport
from issueops.tools import ToolRuntime


class TicketCreationOracle:
    """Execute the known-correct plan used to label generated examples."""

    def run(
        self,
        task: TaskSpec,
        runtime: ToolRuntime,
    ) -> tuple[Trajectory, VerificationReport]:
        issue_id = _issue_id(task)
        issue = runtime.environment.state.business_issues[issue_id]
        before = snapshot_entities(runtime.environment)
        calls = (
            ToolCall("get_business_issue", {"issue_id": issue_id}),
            ToolCall("search_linked_ticket", {"issue_id": issue_id}),
            ToolCall("create_backlog_ticket", {"issue_id": issue_id}),
            ToolCall(
                "add_feature_tag",
                {"ticket_id": f"T-{issue_id}", "tag": issue.affected_product},
            ),
        )
        trajectory = Trajectory(task_id=task.id)
        for call in calls:
            result = runtime.execute(call)
            trajectory.calls.append(call)
            trajectory.results.append(result)
            if not result.ok:
                trajectory.failure_stage = "execution"
                break

        report = verify_task(task, runtime.environment, before)
        trajectory.success = report.success
        if not report.success and trajectory.failure_stage is None:
            trajectory.failure_stage = "verification"
        return trajectory, report


class SprintPlanningOracle:
    """Execute the deterministic priority/capability/capacity planning policy."""

    def run(
        self,
        task: TaskSpec,
        runtime: ToolRuntime,
    ) -> tuple[Trajectory, VerificationReport]:
        before = snapshot_entities(runtime.environment)
        trajectory = Trajectory(task_id=task.id)
        backlog_call = ToolCall("list_backlog_tickets", {})
        backlog_result = runtime.execute(backlog_call)
        trajectory.calls.append(backlog_call)
        trajectory.results.append(backlog_result)
        if backlog_result.ok:
            for ticket in backlog_result.value:
                ticket_id = ticket["id"]
                eligible_call = ToolCall(
                    "list_eligible_developers",
                    {"ticket_id": ticket_id},
                )
                eligible_result = runtime.execute(eligible_call)
                trajectory.calls.append(eligible_call)
                trajectory.results.append(eligible_result)
                if not eligible_result.ok:
                    trajectory.failure_stage = "execution"
                    break
                if not eligible_result.value:
                    continue
                developer_id = eligible_result.value[0]["id"]
                for call in (
                    ToolCall(
                        "assign_ticket",
                        {"ticket_id": ticket_id, "developer_id": developer_id},
                    ),
                    ToolCall("add_ticket_to_sprint", {"ticket_id": ticket_id}),
                ):
                    result = runtime.execute(call)
                    trajectory.calls.append(call)
                    trajectory.results.append(result)
                    if not result.ok:
                        trajectory.failure_stage = "execution"
                        break
                if trajectory.failure_stage:
                    break
        else:
            trajectory.failure_stage = "execution"

        report = verify_task(task, runtime.environment, before)
        trajectory.success = report.success
        if not report.success and trajectory.failure_stage is None:
            trajectory.failure_stage = "verification"
        return trajectory, report


class SprintRolloverOracle:
    """Execute the deterministic rollover policy through allowlisted tools."""

    def run(
        self,
        task: TaskSpec,
        runtime: ToolRuntime,
    ) -> tuple[Trajectory, VerificationReport]:
        before = snapshot_entities(runtime.environment)
        trajectory = Trajectory(task_id=task.id)
        list_call = ToolCall("list_rollover_candidates", {})
        list_result = runtime.execute(list_call)
        trajectory.calls.append(list_call)
        trajectory.results.append(list_result)
        if not list_result.ok:
            trajectory.failure_stage = "execution"
        else:
            start_call = ToolCall("start_next_sprint", {})
            start_result = runtime.execute(start_call)
            trajectory.calls.append(start_call)
            trajectory.results.append(start_result)
            if not start_result.ok:
                trajectory.failure_stage = "execution"

        if trajectory.failure_stage is None:
            for ticket in list_result.value:
                tool = (
                    "defer_blocked_ticket"
                    if ticket["blocked"]
                    else "carry_ticket_to_current_sprint"
                )
                call = ToolCall(tool, {"ticket_id": ticket["id"]})
                result = runtime.execute(call)
                trajectory.calls.append(call)
                trajectory.results.append(result)
                if not result.ok:
                    trajectory.failure_stage = "execution"
                    break

        report = verify_task(task, runtime.environment, before)
        trajectory.success = report.success
        if not report.success and trajectory.failure_stage is None:
            trajectory.failure_stage = "verification"
        return trajectory, report


class PullRequestSynchronizationOracle:
    """Synchronize a PR review and merge lifecycle through allowlisted tools."""

    def run(
        self,
        task: TaskSpec,
        runtime: ToolRuntime,
    ) -> tuple[Trajectory, VerificationReport]:
        before = snapshot_entities(runtime.environment)
        trajectory = Trajectory(task_id=task.id)
        pr_id = _pr_id(task)
        calls = (
            ToolCall("get_pull_request", {"pr_id": pr_id}),
            ToolCall("get_pr_linked_ticket", {"pr_id": pr_id}),
            ToolCall("request_pr_review", {"pr_id": pr_id}),
            ToolCall("record_pr_review", {"pr_id": pr_id, "approved": True}),
            ToolCall("merge_pr", {"pr_id": pr_id}),
        )
        for call in calls:
            result = runtime.execute(call)
            trajectory.calls.append(call)
            trajectory.results.append(result)
            if not result.ok:
                trajectory.failure_stage = "execution"
                break
        report = verify_task(task, runtime.environment, before)
        trajectory.success = report.success
        if not report.success and trajectory.failure_stage is None:
            trajectory.failure_stage = "verification"
        return trajectory, report


class RolloverThenPlanningOracle:
    """Compose the two learned workflows into one held-out executable plan."""

    def run(
        self,
        task: TaskSpec,
        runtime: ToolRuntime,
    ) -> tuple[Trajectory, VerificationReport]:
        before = snapshot_entities(runtime.environment)
        trajectory = Trajectory(task_id=task.id)
        candidates = self._call(trajectory, runtime, "list_rollover_candidates", {})
        if candidates is not None:
            started = self._call(trajectory, runtime, "start_next_sprint", {})
            if started is not None:
                for ticket in candidates:
                    tool = (
                        "defer_blocked_ticket"
                        if ticket["blocked"]
                        else "carry_ticket_to_current_sprint"
                    )
                    if self._call(
                        trajectory,
                        runtime,
                        tool,
                        {"ticket_id": ticket["id"]},
                    ) is None:
                        break

        if trajectory.failure_stage is None:
            backlog = self._call(trajectory, runtime, "list_backlog_tickets", {})
            if backlog is not None:
                for ticket in backlog:
                    eligible = self._call(
                        trajectory,
                        runtime,
                        "list_eligible_developers",
                        {"ticket_id": ticket["id"]},
                    )
                    if eligible is None:
                        break
                    if not eligible:
                        continue
                    developer_id = eligible[0]["id"]
                    if self._call(
                        trajectory,
                        runtime,
                        "assign_ticket",
                        {
                            "ticket_id": ticket["id"],
                            "developer_id": developer_id,
                        },
                    ) is None:
                        break
                    if self._call(
                        trajectory,
                        runtime,
                        "add_ticket_to_sprint",
                        {"ticket_id": ticket["id"]},
                    ) is None:
                        break

        report = verify_task(task, runtime.environment, before)
        trajectory.success = report.success
        if not report.success and trajectory.failure_stage is None:
            trajectory.failure_stage = "verification"
        return trajectory, report

    @staticmethod
    def _call(
        trajectory: Trajectory,
        runtime: ToolRuntime,
        tool: str,
        arguments: dict[str, object],
    ) -> object | None:
        call = ToolCall(tool, arguments)
        result = runtime.execute(call)
        trajectory.calls.append(call)
        trajectory.results.append(result)
        if not result.ok:
            trajectory.failure_stage = "execution"
            return None
        return result.value


def _issue_id(task: TaskSpec) -> str:
    for condition in task.goal_conditions:
        if condition.predicate == "one_ticket_for_issue":
            return condition.arguments[0]
    raise ValueError(f"task {task.id} has no target business issue")


def _pr_id(task: TaskSpec) -> str:
    for condition in task.goal_conditions:
        if condition.predicate == "pr_status":
            return condition.arguments[0]
    raise ValueError(f"task {task.id} has no target pull request")
