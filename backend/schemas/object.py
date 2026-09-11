"""Schemas for space object resources."""

from pydantic import BaseModel


class TLEData(BaseModel):
    line1: str
    line2: str


class ObjectResponse(BaseModel):
    object_id: str
    name: str
    tle: TLEData
    epoch: str
