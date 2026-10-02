from pydantic import BaseModel, Field
from typing import Optional

class IndicateurLigne(BaseModel):
    country_code: str = Field(alias="countryiso3code")
    country_name: Optional[dict] = None 
    indicator_code: Optional[dict] = None 
    year_number: int = Field(alias="date")
    valeur: Optional[float] = Field(None, alias="value")