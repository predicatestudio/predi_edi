import functools
import json
import logging
from abc import abstractclassmethod
from datetime import date
from enum import Enum

from predi.edi import X12Document
from predi.utils import PrediBaseModel, get_nested_subclasses
from pydantic import PositiveInt, validator


class X12MapDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        _type = obj.get("_type")
        if _type is None:
            print("I'm None!")
            return obj

        del obj["_type"]  # Delete the `_type` key as it isn't used in the models

        class_map = get_nested_subclasses(X12BaseModel)  # Create a look-up object to avoid an if-else chain
        return class_map[_type].parse_obj(obj)


class X12BaseModel(PrediBaseModel):
    """A Model class to be used by all sub-models used in an x12 transaction"""

    class Config:
        json_loads: functools.partial(json.loads, cls=X12MapDecoder)

    def dict(self, *, include_type=True, **kwargs):
        super_dict = super().dict(**kwargs)
        if include_type:
            super_dict["_type"] = type(self).__name__
        return super_dict


class X12Field(X12BaseModel):
    """An x12 feature that isn't a component."""

    ...


class Options(X12Field):
    """Options are used to validate incoming data.

    Arguments:
    values -- A list of approved values for this field
    exhaustive -- Toggles strict checking
    """

    values: list[str]
    exhaustive: bool = False

    def validate_options(self, edi_data):
        """Enforces a check based on these options. Returns the value or raises an error."""
        if edi_data in self.values:
            return edi_data
        if not self.exhaustive:
            logging.warning(f"An undocumented option {edi_data} was parsed from an x12 document. Consider expanding the mapping options.")
            return edi_data
        raise Exception(f"An undocumented option {edi_data} was parsed from an x12 document. Strict checking is enabled for this option.")


class CodedOptions(Options):
    """Coded options validate and optionally translate incoming data.

    Arguments:
    values -- A list of approved values for this field
    exhaustive -- Toggles strict checking
    decode -- Toggles translation based on values
    """

    values: dict[str | int, str]
    exhaustive: bool = True
    decode: bool = True

    def validate_options(self, edi_data):
        """Enforces a check based on these options. Returns the value, decoded value, or raises an error."""
        if edi_data in self.values.keys():
            if self.decode:
                return self.values[edi_data]
            return edi_data
        if not self.exhaustive:
            logging.warning(f"An undocumented option {edi_data} was parsed from an x12 document. Consider expanding the mapping options.")
            return edi_data
        raise Exception(f"An undocumented option {edi_data} was parsed from an x12 document. Strict checking is enabled for this option.")


class Reference(X12Field):
    """A pointer to another element to dynamically select keys.

    Arguments:
    reference_name -- A key who's value will replace this element's key
    delete_on_use -- A flag to delete the reference
    """

    reference_name: str
    delete_on_use: bool = True

    def acquire(self, referenced_data: dict) -> tuple[str, dict]:
        """Returns a tuple of the referenced value and the referenced data. Referenced key is deleted if self.delete_on_use."""
        if self.delete_on_use:
            return (referenced_data.pop(self.reference_name), referenced_data)
        else:
            return (referenced_data[self.reference_name], referenced_data)


class NestingRules(X12Field):
    """A set of rules to nest data during parsing

    Argumens:
    name -- A string or Reference object to serve as the key to the nested data.
            None will default to this element's name.
    as_list -- A flag to allow multiple values to be stored as a list."""

    name: str | Reference = None
    as_list: bool = True


class X12Component(X12BaseModel):
    """The core features of an x12 transaction. Namely, segments, elements, and loops."""

    id: str | int
    name: str | None = None
    required: bool = False
    nesting: NestingRules = None

    class Config:
        json_encoders = {
            "X12BaseModel": lambda obj: dict(_type=type(obj).__name__, **obj.dict(exclude_defaults=True)),
            "Segment": lambda obj: dict(_type=type(obj).__name__, **obj.dict(exclude_defaults=True)),
            "Element": lambda obj: dict(_type=type(obj).__name__, **obj.dict(exclude_defaults=True)),
            list: lambda obj: list(
                dict(_type=type(elem).__name__, **elem.dict(exclude_defaults=True)) for elem in obj if isinstance(obj, X12BaseModel)
            ),
        }
        json_loads: functools.partial(json.loads, cls=X12MapDecoder)

    def nest_data(self, component_data, extracted_data):
        """Takes parsed edi data from this component and the data that has already been extracted from the superior loop or transaction.
        Returns the transaction data with parsed data nested within according to nesting rules."""
        # get the name or the referenced name
        name = self.nesting.name if self.nesting.name else self.name
        if isinstance(name, Reference):
            name, component_data = name.acquire(referenced_data=component_data)
        # nest data
        if self.nesting.as_list:
            # get and add to existing list
            if name in extracted_data:
                extracted_data[name].append(component_data)
            else:
                extracted_data[name] = [component_data]
        else:
            extracted_data[name] = component_data
        return extracted_data

    @abstractclassmethod
    def parse_data(self, edi_data):
        """Removes an instance of this component from the edi_data and returns the parsed data a remaining edi_data"""
        ...


