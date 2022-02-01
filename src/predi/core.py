from curses import raw
import json
from typing import IO
import yaml
import markupsafe
from abc import ABC
import dataclasses
import enum
from .edi import *
from .partner import *
from pydantic import BaseModel


def load(fp: Path, decoder_cls: EDI_Decoder = None):
    return loads(
        fp.read(),
        decoder_cls=decoder_cls,
    )


def loads(s: str, decoder_cls: EDI_Decoder = None) -> EDI_Document:
    if not decoder_cls:
        decoder_cls = guess_edi_standard(s).decoder
    decoder = decoder_cls()
    return decoder.parses(s)


def dump(fp: Path, encoder: EDI_Encoder = None):
    return dumps(
        fp.read(),
        encoder=encoder,
    )


def dumps(s: str, encoder: EDI_Encoder = None):
    pass


def main():
    # print("hello from core")
    testpath = Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/sample_targetds_850.edi")
    data: X12_Document = load(testpath.open())

    pprint(data.loops[0].as_nested_loops())
