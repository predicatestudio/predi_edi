import enum
import json
import logging
from abc import ABC, abstractclassmethod, abstractmethod
from collections import UserList
from typing import Optional, Union

import tomlkit
import yaml
from pydantic import BaseModel, validator

#     Utils


class EDI_ValidationError(Exception):
    ...


# x12


class X12ValidationError(EDI_ValidationError):
    ...


class X12TrailerValidationError(X12ValidationError):
    ...


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

    def as_list(self) -> list:
        return [self.elem_term, self.elem_divider, self.seg_term]

    @classmethod
    def from_list(cls, tup: list | tuple) -> "X12Delimeters":
        return cls(elem_term=tup[0], elem_divider=tup[1], seg_term=tup[2])


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

    @staticmethod
    def _flatten_loops(loops, delimeters: X12Delimeters):
        flattened = []
        for loop in loops:
            if isinstance(loop[0], str):
                flattened.append(X12Segment.from_list(loop, delimeters))
            else:
                flattened += X12_Utils._flatten_loops(loop, delimeters)
        return flattened

    @staticmethod
    def get_loop_from_list(LoopClass: type["X12_Loop"], loops: list[list]):
        ...


class X12Doctype(enum.Enum):
    PurchaseOrder = 850


# EDIFACT


class EDIFACT_Utils:
    ...


#     Segments


class EDI_Segment(ABC):
    def is_valid(self):
        ...


# x12


class X12Segment(EDI_Segment, UserList, X12_Utils):
    seg_id: str
    delimeters: X12Delimeters

    raw_x12: str
    seg_len: Optional[int] = None

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

    def as_x12(self) -> str:
        return self.delimeters.elem_term.join(self.data) + self.delimeters.seg_term


# EDIFACT


class EDIFACT_Segment(EDI_Segment):
    ...


#     Loops

# x12


class X12_Loop(ABC, UserList, X12_Utils):
    head_id: str
    tail_id: str
    header: X12Segment
    trailer: X12Segment
    loop_contains: type["X12_Loop"]
    subloops: list["X12_Loop"] | list[X12Segment]
    data: list[Union[X12Segment, list["X12_Loop"]]] | list[X12Segment]

    ctrl_num: str

    def __init__(self, segments: list[X12Segment]):
        self._assign_loop_data(segments)
        self._assign_attrs()
        self.validate()

    def validate(self):
        # self._assign_attrs()
        self._validate_trailer()

    def _assign_loop_data(self, segments: list[X12Segment]) -> None:
        """Given the segments of the loop, assigns header, trailer, subloops, and stores loop as a list"""
        self.header = segments[0]
        self.trailer = segments[-1]
        self.subloops = self.get_seg_loops(self.loop_contains, segments)
        self.data = [self.header, self.subloops, self.trailer] # type: ignore # mypy not understaning internals of list

    @abstractmethod
    def _assign_attrs(self):
        self.num_subloops = int(self.trailer[1])

    def _validate_trailer(self):
        if not self.num_subloops == len(self.subloops):
            raise X12TrailerValidationError(
                f"""x12 loop with header and tailer
            {self.header}
            {self.trailer}
            has {len(self.subloops)} elements, but the {self.tail_id}01 is {self.num_subloops}"""
            )
        assert self.trailer[2] == self.ctrl_num


class TransactionSet(X12_Loop):
    head_id = "ST"
    tail_id = "SE"
    loop_contains: type[X12Segment] = X12Segment  # type: ignore
    subloops: list[X12Segment]

    def _assign_attrs(self):
        super()._assign_attrs()
        st_seg = self.header
        self.transaction_set_code = st_seg[1]
        self.ctrl_num = st_seg[2]
        self.data = self.subloops  # Transactionsets include header and footer

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
    # intchg_ctrl_num = ctrl_num
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


#     Documents


