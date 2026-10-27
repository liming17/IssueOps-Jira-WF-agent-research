"""Reproducible synthetic scenarios for IssueOps research."""

import copy
import random
from dataclasses import dataclass

from issueops.domain import (
    BusinessIssue,
    Developer,
    Priority,
    PullRequest,
    PullRequestStatus,
    Ticket,
    TicketStatus,
)
from issueops.environment.simulator import IssueOpsEnvironment
from issueops.evaluation import snapshot_entities
from issueops.specs import StateCondition, TaskSpec

GENERATOR_VERSION = "ticket-creation-v1"


@dataclass
class GeneratedScenario:
    task: TaskSpec
    environment: IssueOpsEnvironment
    initial_snapshot: dict[str, dict[str, object]]


def generate_ticket_creation_scenario(seed: int) -> GeneratedScenario:
    """Create one deterministic business issue with a verified task contract."""

    rng = random.Random(seed)
    products = (
        ("billing", "invoice_export", "backend"),
        ("accounts", "account_settings", "frontend"),
        ("compliance", "audit_export", "backend"),
        ("checkout", "payment_recovery", "backend"),
    )
    product, feature, capability = rng.choice(products)
    priority = rng.choice(tuple(Priority))
    issue_id = f"BI-{seed:06d}"
    issue = BusinessIssue(
        id=issue_id,
        title=f"Add {feature.replace('_', ' ')}",
        description=f"Business requests {feature.replace('_', ' ')} for {product}.",
        priority=priority,
        affected_product=product,
        requested_feature=feature,
        required_capability=capability,
        estimate=rng.randint(1, 5),
        created_at=seed,
    )
    environment = IssueOpsEnvironment(
        [
            Developer("dev-backend", frozenset({"backend"}), capacity=8),
            Developer("dev-frontend", frozenset({"frontend"}), capacity=8),
        ]
    )
    environment.register_business_issue(issue)
    protected = tuple(snapshot_entities(environment))
    task = TaskSpec(
        id=f"create-ticket-{seed:06d}",
        family="business_issue_to_backlog_ticket",
        instruction=(
            f"Create the backlog ticket for business issue {issue_id}. Preserve its "
            "priority and description, link the source issue, and apply the affected "
            "product as a feature tag. Do not modify unrelated records."
        ),
        seed=seed,
        generator_version=GENERATOR_VERSION,
        required_skills=(
            "retrieve_business_issue",
            "check_duplicate_ticket",
            "create_linked_backlog_ticket",
            "tag_product_feature",
        ),
        goal_conditions=(
            StateCondition("one_ticket_for_issue", (issue_id,)),
            StateCondition("ticket_priority", (issue_id, priority.value)),
            StateCondition("ticket_description", (issue_id, issue.description)),
            StateCondition("ticket_feature_tag", (issue_id, product)),
            StateCondition("ticket_status", (issue_id, "backlog")),
        ),
        protected_entities=protected,
    )
    return GeneratedScenario(task, environment, snapshot_entities(environment))


