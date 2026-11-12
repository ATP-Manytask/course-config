from datetime import datetime
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator

from .group import ManytaskGroupConfig
from .task import ManytaskTaskConfig


class ManytaskDeadlinesType(Enum):
    HARD = "hard"
    INTERPOLATE = "interpolate"


class ManytaskDeadlinesConfig(BaseModel):
    timezone: str

    # Note: use Optional/Union[...] instead of ... | None as pydantic does not support | in older python versions
    deadlines: ManytaskDeadlinesType = ManytaskDeadlinesType.HARD
    max_submissions: Optional[int] = None
    submission_penalty: float = 0
    oral_attempt_limit: int = Field(default=3, gt=0, strict=True)

    schedule: list[ManytaskGroupConfig]  # list of groups with tasks

    def get_now_with_timezone(self) -> datetime:
        return datetime.now(tz=ZoneInfo(self.timezone))

    @field_validator("max_submissions")
    @classmethod
    def check_max_submissions(cls, data: int | None) -> int | None:
        if data is not None and data <= 0:
            raise ValueError("max_submissions should be positive")
        return data

    @field_validator("submission_penalty")
    @classmethod
    def check_submission_penalty(cls, data: float) -> float:
        if data < 0:
            raise ValueError("submission_penalty should be non-negative")
        return data

    @field_validator("timezone")
    @classmethod
    def check_valid_timezone(cls, timezone: str) -> str:
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as e:
            raise ValueError(str(e))
        return timezone

    @field_validator("schedule")
    @classmethod
    def check_group_task_names_unique(cls, data: list[ManytaskGroupConfig]) -> list[ManytaskGroupConfig]:
        group_names = [group.name for group in data]
        tasks_names = [task.name for group in data for task in group.tasks]

        # group names unique
        group_names_duplicates = [name for name in group_names if group_names.count(name) > 1]
        if group_names_duplicates:
            raise ValueError(f"Group names should be unique, duplicates: {group_names_duplicates}")

        # task names unique
        tasks_names_duplicates = [name for name in tasks_names if tasks_names.count(name) > 1]
        if tasks_names_duplicates:
            raise ValueError(f"Task names should be unique, duplicates: {tasks_names_duplicates}")

        # # group names and task names not intersect (except single task in a group with the same name)
        # no_single_task_groups = [group for group in data if not (len(group.tasks) == 1
        # and group.name == group.tasks[0].name)]

        return data

    @model_validator(mode="after")
    def set_timezone(self) -> "ManytaskDeadlinesConfig":
        timezone = ZoneInfo(self.timezone)
        for group in self.schedule:
            group.replace_timezone(timezone)
        return self

    def find_task(self, task_name: str) -> tuple[ManytaskGroupConfig, ManytaskTaskConfig]:
        for group in self.schedule:
            for task in group.tasks:
                if task.name == task_name:
                    return group, task
        raise KeyError(f"Task {task_name} not found")

    def get_groups(
        self,
        enabled: bool | None = None,
        started: bool | None = None,
        *,
        now: datetime | None = None,
    ) -> list[ManytaskGroupConfig]:
        if now is None:
            now = self.get_now_with_timezone()

        groups = [group for group in self.schedule]

        if enabled is not None:
            groups = [group for group in groups if group.enabled == enabled]

        if started is not None:
            if started:
                groups = [group for group in groups if group.start <= now]
            else:
                groups = [group for group in groups if group.start > now]

        return groups

    def get_tasks(
        self,
        enabled: bool | None = None,
        started: bool | None = None,
        is_bonus: bool | None = None,
        *,
        now: datetime | None = None,
    ) -> list[ManytaskTaskConfig]:
        # TODO: refactor
        if now is None:
            now = self.get_now_with_timezone()

        groups = self.get_groups(started=started, now=now)

        if enabled is True:
            groups = [group for group in groups if group.enabled]
            extra_tasks = []
        elif enabled is False:
            groups = groups
            extra_tasks = [task for group in groups for task in group.tasks if not group.enabled]
        else:  # None
            groups = groups
            extra_tasks = []

        tasks = [task for group in groups for task in group.tasks]

        if enabled is not None:
            tasks = [task for task in tasks if task.enabled == enabled]

        for extra_task in extra_tasks:
            if extra_task not in tasks:
                tasks.append(extra_task)

        if is_bonus is not None:
            tasks = [task for task in tasks if task.is_bonus == is_bonus]

        return tasks

    def max_score(self, started: bool | None = True, *, now: datetime | None = None) -> int:
        return sum(task.score for task in self.get_tasks(enabled=True, started=started, is_bonus=False, now=now))

    @property
    def max_score_started(self) -> int:
        return self.max_score(started=True, now=self.get_now_with_timezone())