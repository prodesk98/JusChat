from typing import Literal

from pydantic import BaseModel, Field


class AgentGraphSubquery(BaseModel):
    subquestions: list[str] = Field(
        default_factory=list,
        title="Subquestions",
        description="List of sub-questions generated from the main question. Max 3 questions allowed.",
    )


class AgentGraphRoute(BaseModel):
    route: Literal["generate_subqueries", "answer_final"] = Field(
        default="",
        title="Route",
        description="The route to take based on the sub-questions generated.",
    )

