

from ...utils import PrediBaseModel
from . import x12
from .x12 import X12BasePredimaps


class BaseSpec(PrediBaseModel):
    ...


# print(X12_850.__fields__["title"].default)
# print({val.__fields__["title"].default: val for val in X12Spec.__subclasses__()})