def generate_sprint_planning_scenario(seed: int) -> GeneratedScenario:
    """Create a backlog with capability, availability, and capacity constraints."""

    rng = random.Random(seed)
    developers = [
        Developer(
            "dev-backend",
            frozenset({"backend"}),
            capacity=rng.randint(4, 7),
            available=True,
        ),
        Developer(
            "dev-fullstack",
            frozenset({"backend", "frontend"}),
            capacity=rng.randint(4, 7),
            available=rng.choice((True, True, False)),
        ),
        Developer(
            "dev-frontend",
            frozenset({"frontend"}),
            capacity=rng.randint(3, 6),
            available=True,
        ),
    ]
    environment = IssueOpsEnvironment(developers)
    capabilities = ("backend", "frontend", "backend", "frontend", "mobile")
    estimates = (
        rng.randint(1, 4),
        rng.randint(1, 4),
        rng.randint(2, 5),
        rng.randint(2, 5),
        2,
    )
    for index, (capability, estimate) in enumerate(zip(capabilities, estimates)):
        issue_id = f"SP-{seed:05d}-{index}"
        issue = BusinessIssue(
            id=issue_id,
            title=f"Plan {capability} work {index}",
            description=f"Business request for {capability} delivery.",
            priority=Priority[f"P{index % 4}"],
            affected_product=f"product-{index}",
            requested_feature=f"feature-{index}",
            required_capability=capability,
            estimate=estimate,
            created_at=seed * 10 + index,
        )
        environment.register_business_issue(issue)
        ticket = environment.create_ticket(issue)
        environment.add_feature_tag(ticket.id, issue.affected_product)

    expected = _expected_sprint_assignments(environment)
    initial = snapshot_entities(environment)
    planned_ticket_ids = frozenset(expected)
    protected = tuple(
        entity_id
        for entity_id in initial
        if entity_id.startswith("ticket:")
        and entity_id.removeprefix("ticket:") not in planned_ticket_ids
    )
    goals: list[StateCondition] = []
    committed = {developer.id: 0 for developer in developers}
    for ticket_id, developer_id in expected.items():
        ticket = environment.state.tickets[ticket_id]
        committed[developer_id] += ticket.estimate
        goals.extend(
            (
                StateCondition("ticket_status_by_id", (ticket_id, "todo")),
                StateCondition("ticket_assignee", (ticket_id, developer_id)),
                StateCondition(
                    "ticket_sprint",
                    (ticket_id, str(environment.state.sprint)),
                ),
            )
        )
    goals.extend(
        StateCondition("developer_committed", (developer_id, str(load)))
        for developer_id, load in committed.items()
    )
    task = TaskSpec(
        id=f"plan-sprint-{seed:06d}",
        family="priority_capability_capacity_sprint_planning",
        instruction=(
            "Plan the active sprint. Process backlog tickets by business priority "
            "and age, assign only available developers with the required capability "
            "and remaining capacity, and leave infeasible tickets unchanged."
        ),
        seed=seed,
        generator_version="sprint-planning-v1",
        required_skills=(
            "prioritize_backlog",
            "match_developer",
            "assign_ticket",
            "schedule_ticket",
        ),
        goal_conditions=tuple(goals),
        protected_entities=protected,
    )
    return GeneratedScenario(task, environment, initial)


def _expected_sprint_assignments(
    environment: IssueOpsEnvironment,
) -> dict[str, str]:
    """Reference policy kept separate from the mutable simulator methods."""

    loads = {
        developer.id: developer.committed
        for developer in environment.state.developers.values()
    }
    assignments: dict[str, str] = {}
    tickets = sorted(
        environment.state.tickets.values(),
        key=lambda ticket: (ticket.priority.rank, ticket.created_at, ticket.id),
    )
    for ticket in tickets:
        eligible = sorted(
            (
                developer
                for developer in environment.state.developers.values()
                if developer.available
                and ticket.required_capability in developer.capabilities
                and developer.capacity - loads[developer.id] >= ticket.estimate
            ),
            key=lambda developer: (loads[developer.id], developer.id),
        )
        if eligible:
            developer = eligible[0]
            assignments[ticket.id] = developer.id
            loads[developer.id] += ticket.estimate
    return assignments


