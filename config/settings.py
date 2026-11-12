from pydantic import AnyUrl, BaseModel


class ManytaskSettingsConfig(BaseModel):
    """Manytask settings."""

    course_name: str
    gitlab_base_url: AnyUrl
    public_repo: str
    students_group: str