from ctypes import Union
from enum import Enum
from typing import Dict, Optional


from predi.utils import PrediBaseModel
from pydantic import PositiveInt, validator


class X12Field(PrediBaseModel):
    ...


class Options(X12Field):
    values: list[str]
    exhaustive: bool = False


class CodedOptions(Options):
    values: dict[str | int, str]
    exhaustive: bool = True


class X12Component(PrediBaseModel):
    id: str | int
    name: Optional[str] = None
    required: bool = False
    reference_tag: Optional[str] = None


class Element(X12Component):
    id: int
    options: Optional[Options] = None


class QualifiedElement(Element):
    qualifier_tag: str


class Segment(X12Component):
    id: str
    max_use: Optional[PositiveInt]
    elements: list[Element]


class Loop(X12Component):
    id: str
    max_use: Optional[PositiveInt]
    components: list[Segment,"Loop"]


class X12Spec(PrediBaseModel):
    title: str
    components: list[Segment | Loop]


class X12_850(X12Spec):
    @validator("components")
    def is_850(cls, v):
        assert isinstance(v, list)
        return v

print([x.__name__ for x in X12Spec.__subclasses__()])
X12TransactionList: Enum = Enum("X12TransactionList", {val.__name__: val for val in X12Spec.__subclasses__()})

# print(X12_850.__fields__["title"].default)
# print({val.__fields__["title"].default: val for val in X12Spec.__subclasses__()})