def generate_sprint_rollover_scenario(seed: int) -> GeneratedScenario:
    """Create unfinished, blocked, completed, and capacity-shifted sprint work."""

    environment = IssueOpsEnvironment(
        [
            Developer("dev-backend", frozenset({"backend"}), capacity=8),
            Developer("dev-frontend", frozenset({"frontend"}), capacity=5),
        ]
    )
    definitions = (
        ("carry-todo", "backend", 4, Priority.P0),
        ("carry-progress", "backend", 3, Priority.P1),
        ("defer-blocked", "frontend", 2, Priority.P2),
        ("preserve-done", "frontend", 1, Priority.P3),
    )
    tickets = {}
    for index, (name, capability, estimate, priority) in enumerate(definitions):
        issue_id = f"RO-{seed:05d}-{index}"
        issue = BusinessIssue(
            id=issue_id,
            title=name.replace("-", " ").title(),
            description=f"Rollover fixture for {name}.",
            priority=priority,
            affected_product=f"rollover-{index}",
            requested_feature=name,
            required_capability=capability,
            estimate=estimate,
            created_at=seed * 10 + index,
        )
        environment.register_business_issue(issue)
        ticket = environment.create_ticket(issue)
        environment.add_feature_tag(ticket.id, issue.affected_product)
        tickets[name] = ticket

    for name, developer_id in (
        ("carry-todo", "dev-backend"),
        ("carry-progress", "dev-backend"),
        ("defer-blocked", "dev-frontend"),
    ):
        environment.assign_ticket(tickets[name].id, developer_id)
        environment.add_ticket_to_sprint(tickets[name].id)
    environment.start_ticket(tickets["carry-progress"].id)
    environment.set_blocked(tickets["defer-blocked"].id, "External dependency")

    done = tickets["preserve-done"]
    done.status = TicketStatus.DONE
    done_pr = PullRequest(
        id=f"PR-DONE-{seed:05d}",
        ticket_id=done.id,
        status=PullRequestStatus.MERGED,
    )
    environment.state.pull_requests[done_pr.id] = done_pr

    # Capacity changed after the prior sprint was planned. Mandatory rollover
    # remains valid, but later planning cannot add more backend work.
    environment.state.developers["dev-backend"].capacity = 5
    initial = snapshot_entities(environment)
    next_sprint = environment.state.sprint + 1
    goals: list[StateCondition] = [
        StateCondition("current_sprint", (str(next_sprint),)),
        StateCondition("developer_committed", ("dev-backend", "7")),
        StateCondition("developer_committed", ("dev-frontend", "0")),
    ]
    for name in ("carry-todo", "carry-progress"):
        ticket = tickets[name]
        goals.extend(
            (
                StateCondition("ticket_status_by_id", (ticket.id, ticket.status.value)),
                StateCondition("ticket_assignee", (ticket.id, ticket.assignee or "")),
                StateCondition("ticket_sprint", (ticket.id, str(next_sprint))),
                StateCondition(
                    "ticket_priority_by_id",
                    (ticket.id, ticket.priority.value),
                ),
                StateCondition(
                    "ticket_source_issue",
                    (ticket.id, ticket.source_issue_id),
                ),
                StateCondition(
                    "ticket_feature_tags",
                    (ticket.id, ",".join(sorted(ticket.feature_tags))),
                ),
            )
        )
    blocked = tickets["defer-blocked"]
    goals.extend(
        (
            StateCondition("ticket_status_by_id", (blocked.id, "backlog")),
            StateCondition("ticket_has_no_assignee", (blocked.id,)),
            StateCondition("ticket_has_no_sprint", (blocked.id,)),
            StateCondition("ticket_blocked", (blocked.id, "true")),
            StateCondition(
                "ticket_priority_by_id",
                (blocked.id, blocked.priority.value),
            ),
            StateCondition(
                "ticket_source_issue",
                (blocked.id, blocked.source_issue_id),
            ),
        )
    )
    task = TaskSpec(
        id=f"rollover-sprint-{seed:06d}",
        family="deterministic_sprint_rollover",
        instruction=(
            "Close the current sprint. Carry every unfinished unblocked ticket "
            "into the next sprint with its assignee and lifecycle state preserved. "
            "Return blocked unfinished tickets to backlog without losing blocker "
            "information. Leave completed work unchanged."
        ),
        seed=seed,
        generator_version="sprint-rollover-v1",
        required_skills=(
            "collect_unfinished_work",
            "open_next_sprint",
            "carry_unblocked_work",
            "defer_blocked_work",
        ),
        goal_conditions=tuple(goals),
        protected_entities=(f"ticket:{done.id}", f"pr:{done_pr.id}"),
    )
    return GeneratedScenario(task, environment, initial)