class EDI_Document(ABC, X12_Utils):
    @abstractclassmethod
    def from_x12(cls, doc_data: str) -> "EDI_Document":
        """Generates EDI_Document from a compliant x12 document"""
        ...

    @abstractmethod
    def as_x12(self) -> str:
        """Returns an x12 document in the form of a string"""
        ...

    @abstractclassmethod
    def from_json(cls, doc_data: str) -> "EDI_Document":
        """Generates EDI_Document from json compliant with predi-json standards.
        (json of the same format as is generated by PrEDIEncoder_JSON)"""
        ...

    @abstractmethod
    def as_json(self, indent: int | None = None) -> str:
        """Generates a predi-json compliant json string."""
        ...

    @abstractclassmethod
    def from_yaml(cls, doc_data: str) -> "EDI_Document":
        ...

    @abstractmethod
    def as_yaml(self) -> str:
        ...

    @abstractclassmethod
    def from_toml(cls, doc_data: str) -> "EDI_Document":
        ...

    @abstractmethod
    def as_toml(self) -> str:
        ...

    # @abstractclassmethod
    # def from_markup(cls, doc_data: str) -> "EDI_Document":
    #     ...

    # @abstractmethod
    # def as_markup(self) -> str:
    #     ...

    # @abstractclassmethod
    # def from_xml(cls, doc_data: str) -> "EDI_Document":
    #     ...

    # @abstractmethod
    # def as_xml(self) -> str:
    #     ...

    # @abstractclassmethod
    # def from_csv(cls, doc_data: str) -> "EDI_Document":
    #     ...

    # @abstractmethod
    # def as_csv(self) -> str:
    #     ...

    # @abstractclassmethod
    # def from_edifact(cls, doc_data: str) -> "EDI_Document":
    #     ...

    # @abstractmethod
    # def as_edifact(self) -> str:
    #     ...

    @abstractmethod
    def get_defining_attributes(self, soft: bool = False) -> list:
        ...


class X12Document(EDI_Document, UserList):
    delimeters: X12Delimeters
    raw_x12: str
    data: list[X12_Loop]
    flattened_list: list[X12Segment]

    @classmethod
    def from_x12(cls, doc_data: str) -> "X12Document":
        doc: X12Document = cls()
        doc.raw_x12 = doc_data
        doc.delimeters = doc._parse_delimeters()
        doc.flattened_list = doc._parse_x12_to_list()
        doc.data = doc.get_seg_loops(InterchangeEnvelope, doc.flattened_list)

        doc._validate_x12()
        return doc

    @classmethod
    def from_dict(cls, doc_data: dict) -> "X12Document":
        """Generates X12Document from json compliant with predi-json standards.
        (json of the same format as is generated by PrEDIEncoder_JSON)"""
        doc: X12Document = cls()
        doc.delimeters = X12Delimeters.from_list(doc_data["x12_delimeters"])
        doc.flattened_list = doc._flatten_loops(doc_data["x12"], doc.delimeters)
        # pprint([(doc.flattened_list.index(seg), seg) for seg in doc.flattened_list])
        doc.data = doc.get_seg_loops(InterchangeEnvelope, doc.flattened_list)
        doc.raw_x12 = doc.as_x12()
        doc._validate_x12()
        return doc

    @classmethod
    def from_json(cls, doc_data: str) -> "X12Document":
        """Generates X12Document from json compliant with predi-json standards.
        (json of the same format as is generated by PrEDIEncoder_JSON)"""
        data_dict = json.loads(doc_data)
        return cls.from_dict(data_dict)

    @classmethod
    def from_yaml(cls, doc_data: str) -> "X12Document":
        """Generates X12Document from yaml compliant with predi-yaml standards.
        (yaml of the same format as is generated by PrEDIEncoder_YAML)"""
        data_dict = yaml.safe_load(doc_data)
        return cls.from_dict(data_dict)

    @classmethod
    def from_toml(cls, doc_data: str) -> "X12Document":
        """Generates X12Document from toml compliant with predi-toml standards.
        (toml of the same format as is generated by PrEDIEncoder_TOML)"""
        data_dict = tomlkit.loads(doc_data)
        return cls.from_dict(data_dict)

    def _parse_delimeters(self):
        """Returns delimiters from supposed valid x12 stored in self.raw_x12"""
        elem_term, elem_divider, seg_term = self.raw_x12[103:106]
        return X12Delimeters(elem_term=elem_term, elem_divider=elem_divider, seg_term=seg_term)

    def _parse_x12_to_list(self) -> list[X12Segment]:
        segments = self.raw_x12.split(self.delimeters.seg_term)
        return [X12Segment.from_x12(seg_data=segment, delimeters=self.delimeters) for segment in segments if segment]

    def _validate_x12(self):
        assert True

    def get_defining_attributes(self, soft: bool = False) -> list:
        attrs = [
            self.data,
            self.flattened_list,
        ]
        if soft:
            return attrs + [
                self.delimeters,
                self.raw_x12,
            ]
        return attrs

    def as_x12(self) -> str:
        x12_segments = [seg.as_x12() for seg in self.flattened_list]
        x12 = "".join(x12_segments)
        return x12

    def as_dict(self) -> dict:
        return {
            "x12_delimeters": self.delimeters.as_list(),
            "x12": self.data,
        }

    def as_json(self, indent: int | None = None) -> str:
        """Generates a predi-json compliant toml string."""
        return json.dumps(self.as_dict(), cls=EDI_Serializer, indent=indent)

    def as_yaml(self) -> str:
        return yaml.safe_dump(json.loads(self.as_json()))  # This is hacky as heck

    def as_toml(self) -> str:
        """Generates a predi-json compliant toml string."""
        return tomlkit.dumps(json.loads(self.as_json()))


