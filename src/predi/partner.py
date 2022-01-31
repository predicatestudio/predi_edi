import json
from typing import IO
import yaml
import markupsafe
from abc import ABC
import dataclasses
import enum
from .edi import EDI_Document
from pydantic import BaseModel


class Partner:
    # TODO make dataclass

    def __init_(self, name: str, email: str, address: str = None):
        self.name = name
        self.email = email
        self.address = address


class PartnerMap:
    def __init__(self, partner: Partner, document_type: EDI_Document):
        self.partner = partner
        self.document_type = document_type