def generate_pr_synchronization_scenario(seed: int) -> GeneratedScenario:
    """Create an open PR linked to one in-progress ticket and unrelated work."""

    environment = IssueOpsEnvironment(
        [
            Developer("dev-backend", frozenset({"backend"}), capacity=5),
            Developer("dev-frontend", frozenset({"frontend"}), capacity=5),
        ]
    )
    tickets = []
    for index, capability in enumerate(("backend", "frontend")):
        issue_id = f"PR-{seed:05d}-{index}"
        issue = BusinessIssue(
            id=issue_id,
            title=f"PR synchronization fixture {index}",
            description=f"Development work for {capability}.",
            priority=Priority[f"P{index}"],
            affected_product=f"pr-product-{index}",
            requested_feature=f"pr-feature-{index}",
            required_capability=capability,
            estimate=2,
            created_at=seed * 10 + index,
        )
        environment.register_business_issue(issue)
        ticket = environment.create_ticket(issue)
        environment.add_feature_tag(ticket.id, issue.affected_product)
        tickets.append(ticket)
    environment.plan_sprint()
    target, unrelated = tickets
    environment.start_ticket(target.id)
    pr = environment.open_pr(target.id, f"GH-PR-{seed:06d}")
    initial = snapshot_entities(environment)
    task = TaskSpec(
        id=f"sync-pr-{seed:06d}",
        family="pr_review_merge_synchronization",
        instruction=(
            f"Synchronize pull request {pr.id}: resolve its linked ticket, process "
            "the review request and approval, then mark the ticket done when the "
            "PR merges. Do not modify unrelated tickets or developer assignments."
        ),
        seed=seed,
        generator_version="pr-synchronization-v1",
        required_skills=(
            "resolve_pr_ticket",
            "synchronize_review_request",
            "record_review_decision",
            "synchronize_merge_completion",
        ),
        goal_conditions=(
            StateCondition("pr_status", (pr.id, "merged")),
            StateCondition("pr_linked_ticket", (pr.id, target.id)),
            StateCondition("ticket_status_by_id", (target.id, "done")),
            StateCondition("ticket_assignee", (target.id, target.assignee or "")),
            StateCondition("ticket_sprint", (target.id, str(target.sprint))),
            StateCondition("ticket_priority_by_id", (target.id, target.priority.value)),
            StateCondition("ticket_source_issue", (target.id, target.source_issue_id)),
            StateCondition(
                "ticket_feature_tags",
                (target.id, ",".join(sorted(target.feature_tags))),
            ),
        ),
        protected_entities=(
            f"ticket:{unrelated.id}",
            "developer:dev-backend",
            "developer:dev-frontend",
        ),
    )
    return GeneratedScenario(task, environment, initial)


def generate_rollover_then_planning_scenario(seed: int) -> GeneratedScenario:
    """Compose rollover and planning without exposing the full sequence in training."""

    base = generate_sprint_rollover_scenario(seed)
    environment = base.environment
    new_definitions = (
        ("new-backend-infeasible", "backend", 1, Priority.P0),
        ("new-frontend-feasible", "frontend", 3, Priority.P1),
        ("new-mobile-infeasible", "mobile", 1, Priority.P2),
    )
    new_tickets = {}
    for index, (name, capability, estimate, priority) in enumerate(new_definitions):
        issue_id = f"CP-{seed:05d}-{index}"
        issue = BusinessIssue(
            id=issue_id,
            title=name.replace("-", " ").title(),
            description=f"Composed workflow fixture for {name}.",
            priority=priority,
            affected_product=f"composition-{index}",
            requested_feature=name,
            required_capability=capability,
            estimate=estimate,
            created_at=seed * 10 + 100 + index,
        )
        environment.register_business_issue(issue)
        ticket = environment.create_ticket(issue)
        environment.add_feature_tag(ticket.id, issue.affected_product)
        new_tickets[name] = ticket

    initial = snapshot_entities(environment)
    goals = [
        condition
        for condition in base.task.goal_conditions
        if condition.predicate != "developer_committed"
    ]
    feasible = new_tickets["new-frontend-feasible"]
    goals.extend(
        (
            StateCondition("developer_committed", ("dev-backend", "7")),
            StateCondition("developer_committed", ("dev-frontend", "3")),
            StateCondition("ticket_status_by_id", (feasible.id, "todo")),
            StateCondition("ticket_assignee", (feasible.id, "dev-frontend")),
            StateCondition("ticket_sprint", (feasible.id, "2")),
        )
    )
    protected = list(base.task.protected_entities)
    protected.extend(
        f"ticket:{new_tickets[name].id}"
        for name in ("new-backend-infeasible", "new-mobile-infeasible")
    )
    task = TaskSpec(
        id=f"compose-rollover-planning-{seed:06d}",
        family="heldout_rollover_then_planning",
        instruction=(
            "Close the current sprint, carry or defer unfinished work according "
            "to blocker state, recompute remaining developer capacity, and then "
            "plan feasible backlog work by business priority. An infeasible "
            "high-priority ticket must not block later feasible work."
        ),
        seed=seed,
        generator_version="rollover-then-planning-v1",
        required_skills=(
            "collect_unfinished_work",
            "open_next_sprint",
            "carry_unblocked_work",
            "defer_blocked_work",
            "prioritize_backlog",
            "match_developer",
            "assign_ticket",
            "schedule_ticket",
        ),
        goal_conditions=tuple(goals),
        protected_entities=tuple(protected),
    )
    return GeneratedScenario(task, environment, initial)


