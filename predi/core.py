import json
from typing import IO
import yaml
import markupsafe
# from abc import ABC
import dataclasses
import enum

class EDI_Document():
    def init(self):
        self.x12_name: int = None
        self.edifact_name: str = None

    def as_yaml():
        pass

    def as_json():
        pass

    def as_markup():
        pass

class Partner():
    #TODO make dataclass

    def __init_(self, name: str, email: str, address: str = None):
        self.name = name
        self.email = email
        self.address=address

class PartnerMap():
    def __init__(self, partner: Partner, document_type: EDI_Document):
        self.partner = partner
        self.document_type = document_type

class TransactionMap():
    pass

class PurchaseOrder(EDI_Document):
    pass

class X12_Delfimeters():
    def __init__(self, segment_terminator="~", element_terminator="*", element_divider="'") -> None:
        self.segment = segment_terminator
        
class ISASegment():
    pass

class EDIParser():
    def __init__(self, x12_delimeters: X12_Delfimeters = None) -> None:
        self.x12_delimeters = x12_delimeters
    
    def _parse_isa(self, x12:IO):
        isa = ISASegment
        isa.elem_sep = x12[3]
        isa.rep_sep = x12[82]
        isa.comp_elem_sep = x12[104]
        isa.seg_term = x12[105]

        return isa

    def parse(self, x12: IO, str):
        if type(x12) == IO:
            x12 = x12.read()
        isa = self._parse_isa(x12)
        


