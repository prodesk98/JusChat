from typing import Literal

from pydantic import BaseModel, Field


class AgentGraphSubquery(BaseModel):
    subquestions: list[str] = Field(
        default_factory=list,
        title="Subquestions",
        description="List of sub-questions generated from the main question. Max 3 questions allowed.",
    )


class AgentGraphRoute(BaseModel):
    route: Literal[
        "search_graph",
        "search_vector",
        "answer_final"
    ] = Field(
        default="",
        title="Route",
        description="Determines the next action for the agent based on the question and context."
    )


class AgentGraphStart(BaseModel):
    route: Literal[
        "needs_search",
        "answer_final"
    ] = Field(
        default="needs_search",
        title="Route",
        description="Determines if the question needs further search or can be answered directly."
    )