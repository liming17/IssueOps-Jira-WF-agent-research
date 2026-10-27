"""Initial structured skills for the ticket-creation workflow."""

from issueops.specs import SkillSpec

TICKET_CREATION_SKILLS: tuple[SkillSpec, ...] = (
    SkillSpec(
        name="retrieve_business_issue",
        description="Load the authoritative business request before acting.",
        parameters=("issue_id",),
        preconditions=("business issue exists",),
        actions=("get_business_issue",),
        postconditions=("business issue fields are available",),
        failure_modes=("unknown issue",),
    ),
    SkillSpec(
        name="check_duplicate_ticket",
        description="Check whether the business issue already has a primary ticket.",
        parameters=("issue_id",),
        preconditions=("business issue exists",),
        actions=("search_linked_ticket",),
        postconditions=("existing linked ticket is known or confirmed absent",),
        failure_modes=("duplicate ticket",),
    ),
    SkillSpec(
        name="create_linked_backlog_ticket",
        description="Create one backlog ticket linked to the business issue.",
        parameters=("issue_id",),
        preconditions=("no linked ticket exists",),
        actions=("create_backlog_ticket",),
        postconditions=("ticket exists with copied priority and source link",),
        failure_modes=("duplicate ticket", "incorrect field binding"),
    ),
    SkillSpec(
        name="tag_product_feature",
        description="Apply the business issue's affected product as a feature tag.",
        parameters=("ticket_id", "tag"),
        preconditions=("ticket exists", "tag comes from affected_product"),
        actions=("add_feature_tag",),
        postconditions=("ticket contains the expected feature tag",),
        failure_modes=("wrong ticket", "wrong tag"),
    ),
)


SPRINT_PLANNING_SKILLS: tuple[SkillSpec, ...] = (
    SkillSpec(
        name="prioritize_backlog",
        description="List backlog work in business-priority and age order.",
        parameters=(),
        preconditions=("sprint rollover has completed",),
        actions=("list_backlog_tickets",),
        postconditions=("candidate tickets are ordered by P0-P3 then created_at",),
        failure_modes=("priority ordering error",),
    ),
    SkillSpec(
        name="match_developer",
        description="Find available developers with capability and capacity.",
        parameters=("ticket_id",),
        preconditions=("ticket is in backlog",),
        actions=("list_eligible_developers",),
        postconditions=("eligible developers are ordered by load then id",),
        failure_modes=(
            "capability mismatch",
            "unavailable developer",
            "insufficient capacity",
        ),
    ),
    SkillSpec(
        name="assign_ticket",
        description="Assign a backlog ticket to one eligible developer.",
        parameters=("ticket_id", "developer_id"),
        preconditions=("developer is eligible",),
        actions=("assign_ticket",),
        postconditions=("ticket assignee equals developer_id",),
        failure_modes=("wrong developer", "argument-binding error"),
    ),
    SkillSpec(
        name="schedule_ticket",
        description="Add an assigned ticket to the active sprint.",
        parameters=("ticket_id",),
        preconditions=("ticket is assigned and capacity remains",),
        actions=("add_ticket_to_sprint",),
        postconditions=("ticket is TODO in the active sprint",),
        failure_modes=("capacity violation", "missing assignment"),
    ),
)


SPRINT_ROLLOVER_SKILLS: tuple[SkillSpec, ...] = (
    SkillSpec(
        name="collect_unfinished_work",
        description="List unfinished tickets in the sprint being closed.",
        parameters=(),
        preconditions=("an active sprint exists",),
        actions=("list_rollover_candidates",),
        postconditions=("all TODO, IN_PROGRESS, and IN_REVIEW tickets are known",),
        failure_modes=("missed unfinished ticket",),
    ),
    SkillSpec(
        name="open_next_sprint",
        description="Advance the sprint and reset committed capacity accounting.",
        parameters=(),
        preconditions=("rollover candidates have been captured",),
        actions=("start_next_sprint",),
        postconditions=("the next sprint is active",),
        failure_modes=("ordering error",),
    ),
    SkillSpec(
        name="carry_unblocked_work",
        description="Carry unfinished unblocked work forward with its assignee.",
        parameters=("ticket_id",),
        preconditions=("ticket is unfinished, assigned, and not blocked",),
        actions=("carry_ticket_to_current_sprint",),
        postconditions=("ticket keeps status and assignee in the new sprint",),
        failure_modes=("blocked ticket carried", "assignee lost"),
    ),
    SkillSpec(
        name="defer_blocked_work",
        description="Return blocked unfinished work to backlog without reassigning it.",
        parameters=("ticket_id",),
        preconditions=("ticket is unfinished and blocked",),
        actions=("defer_blocked_ticket",),
        postconditions=("ticket is unassigned in backlog with blocker preserved",),
        failure_modes=("unblocked ticket deferred", "blocker lost"),
    ),
)


PR_SYNCHRONIZATION_SKILLS: tuple[SkillSpec, ...] = (
    SkillSpec(
        name="resolve_pr_ticket",
        description="Load a PR and resolve its single linked IssueOps ticket.",
        parameters=("pr_id",),
        preconditions=("PR exists", "linked ticket exists"),
        actions=("get_pull_request", "get_pr_linked_ticket"),
        postconditions=("PR and ticket relationship is known",),
        failure_modes=("unknown PR", "broken ticket link"),
    ),
    SkillSpec(
        name="synchronize_review_request",
        description="Move an in-progress ticket into review when review is requested.",
        parameters=("pr_id",),
        preconditions=("PR is open", "ticket is unblocked and in progress"),
        actions=("request_pr_review",),
        postconditions=("PR is review-requested and ticket is in review",),
        failure_modes=("invalid ticket state", "blocked ticket"),
    ),
    SkillSpec(
        name="record_review_decision",
        description="Record approval or requested changes for a PR under review.",
        parameters=("pr_id", "approved"),
        preconditions=("PR has review requested",),
        actions=("record_pr_review",),
        postconditions=("review decision is synchronized",),
        failure_modes=("review ordering error",),
    ),
    SkillSpec(
        name="synchronize_merge_completion",
        description="Mark the linked ticket done after an approved PR is merged.",
        parameters=("pr_id",),
        preconditions=("PR is approved", "ticket is in review"),
        actions=("merge_pr",),
        postconditions=("PR is merged and ticket is done",),
        failure_modes=("merge before approval", "wrong linked ticket"),
    ),
)


ROLLOVER_THEN_PLANNING_SKILL = SkillSpec(
    name="rollover_then_plan",
    description=(
        "Compose sprint rollover with capacity-aware backlog planning without "
        "changing either atomic workflow's business rules."
    ),
    parameters=(),
    preconditions=("an active sprint exists",),
    actions=(
        "collect unfinished work",
        "open the next sprint",
        "resolve each captured rollover candidate",
        "plan backlog work",
    ),
    postconditions=(
        "rollover completes before backlog planning",
        "every feasible backlog ticket is considered in priority order",
    ),
    failure_modes=(
        "planning before rollover",
        "multiple entity arguments collapsed into one call",
        "infeasible work blocks later feasible work",
    ),
    version="1",
)
