
from enum import Enum

from pydantic import BaseModel, Field


class OutreachStatus(str, Enum):
    DRAFT = "Draft"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class OutreachDraft(BaseModel):

    subject: str = Field(
        min_length=1,
        max_length=150,
    )

    body: str = Field(
        min_length=1,
        max_length=3000,
    )

    source_indices: list[int] = Field(
        min_length=1,
    )

    reasoning: str
