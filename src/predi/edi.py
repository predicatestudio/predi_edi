from collections import OrderedDict, UserList
import json
import logging
from pathlib import Path
from pprint import pprint
from time import time
from typing import  Optional
import yaml
import markupsafe
from abc import ABC, abstractclassmethod, abstractmethod
import dataclasses
import enum
from pydantic import BaseModel, validator


class EDI_ValidationError(Exception):
    pass


class X12ValidationError:
    pass


class X12Delimeters(BaseModel):
    elem_term: str  # = "*"
    elem_divider: str  # = ":"
    seg_term: str  # = "~"

    @validator("*")
    def check_single_char(cls, v):
        if len(v) != 1:
            raise ValueError(f"Delimiters must be a single char.\n{v=} has length of {len(v)}")
        return v

    @validator("*")
    def check_no_duplicates(cls, v, values, field):
        # del values[field]
        if v in values.values():
            raise ValueError(f"Delimiters cannot be used twice.\nSee: {v=}")
        return v


class X12Doctype(enum.Enum):
    PurchaseOrder = 850


## Documents
class X12_Utils:
    @staticmethod
    def get_seg_loops(LoopClass: type["X12_Loop"], segments: list["X12Segment"]) -> list[list["X12_Loop"]]:
        loops: list = []
        loop: list = []
        loop_active: bool = False
        for seg in segments:
            if seg.seg_id == LoopClass.head_id:
                loop_active = True
            if loop_active:
                loop.append(seg)
            if seg.seg_id == LoopClass.tail_id:
                loops.append(LoopClass(loop))
                loop.clear()
                loop_active = False
        return loops


class EDI_Document(ABC, X12_Utils):
    x12_name: int
    edifact_name: str

    def as_yaml():
        pass

    def as_json():
        pass

    def as_toml():
        pass

    def as_markup():
        pass

    def as_xml():
        pass

    def as_csv():
        pass



class X12_Loop(ABC, UserList, X12_Utils):
    head_id: str
    tail_id: str
    header: "EDI_Segment"
    trailer: "EDI_Segment"
    subloops: "X12_Loop"

    def __init__(self, data: Optional[list["X12Segment"]] = None):
        self.data = data
        if data:
            self.validate()

    def _assign_attrs(self):
        self.header = self.data[0]
        self.trailer = self.data[-1]

    @abstractmethod
    def validate(self):
        self._assign_attrs()

    def get_seg_loops(self, LoopClass: type["X12_Loop"]):
        return super().get_seg_loops(LoopClass=LoopClass, segments=self.data)

    def as_nested_loops(self):
        return [loop.as_nested_loops() for loop in self.subloops]

    def _validate_trailer(self):
        assert int(self.trailer[1]) == len(self.subloops)
        assert self.trailer[2] == self.ctrl_num

class TransactionSet(X12_Loop):
    head_id = "ST"
    tail_id = "SE"
    # subloops = None

    def validate(self):
        self._assign_attrs()
        self._validate_trailer()

    def _assign_attrs(self):
        super()._assign_attrs()
        st_seg = self.data[0]
        self.transaction_set_code = st_seg[1]
        self.ctrl_num = st_seg[2]
        self.subloops = self.data
        # self.subloops = self.get_seg_loops(TransactionSet)

    def _validate_trailer(self):

        assert int(self.trailer[1]) == len(self.data)
        assert self.trailer[2] == self.ctrl_num

    def as_nested_loops(self):
        return self.data

    

class FunctionalGroup(X12_Loop):
    head_id = "GS"
    tail_id = "GE"
    subloops: list[TransactionSet]

    func_id: str
    sender_id: str
    receiver_id: str
    date: str
    time: str
    ctrl_num: str
    resp_agency: str
    version_code: str

    def validate(self):
        self._assign_attrs()
        self._validate_trailer()

    def _assign_attrs(self):
        super()._assign_attrs()
        gs_seg = self.data[0]
        self.func_id = gs_seg[1]
        self.sender_id = gs_seg[2]
        self.receiver_id = gs_seg[3]
        self.date = gs_seg[4]
        self.time = gs_seg[5]
        self.ctrl_num = gs_seg[6]
        self.resp_agency = gs_seg[7]
        self.version_code = gs_seg[8]
        self.subloops = self.get_seg_loops(TransactionSet)