#     Decoders


class EDI_Decoder(ABC):
    @abstractmethod
    def decode(self, raw_edi: str) -> EDI_Document:
        ...


class X12Decoder(EDI_Decoder):
    def decode(self, raw_edi: str) -> X12Document:
        edi_doc = X12Document.from_x12(raw_edi)
        return edi_doc


class PrEDIDecoder_JSON(EDI_Decoder):
    def decode(self, raw_edi: str) -> EDI_Document:
        edi_doc = X12Document.from_json(raw_edi)
        return edi_doc


class PrEDIDecoder_YAML(EDI_Decoder):
    def decode(self, raw_edi: str) -> EDI_Document:
        edi_doc = X12Document.from_yaml(raw_edi)
        return edi_doc


class PrEDIDecoder_TOML(EDI_Decoder):
    def decode(self, raw_edi: str) -> EDI_Document:
        edi_doc = X12Document.from_toml(raw_edi)
        return edi_doc


#     Encoders


class EDI_Encoder(ABC):
    def __init__(self, indent: int = None):
        self.indent = indent

    @abstractmethod
    def encode(self, edi_doc: EDI_Document) -> str:
        ...


class X12Encoder(EDI_Encoder):
    def encode(self, edi_doc: EDI_Document) -> str:
        return edi_doc.as_x12()


class PrEDIEncoder_JSON(EDI_Encoder):
    def encode(self, edi_doc: EDI_Document) -> str:
        return edi_doc.as_json(indent=self.indent)


class PrEDIEncoder_YAML(EDI_Encoder):
    def encode(self, edi_doc: EDI_Document) -> str:
        return edi_doc.as_yaml()


class PrEDIEncoder_TOML(EDI_Encoder):
    def encode(self, edi_doc: EDI_Document) -> str:
        return edi_doc.as_toml()


# Helpers


class EDI_Serializer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UserList):
            return obj.data
        return obj


class EDI_Standard(ABC):
    name: str
    decoder: EDI_Decoder
    encoder: EDI_Encoder
    file_suffix: str


class X12Standard(EDI_Standard):
    name = "x12"
    decoder = X12Decoder()
    encoder = X12Encoder()
    file_suffix = ".edi"


class PrEDI_JSONStandard(EDI_Standard):
    name = "json"
    decoder = PrEDIDecoder_JSON()
    encoder = PrEDIEncoder_JSON(indent=2)
    file_suffix = ".json"


class PrEDI_YAMLStandard(EDI_Standard):
    name = "yaml"
    decoder = PrEDIDecoder_YAML()
    encoder = PrEDIEncoder_YAML()
    file_suffix = ".yaml"


class PrEDI_TOMLStandard(EDI_Standard):
    name = "toml"
    decoder = PrEDIDecoder_TOML()
    encoder = PrEDIEncoder_TOML()
    file_suffix = ".toml"


class Standards(enum.Enum):
    x12 = X12Standard()
    json = PrEDI_JSONStandard()
    yaml = PrEDI_YAMLStandard()
    toml = PrEDI_TOMLStandard()


def get_standard(edi_lang: str):
    return Standards[edi_lang].value


def guess_edi_standard(edi) -> EDI_Standard:
    # standards = Standards()
    standard: EDI_Standard = Standards.x12.value  # logic needs to go here for guessing
    logging.warning(f"Guessing EDI standard. guess: {standard.name}")
    return standard
