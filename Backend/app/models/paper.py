from pydantic import BaseModel
from typing import Optional, List


class CompareRequest(BaseModel):
    paper_ids: Optional[List[str]] = None
    compare_all: bool = False
    dimensions: Optional[List[str]] = None