class InterchangeEnvelope(X12_Loop):
    head_id = "ISA"
    tail_id = "IEA"
    subloops: list[FunctionalGroup]

    authorization_info_qualifier: str
    auth_info: str
    security_info_qualifier: str
    security_info: str
    intchg_sender_id_qualifier: str
    intchg_sender_id: str
    intchg_receiver_id_qualifier: str
    intchg_receiver_id: str
    intchg_date: str
    intchg_time: str
    intchg_standards_id: str
    intchg_control_version_number: str
    intchg_control_number: str
    acknowledgment_requested: str
    test_indicator: str



    def validate(self):
        self._assign_attrs()
        self._validate_trailer()

    def _assign_attrs(self):
        super()._assign_attrs()
        isa_seg = self.data[0]
        self.seg_id = isa_seg[0]
        self.authorization_info_qualifier = isa_seg[1]
        self.auth_info = isa_seg[2]
        self.security_info_qualifier = isa_seg[3]
        self.security_info = isa_seg[4]
        self.intchg_sender_id_qualifier = isa_seg[5]
        self.intchg_sender_id = isa_seg[6]
        self.intchg_receiver_id_qualifier = isa_seg[7]
        self.intchg_receiver_id = isa_seg[8]
        self.intchg_date = isa_seg[9]
        self.intchg_time = isa_seg[10]
        self.intchg_standards_id = isa_seg[11]
        self.intchg_control_version_number = isa_seg[12]
        self.intchg_control_number = isa_seg[13]
        self.acknowledgment_requested = isa_seg[14]
        self.test_indicator = isa_seg[15]

        self.subloops = self.get_seg_loops(FunctionalGroup)

    def _validate_trailer(self):
        self.subloops = self.get_seg_loops(TransactionSet)
        ge_seg = self.data[-1]
        assert int(ge_seg[1]) == len(self.subloops)
        assert ge_seg[2] == self.ctrl_num


class X12_Document(EDI_Document, UserList):
    doc_type: X12Doctype
    delimeters: X12Delimeters
    raw_x12: str
    isa: "ISASegment"
    loops: list["FunctionalGroup"]

    @classmethod
    def from_x12(cls, doc_data: str):
        doc: X12_Document = cls()
        doc.raw_x12 = doc_data
        doc.isa = doc._parse_isa(doc_data)
        doc.delimeters = doc.isa.delimeters
        doc.data = doc._parse_doc_to_list()
        doc.loops = doc.get_seg_loops(FunctionalGroup, doc.data)

        doc._validate_x12()
        return doc

    @staticmethod
    def _parse_isa(x12: str):
        isa = ISASegment.from_x12(seg_data=x12[:106])
        return isa

    def _parse_doc_to_list(self):
        segments = self.raw_x12.split(self.delimeters.seg_term)
        return [X12Segment.from_x12(seg_data=segment, delimeters=self.delimeters) for segment in segments if segment]

    def _validate_x12(self):
        assert True

    def as_x12(self):
        x12_segments = [seg.as_x12() for seg in self.data]
        x12 = "".join(x12_segments)
        return x12


class TransactionMap:
    pass


## Segments


class EDI_Segment(ABC, X12_Utils):
    def is_valid(self):
        pass


class X12Segment(EDI_Segment, UserList):
    seg_id: str
    delimeters: X12Delimeters

    raw_x12: str
    seg_len: Optional[int] = None

    # elem_term: str
    # elem_divider: str
    # seg_term: str

    # def __init__(self):
    #     self.seg_len = len(self.data)
    #     self.elements = self.get_elements()

    # @abstractmethod
    # def get_elements(self):
    #     pass

    @classmethod
    def from_x12(cls, seg_data: str, delimeters: X12Delimeters):
        seg: X12Segment = cls()
        seg.delimeters = delimeters
        seg.data = seg_data.split(delimeters.elem_term)
        seg.seg_id = seg.data[0]
        seg.raw_x12 = seg.as_x12
        return seg

    @classmethod
    def from_list(cls, seg_data: list, delimeters: X12Delimeters):
        seg: X12Segment = cls()
        seg.delimeters = delimeters
        seg.data = seg_data
        seg.seg_id = seg.data[0]
        seg.raw_x12 = seg.as_x12
        return seg

    def as_x12(self):
        return self.delimeters.elem_term.join(self.data) + self.delimeters.seg_term


