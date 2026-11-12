from enum import Enum
from typing import Optional

from pydantic import AnyUrl, BaseModel, Field, field_validator


class ManytaskReviewStage(str, Enum):
    ORAL = "oral"
    CODEREVIEW = "codereview"


DEFAULT_REVIEW_STAGES = (
    ManytaskReviewStage.ORAL,
    ManytaskReviewStage.CODEREVIEW,
)


class ManytaskTaskConfig(BaseModel):
    task: str
    review_stages: tuple[ManytaskReviewStage, ...] = Field(
        default=DEFAULT_REVIEW_STAGES, min_length=1, max_length=2)

    enabled: bool = True

    score: int
    special: int = 0

    is_bonus: bool = False
    is_special: bool = False

    # Note: use Optional/Union[...] instead of ... | None as pydantic does not support | in older python versions
    url: Optional[AnyUrl] = None

    @field_validator("review_stages")
    @classmethod
    def check_review_stages(cls, stages: tuple[ManytaskReviewStage, ...]) -> tuple[ManytaskReviewStage, ...]:
        if len(set(stages)) != len(stages):
            raise ValueError("Review stages must be unique")
        return stages

    @property
    def name(self) -> str:
        return self.task
