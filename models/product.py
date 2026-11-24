
from pydantic import BaseModel, Field


class Product(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)

    features: list[str] = Field(default_factory=list)

    technical_constraints: str = ""
    existing_customers: str = ""
    reference_wins: str = ""
    pricing: str = ""
    contract_value: str = ""
    monetization_model: str = ""
    target_regions: list[str] = Field(default_factory=list)
