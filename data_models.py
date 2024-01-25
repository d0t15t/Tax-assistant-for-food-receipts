from typing import Sequence
from langchain_core.pydantic_v1 import BaseModel, Field
from json import JSONEncoder

class VAT(BaseModel):
    """Identifying VAT Values."""
    percentage: float = Field(..., description="The percentage of the tax. Convert commas to periods.")
    amount_taxed: float = Field(..., description="The amount taxed. Convert commas to periods.")
    value_added: float = Field(..., description="The amount of VAT added. Convert commas to periods.")
    
class BillingValues(BaseModel):
    """Identifying Billing Values."""
    date: str = Field(..., description="The date of the billing in the format YYYY.MMM.DD")
    location_name: str = Field(..., description="The name of the place")
    address: str = Field(..., description="The address of the place including street and number, city, postal code, and country")
    currency_symbol: str = Field(..., description="The currency of the billing")
    currency_code: str = Field(..., description="The currency code of the billing")
    taxes: Sequence[VAT] = Field(..., description="Sequence of VATs")
    total_without_tip: float = Field(..., description="The total without tip. Convert commas to periods.")
    total_with_tip: float = Field(..., description="The total with tip. Convert commas to periods.")
    tip_amount: float = Field(..., description="The tip amount. Convert commas to periods.")
    tip_percentage: float = Field(..., description="The tip percentage. Convert commas to periods.")

class Encoder(JSONEncoder):
        def default(self, o):
            return o.__dict__
