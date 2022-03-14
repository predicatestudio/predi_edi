from enum import Enum
from turtle import title

from ...utils import PrediBaseModel
from .old_specs import TransactionTemplate


class BaseSpec(PrediBaseModel):
    ...


# X12
class X12Spec(BaseSpec):
    title: str


class X12_850(X12Spec):
    title: str = "x850"


X12TransactionList = 1
X12TransactionList: Enum = Enum("X12TransactionList", {val.__fields__["title"].default: val for val in X12Spec.__subclasses__()})

# print(X12_850.__fields__["title"].default)
# print({val.__fields__["title"].default: val for val in X12Spec.__subclasses__()})
