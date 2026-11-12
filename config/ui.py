from pydantic import BaseModel, Field, field_validator


class ManytaskUiConfig(BaseModel):
    task_url_template: str  # $GROUP_NAME $TASK_NAME vars are available
    links: dict[str, str] = Field(default_factory=dict)

    @field_validator("task_url_template")
    @classmethod
    def check_task_url_template(cls, data: str | None) -> str | None:
        if data is not None and not data.startswith("https://"):
            raise ValueError("task_url_template should be https")
        # if data is not None and "$GROUP_NAME" not in data and "$TASK_NAME" not in data:
        #     raise ValueError("task_url should contain at least one of $GROUP_NAME and $TASK_NAME vars")
        return data