def generate_rollover_then_planning_v2_scenario(seed: int) -> GeneratedScenario:
    """Generate structurally varied rollover/planning compositions for RQ2.

    Version one varied external identifiers and timestamps while keeping one
    fixed aliased tool plan.  This generator deliberately varies the number and
    state of rollover candidates, the post-rollover capacity boundary, and the
    number and feasibility of new backlog tickets.  It remains the same
    business workflow and is kept evaluation-only.
    """

    rng = random.Random(seed)
    environment = IssueOpsEnvironment(
        [
            Developer("dev-backend", frozenset({"backend"}), capacity=24),
            Developer("dev-frontend", frozenset({"frontend"}), capacity=24),
        ]
    )

    old_tickets = []
    carry_count, blocked_count = ((1, 1), (2, 1), (1, 2))[seed % 3]
    for index in range(carry_count + blocked_count):
        blocked = index >= carry_count
        capability = "backend" if index % 2 == 0 else "frontend"
        estimate = 1 + rng.randrange(3)
        issue = _register_generated_issue(
            environment,
            issue_id=f"R2-OLD-{seed:05d}-{index}",
            title=f"old-{index}",
            priority=Priority[f"P{index % 4}"],
            capability=capability,
            estimate=estimate,
            created_at=seed * 100 + index,
            product=f"rq2-old-{index}",
        )
        ticket = environment.create_ticket(issue)
        environment.add_feature_tag(ticket.id, issue.affected_product)
        developer_id = "dev-backend" if capability == "backend" else "dev-frontend"
        environment.assign_ticket(ticket.id, developer_id)
        environment.add_ticket_to_sprint(ticket.id)
        if (seed + index) % 2:
            environment.start_ticket(ticket.id)
        if blocked:
            environment.set_blocked(ticket.id, f"dependency-{index}")
        old_tickets.append(ticket)

    carried_loads = {"backend": 0, "frontend": 0}
    for ticket in old_tickets:
        if not ticket.blocked:
            carried_loads[ticket.required_capability] += ticket.estimate
    backend_margin = (seed // 5) % 2
    frontend_margin = 2 + (seed // 11) % 4
    environment.state.developers["dev-backend"].capacity = max(
        1, carried_loads["backend"] + backend_margin
    )
    environment.state.developers["dev-frontend"].capacity = max(
        3, carried_loads["frontend"] + frontend_margin
    )
    # Keep six total tickets so the prompt plus a bounded skill update fits the
    # fixed 2,048-token model context while plan structure still varies.
    new_count = 6 - len(old_tickets)
    definitions = [
        ("backend", environment.state.developers["dev-backend"].capacity + 1),
        ("frontend", 1 + seed % min(frontend_margin, 3)),
        ("mobile", 1),
    ]
    for index in range(3, new_count):
        capability = "frontend" if (seed + index) % 2 else "backend"
        definitions.append((capability, 1 + rng.randrange(3)))
    for index, (capability, estimate) in enumerate(definitions):
        issue = _register_generated_issue(
            environment,
            issue_id=f"R2-NEW-{seed:05d}-{index}",
            title=f"new-{capability}-{index}",
            priority=Priority[f"P{index % 4}"],
            capability=capability,
            estimate=estimate,
            created_at=seed * 100 + 100 + index,
            product=f"rq2-new-{index}",
        )
        ticket = environment.create_ticket(issue)
        environment.add_feature_tag(ticket.id, issue.affected_product)

    initial = snapshot_entities(environment)
    reference = copy.deepcopy(environment)
    provisional = TaskSpec(
        id=f"rq2-compose-{seed:06d}",
        family="heldout_rollover_then_planning_v2",
        instruction="",
        seed=seed,
        generator_version="rollover-then-planning-v2",
        required_skills=(),
        goal_conditions=(),
    )
    # The oracle is used only to derive the exact expected state.  The returned
    # plan remains excluded from all model training and retrieval pools.
    from issueops.agents import RolloverThenPlanningOracle
    from issueops.tools import ToolRuntime

    trajectory, _ = RolloverThenPlanningOracle().run(
        provisional, ToolRuntime(reference)
    )
    if trajectory.failure_stage is not None:
        raise RuntimeError(f"RQ2 reference execution failed for seed {seed}")

    goals: list[StateCondition] = [
        StateCondition("current_sprint", (str(reference.state.sprint),))
    ]
    for developer in sorted(reference.state.developers.values(), key=lambda d: d.id):
        goals.append(
            StateCondition(
                "developer_committed", (developer.id, str(developer.committed))
            )
        )
    for ticket in sorted(reference.state.tickets.values(), key=lambda item: item.id):
        goals.extend(_ticket_final_state_conditions(ticket))

    protected = tuple(
        entity_id
        for entity_id, value in initial.items()
        if entity_id.startswith("ticket:")
        and snapshot_entities(reference).get(entity_id) == value
    )
    task = TaskSpec(
        id=f"rq2-compose-{seed:06d}",
        family="heldout_rollover_then_planning_v2",
        instruction=(
            "Close the sprint before planning. Carry unblocked work, defer blocked "
            "work with its blocker intact, then plan feasible backlog tickets in "
            "priority and age order without letting infeasible work block later work."
        ),
        seed=seed,
        generator_version="rollover-then-planning-v2",
        required_skills=(
            "collect_unfinished_work",
            "open_next_sprint",
            "carry_unblocked_work",
            "defer_blocked_work",
            "prioritize_backlog",
            "match_developer",
            "assign_ticket",
            "schedule_ticket",
        ),
        goal_conditions=tuple(goals),
        protected_entities=protected,
    )
    return GeneratedScenario(task, environment, initial)


def _register_generated_issue(
    environment: IssueOpsEnvironment,
    *,
    issue_id: str,
    title: str,
    priority: Priority,
    capability: str,
    estimate: int,
    created_at: int,
    product: str,
) -> BusinessIssue:
    issue = BusinessIssue(
        id=issue_id,
        title=title,
        description="RQ2 fixture.",
        priority=priority,
        affected_product=product,
        requested_feature=title,
        required_capability=capability,
        estimate=estimate,
        created_at=created_at,
    )
    environment.register_business_issue(issue)
    return issue


def _ticket_final_state_conditions(ticket: Ticket) -> tuple[StateCondition, ...]:
    conditions = [
        StateCondition("ticket_status_by_id", (ticket.id, ticket.status.value)),
        StateCondition("ticket_priority_by_id", (ticket.id, ticket.priority.value)),
        StateCondition("ticket_source_issue", (ticket.id, ticket.source_issue_id)),
        StateCondition(
            "ticket_feature_tags",
            (ticket.id, ",".join(sorted(ticket.feature_tags))),
        ),
        StateCondition("ticket_blocked", (ticket.id, str(ticket.blocked).lower())),
    ]
    if ticket.blocked_reason is not None:
        conditions.append(
            StateCondition("ticket_blocked_reason", (ticket.id, ticket.blocked_reason))
        )
    conditions.append(
        StateCondition("ticket_assignee", (ticket.id, ticket.assignee))
        if ticket.assignee is not None
        else StateCondition("ticket_has_no_assignee", (ticket.id,))
    )
    conditions.append(
        StateCondition("ticket_sprint", (ticket.id, str(ticket.sprint)))
        if ticket.sprint is not None
        else StateCondition("ticket_has_no_sprint", (ticket.id,))
    )
    return tuple(conditions)
