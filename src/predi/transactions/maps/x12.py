from ctypes import Union
from datetime import date, datetime
from enum import Enum
from lib2to3.pgen2.token import OP
from typing import Dict, Optional
from predi.edi import X12Document

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
    components: list[Segment, "Loop"]


class X12PrediMap(PrediBaseModel):
    author: str
    title: str
    version: str
    version_date: Optional[date]
    predimap_version: str
    components: list[Segment | Loop]


class X12_850(X12PrediMap):
    @validator("components")
    def is_850(cls, v):
        assert isinstance(v, list)
        return v


X12BasePredimaps: Enum = Enum("X12TransactionList", {val.__name__: val for val in X12PrediMap.__subclasses__()})

class X12_Mapper():
    def __init__(self, map: X12PrediMap=None):
        self.map = map
    
    def parse(self, x12_document: X12Document, map=None):
        interchange_envelope=[x12_document[0][0], x12_document[0][-1]]
        functional_group=[x12_document[0][1][0][0], x12_document[0][1][0][-1]]
        transaction_sets=x12_document[0][1][0][1]
        transactions=[]
        map = map if map else self.map
        for transaction in transaction_sets:
            top_line=transaction[0]
            print(top_line)
            for component in map.components:
                if component.id == top_line[0]:
                    print(top_line[1:])


        # print(type(x12_document[0][1][0][1]))
        # return transaction_sets
        # return (self.map.components)

# print(X12_850.__fields__["title"].default)
# print({val.__fields__["title"].default: val for val in X12PrediMap.__subclasses__()})