class ISASegment(X12Segment):
    """
    Interchange Control Trailer
    Contains key data for parsing and validation of the EDI document
    Should be created using a factory.
    """

    def __init__(self):
        pass

    authorization_info_qualifier: str
    auth_info: str
    security_info_qualifier: str
    security_info: str
    intchg_sender_id_qualifier: str
    intchg_sender_id: str
    intchg_receiver_id_qualifier: str
    intchg_receiver_id: str
    intchg_date: str
    intchg_time: str
    intchg_standards_id: str
    intchg_control_version_number: str
    intchg_control_number: str
    acknowledgment_requested: str
    test_indicator: str

    raw_x12: str

    @classmethod
    def from_x12(cls, seg_data: str):
        isa = cls()

        isa.seg_id = seg_data[0:3]
        isa.authorization_info_qualifier = seg_data[4:6]
        isa.auth_info = seg_data[7:17]
        isa.security_info_qualifier = seg_data[18:20]
        isa.security_info = seg_data[21:31]
        isa.intchg_sender_id_qualifier = seg_data[32:34]
        isa.intchg_sender_id = seg_data[35:50]
        isa.intchg_receiver_id_qualifier = seg_data[51:53]
        isa.intchg_receiver_id = seg_data[54:69]
        isa.intchg_date = seg_data[70:76]
        isa.intchg_time = seg_data[77:81]
        isa.intchg_standards_id = seg_data[82]
        isa.intchg_control_version_number = seg_data[84:89]
        isa.intchg_control_number = seg_data[90:99]
        isa.acknowledgment_requested = seg_data[100]
        isa.test_indicator = seg_data[102]
        # delemeters
        elem_term = seg_data[103]
        elem_divider = seg_data[104]
        seg_term = seg_data[105]
        isa.delimeters = X12Delimeters(elem_term=elem_term, elem_divider=elem_divider, seg_term=seg_term)

        isa.raw_x12 = seg_data
        isa.data = isa._parse_seg_to_list()
        isa._validate_x12()

        # isa.is_valid()
        return isa

    def _parse_seg_to_list(self):
        """Generates list data from fresh x12 data"""
        elements = self.raw_x12[:-1].split(self.delimeters.elem_term)
        return elements

    def _validate_x12(self) -> None:
        """A validation for freshly parsed x12 data."""
        assert len(self.raw_x12) == 106
        assert self.raw_x12 == self.as_x12()

    @classmethod
    def from_list(cls, seg_data: list, elem_term: str = "*", seg_term: str = "~"):
        isa = cls()

        isa.seg_id = seg_data[0]
        isa.authorization_info_qualifier = seg_data[1]
        isa.auth_info = seg_data[2]
        isa.security_info_qualifier = seg_data[3]
        isa.security_info = seg_data[4]
        isa.intchg_sender_id_qualifier = seg_data[5]
        isa.intchg_sender_id = seg_data[6]
        isa.intchg_receiver_id_qualifier = seg_data[7]
        isa.intchg_receiver_id = seg_data[8]
        isa.intchg_date = seg_data[9]
        isa.intchg_time = seg_data[10]
        isa.intchg_standards_id = seg_data[11]
        isa.intchg_control_version_number = seg_data[12]
        isa.intchg_control_number = seg_data[13]
        isa.acknowledgment_requested = seg_data[14]
        isa.test_indicator = seg_data[15]
        # delemeters

        isa.delimeters = X12Delimeters(elem_term, seg_data[16], seg_term)

        isa.raw_x12 = elem_term.join(seg_data) + seg_term
        isa.data = isa._parse_seg_to_list()
        isa._validate_x12()

        # isa.is_valid()
        return isa

    def _validate_delimeters(self):
        pass

    def is_valid(self):
        pass


class EDIFACT_Segment(EDI_Segment):
    pass


## Settings


## Decoders


class EDI_Decoder(ABC):
    pass


class X12Decoder(EDI_Decoder):
    # @staticmethod
    # def _parse_isa(x12: str):
    #     return ISASegment.from_x12(seg_data=x12[:106])

    def __init__(self, x12_delimeters: X12Delimeters = None) -> None:
        # self.x12_delimeters = x12_delimeters or X12Delimeters()
        pass

    def parse(self, x12: Path):
        with x12.open("r") as f:
            return self.parses(f.read())

    def parses(self, x12: str):
        edi_doc = X12_Document.from_x12(x12)
        return edi_doc


def main():
    x12_path = Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/sample_amz_850.edi")
    # isa = ISASegment.from_x12(x12_path.open().read())
    decoder = X12Decoder()


## Encoders


class EDI_Encoder(ABC):
    pass


class X12Encoder(ABC):
    pass


## Helper functions
class EDI_Standard:
    decoder: X12Decoder
    encoder: X12Encoder


class X12Standard(EDI_Standard):
    name = "X12"
    decoder = X12Decoder
    encoder = X12Encoder


class Standards(enum.Enum):
    X12 = X12Standard


def guess_edi_standard(edi):
    # standards = Standards()
    standard = Standards.X12.value  # logic needs to go here for guessing
    logging.warning(f"Guessing EDI standard. guess: {standard.name}")
    return standard
