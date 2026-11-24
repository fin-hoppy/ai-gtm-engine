
from typing import Annotated

from pydantic import BaseModel, Field


Confidence = Annotated[float, Field(ge=0, le=1)]


class Industry(BaseModel):
    name: str
    naics_code: str | None = None
    sic_code: str | None = None
    confidence: Confidence


class CompanySize(BaseModel):
    min_employees: int | None = Field(default=None, ge=0)
    max_employees: int | None = Field(default=None, ge=0)
    annual_revenue: str | None = None
    confidence: Confidence


class BuyerPersona(BaseModel):
    title: str
    department: str
    seniority: str
    pain_points: list[str]
    confidence: Confidence


class BuyingSignal(BaseModel):
    event: str
    reasoning: str
    confidence: Confidence


class ExpansionSegment(BaseModel):
    industry: str
    use_case: str
    reasoning: str
    confidence: Confidence


class ICP(BaseModel):
    summary: str

    industries: list[Industry]
    company_size: CompanySize
    buyer_personas: list[BuyerPersona]
    buying_signals: list[BuyingSignal]
    expansion_segments: list[ExpansionSegment]

    target_regions: list[str]
    negative_signals: list[str]
    assumptions: list[str]
