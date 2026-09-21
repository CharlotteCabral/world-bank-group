from pydantic import BaseModel
from typing import Optional

class IndicateurLigne(BaseModel):
    country_code: str
    country_name: str
    indicator_code: str
    indicator_label_fr: Optional[str] = None
    year_number: int
    valeur: Optional[float] = None