class Element(X12Component):
    id: int
    options: Options | None = None

    def parse_data(self, edi_data):
        # print(self)
        if self.options:
            edi_data = self.options.validate_options(edi_data)
        return {self.name: edi_data}


class QualifiedElement(Element):
    qualifier_tag: str

    def qualify_name(self, qualified_name):
        self.name = qualified_name


class BlankElement(Element):
    """This element will not be parsed"""

    error_on_value: bool = False

    def parse_data(self, edi_data):
        if edi_data:
            if self.error_on_value:
                raise Exception("I'm supposed to be blank")
            else:
                logging.warning(f"A blank element contained data {edi_data}")
        return {}


class Segment(X12Component):
    id: str
    max_use: PositiveInt | None
    elements: list[Element]

    class Config:
        json_encoders = {
            "X12BaseModel": lambda obj: dict(_type=type(obj).__name__, **obj.dict(exclude_defaults=True)),
            "Segment": lambda obj: dict(_type=type(obj).__name__, **obj.dict(exclude_defaults=True)),
            "Element": lambda obj: dict(_type=type(obj).__name__, **obj.dict(exclude_defaults=True)),
            list: lambda obj: list(
                dict(_type=type(elem).__name__, **elem.dict(exclude_defaults=True)) for elem in obj if isinstance(obj, X12BaseModel)
            ),
        }

    def parse_data(self, edi_data):
        mapping = {}
        edi_segment_data = edi_data.pop(0)
        if not self.id.lower() == edi_segment_data[0].lower():
            return Exception, edi_segment_data + edi_data
        for map_element, data_element in zip(self.elements, edi_segment_data[1:]):
            if isinstance(map_element, QualifiedElement):
                qualified_name = mapping.pop(map_element.qualifier_tag)
                map_element.qualify_name(qualified_name=qualified_name)
            el_mapping = map_element.parse_data(data_element)
            mapping.update(el_mapping)

        return mapping, edi_data


class Loop(X12Component):
    id: str
    max_use: PositiveInt | None
    components: list[Segment, "Loop"]

    def parse_data(self, edi_data):
        loop_data = {}
        for component in self.components:
            component_usages = 0
            while not component_usages == component.max_use:
                if component.id == edi_data[0][0]:
                    # print(current_segment[1:])
                    component_data, edi_data = component.parse_data(edi_data)
                    loop_data.update(component_data)
                    component_usages += 1
                else:
                    break

        return loop_data, edi_data


class X12PrediMap(X12BaseModel):
    author: str
    title: str
    version: str
    version_date: date | None
    predimap_version: str
    components: list[X12Component]


class X12_850(X12PrediMap):
    @validator("components")
    def is_850(cls, v):
        assert isinstance(v, list)
        return v


X12BasePredimaps: Enum = Enum("X12TransactionList", {val.__name__: val for val in X12PrediMap.__subclasses__()})


class X12_Mapper:
    def __init__(self, map: X12PrediMap = None):
        self.map = map

    def parse_data(self, x12_document: X12Document, map=None):
        # These two are not currently implemented, but should be utilized in the future
        interchange_envelope = [x12_document[0][0], x12_document[0][-1]]
        functional_group = [x12_document[0][1][0][0], x12_document[0][1][0][-1]]
        transaction_sets = x12_document[0][1][0][1]
        transactions = []
        transaction_data = {}

        map = map if map else self.map
        for transaction in transaction_sets:
            for component in map.components:
                component_usages = 0
                while not component_usages == component.max_use:
                    if component.id == transaction[0][0]:
                        component_data, transaction = component.parse_data(transaction)
                        if component.nesting:
                            transaction_data = component.nest_data(component_data, transaction_data)
                        else:
                            transaction_data.update(component_data)
                        component_usages += 1
                    else:
                        break
            transactions.append(transaction_data)
            transaction_data = {}
        return transactions
