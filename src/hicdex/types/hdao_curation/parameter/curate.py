# generated by datamodel-codegen:
#   filename:  curate.json

from __future__ import annotations

from pydantic import BaseModel


class CurateParameter(BaseModel):
    hDAO_amount: str
    issuer: str
    objkt_id: str