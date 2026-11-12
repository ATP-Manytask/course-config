from datetime import datetime, timedelta
from typing import Union
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, model_validator

from .task import ManytaskTaskConfig


class ManytaskGroupConfig(BaseModel):
    group: str

    enabled: bool = True

    # Note: use Optional/Union[...] instead of ... | None as pydantic does not support | in older python versions
    start: datetime
    steps: dict[float, Union[datetime, timedelta]] = Field(default_factory=dict)
    end: Union[datetime, timedelta]

    tasks: list[ManytaskTaskConfig] = Field(default_factory=list)

    @property
    def name(self) -> str:
        return self.group

    def get_percents_before_deadline(self) -> dict[float, datetime]:
        return {
            percent: (date_or_delta if isinstance(date_or_delta, datetime) else self.start + date_or_delta)
            for percent, date_or_delta in zip([1.0, *self.steps.keys()], [*self.steps.values(), self.end])
        }

    def get_current_percent_multiplier(self, now: datetime) -> float:
        percents = self.get_percents_before_deadline()
        for percent, date in percents.items():
            if now <= date:
                return percent
        return 0.0

    def replace_timezone(self, timezone: ZoneInfo) -> None:
        self.start = self.start.replace(tzinfo=timezone)
        self.end = self.end.replace(tzinfo=timezone) if isinstance(self.end, datetime) else self.end
        self.steps = {k: v.replace(tzinfo=timezone) for k, v in self.steps.items() if isinstance(v, datetime)}

    @model_validator(mode="after")
    def check_dates(self) -> "ManytaskGroupConfig":
        # check end
        if isinstance(self.end, timedelta) and self.end < timedelta():
            raise ValueError(f"end timedelta <{self.end}> should be positive")
        if isinstance(self.end, datetime) and self.end < self.start:
            raise ValueError(f"end datetime <{self.end}> should be after the start <{self.start}>")

        # check steps
        last_step_date_or_delta: datetime | timedelta = self.start
        for _, date_or_delta in self.steps.items():
            step_date = self.start + date_or_delta if isinstance(date_or_delta, timedelta) else date_or_delta
            last_step_date = (
                self.start + last_step_date_or_delta
                if isinstance(last_step_date_or_delta, timedelta)
                else last_step_date_or_delta
            )

            if isinstance(date_or_delta, timedelta) and date_or_delta < timedelta():
                raise ValueError(f"step timedelta <{date_or_delta}> should be positive")
            if isinstance(date_or_delta, datetime) and date_or_delta <= self.start:
                raise ValueError(f"step datetime <{date_or_delta}> should be after the start {self.start}")

            if step_date <= last_step_date:
                raise ValueError(
                    f"step datetime/timedelta <{date_or_delta}> "
                    f"should be after the last step <{last_step_date_or_delta}>"
                )
            last_step_date_or_delta = date_or_delta

        return self