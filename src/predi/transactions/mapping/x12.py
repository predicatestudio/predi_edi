import logging
from datetime import date
from enum import Enum
from typing import Optional

from predi.edi import X12Document
from predi.utils import PrediBaseModel
from pydantic import PositiveInt, validator


class X12Field(PrediBaseModel):
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
    reference_name: str
    delete_on_use: bool = True

    def acquire(self, referenced_data: dict) -> tuple[str, dict]:
        """Returns a tuple of the referenced value and the referenced data. Referenced key is deleted if self.delete_on_use."""
        if self.delete_on_use:
            return (referenced_data.pop(self.reference_name), referenced_data)
        else:
            return (referenced_data[self.reference_name], referenced_data)


class NestingRules(X12Field):
    name: str | Reference = None
    as_list: bool = True


class X12Component(PrediBaseModel):
    id: str | int
    name: Optional[str] = None
    required: bool = False
    # reference_tag: Optional[str] = None
    nesting: NestingRules = None

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

    def parse(self, edi_data):
        raise NotImplementedError


class Element(X12Component):
    id: int
    options: Optional[Options] = None

    def parse(self, edi_data):
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

    def parse(self, edi_data):
        if edi_data:
            if self.error_on_value:
                raise Exception("I'm supposed to be blank")
            else:
                logging.warning(f"A blank element contained data {edi_data}")
        return {}


class Segment(X12Component):
    id: str
    max_use: Optional[PositiveInt]
    elements: list[Element]

    def parse(self, edi_data):
        mapping = {}
        edi_segment_data = edi_data.pop(0)
        if not self.id.lower() == edi_segment_data[0].lower():
            return Exception, edi_segment_data + edi_data
        for map_element, data_element in zip(self.elements, edi_segment_data[1:]):
            if isinstance(map_element, QualifiedElement):
                qualified_name = mapping.pop(map_element.qualifier_tag)
                map_element.qualify_name(qualified_name=qualified_name)
            el_mapping = map_element.parse(data_element)
            mapping.update(el_mapping)

        #     el_map_name, el_map_value = map_element.parse(data_element)
        #     if isinstance(map_element, BlankElement):
        #         continue
        #     elif isinstance(map_element, QualifiedElement):
        #         el_map_name = mapping.pop(map_element.qualifier_tag)

        #     mapping[el_map_name] = el_map_value
        # print(mapping)
        return mapping, edi_data


class Loop(X12Component):
    id: str
    max_use: Optional[PositiveInt]
    components: list[Segment, "Loop"]

    def parse(self, edi_data):
        # raise NotImplementedError
        loop_data = {}
        for component in self.components:
            component_usages = 0
            while not component_usages == component.max_use:
                if component.id == edi_data[0][0]:
                    # print(current_segment[1:])
                    component_data, edi_data = component.parse(edi_data)
                    loop_data.update(component_data)
                    component_usages += 1
                else:
                    break

        return loop_data, edi_data


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


class X12_Mapper:
    def __init__(self, map: X12PrediMap = None):
        self.map = map

    def parse(self, x12_document: X12Document, map=None):
        interchange_envelope = [x12_document[0][0], x12_document[0][-1]]
        functional_group = [x12_document[0][1][0][0], x12_document[0][1][0][-1]]
        transaction_sets = x12_document[0][1][0][1]
        transactions = []
        transaction_data = {}

        map = map if map else self.map
        for transaction in transaction_sets:
            # print(current_segment)
            for component in map.components:
                component_usages = 0
                while not component_usages == component.max_use:
                    if component.id == transaction[0][0]:
                        # print(current_segment[1:])
                        component_data, transaction = component.parse(transaction)
                        if component.nesting:
                            transaction_data = component.nest_data(component_data, transaction_data)
                        else:
                            transaction_data.update(component_data)
                        component_usages += 1
                    else:
                        break
        return transaction_data

        # print(type(x12_document[0][1][0][1]))
        # return transaction_sets
        # return (self.map.components)


# print(X12_850.__fields__["title"].default)
# print({val.__fields__["title"].default: val for val in X12PrediMap.__subclasses__()})
