from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

from .deadlines import ManytaskDeadlinesConfig
from .group import ManytaskGroupConfig
from .settings import ManytaskSettingsConfig
from .task import ManytaskTaskConfig
from .ui import ManytaskUiConfig


class ManytaskConfig(BaseModel):
    """Manytask configuration."""

    version: int  # if config exists, version is always present

    settings: ManytaskSettingsConfig
    ui: ManytaskUiConfig
    deadlines: ManytaskDeadlinesConfig

    def get_groups(
        self,
        enabled: bool | None = None,
        started: bool | None = None,
        *,
        now: datetime | None = None,
    ) -> list[ManytaskGroupConfig]:
        return self.deadlines.get_groups(enabled=enabled, started=started, now=now)

    def get_tasks(
        self,
        enabled: bool | None = None,
        started: bool | None = None,
        *,
        now: datetime | None = None,
    ) -> list[ManytaskTaskConfig]:
        return self.deadlines.get_tasks(enabled=enabled, started=started, now=now)

    @field_validator("version")
    @classmethod
    def check_version(cls, data: int) -> int:
        if data != 1:
            raise ValueError(f"Only version 1 is supported for {cls.__name__}")
        return data
