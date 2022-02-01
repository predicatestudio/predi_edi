from collections import OrderedDict, UserList
import logging
from pathlib import Path
from pprint import pprint
from time import time
from typing import Optional, Union
from abc import ABC, abstractmethod
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
    def get_seg_loops(LoopClass: type["X12_Loop"], segments: list["X12Segment"]) -> list["X12_Loop"]:
        loops: list = []
        loop: list = []
        loop_active: bool = False
        for seg in segments:
            if seg.seg_id == LoopClass.head_id:
                loop_active = True
            if loop_active:
                loop.append(seg)
            if seg.seg_id == LoopClass.tail_id:
                loops.append(LoopClass(loop.copy()))
                loop.clear()
                loop_active = False
        return loops


## Segments


class EDI_Segment(ABC):
    def is_valid(self):
        pass


class X12Segment(EDI_Segment, UserList, X12_Utils):
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
    def from_x12(cls, seg_data: str, delimeters: X12Delimeters) -> "X12Segment":
        seg: X12Segment = cls()
        seg.delimeters = delimeters
        seg.data = seg_data.split(delimeters.elem_term)
        seg.seg_id = seg.data[0]
        seg.raw_x12 = seg.as_x12()
        return seg

    @classmethod
    def from_list(cls, seg_data: list, delimeters: X12Delimeters):
        seg: X12Segment = cls()
        seg.delimeters = delimeters
        seg.data = seg_data
        seg.seg_id = seg.data[0]
        seg.raw_x12 = seg.as_x12()
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
    def from_x12(cls, seg_data: str, delimeters=None) -> "ISASegment":
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
    def from_list(cls, seg_data: list, delimeters: X12Delimeters):  # elem_term: str = "*", seg_term: str = "~"):
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

        isa.delimeters = delimeters

        isa.raw_x12 = isa.delimeters.elem_term.join(seg_data) + isa.delimeters.seg_term
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


class EDI_Document(ABC, X12_Utils):
    x12_name: int
    edifact_name: str

    def as_yaml(self):
        pass

    def as_json(self):
        pass

    def as_toml(self):
        pass

    def as_markup(self):
        pass

    def as_xml(self):
        pass

    def as_csv(self):
        pass

    def as_x12(self):
        pass

    def as_edifact(self):
        pass


class X12_Loop(ABC, UserList, X12_Utils):
    head_id: str
    tail_id: str
    header: X12Segment
    trailer: X12Segment
    loop_contains: type["X12_Loop"]
    subloops: list["X12_Loop"] | list[X12Segment]
    data: list[Union[X12Segment, list["X12_Loop"]]]

    ctrl_num: str

    def __init__(self, segments: list[X12Segment]):
        self._assign_loop_data(segments)
        self._assign_attrs()
        self.validate()

    def validate(self):
        # self._assign_attrs()
        self._validate_trailer()

    def _assign_loop_data(self, segments) -> None:
        """Given the segments of the loop, assigns header, trailer, subloops, and stores loop as a list"""
        self.header = segments[0]
        self.trailer = segments[-1]
        self.subloops = self.get_seg_loops(self.loop_contains, segments)
        self.data = [self.header, self.subloops, self.trailer]

    @abstractmethod
    def _assign_attrs(self):
        self.num_subloops = int(self.trailer[1])

    def _validate_trailer(self):
        assert self.num_subloops == len(self.subloops)
        assert self.trailer[2] == self.ctrl_num

    def as_nested_loops(self):
        return self
        return [loop.as_nested_loops() for loop in self.subloops]


class TransactionSet(X12_Loop):
    head_id = "ST"
    tail_id = "SE"
    loop_contains: type[X12Segment] = X12Segment  # type: ignore

    def _assign_attrs(self):
        super()._assign_attrs()
        st_seg = self.header
        self.transaction_set_code = st_seg[1]
        self.ctrl_num = st_seg[2]

    def as_nested_loops(self):
        return self.data

    def get_seg_loops(self, _, segments):
        return segments


class FunctionalGroup(X12_Loop):
    head_id = "GS"
    tail_id = "GE"
    subloops: list[TransactionSet]  # type: ignore
    loop_contains = TransactionSet

    func_id: str
    sender_id: str
    receiver_id: str
    date: str
    time: str

    resp_agency: str
    version_code: str

    def validate(self):
        self._assign_attrs()
        self._validate_trailer()

    def _assign_attrs(self):
        super()._assign_attrs()
        gs_seg = self.header
        self.func_id = gs_seg[1]
        self.sender_id = gs_seg[2]
        self.receiver_id = gs_seg[3]
        self.date = gs_seg[4]
        self.time = gs_seg[5]
        self.ctrl_num = gs_seg[6]
        self.resp_agency = gs_seg[7]
        self.version_code = gs_seg[8]
        # self.subloops = self.get_seg_loops(self.loop_contains)


class InterchangeEnvelope(X12_Loop):
    head_id = "ISA"
    tail_id = "IEA"
    subloops: list[FunctionalGroup]  # type: ignore
    loop_contains = FunctionalGroup

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

    intchg_control_number: str
    acknowledgment_requested: str
    test_indicator: str

    def validate(self):
        self._assign_attrs()
        self._validate_trailer()

    def _assign_attrs(self):
        super()._assign_attrs()
        isa_seg = self.header
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
        self.ctrl_num = isa_seg[13]
        self.acknowledgment_requested = isa_seg[14]
        self.test_indicator = isa_seg[15]

        # self.subloops = self.get_seg_loops(self.loop_contains)


class X12_Document(EDI_Document, UserList):
    doc_type: X12Doctype
    delimeters: X12Delimeters
    raw_x12: str
    isa: "ISASegment"
    loops: list[X12_Loop]

    @classmethod
    def from_x12(cls, doc_data: str):
        doc: X12_Document = cls()
        doc.raw_x12 = doc_data
        doc.isa = doc._parse_isa(doc_data)
        doc.delimeters = doc.isa.delimeters
        doc.data = doc._parse_doc_to_list()
        doc.loops = doc.get_seg_loops(InterchangeEnvelope, doc.data)

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


## Settings


## Decoders


class EDI_Decoder(ABC):
    @abstractmethod
    def parse(self, raw_edi: Path) -> EDI_Document:
        pass

    @abstractmethod
    def parses(self, raw_edi: str) -> EDI_Document:
        pass


class X12Decoder(EDI_Decoder):
    # @staticmethod
    # def _parse_isa(x12: str):
    #     return ISASegment.from_x12(seg_data=x12[:106])

    # def __init__(self, x12_delimeters: X12Delimeters = None) -> None:
    #     # self.x12_delimeters = x12_delimeters or X12Delimeters()
    #     pass

    def parse(self, raw_edi: Path) -> X12_Document:
        with raw_edi.open("r") as f:
            return self.parses(f.read())

    def parses(self, raw_edi: str) -> X12_Document:
        edi_doc = X12_Document.from_x12(raw_edi)
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
    name: str
    decoder: type[X12Decoder]
    encoder: type[X12Encoder]


class X12Standard(EDI_Standard):
    name = "X12"
    decoder = X12Decoder
    encoder = X12Encoder


class Standards(enum.Enum):
    X12 = X12Standard()


def guess_edi_standard(edi) -> EDI_Standard:
    # standards = Standards()
    standard: EDI_Standard = Standards.X12.value  # logic needs to go here for guessing
    logging.warning(f"Guessing EDI standard. guess: {standard.name}")
    return standard
