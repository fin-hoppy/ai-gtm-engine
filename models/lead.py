
from pydantic import BaseModel, Field, HttpUrl


class Evidence(BaseModel):
    url: HttpUrl
    title: str
    excerpt: str


class Prospect(BaseModel):
    company_name: str
    website: HttpUrl
    industry: str

    description: str

    employee_count: int | None = Field(
        default=None,
        ge=0,
    )

    headquarters: str | None = None

    buyer_name: str | None = None
    buyer_title: str | None = None

    buying_signals: list[str]

    fit_score: int = Field(ge=0, le=100)

    match_reason: str

    negative_signals: list[str] = Field(
        default_factory=list
    )

    sources: list[Evidence] = Field(min_length=1)


class Competitor(BaseModel):
    company_name: str
    website: HttpUrl

    product_name: str
    positioning: str
    value_proposition: str

    pricing: str | None = None

    differentiators: list[str]

    sources: list[Evidence] = Field(min_length=1)


class DiscoveryResult(BaseModel):
    prospects: list[Prospect] = Field(max_length=3)
    competitors: list[Competitor] = Field(max_length=2)
