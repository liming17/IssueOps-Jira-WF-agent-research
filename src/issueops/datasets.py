"""Generate validated JSONL datasets from deterministic IssueOps scenarios."""

import argparse
import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from issueops.agents import (
    PullRequestSynchronizationOracle,
    RolloverThenPlanningOracle,
    SprintPlanningOracle,
    SprintRolloverOracle,
    TicketCreationOracle,
)
from issueops.environment.generator import (
    generate_pr_synchronization_scenario,
    generate_rollover_then_planning_scenario,
    generate_sprint_planning_scenario,
    generate_sprint_rollover_scenario,
    generate_ticket_creation_scenario,
)
from issueops.tools import ToolRuntime


def generate_records(
    start_seed: int,
    count: int,
    family: str = "ticket_creation",
) -> list[dict[str, Any]]:
    if family == "ticket_creation":
        oracle = TicketCreationOracle()
        generator = generate_ticket_creation_scenario
    elif family == "sprint_planning":
        oracle = SprintPlanningOracle()
        generator = generate_sprint_planning_scenario
    elif family == "sprint_rollover":
        oracle = SprintRolloverOracle()
        generator = generate_sprint_rollover_scenario
    elif family == "pr_synchronization":
        oracle = PullRequestSynchronizationOracle()
        generator = generate_pr_synchronization_scenario
    elif family == "rollover_then_planning":
        oracle = RolloverThenPlanningOracle()
        generator = generate_rollover_then_planning_scenario
    else:
        raise ValueError(f"unknown task family: {family}")
    records: list[dict[str, Any]] = []
    for seed in range(start_seed, start_seed + count):
        scenario = generator(seed)
        initial_world = _jsonable(scenario.environment.state)
        trajectory, report = oracle.run(
            scenario.task,
            ToolRuntime(scenario.environment),
        )
        if not report.success:
            raise RuntimeError(f"oracle failed generated task {scenario.task.id}")
        records.append(
            {
                "task": _jsonable(scenario.task),
                "initial_world": initial_world,
                "oracle_trajectory": _jsonable(trajectory),
                "verification": _jsonable(report),
            }
        )
    return records


def write_jsonl(records: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    temporary.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument(
        "--family",
        choices=(
            "ticket_creation",
            "sprint_planning",
            "sprint_rollover",
            "pr_synchronization",
            "rollover_then_planning",
        ),
        default="ticket_creation",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/ticket_creation_v1.jsonl"),
    )
    args = parser.parse_args()
    if args.count <= 0:
        parser.error("--count must be positive")
    records = generate_records(args.start_seed, args.count, args.family)
    write_jsonl(records, args.output)
    print(f"wrote {len(records)} verified records to {args.output}")


def _jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    main()
